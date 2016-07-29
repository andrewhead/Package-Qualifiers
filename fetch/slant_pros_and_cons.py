#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import time
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker

from fetch.api import make_request, default_requests_session
from models import Viewpoint, ViewpointSection
from lock import lock_method


logger = logging.getLogger('data')


LOCK_FILENAME = '/tmp/slant-pros-and-cons-fetcher.lock'
SLANT_URL = "https://www.slant.co"
REQUEST_DELAY = 1


def get_slant_pros_and_cons(show_progress):

    # Create a new fetch index
    last_fetch_index = ViewpointSection.select(fn.Max(ViewpointSection.fetch_index)).scalar() or 0
    fetch_index = last_fetch_index + 1

    # Get the index of the latest fetch of topics and viewpoints.
    # We will only collect pros and cons for this set of topics.
    viewpoint_fetch_index = Viewpoint.select(fn.Max(Viewpoint.fetch_index)).scalar() or 0
    latest_viewpoint_batch = (
        Viewpoint
        .select()
        .where(Viewpoint.fetch_index == viewpoint_fetch_index)
    )

    # Initialize the progress bar if requested
    if show_progress:
        viewpoint_count = latest_viewpoint_batch.count()
        progress_bar = ProgressBar(maxval=viewpoint_count, widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Collected pros and cons for viewpoint ',
            Counter(), ' / ' + str(viewpoint_count) + '.'
        ])
        progress_bar.start()

    # For every viewpoint, fetch and save all pros and cons
    for viewpoint_index, viewpoint in enumerate(latest_viewpoint_batch, start=1):

        # Without the format=json parameter, the Slant server will return
        # HTML for the viewpoint.  We get something resembling a JSON API
        # response if we ask for JSON format.
        response = make_request(
            default_requests_session.get,
            SLANT_URL + viewpoint.url_path,
            params={'format': 'json'},
        )

        # Skip all missing responses
        if response is None:
            continue

        results = response.json()

        # If we have somehow ended up on an entry where it has an error field
        # with the 404 code, something was probably wrong with the request.
        # Just skip this entry and move on.
        if 'error' in results and results['error'] == 404:
            logger.warn("Got 404 when retrieving viewpoint with path %s.", viewpoint.url_path)
            break

        # Each 'section' for a view point is a pro or a con.  Save a record for each one.
        for section in results['sections']['children']:

            ViewpointSection.create(
                fetch_index=fetch_index,
                viewpoint=viewpoint,
                section_index=section['id'],
                title=section['revision']['title'],
                text=section['revision']['text'],
                is_con=section['isCon'],
                upvotes=section['votes']['upvotes'],
                downvotes=section['votes']['downvotes'],
            )

        if show_progress:
            progress_bar.update(viewpoint_index)

        # Pause so that we don't bombard the server with requests
        time.sleep(REQUEST_DELAY)

    if show_progress:
        progress_bar.finish()


@lock_method(LOCK_FILENAME)
def main(show_progress, *args, **kwargs):
    get_slant_pros_and_cons(show_progress)


def configure_parser(parser):
    parser.description =\
        "Fetch all pro / con feedback for Slant topics.  " +\
        "This module assumes you have already fetched data for Slant topics " +\
        "with the 'slant_topics' command.  Pros and cons will be retrieved for the " +\
        "latest version of the topics and viewpoints data that you fetched."
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress of the number of viewpoints for which pros/cons have been fetched."
    )
