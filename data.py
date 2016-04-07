#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import argparse

from models import create_tables, init_database
from fetch import queries, results, results_content, histories
from import_ import stackoverflow
from compute import post_tags, tasks
from migrate import run_migration
from dump import node_post_stats, popular_tag_post_stats


logging.basicConfig(level=logging.INFO, format="%(message)s")
COMMANDS = {
    'fetch': {
        'description': "Fetch data from the web.",
        'module_help': "Type of data to fetch.",
        'modules': [queries, results, results_content, histories],
    },
    'import': {
        'description': "Import data from a local data source.",
        'module_help': "Type of data to import.",
        'modules': [stackoverflow],
    },
    'compute': {
        'description': "Compute derived fields from existing data.",
        'module_help': "Type of data to compute.",
        'modules': [post_tags, tasks],
    },
    'migrate': {
        'description':
            "Manage database migrations. (Should only be necessary if you initialized " +
            "your database and then the model files were updated.)",
        'module_help': "Migration operation.",
        'modules': [run_migration],
    },
    'dump': {
        'description': "Dump data to a JSON file.",
        'module_help': "Type of data to dump.",
        'modules': [node_post_stats, popular_tag_post_stats],
    },
}


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Manage data for software packages.")
    subparsers = parser.add_subparsers(help="Sub-commands for managing data")

    for command in COMMANDS.keys():

        # Create a parser for each top-level command, with subparsers for each module
        command_spec = COMMANDS[command]
        command_parser = subparsers.add_parser(command, description=command_spec['description'])
        command_subparsers = command_parser.add_subparsers(help=command_spec['module_help'])

        # Initialize arguments for each module of each command
        for module in command_spec['modules']:

            # Create a parser for each low-level module
            module_basename = module.__name__.split('.')[-1]
            module_parser = command_subparsers.add_parser(module_basename)

            # Add default arguments for each fetcher (database configuration)
            module_parser.add_argument(
                '--db',
                default='sqlite',
                help="which type of database to use (postgres, sqlite). Defaults to sqlite."
            )
            module_parser.add_argument(
                '--db-config',
                help="Name of file containing database configuration."
            )

            # Each module defines additional arguments
            module.configure_parser(module_parser)
            module_parser.set_defaults(func=module.main)

    # Parse arguments
    args = parser.parse_args()

    # Initialize database
    init_database(args.db, config_filename=args.db_config)
    create_tables()

    # Invoke the main program that was specified by the submodule
    if args.func is not None:
        args.func(**vars(args))
