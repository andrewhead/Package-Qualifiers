#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker

from models import BatchInserter
from models import Post, Tag, PostTag


logging.basicConfig(level=logging.INFO, format="%(message)s")
PAGE_LENGTH = 1000  # chosen to be some number of posts that will probably fit into memory


def main(batch_size, show_progress, *args, **kwargs):

    batch_inserter = BatchInserter(PostTag, batch_size=batch_size)

    if show_progress:
        progress_bar = ProgressBar(maxval=Post.select().count(), widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Tagged ', Counter(), ' posts.'
        ])
        progress_bar.start()

    post_count = Post.select().count()
    posts_processed = 0

    # There are a small number of tags (~50,000 at the time of writing this),
    # so we just cache them all in a map from name to model to avoid
    # unnecessary queries.
    tag_cache = {}

    # We intentionally separate the iterators through the different models,
    # and do all selections and insertions in batches.  We found out that
    # having nested iterators over database objects caused the cursor
    # to jump around in one of the iterators, so we're sticking to one
    # iterator at a time.

    # Pages with Peewee queries are indexed starting at 1
    last_page = (post_count / PAGE_LENGTH) + 1
    for post_page in range(1, last_page + 2):

        posts = Post.select().paginate(post_page, paginate_by=PAGE_LENGTH)
        post_tag_names = {}

        for post_index, post in enumerate(posts):

            tags_string = post.tags
            if tags_string is not None:

                # I have verified that at the time of writing this, no tags on Stack Overflow
                # have the substrings.  '<' or '>' in their names.  This suggests that we won't
                # break on incorrect boundaries within tag names if we split on the string
                # '><' and strip '<' and ''>' from the resulting tags.
                tag_names = [s.rstrip('>').lstrip('<') for s in tags_string.split('><')]
                post_tag_names[post.id] = tag_names

            posts_processed += 1
            if show_progress:
                progress_bar.update(posts_processed)

            # Break out from loop early if this is the last page
            if post_page == last_page and post_index == (post_count % PAGE_LENGTH) - 1:
                break

        for post_id, tag_names in post_tag_names.items():

            for tag_name in tag_names:
                if tag_name in tag_cache:
                    tag = tag_cache[tag_name]
                else:
                    tag = Tag.get(tag_name=tag_name)
                    tag_cache[tag_name] = tag
                batch_inserter.insert({'post_id': post_id, 'tag_id': tag.id})

    batch_inserter.flush()

    print posts_processed
    if show_progress:
        progress_bar.finish()


def configure_parser(parser):
    parser.description =\
        "Generate a table that links Stack Overflow posts to their tags. " +\
        "Assumes that the table either doesn't yet exist or is empty."
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help="The number of post-tag links to insert at a time. Increasing this value " +
        "should greatly increase the speed of importing data. "
    )
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress in loading content from the file. " +
        "Note that this may slow down execution as the program will have " +
        "to count the amount of the file that is being read."
    )
