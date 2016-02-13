#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime
import json
from peewee import Model, SqliteDatabase, Proxy, PostgresqlDatabase, \
    CharField, IntegerField, ForeignKeyField, DateTimeField


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


def init_database(db_type=None, creds_filename=None):

    if db_type == 'postgres':

        # If the user wants to use Postgres, they should define their credentials
        # in an external config file, which are used here to access the database.
        creds_filename = creds_filename if creds_filename else POSTGRES_CONFIG_NAME
        with open(creds_filename) as pg_config_file:
            pg_config = json.load(pg_config_file)

        creds = {}
        creds['user'] = pg_config['dbusername']
        if 'dbpassword' in pg_config:
            creds['password'] = pg_config['dbpassword']

        db = PostgresqlDatabase(DATABASE_NAME, **creds)

    # Sqlite is the default type of database.
    elif db_type == 'sqlite' or not db_type:
        db = SqliteDatabase(DATABASE_NAME + '.db')

    db_proxy.initialize(db)


def create_tables():
    db_proxy.create_tables([Query, Seed], safe=True)
