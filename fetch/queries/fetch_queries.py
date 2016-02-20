#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from xml.etree import ElementTree

from peewee import fn
from api import make_request, default_requests_session
from models import Query, Seed, create_tables, init_database
import time
import argparse
import fcntl


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
    valid_results = []
    rank = 1

    for comp_sugg in doc.iterfind('CompleteSuggestion'):
        for suggestion in comp_sugg.iterfind('suggestion'):

            # Create a new query and add to the database
            data = suggestion.attrib['data']

            if data.startswith(seed.seed):
                query = Query.create(
                    fetch_index=fetch_index,
                    seed=seed,
                    query=data,
                    rank=rank,
                    depth=seed.depth,
                )
                valid_results.append(query)

            num_results += 1
            rank += 1

    # Only expand this seed into new seeds if we got a full set of results and
    # we have not yet descended to the maximum depth.
    if num_results == MAX_RESULTS and len(valid_results) > 0 and seed.depth < MAX_DEPTH:

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


if __name__ == '__main__':

    # Only run this program if it's not already running
    # Snippet based on
    # http://linux.byexamples.com/archives/494/how-can-i-avoid-running-a-python-script-multiple-times-implement-file-locking/
    fp = open(LOCK_FILENAME, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        raise SystemExit(
            "This program is already running.  Please stop the current process or " +
            "remove " + LOCK_FILENAME + " to run this script."
        )

    # Parse arguments
    parser = argparse.ArgumentParser(description="fetch autocomplete queries for a see query.")
    parser.add_argument('seeds', help="the name of a file containing a list of seed queries.")
    parser.add_argument(
        '--db', help="which type of database to use (postgres, sqlite)." +
        "Defaults to sqlite.")
    parser.add_argument('--db-config', help="Name of file containing database configuration.")
    args = parser.parse_args()

    # Initialize database
    init_database(args.db, config_filename=args.db_config)
    create_tables()

    # Fetch autocomplete results
    with open(args.seeds) as seeds_file:
        seeds = [l.strip() for l in seeds_file]
        get_results_for_seeds(seeds)
