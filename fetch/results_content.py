#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import time
from peewee import JOIN_LEFT_OUTER

from fetch.api import make_request, default_requests_session
from models import Search, SearchResult, WebPageContent, SearchResultContent


logger = logging.getLogger('data')
DELAY_TIME = 0.5


def get_results_content(fetch_all, fetch_indexes, share_content):

    # We order search results by URL so that we can visit search results that share the
    # same URL one after the other.  This way we can associate the same fetched contents
    # with all search results that share a URL at the same time.
    results = (
        SearchResult
        .select()
        .order_by(SearchResult.url)
    )
    if fetch_all:
        results = results
    elif fetch_indexes:
        results = (
            results
            .join(Search)
            .where(Search.fetch_index << fetch_indexes)
        )
    else:
        results = (
            results
            .join(SearchResultContent, JOIN_LEFT_OUTER)
            .where(SearchResultContent.content >> None)
        )

    previous_url = None
    previous_content = None

    for search_result in results:

        # If the caller has specified that we should share fetched contents between
        # search results with the same URL, then check to see if the URL has stayed the same.
        if share_content and search_result.url == previous_url:
            logger.debug("Already called URL %s.  Reusing its response.", search_result.url)
            if previous_content is not None:
                SearchResultContent.create(search_result=search_result, content=previous_content)
            continue

        # Fetch content for the search result
        resp = make_request(default_requests_session.get, search_result.url)

        # Associate the scraped content to a URL
        if hasattr(resp, 'content'):
            # To avoid redundant storage, we create a record for web page
            # contents that can be shared across multiple URLs.
            # As it turns out, we want "response.text" (Unicode) and not "response.content" (bytes),
            # if we want to successfully store the responses from all URLs.
            web_page_content = WebPageContent.create(url=search_result.url, content=resp.text)
            SearchResultContent.create(search_result=search_result, content=web_page_content)
            previous_content = web_page_content
        else:
            logger.warn("Error fetching content from URL: %s", search_result.url)
            previous_content = None

        # With either a successful or failed response, save that we queried this URL
        previous_url = search_result.url

        # Even though most of the pages will be from different domains, we pause between
        # fetching the content for each result to avoid spamming any specific domain with requests.
        time.sleep(DELAY_TIME)


def main(fetch_all, fetch_indexes, no_share_content, *args, **kwargs):
    get_results_content(fetch_all, fetch_indexes, (not no_share_content))


def configure_parser(parser):
    parser.description = "Fetch HTML contents for webpages at search results URLs." +\
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
    parser.add_argument(
        '--no-share-content',
        action='store_true',
        help="By default, this program only fetch contents once for each distinct URL in " +
             "the fetch set.  This is to avoid unnecessary fetches and speed up the " +
             "program.  If you set this flag, then this script will fetch each URL anew " +
             "each time that it appears in a search result."
    )
