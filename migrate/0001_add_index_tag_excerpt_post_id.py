#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from playhouse.migrate import migrate


logger = logging.getLogger('data')


def forward(migrator):
    migrate(
        migrator.add_index('tag', ('excerpt_post_id',), False)
    )
