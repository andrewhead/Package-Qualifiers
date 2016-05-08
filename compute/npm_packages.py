#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker
from bs4 import BeautifulSoup
from peewee import fn
import re
import bashlex

from models import Post, PostTag, Tag, PostNpmInstallPackage
from compute._scan import NodeScanner


logger = logging.getLogger('data')


def extract_npm_install_packages(compute_index, show_progress=False):

    # Fetch all posts, filtering by those for which tags have been specified
    posts = (
        Post.select(Post.id, Post.body)
        .join(PostTag, on=(Post.id == PostTag.post_id))
        .join(Tag, on=(Tag.id == PostTag.tag_id))
        .where(Tag.tag_name << ['npm', 'node.js'])
    )

    # Initialize the progress bar
    if show_progress:
        post_count = posts.count()
        progress_bar = ProgressBar(maxval=post_count, widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Processing web page ', Counter(), ' / ' + str(post_count) + '.'
        ])
        progress_bar.start()

    # Initialize the scanner that will find packages mentioned in 'npm install'
    # commands in HTML elements that look like code
    extractor = NpmInstallPackageExtractor()
    scanner = NodeScanner(extractor, tags=['pre', 'code'])

    # For each post, extract all packages referenced in 'npm install' commands.
    for post_index, post in enumerate(posts, start=1):

        document = BeautifulSoup(post.body, 'html.parser')
        packages = scanner.scan(document)

        # Store a record of each package name that was found
        for package in packages:
            PostNpmInstallPackage.create(
                post=post,
                package=package,
                compute_index=compute_index,
            )

        if show_progress:
            progress_bar.update(post_index)

    if show_progress:
        progress_bar.finish()


class NpmInstallPackageExtractor(object):
    '''
    Given a BeautifulSoup representation of an HTML node, this returns a list of
    all packages that are positional arguments to a left-justified 'npm install' command.
    '''

    def extract(self, node):

        packages = []
        content = node.text

        lines = content.splitlines()
        for line in lines:
            # The use of the 'match' function that 'npm install' must appear as the first
            # substring on the line.  There can be no tokens besides whitespace before it.
            if re.match('\s*npm\s+install\s+', line):
                line_packages = [_ for _ in self._get_package_names(line)]
                packages.extend(line_packages)

        return packages

    def _get_package_names(self, command):

        OPTIONS_WITH_VALUES = ['--nodedir', '--only', '--tag']

        waiting_for_word_npm = True
        waiting_for_word_install = False
        consume_next_word = False

        try:
            parse_tree = bashlex.parse(command)
        # If bashlex fails to parse this command, we can't do anything with it.
        # Stop iteration to return an empty list of packages.
        except bashlex.errors.ParsingError:
            raise StopIteration

        for word in parse_tree[0].parts:

            # As this is an undocumented part of the API and bashlex has proved unreliable
            # in the past, we do some pretty explicit checks ot make sure this is a
            # "Word" node in the bash AST.
            if word.kind == 'word' and hasattr(word, 'word'):

                if waiting_for_word_npm and word.word == 'npm':
                    waiting_for_word_npm = False
                    waiting_for_word_install = True
                elif waiting_for_word_install and word.word == 'install':
                    waiting_for_word_install = False
                elif consume_next_word:  # this word followed an argument that needs a value
                    consume_next_word = False
                elif word.word.startswith('-'):
                    consume_next_word = (any(
                        [word.word.startswith(option) and
                         not word.word.startswith(option + '=')
                         for option in OPTIONS_WITH_VALUES]))
                else:
                    match = re.match(r'(@[^/]+/)?([^@]+)(@.+)?', word.word)
                    if match:
                        yield match.group(2)


def main(show_progress, *args, **kwargs):

    # Create a new index for this computation
    last_compute_index = PostNpmInstallPackage.select(
        fn.Max(PostNpmInstallPackage.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Run snippet extraction
    extract_npm_install_packages(compute_index, show_progress)


def configure_parser(parser):
    parser.description = "Extract names of packages that are npm-installed in Stack Overflow posts."
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress of the number of posts scanned."
    )
