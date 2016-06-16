#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import functools
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker

from fetch.api import github_get, GITHUB_API_URL
from models import GitHubProject, Issue, IssueEvent, BatchInserter
from lock import lock_method


logger = logging.getLogger('data')
LOCK_FILENAME = '/tmp/issue-events-fetcher.lock'
issue_cache = {}
batch_inserter = BatchInserter(IssueEvent, batch_size=100)


def get_issue_events(show_progress):

    # Retrieve the list of all projects for which issue events should be fetched.
    github_projects = (
        GitHubProject
        .select(GitHubProject.owner, GitHubProject.repo)
        .group_by(GitHubProject.owner, GitHubProject.repo)
    )

    if show_progress:
        progress_bar = ProgressBar(maxval=github_projects.count(), widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Processing project ', Counter(), ' / ' + str(github_projects.count()) + '.'
        ])
        progress_bar.start()

    # Create a new fetch index
    last_fetch_index = IssueEvent.select(fn.Max(IssueEvent.fetch_index)).scalar() or 0
    fetch_index = last_fetch_index + 1
    issue_fetch_index = Issue.select(fn.Max(Issue.fetch_index)).scalar() or 0

    for project_index, project in enumerate(github_projects, start=1):

        # Wrap a callback that will save fetched events
        save_events_callback = functools.partial(
            save_events,
            project=project,
            fetch_index=fetch_index,
            issue_fetch_index=issue_fetch_index,
        )

        # Fetch all events for all issues for the project
        github_get(
            start_url=(
                GITHUB_API_URL + '/repos/' + project.owner + '/' +
                project.repo + '/issues/events'
            ),
            results_callback=save_events_callback,
        )

        if show_progress:
            progress_bar.update(project_index)

    if show_progress:
        progress_bar.finish()

    # Make sure that all records from the batch inserter have been written out
    batch_inserter.flush()


def save_events(events, project, fetch_index, issue_fetch_index):

    for event in events:

        # Only process this event if it has a record of the issue it is associated with.
        # We have found that this field is missing for some event records.
        if event['issue'] is None:
            continue

        # Get the ID of the issue that is associated with this event
        issue_id = event['issue']['id']

        # Check the cache for the associated issue.  If it's not present in the cache,
        # fetch it and then store it in the cache.
        # We query only for a specific version of the issue (fetched with a certain fetch index).
        if issue_id not in issue_cache:
            latest_issue_version = (
                Issue
                .select()
                .where(
                    Issue.github_id == issue_id,
                    Issue.fetch_index == issue_fetch_index,
                )
            )
            issue_cache[issue_id] = latest_issue_version.first()\
                if latest_issue_version.count() != 0 else None

        # Retrive the issue from the cache.  If it is found, then create a event
        # associated with this issue.
        issue = issue_cache[issue_id]
        if issue is not None:
            batch_inserter.insert({
                'fetch_index': fetch_index,
                'github_id': event['id'],
                'issue': issue,
                'event': event['event'],
                'created_at': event['created_at'],
            })


@lock_method(LOCK_FILENAME)
def main(show_progress, *args, **kwargs):
    get_issue_events(show_progress)


def configure_parser(parser):
    parser.description = "Fetch all events for the latest fetched issues."
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress of the number of projects for which issue events have been saved."
    )
