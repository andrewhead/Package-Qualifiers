#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import time
import datetime

from fetch.api import make_request, default_requests_session
from lock import lock_method
from models import SearchResult, WebPageVersion


logger = logging.getLogger('data')
ARCHIVE_URL = 'http://web.archive.org/cdx/search/cdx'
DEFAULT_PARAMS = {
    'limit': 50,  # default page size for CDX pagination
    'output': 'json',
    'showResumeKey': 'true',  # lightweight pagination of results
}
REQUEST_DELAY = 1.5
LOCK_FILENAME = '/tmp/histories-fetcher.lock'


def get_history(url, fetch_index):

    params = DEFAULT_PARAMS.copy()
    params['url'] = url

    # Flags for controlling paging and scanning results
    more_results = True
    watch_for_resume_key = False

    while more_results:

        more_results = False
        response = make_request(default_requests_session.get, ARCHIVE_URL, params=params)
        time.sleep(REQUEST_DELAY)  # Pause so that we don't bombard the server with requests

        if response is None:
            break
        results = response.json()

        for result_index, result in enumerate(results):

            # Read the field names from the first result
            if result_index == 0:
                field_names = result
                continue

            # Resumption key appears after one blank record after the rest of the records
            # These two lines keep watch for the resumption key and exit the loop once
            # it has been found.
            if result == []:
                watch_for_resume_key = True
                continue
            elif watch_for_resume_key:
                # Setting this parameter advances the page of results for the next query
                params['resumeKey'] = result[0]
                more_results = True
                watch_for_resume_key = False
                break

            # If the code has made it this far, this record is a web
            # page version, and we want to save it.
            data = dict(zip(field_names, result))
            _save_record(url, data, fetch_index)


def _save_record(url, record, fetch_index):

    # Convert string for the timestamp into a proper datetime object
    timestamp_datetime = datetime.datetime.strptime(
        record['timestamp'],
        '%Y%m%d%H%M%S',
    )

    # We'll create a new record for the version only if it doesn't yet exist.
    try:
        WebPageVersion.get(
            url=url,
            timestamp=timestamp_datetime,
        )
    except WebPageVersion.DoesNotExist:
        WebPageVersion.create(
            fetch_index=fetch_index,
            url=url,
            url_key=record['urlkey'],
            timestamp=timestamp_datetime,
            original=record['original'],
            mime_type=record['mimetype'],
            status_code=record['statuscode'],
            digest=record['digest'],
            length=record['length'],
        )


@lock_method(LOCK_FILENAME)
def main(*args, **kwargs):

    # Create a new fetch index.
    last_fetch_index = WebPageVersion.select(fn.Max(WebPageVersion.fetch_index)).scalar() or 0
    fetch_index = last_fetch_index + 1
    search_results = SearchResult.select(SearchResult.url).distinct()
    for search_result in search_results:
        get_history(search_result.url, fetch_index)


def configure_parser(parser):
    parser.description = "Get Internet Archive histories for all stored search results."
