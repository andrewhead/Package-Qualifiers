#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from playhouse.migrate import migrate


logger = logging.getLogger('data')


def forward(migrator):
    # This migration may take some time to run.
    # It adds indexes to integer fields that should have been indexed all
    # along, for many models.
    migrate(
        migrator.add_index('seed', ('fetch_index',), False),
        migrator.add_index('query', ('fetch_index',), False),
        migrator.add_index('search', ('fetch_index',), False),
        migrator.add_index('webpageversion', ('fetch_index',), False),
        migrator.add_index('questionsnapshot', ('fetch_index',), False),
        migrator.add_index('githubproject', ('fetch_index',), False),
        migrator.add_index('issue', ('fetch_index',), False),
        migrator.add_index('issuecomment', ('fetch_index',), False),
        migrator.add_index('issueevent', ('fetch_index',), False),
        migrator.add_index('postsnippet', ('compute_index',), False),
        migrator.add_index('postnpminstallpackage', ('compute_index',), False),
        migrator.add_index('task', ('compute_index',), False),
    )
