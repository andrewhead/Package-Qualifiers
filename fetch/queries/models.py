#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime
from peewee import Model, SqliteDatabase,\
    CharField, IntegerField, ForeignKeyField, DateTimeField


logging.basicConfig(level=logging.INFO, format="%(message)s")
db = SqliteDatabase('queries.db')


class Seed(Model):
    ''' An initial query given by a user for which autocomplete results are shown. '''

    # Fetch logistics
    fetch_index = IntegerField()
    date = DateTimeField(index=True, default=datetime.datetime.now)

    # Data about the query
    parent = ForeignKeyField('self', null=True, related_name='children')
    seed = CharField()
    depth = IntegerField()

    class Meta:
        database = db


class Query(Model):
    ''' An instance of a suggestion returned in response to a seed query. '''

    # Fetch logistics
    fetch_index = IntegerField()
    date = DateTimeField(index=True, default=datetime.datetime.now)

    # Data about the query
    seed = ForeignKeyField(Seed)
    query = CharField()
    depth = IntegerField()
    rank = IntegerField()

    class Meta:
        database = db


def create_tables():
    db.create_tables([Query, Seed], safe=True)
