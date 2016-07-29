#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import time
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker

from fetch.api import make_request, default_requests_session
from models import SlantTopic, Viewpoint
from lock import lock_method


logger = logging.getLogger('data')


LOCK_FILENAME = '/tmp/slant-topics-fetcher.lock'
DEFAULT_PARAMS = {
    'page': 0,
    'filter': 'feed',
    'tags': 'development',
    'format': 'json',
}
SLANT_URL = "https://www.slant.co"
SLANT_TOPICS_URL = SLANT_URL + "/topics"
REQUEST_DELAY = 1


def get_slant_topics(show_progress):

    # Create a new fetch index
    last_fetch_index = SlantTopic.select(fn.Max(SlantTopic.fetch_index)).scalar() or 0
    fetch_index = last_fetch_index + 1

    params = DEFAULT_PARAMS.copy()
    first_request = True
    next_url = None
    count_of_processed_topics = 0

    # Loop through requests to the Slant server until we reach an empty
    # response or the end of the pages.
    while True:

        # All requests after our first one are made to a URL returned by
        # the previous request.  So there's a little logic here to use verbose
        # parameters for the first request.  They should be included by
        # default in all requests after that.
        if first_request:
            response = make_request(
                default_requests_session.get,
                SLANT_TOPICS_URL,
                params=params,
            )
        # We found that for some reason, the next page path is missing a parameter
        # to specify that we still want the results of the next page as JSON.
        # So we explicitly specify the format here.
        else:
            response = make_request(
                default_requests_session.get,
                next_url,
                params={'format': 'json'},
            )

        # Leave this loop if the fetch failed
        if response is None:
            break

        results = response.json()

        # If we have somehow ended up on an entry where it has an error field
        # with the 404 code, we have probably seen all results.  Break out of the loop.
        if 'error' in results and results['error'] == 404:
            break

        # If this is the first request, initialize the progress bar with
        # the number of results retrieved from the results
        if first_request and show_progress:
            progress_bar = ProgressBar(maxval=results['count'], widgets=[
                'Progress: ', Percentage(),
                ' ', Bar(marker=RotatingMarker()),
                ' ', ETA(),
                ' Fetched ', Counter(), ' / ' + str(results['count']) + ' topics.'
            ])
            progress_bar.start()

        for topic in results['children']:

            # Each child in the list is a topic.
            # Save each of these as a new topic.
            topic_record = SlantTopic.create(
                fetch_index=fetch_index,
                topic_id=topic['uuid'],
                title=topic['revision']['title'],
                url_path=topic['URL'],
                owner_username=topic['createdEvent']['user']['username'],
            )

            # A topic on Slant has a number of "viewpoints" or alternatives.
            # Save each one and a URL to the site where we can visit each one.
            for viewpoint in topic['viewpoints']['children']:
                Viewpoint.create(
                    fetch_index=fetch_index,
                    viewpoint_index=viewpoint['id'],
                    title=viewpoint['revision']['title'],
                    topic=topic_record,
                    url_path=viewpoint['URL'],
                )

            count_of_processed_topics += 1

        if show_progress:
            progress_bar.update(count_of_processed_topics)

        # We are also finished looping through results when there is no longer a 'next'
        # page in the page properties.  It's just a guess on our part that this endpoint
        # will always report a next page when there is one, as there isn't an official
        # API and there isn't any documentation for it.
        if 'next' not in results['properties']['page']:
            if show_progress:
                progress_bar.finish()
            break

        next_page_path = results['properties']['page']['next']
        next_url = SLANT_URL + next_page_path

        # Pause so that we don't bombard the server with requests
        time.sleep(REQUEST_DELAY)

        # Reset the flag that cues us to take actions for the first request
        first_request = False


@lock_method(LOCK_FILENAME)
def main(show_progress, *args, **kwargs):
    get_slant_topics(show_progress)


def configure_parser(parser):
    parser.description = "Fetch all Slant topics related to development tools."
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress of the number of topics that have been fetched."
    )
