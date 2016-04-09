#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker
import numpy as np

from dump import dump_json
from models import Post, Tag, PostTag


logger = logging.getLogger('data')
TAGS = [
    "javascript",
    "java",
    "c#",
    "php",
    "android",
    "jquery",
    "python",
    "html",
    "c++",
    "ios",
    "mysql",
    "css",
    "sql",
    "asp.net",
    "objective-c",
    "ruby-on-rails",
    ".net",
    "c",
    "iphone",
    "arrays",
    "angularjs",
    "sql-server",
    "ruby",
    "json",
    "ajax",
    "regex",
    "xml",
    "r",
    "asp.net-mvc",
    "linux",
    "django",
    "wpf",
    "node.js",
    "database",
]


@dump_json(__name__)
def main(sample_size, show_progress, *args, **kwargs):

    # Set up progress bar.
    if show_progress:
        progress_bar = ProgressBar(maxval=len(TAGS), widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Fetched posts for ', Counter(), ' / ' + str(len(TAGS)) + ' tags.'
        ])
        progress_bar.start()

    # Fetch statistics for posts related to each tag
    for tag_count, tag in enumerate(TAGS, start=1):

        # As it turns out, we can make the selection of random posts tractable if we
        # don't do a random ordering in SQL but instead do a random selection
        # in Python.  So we start by fetching all of the post IDs for a tag,
        # make the random choice locally, and then query for the posts in this subset.
        post_id_tuples = (
            PostTag.select()
            .join(Tag, on=(PostTag.tag_id == Tag.id))
            .where(Tag.tag_name == tag)
            .select(PostTag.post_id)
            .tuples()
        )

        # We convert this from a 2D Nx1 matrix to a 1D N-length matrix by taking its
        # transpose and then getting the "first row" of the transpose.
        post_ids = np.array(post_id_tuples).T[0]
        sample_post_ids = np.random.choice(post_ids, sample_size, replace=False).tolist()

        post_records = (
            Post.select(Post.title, Post.creation_date, Post.answer_count, Post.comment_count,
                        Post.favorite_count, Post.score, Post.view_count)
            .where(Post.id << sample_post_ids)
            .dicts()
        )

        # Store which tag this record is associated with
        for record in post_records:
            record['tag_name'] = tag

        yield post_records

        if show_progress:
            progress_bar.update(tag_count)

    if show_progress:
        progress_bar.finish()

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump count statistics for posts for frequent Stack Overflow tags."
    parser.add_argument(
        '--sample-size',
        type=int,
        default=2000,
        help="The maximum number of random posts to fetch for a tag." +
             "Performance should be pretty invariant to this number."
    )
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress in loading content from the file."
    )
