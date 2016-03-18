#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime
import json
from peewee import Model, SqliteDatabase, Proxy, PostgresqlDatabase, \
    CharField, IntegerField, ForeignKeyField, DateTimeField, TextField, BooleanField


logging.basicConfig(level=logging.INFO, format="%(message)s")

POSTGRES_CONFIG_NAME = 'postgres-credentials.json'
DATABASE_NAME = 'fetcher'
db_proxy = Proxy()


class ProxyModel(Model):
    ''' A peewee model that is connected to the proxy defined in this module. '''

    class Meta:
        database = db_proxy


class Seed(ProxyModel):
    ''' An initial query given by a user for which autocomplete results are shown. '''

    # Fetch logistics
    fetch_index = IntegerField()
    date = DateTimeField(index=True, default=datetime.datetime.now)

    # Data about the query
    parent = ForeignKeyField('self', null=True, related_name='children')
    seed = CharField()
    depth = IntegerField()


class Query(ProxyModel):
    ''' An instance of a suggestion returned in response to a seed query. '''

    # Fetch logistics
    fetch_index = IntegerField()
    date = DateTimeField(index=True, default=datetime.datetime.now)

    # Data about the query
    seed = ForeignKeyField(Seed)
    query = CharField()
    depth = IntegerField()
    rank = IntegerField()


class Search(ProxyModel):
    ''' A search query made to a search engine. '''

    fetch_index = IntegerField()
    date = DateTimeField(index=True, default=datetime.datetime.now)

    query = CharField()
    page_index = IntegerField()
    requested_count = IntegerField()
    result_count_on_page = IntegerField()
    estimated_results_count = IntegerField()


class SearchResult(ProxyModel):
    ''' A result to a search query submitted to a search engine. '''

    search = ForeignKeyField(Search, related_name='results')
    title = TextField()
    snippet = TextField(null=True)
    link = CharField()
    url = CharField()
    updated_date = DateTimeField()
    rank = IntegerField()


class SearchResultContent(ProxyModel):
    ''' Webpage content at a search results URL. '''

    date = DateTimeField(index=True, default=datetime.datetime.now)
    search_result = ForeignKeyField(SearchResult, related_name='content')
    content = TextField()


class Post(ProxyModel):
    '''
    A post from Stack Overflow.

    For this schema and others for Stack Overflow data, we rely on the Stack Exchange
    data explorer to describe the types of each of the fields
    (see http://data.stackexchange.com/stackoverflow/query/new).

    Each of these models has an implicit "id" field that will correspond to
    its original ID in the Stack Overflow data dump.

    While some of fields refer to entries in other tables, we don't use indexes or
    foreign keys for the first iteration of these models.
    We don't yet know what queries we have to optimize for.

    I enabled some of the fields to be 'null' based on the ones that were not
    defined in a subset of the data to be imported.  It could be that other
    fields should be nullable that I haven't yet marked.

    For strings that require more than 255 bytes, we create TextFields.
    This is because the peewee reference states that CharFields are for storing
    "small strings (0-255 bytes)".
    We also store tinyints in IntegerFields.

    When setting the length for CharFields thar are supposed to store data
    that was originally "nvarchar", we double the count for the expected
    max_length, using the claim from raymondlewallen that nvarchar stored
    Unicode data, which needs two bytes per character:
    http://codebetter.com/raymondlewallen/2005/12/30/database-basics-quick-note-the-difference-in-varchar-and-nvarchar-data-types/
    '''
    # Default StackOverflow fields
    post_type_id = IntegerField()
    accepted_answer_id = IntegerField(null=True)
    parent_id = IntegerField(null=True)
    creation_date = DateTimeField()
    deletion_date = DateTimeField(null=True)
    score = IntegerField()
    view_count = IntegerField(null=True)
    body = TextField()
    owner_user_id = IntegerField(null=True)
    owner_display_name = CharField(max_length=80, null=True)
    last_editor_user_id = IntegerField(null=True)
    last_editor_display_name = CharField(max_length=80, null=True)
    last_edit_date = DateTimeField(null=True)
    last_activity_date = DateTimeField()
    title = TextField(null=True)
    tags = TextField(null=True)
    answer_count = IntegerField(null=True)
    comment_count = IntegerField()
    favorite_count = IntegerField(null=True)
    closed_date = DateTimeField(null=True)
    community_owned_date = DateTimeField(null=True)


class Tag(ProxyModel):
    ''' A tag for Stack Overflow posts. '''
    tag_name = CharField(max_length=70)
    count = IntegerField()
    excerpt_post_id = IntegerField(null=True)
    wiki_post_id = IntegerField(null=True)


class PostHistory(ProxyModel):
    '''
    Some event related to a Stack Overflow post.

    'uniqueidentifier' is described to be a 16-byte GUID here:
    https://msdn.microsoft.com/en-us/library/ms187942.aspx
    So, we store the uniqueidentifier of the revision_guid field in a 16-byte character field.
    '''
    post_history_type_id = IntegerField()
    post_id = IntegerField()
    revision_guid = CharField(max_length=16)
    creation_date = DateTimeField()
    user_id = IntegerField(null=True)
    user_display_name = CharField(max_length=80, null=True)
    comment = TextField(null=True)
    text = TextField()


class PostLink(ProxyModel):
    ''' Link between Stack Overflow posts. '''
    creation_date = DateTimeField()
    post_id = IntegerField()
    related_post_id = IntegerField()
    link_type_id = IntegerField()


class Vote(ProxyModel):
    ''' A vote on a Stack Overflow post. '''
    post_id = IntegerField()
    vote_type_id = IntegerField()
    user_id = IntegerField(null=True)
    creation_date = DateTimeField()
    bounty_amount = IntegerField(null=True)


class Comment(ProxyModel):
    ''' Comment on a Stack Overflow post. '''
    post_id = IntegerField()
    score = IntegerField()
    text = TextField()
    creation_date = DateTimeField()
    user_display_name = CharField(max_length=60, null=True)
    user_id = IntegerField(null=True)


class Badge(ProxyModel):
    ''' Badge assigned to a Stack Overflow user. '''
    user_id = IntegerField()
    name = CharField(max_length=100)
    date = DateTimeField()
    class_ = IntegerField()
    tag_based = BooleanField()


class User(ProxyModel):
    ''' User on Stack Overflow. '''
    reputation = IntegerField()
    creation_date = DateTimeField()
    display_name = CharField(max_length=80)
    last_access_date = DateTimeField()
    website_url = TextField(null=True)
    location = CharField(max_length=200, null=True)
    about_me = TextField(null=True)
    views = IntegerField()
    up_votes = IntegerField()
    down_votes = IntegerField()
    profile_image_url = TextField(null=True)
    email_hash = CharField(max_length=32, null=True)
    age = IntegerField(null=True)
    account_id = IntegerField()


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
    db_proxy.create_tables([
        Query,
        Seed,
        Search,
        SearchResult,
        SearchResultContent,
        Post,
        Tag,
        PostHistory,
        PostLink,
        Vote,
        Comment,
        Badge,
        User,
    ], safe=True)
