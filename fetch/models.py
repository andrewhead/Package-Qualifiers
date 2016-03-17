#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime
import json
from peewee import Model, SqliteDatabase, Proxy, PostgresqlDatabase, \
    CharField, IntegerField, ForeignKeyField, DateTimeField, TextField


logging.basicConfig(level=logging.INFO, format="%(message)s")

POSTGRES_CONFIG_NAME = 'postgres-credentials.json'
DATABASE_NAME = 'fetcher'
db_proxy = Proxy()


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
        database = db_proxy


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
        database = db_proxy


class Search(Model):
    ''' A search query made to a search engine. '''

    fetch_index = IntegerField()
    date = DateTimeField(index=True, default=datetime.datetime.now)

    query = CharField()
    page_index = IntegerField()
    requested_count = IntegerField()
    result_count_on_page = IntegerField()
    estimated_results_count = IntegerField()

    class Meta:
        database = db_proxy


class SearchResult(Model):
    ''' A result to a search query submitted to a search engine. '''

    search = ForeignKeyField(Search, related_name='results')
    title = TextField()
    snippet = CharField(null=True)
    link = TextField()
    url = CharField()
    updated_date = DateTimeField()
    rank = IntegerField()

    class Meta:
        database = db_proxy


class SearchResultContent(Model):
    ''' Webpage content at a search results URL. '''

    date = DateTimeField(index=True, default=datetime.datetime.now)
    search_result = ForeignKeyField(SearchResult, related_name='content')
    content = TextField()

    class Meta:
        database = db_proxy


def init_database(db_type=None, config_filename=None):

    if db_type == 'postgres':

        # If the user wants to use Postgres, they should define their credentials
        # in an external config file, which are used here to access the database.
        config_filename = config_filename if config_filename else POSTGRES_CONFIG_NAME
        with open(config_filename) as pg_config_file:
            pg_config = json.load(pg_config_file)

        config = {}
        config['user'] = pg_config['dbusername']
        if 'dbpassword' in pg_config:
            config['password'] = pg_config['dbpassword']
        if 'host' in pg_config:
            config['host'] = pg_config['host']

        db = PostgresqlDatabase(DATABASE_NAME, **config)

    # Sqlite is the default type of database.
    elif db_type == 'sqlite' or not db_type:
        db = SqliteDatabase(DATABASE_NAME + '.db')

    db_proxy.initialize(db)


def create_tables():
    db_proxy.create_tables([Query, Seed, Search, SearchResult, SearchResultContent], safe=True)
