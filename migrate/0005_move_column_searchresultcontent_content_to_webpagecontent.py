#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from playhouse.migrate import migrate
from peewee import ForeignKeyField, SQL

from models import WebPageContent, SearchResult, SearchResultContent


logger = logging.getLogger('data')


def forward(migrator):

    # Add a placeholder field for storing a link to a WebPageContent object
    migrate(
        migrator.add_column(
            'searchresultcontent',
            'webpagecontent_id',
            ForeignKeyField(WebPageContent, null=True, to_field=WebPageContent.id),
        ),
    )

    # Move the data previously in SearchResultContent model into WebPageContent,
    # and link the WebPageContent to the SearchResultContent.
    # Note that because the model for SearchResultContent has already been updated beyond the
    # state of the table, we have to access the 'content' and 'date' fields through the "SQL"
    # class instead of a field on the model.  This is also the reason that we mix both
    # Query object methods and raw queries below.  The models access the future field names,
    # and the raw queries access the past field names.
    content_records = (
        SearchResultContent
        .select(SQL('content'), SQL('date'), SearchResult.url, SearchResultContent.id)
        .join(SearchResult)
        .dicts()
    )

    for record in content_records:
        web_page_content = WebPageContent.create(
            content=record['content'],
            date=record['date'],
            url=record['url'],
        )
        SearchResultContent.raw(
            "UPDATE searchresultcontent SET webpagecontent_id = ? WHERE id = ?",
            web_page_content.id, record['id']
        ).execute()

    # Drop unnecessary columns from SearchResultContent model
    migrate(
        migrator.drop_column('searchresultcontent', 'date'),
        migrator.drop_column('searchresultcontent', 'content'),
        migrator.rename_column('searchresultcontent', 'webpagecontent_id', 'content_id'),
        migrator.drop_not_null('searchresultcontent', 'content_id'),
    )
