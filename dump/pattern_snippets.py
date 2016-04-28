#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_json
from models import SnippetPattern, PostSnippet


logger = logging.getLogger('data')


@dump_json(__name__)
def main(patterns, *args, **kwargs):

    # Read names of patterns from file
    with open(patterns) as patterns_file:
        pattern_list = [line.strip() for line in patterns_file.readlines()]

    # Fetch snippets for each post and yield them to file
    for pattern_count, pattern in enumerate(pattern_list, start=1):

        snippets = (
            PostSnippet
            .select()
            .join(SnippetPattern)
            .where(SnippetPattern.pattern == pattern)
        )

        snippet_texts = [s.snippet for s in snippets]
        record = {
            'pattern': pattern,
            'snippets': snippet_texts,
        }
        yield [record]

    raise StopIteration


def configure_parser(parser):
    parser.description =\
        "Dump code snippets that match a set of patterns. " +\
        "This should be run after computing the snippets for posts."
    parser.add_argument(
        'patterns',
        help="Name of file containing patterns for which snippets will be dumped."
    )
