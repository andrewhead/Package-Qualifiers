#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from playhouse.migrate import migrate


logging.basicConfig(level=logging.INFO, format="%(message)s")


def forward(migrator):
    migrate(
        migrator.add_index('tag', ('excerpt_post_id',), False)
    )
