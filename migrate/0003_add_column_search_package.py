#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from playhouse.migrate import migrate
from peewee import TextField


logger = logging.getLogger('data')


def forward(migrator):
    migrate(
        migrator.add_column('search', 'package', TextField(null=True)),
        migrator.add_index('search', ('package',)),
    )
