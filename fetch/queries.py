#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from xml.etree import ElementTree
from peewee import fn
import time


from fetch.api import make_request, default_requests_session
from models import Query, Seed
from lock import lock_method


logging.basicConfig(level=logging.INFO, format="%(message)s")


# Query URL and parameters from http://stackoverflow.com/questions/5102878/google-suggest-api
URL = "https://suggestqueries.google.com/complete/search?output=toolbar&hl=en"
DEFAULT_PARAMS = {
    'hl': 'en',
    'output': 'toolbar',
}
MAX_RESULTS = 10
ALPHABET = " abcdefghijklmnopqrstuvwxyz0123456789.'-_"
REQUEST_DELAY = 1.5
LOCK_FILENAME = '/tmp/query-fetcher.lock'
MAX_DEPTH = 5  # this number was in no way empirically determined


def get_results_for_seeds(seeds):

    # Create a new fetch index.
    last_fetch_index = Seed.select(fn.Max(Seed.fetch_index)).scalar() or 0
    fetch_index = last_fetch_index + 1

    for seed_text in seeds:

        # Create a new seed record from the text
        seed = Seed.create(
            fetch_index=fetch_index,
            seed=seed_text,
            depth=0,
        )

        # Fetch the autocomplete results!
        get_results(seed)


def get_results(seed):

    fetch_index = seed.fetch_index

    # Request for autocomplete results
    params = DEFAULT_PARAMS.copy()
    params['q'] = seed.seed
    response = make_request(default_requests_session.get, URL, params=params)
    time.sleep(REQUEST_DELAY)  # enforce a pause between each fetch to be respectful to API

    # Go no further if the call failed
    if not response:
        return []

    # Store data from the fetched queries
    doc = ElementTree.fromstring(response.text.encode('utf-8'))
    num_results = 0
    rank = 1

    for comp_sugg in doc.iterfind('CompleteSuggestion'):
        for suggestion in comp_sugg.iterfind('suggestion'):

            # Create a new query and add to the database
            data = suggestion.attrib['data']

            # In Fourney et al.'s implementation of CUTS, the returned queries were checked so that
            # they started with the exactly the seed.  We relax this restriction here.
            # We note that in some autocomplete entries use valuable synonyms for our
            # queries, such as converting node -> js or rearranging the terms.  These modified
            # prefixes yield interesting queries that we don't want to miss.
            Query.create(
                fetch_index=fetch_index,
                seed=seed,
                query=data,
                rank=rank,
                depth=seed.depth,
            )

            num_results += 1
            rank += 1

    # Only expand this seed into new seeds if we got a full set of results and
    # we have not yet descended to the maximum depth.
    if num_results == MAX_RESULTS and seed.depth < MAX_DEPTH:

        for char in ALPHABET:

            # The initial query should be followed by a space.
            if seed.depth == 0 and char != ' ':
                continue

            # There shouldn't be any sequence of two spaces.
            if char == ' ' and seed.seed.endswith(' '):
                continue

            # Create and store new seed
            new_seed_text = seed.seed + char
            new_seed = Seed.create(
                fetch_index=fetch_index,
                parent=seed,
                seed=new_seed_text,
                depth=seed.depth + 1,
            )

            # Fetch results for the new seed.
            get_results(new_seed)


@lock_method(LOCK_FILENAME)
def main(seeds, *args, **kwargs):

    # Fetch autocomplete results
    with open(seeds) as seeds_file:
        seeds = [l.strip() for l in seeds_file]
        get_results_for_seeds(seeds)


def configure_parser(parser):
    parser.description = "Fetch autocomplete queries for a see query."
    parser.add_argument(
        'seeds',
        type=str,
        help="the name of a file containing a list of seed queries."
    )
