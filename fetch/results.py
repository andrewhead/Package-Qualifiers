#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
from bs4 import BeautifulSoup
import time
import datetime
import json
import re

from lock import lock_method
from models import Search, SearchResult
from api import make_request, default_requests_session


logging.basicConfig(level=logging.INFO, format="%(message)s")
SEARCH_URL = 'https://www.googleapis.com/customsearch/v1'
REQUESTED_RESULT_COUNT = 10
DEFAULT_PARAMS = {
    'num': REQUESTED_RESULT_COUNT,  # we can request at maximum 10 search results
    'alt': 'atom',
}
REQUEST_DELAY = 1.5
LOCK_FILENAME = '/tmp/results-fetcher.lock'


def get_results_for_queries(queries, include_stack_overflow, search_id, api_key):

    # Create a new fetch index.
    last_fetch_index = Search.select(fn.Max(Search.fetch_index)).scalar() or 0
    fetch_index = last_fetch_index + 1

    for query in queries:
        get_results(query, include_stack_overflow, fetch_index, search_id, api_key)


def get_results(query, include_stack_overflow, fetch_index, search_id, api_key):

    # Make request for search results
    params = DEFAULT_PARAMS.copy()
    params['key'] = api_key
    params['cx'] = search_id
    params['q'] = query
    if not include_stack_overflow:
        params['siteSearch'] = 'stackoverflow.com'
        params['siteSearchFilter'] = 'e'  # 'e' for 'exclude'
    response = make_request(default_requests_session.get, SEARCH_URL, params=params)

    # Parse search results
    soup = BeautifulSoup(response.content, 'html.parser')
    url = soup.find('opensearch:Url')
    entry_count = len(soup.find_all('entry'))

    # The Atom spec for the search API
    # (https://developers.google.com/custom-search/json-api/v1/reference/cse/list#response)
    # mentions that the estimated results count may be a long integer.
    # To my knowledge, peewee (our ORM) doesn't support long integer fields.
    # So, I cast this to an integer instead and cross my fingers there is no overflow.
    search = Search.create(
        fetch_index=fetch_index,
        query=query,
        page_index=0,
        requested_count=REQUESTED_RESULT_COUNT,
        result_count_on_page=entry_count,
        estimated_results_count=int(
            soup.find('cse:searchinformation').find('cse:totalresults').text)
    )

    # Fetch the first "entry" or search result
    entry = soup.entry

    # Save all of the search results from first to last.
    # Maintaining consistency with our query scraping, ranking starts at 1.
    for rank in range(1, entry_count + 1):

        # Extract fields from the entry
        updated_datetime_without_milliseconds = re.sub('\.\d\d\dZ', 'Z', entry.updated.text)
        updated_datetime = datetime.datetime.strptime(
            updated_datetime_without_milliseconds,
            "%Y-%m-%dT%H:%M:%SZ"
        )
        link = entry.link['href']
        snippet = entry.summary.string
        title = entry.title.text
        url = entry.id.text

        # Create a record for this search result
        SearchResult.create(
            search=search,
            title=title,
            snippet=snippet,
            link=link,
            url=url,
            updated_date=updated_datetime,
            rank=rank,
        )

        # To my knowledge, this is the only method for which it is strongly implied in
        # the BeautifulSoup documentation that you are fetching the next result
        # in the sequence.  I also assume that the search API is returning results
        # in the order of decreasing relevance, such that rank increases (gets bigger)
        # with each successive entry visited.
        entry = entry.find_next('entry')

    # Pause so that we don't bombard the server with requests
    time.sleep(REQUEST_DELAY)


@lock_method(LOCK_FILENAME)
def main(queries, google_config, include_stack_overflow, *args, **kwargs):

    with open(google_config) as google_config_file:
        config = json.load(google_config_file)
        search_id = config['search_id']
        api_key = config['api_key']

    with open(queries) as queries_file:
        queries = [l.strip() for l in queries_file]
        get_results_for_queries(queries, include_stack_overflow, search_id, api_key)


def configure_parser(parser):

    parser.description = "fetch top search results for a set of packages"
    parser.add_argument('queries', help="the name of a file containing a list of queries")
    parser.add_argument(
        'google_config',
        metavar='google-config',
        help="a file with keys to a Google APIs custom search engine"
    )

    # In case Stack Overflow dominates the search results, this flag
    # will allow the caller to query only for results that are not from Stack Overflow.
    parser.add_argument(
        '--include-stack-overflow',
        action='store_true',
        help="Include results from the domain stackoverflow.com"
    )
