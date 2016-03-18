#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import xml.etree.cElementTree as etree
import re
import peewee
import os.path
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker

from models import Post, Tag, PostHistory, PostLink, Vote, Comment, Badge, User


logging.basicConfig(level=logging.INFO, format="%(message)s")

# This is a map from names of data types to the models they correspond to.
# To enable importing a new type of data, one should define a new model
# in the models module, and then add an entry here.
DATA_TYPES = {
    'posts': Post,
    'tags': Tag,
    'post-histories': PostHistory,
    'post-links': PostLink,
    'votes': Vote,
    'comments': Comment,
    'badges': Badge,
    'users': User,
}


def camel_case_to_underscores(string):
    '''
    Method courtesy of Stack Overflow user epost:
    http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    '''
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def main(data_type, data_file, show_progress, *args, **kwargs):
    '''
    Parsing procedure is based on a script by a user on the Meta Stack Exchange:
    http://meta.stackexchange.com/questions/28221/scripts-to-convert-data-dump-to-other-formats
    '''

    # Fetch the type of database model that we'll be creating
    Model = DATA_TYPES[data_type]

    # Set up progress bar.
    if show_progress:
        file_size = os.path.getsize(data_file)
        progress_bar = ProgressBar(maxval=file_size, widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Read ', Counter(), ' characters.'
        ])
        progress_bar.start()
        amount_read = 0

    # Read data from XML file and load it into the table
    with open(data_file) as data_file_obj:

        tree = etree.iterparse(data_file_obj)
        for event, row in tree:

            # Check that this is a primary record in the file
            if not (event == 'end' and row.tag == 'row'):
                continue

            # Format attributes as kwargs for creating the model
            attributes = row.attrib
            renamed_attributes = {camel_case_to_underscores(k): v for k, v in attributes.items()}

            # Records shouldn't have a 'class' field, as this conflicts with Python syntax
            if 'class' in renamed_attributes.keys():
                renamed_attributes['class_'] = renamed_attributes['class']
                del(renamed_attributes['class'])

            # Create the entry with all of the attributes found in the XML
            try:
                Model.create(**renamed_attributes)
            except peewee.IntegrityError as e:
                logging.warn(
                    "IntegrityError (%s) adding record %d. " +
                    "It may have already been added to the database",
                    str(e), int(renamed_attributes['id']),
                )

            if show_progress:
                string_size = len(etree.tostring(row))
                amount_read += string_size
                progress_bar.update(amount_read)

    if show_progress:
        progress_bar.finish()


def configure_parser(parser):
    parser.description = "Import data from a Stack Overflow dump."
    parser.add_argument(
        'data_type',
        choices=DATA_TYPES.keys(),
        help="The type of data to import."
    )
    parser.add_argument(
        'data_file',
        help="XML file containing a dump of Stack Overflow data."
    )
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress in loading content from the file. " +
        "Note that this may slow down execution as the program will have " +
        "to count the amount of the file that is being read."
    )
