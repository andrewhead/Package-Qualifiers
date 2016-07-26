#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from playhouse.migrate import migrate
from peewee import IntegerField


logger = logging.getLogger('data')


def forward(migrator):
    migrate(
        migrator.add_column(
            'issue',
            'user_id',
            IntegerField(
                index=True,
                null=True,
                default=None
            )
        ),
        migrator.add_column(
            'issuecomment',
            'user_id',
            IntegerField(
                index=True,
                null=True,
                default=None
            )
        ),
    )
