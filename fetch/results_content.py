#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import time
from peewee import JOIN_LEFT_OUTER

from fetch.api import make_request, default_requests_session
from models import Search, SearchResult, SearchResultContent


logging.basicConfig(level=logging.INFO, format="%(message)s")
DELAY_TIME = 0.5


def get_results_content(fetch_all, fetch_indexes):

    if fetch_all:
        results = SearchResult.select()
    elif fetch_indexes:
        results = (
            SearchResult
            .select()
            .join(Search)
            .where(Search.fetch_index << fetch_indexes)
        )
    else:
        results = (
            SearchResult
            .select()
            .join(SearchResultContent, JOIN_LEFT_OUTER)
            .where(SearchResultContent.content >> None)
            )

    for search_result in results:

        # Fetch content for the search result
        resp = make_request(default_requests_session.get, search_result.url)

        # Save the content
        if hasattr(resp, 'content'):
            SearchResultContent.create(search_result=search_result, content=resp.content)
        else:
            logging.warn("Error fetching content from URL: %s", search_result.url)

        # Even though most of the pages will be from different domains, we pause between
        # fetching the content for each result to avoid spamming any specific domain with requests.
        time.sleep(DELAY_TIME)


def main(fetch_all, fetch_indexes, *args, **kwargs):
    get_results_content(fetch_all, fetch_indexes)


def configure_parser(parser):
    parser.description = "fetch HTML contents for webpages at search results URLs." +\
        "The default action is to fetch only search results for which no contents have been " +\
        "fetched before."
    parser.add_argument(
        '--fetch-all',
        action='store_true',
        help="fetch contents for all search results."
    )
    parser.add_argument(
        '--fetch-indexes',
        type=int,
        nargs='+',
        help="fetch contents for records with the specified fetch indexes"
    )
