#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import argparse
import unittest
import os

# Set up logger for the sub-commands to use.
# Note that this setup must occur before the other modules are imported.
# Code stub courtesy of http://stackoverflow.com/questions/7621897/python-logging-module-globally
log_formatter = logging.Formatter(
    fmt="[%(levelname)s] %(asctime)s (%(module)s:%(lineno)d): %(message)s")
log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)
data_logger = logging.getLogger('data')
data_logger.setLevel(logging.INFO)
data_logger.addHandler(log_handler)
data_logger.propagate = False

from models import create_tables, init_database
from fetch import queries, results, results_content, histories, stack_overflow_questions, issues,\
    issue_comments, issue_events, slant_topics, slant_pros_and_cons
from import_ import stackoverflow
from compute import code, npm_packages, post_tags, python_snippets, tasks
from migrate import run_migration
from dump import node_post_stats, package_top_queries, pattern_snippets, popular_tag_post_stats,\
    slant_community_pros_and_cons


COMMANDS = {
    'fetch': {
        'description': "Fetch data from the web.",
        'module_help': "Type of data to fetch.",
        'modules': [
            histories, queries, results, results_content, stack_overflow_questions, issues,
            issue_comments, issue_events, slant_topics, slant_pros_and_cons
        ],
    },
    'import': {
        'description': "Import data from a local data source.",
        'module_help': "Type of data to import.",
        'modules': [stackoverflow],
    },
    'compute': {
        'description': "Compute derived fields from existing data.",
        'module_help': "Type of data to compute.",
        'modules': [code, npm_packages, post_tags, python_snippets, tasks],
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
        'modules': [
            node_post_stats, pattern_snippets, package_top_queries, popular_tag_post_stats,
            slant_community_pros_and_cons
        ],
    },
}


def run_tests(*args, **kwargs):
    suite = unittest.defaultTestLoader.discover(os.getcwd())
    unittest.TextTestRunner().run(suite)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Manage data for software packages.")
    subparsers = parser.add_subparsers(help="Sub-commands for managing data", dest='command')

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

    # Add command for running unit tests
    test_parser = subparsers.add_parser('tests', description="Run unit tests.")
    test_parser.set_defaults(func=run_tests)

    # Parse arguments
    args = parser.parse_args()

    # Initialize database
    if args.command != 'tests':
        init_database(args.db, config_filename=args.db_config)
        create_tables()

    # Invoke the main program that was specified by the submodule
    if args.func is not None:
        args.func(**vars(args))
