#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import argparse

import queries
from models import create_tables, init_database


logging.basicConfig(level=logging.INFO, format="%(message)s")
SUBMODULES = [queries]


if __name__ == '__main__':

    # Collect default arguments
    parser = argparse.ArgumentParser(description="fetch data for software packages.")

    # Add arguments for sub-commands
    subparsers = parser.add_subparsers(help="sub-commands for fetching")

    for submodule in SUBMODULES:
        subparser = subparsers.add_parser(submodule.__name__)

        # Add default arguments for each fetcher (database configuration)
        subparser.add_argument(
            '--db',
            help="which type of database to use (postgres, sqlite). Defaults to sqlite."
        )
        subparser.add_argument(
            '--db-config',
            help="Name of file containing database configuration."
        )

        # Enable each module to define additional arguments
        submodule.configure_parser(subparser)
        subparser.set_defaults(func=submodule.main)

    # Parse arguments
    args = parser.parse_args()

    # Initialize database
    init_database(args.db, config_filename=args.db_config)
    create_tables()

    # Invoke the main program that was specified by the submodule
    if args.func is not None:
        args.func(**vars(args))
