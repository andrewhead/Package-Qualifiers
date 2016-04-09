#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker
from peewee import fn, SQL

from dump import dump_json
from models import Query, Seed


logger = logging.getLogger('data')


@dump_json(__name__)
def main(packages, fetch_index, num_queries, show_progress, *args, **kwargs):

    # Read names of target packages from file
    with open(packages) as packages_file:
        package_list = [line.strip() for line in packages_file.readlines()]

    # Set up progress bar.
    if show_progress:
        progress_bar = ProgressBar(maxval=len(package_list), widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Fetched posts for ', Counter(), ' / ' + str(len(package_list)) + ' packages.'
        ])
        progress_bar.start()

    # Fetch statistics for posts related to each tag
    for package_count, package in enumerate(package_list, start=1):

        # We identify the queries related to a package as those that have seeds
        # that begin with the package name followed by a space.
        # We then group the queries, annotating them with a score that's computed
        # as the sum of reciprocal depths where it appears.
        top_queries = (
            Query.select(
                Query.query,
                fn.Sum(1.0 / (Query.depth + 1)).alias('score')
            )
            .join(Seed, on=(Seed.id == Query.seed))
            .where(Seed.seed % (package + ' %'))
            .where(Query.fetch_index == fetch_index)
            .group_by(Query.query).order_by(SQL('score').desc())
            .limit(num_queries)
        )

        records = []
        for query in top_queries:
            records.append({
                'package': package,
                'query': query.query,
            })
        yield records

        if show_progress:
            progress_bar.update(package_count)

    if show_progress:
        progress_bar.finish()

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump count statistics for frequently used Node packages."
    parser.add_argument(
        'packages',
        help="Name of file containing names of packages for which top queries will be picked."
    )
    parser.add_argument(
        '--fetch-index',
        default=30,
        help="The index of query fetching data in which to pick top queries (default: %(default)s)"
    )
    parser.add_argument(
        '--num-queries',
        default=30,
        help="Number of top queries to retrieve for each package (default: %(default)s)."
    )
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress in loading content from the file."
    )
