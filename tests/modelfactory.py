#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime

from models import Post, Tag


logger = logging.getLogger('data')


'''
This file contains functions that help us create models with mostly default properties, but
with the ability to configure any one specific field without having to define the others.
This is particularly helpful when we need to create test data, but don't want our test
logic to include many lines of model definitions.
'''


def create_post(
        post_type_id=1,
        accepted_answer_id=1,
        parent_id=2,
        creation_date=datetime.datetime.utcnow(),
        deletion_date=datetime.datetime.utcnow(),
        score=0,
        view_count=1,
        body="Body",
        owner_user_id=1,
        owner_display_name="Owner Name",
        last_editor_user_id=2,
        last_editor_display_name="Editor Name",
        last_edit_date=datetime.datetime.utcnow(),
        last_activity_date=datetime.datetime.utcnow(),
        title="A Post",
        tags="<tag1><tag2>",
        answer_count=1,
        comment_count=1,
        favorite_count=3,
        closed_date=datetime.datetime.utcnow(),
        community_owned_date=datetime.datetime.utcnow()):
    return Post.create(
        post_type_id=post_type_id,
        accepted_answer_id=accepted_answer_id,
        parent_id=parent_id,
        creation_date=creation_date,
        deletion_date=deletion_date,
        score=score,
        view_count=view_count,
        body=body,
        owner_user_id=owner_user_id,
        owner_display_name=owner_display_name,
        last_editor_user_id=last_editor_user_id,
        last_editor_display_name=last_editor_display_name,
        last_edit_date=last_edit_date,
        last_activity_date=last_activity_date,
        title=title,
        tags=tags,
        answer_count=answer_count,
        comment_count=comment_count,
        favorite_count=favorite_count,
        closed_date=closed_date,
        community_owned_date=community_owned_date,
    )


def create_tag(
        tag_name="tag-name",
        count=3,
        excerpt_post_id=0,
        wiki_post_id=1):
    return Tag.create(
        tag_name=tag_name,
        count=count,
        excerpt_post_id=excerpt_post_id,
        wiki_post_id=wiki_post_id
    )
