#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker

from models import BatchInserter
from models import Post, Tag, PostTag


logger = logging.getLogger('data')

# Paginating with Peewee is very slow, as it requires counting up the entries
# in the pages before for each new query for a page.  But we want to do some
# paginating, so that we can process SELECT statements as a group, instead of one
# for each post that we're considering.
# While there may be some more efficient way of paginating on SQL record index with
# the Postgres driver directly, we use a workaround that can work with Peewee.
# IDs are already indexes and can be queried very quickly.
# So we provide a range of IDs that we're looking at, instead of a range of row indexes.
# In the posts dataset we have already uploaded to SQL, we see that there are, on average
# 1000 records for a jump in ID of 1200.  So to query around ~1000 posts at a time,
# we select ranges of IDs that are 1200 long.
ID_HOP = 1200


def main(batch_size, show_progress, *args, **kwargs):

    batch_inserter = BatchInserter(PostTag, batch_size=batch_size)

    # Get the ID of the record with the highest ID.
    last_id = (
        Post
        .select()
        .order_by(Post.id.desc())
        .get()
        .id
    )

    if show_progress:
        progress_bar = ProgressBar(maxval=last_id, widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Processing ID ', Counter(), ' / ' + str(last_id) + '.'
        ])
        progress_bar.start()

    # There are a small number of tags (~50,000 at the time of writing this),
    # so we just cache them all in a map from name to model to avoid
    # unnecessary queries.
    tag_cache = {}

    # In previous versions of this code, we intentionally separated the iterators through
    # the different models, and did all selections and insertions in batches.  We found out that
    # having nested iterators over database objects caused the cursor to jump around in one
    # of the iterators, so we're sticking to one iterator at a time.
    id_window_start = 0
    while id_window_start <= last_id:

        if show_progress:
            progress_bar.update(id_window_start)

        posts = Post.select().where(
            Post.id >= id_window_start,
            Post.id < id_window_start + ID_HOP
        )
        post_tag_names = {}

        for post in posts:

            tags_string = post.tags
            if tags_string is not None:

                # I have verified that at the time of writing this, no tags on Stack Overflow
                # have the substrings.  '<' or '>' in their names.  This suggests that we won't
                # break on incorrect boundaries within tag names if we split on the string
                # '><' and strip '<' and ''>' from the resulting tags.
                tag_names = [s.rstrip('>').lstrip('<') for s in tags_string.split('><')]
                post_tag_names[post.id] = tag_names

        for post_id, tag_names in post_tag_names.items():

            for tag_name in tag_names:

                if tag_name in tag_cache:
                    tag = tag_cache[tag_name]
                else:
                    try:
                        tag = Tag.get(tag_name=tag_name)
                    except Tag.DoesNotExist:
                        tag = None
                    tag_cache[tag_name] = tag

                if tag is not None:
                    batch_inserter.insert({'post_id': post_id, 'tag_id': tag.id})
                else:
                    logging.warn("No tag found for tag name [%s] for post %d", tag_name, post_id)

        id_window_start += ID_HOP

    batch_inserter.flush()

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
