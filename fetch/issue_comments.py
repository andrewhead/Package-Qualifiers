#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import functools
import re
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker

from fetch.api import github_get, GITHUB_API_URL
from models import GitHubProject, Issue, IssueComment, BatchInserter
from lock import lock_method


logger = logging.getLogger('data')
LOCK_FILENAME = '/tmp/issue-comments-fetcher.lock'
issue_cache = {}
batch_inserter = BatchInserter(IssueComment, batch_size=100)


def get_issue_comments(show_progress):

    # Retrieve the list of all projects for which issue comments should be fetched.
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
    last_fetch_index = IssueComment.select(fn.Max(IssueComment.fetch_index)).scalar() or 0
    fetch_index = last_fetch_index + 1
    issue_fetch_index = Issue.select(fn.Max(Issue.fetch_index)).scalar() or 0

    for project_index, project in enumerate(github_projects, start=1):

        # Wrap a callback that will save fetched comments
        save_comments_callback = functools.partial(
            save_comments,
            project=project,
            fetch_index=fetch_index,
            issue_fetch_index=issue_fetch_index,
        )

        # Fetch all comments for all issues for the project
        github_get(
            start_url=(
                GITHUB_API_URL + '/repos/' + project.owner + '/' +
                project.repo + '/issues/comments'
            ),
            results_callback=save_comments_callback,
        )

        if show_progress:
            progress_bar.update(project_index)

    if show_progress:
        progress_bar.finish()

    # Make sure that all records from the batch inserter have been written out
    batch_inserter.flush()


def save_comments(comments, project, fetch_index, issue_fetch_index):

    # This inline function provides a unique key for caching issues based
    # on the number of the issue and the project.
    make_issue_key = lambda project, issue_number:\
        project.owner + '/' + project.repo + '/' + str(issue_number)

    for comment in comments:

        # Get the number of the issue that is associated with this comment
        issue_number = re.match('.*/issues/(\d+)$', comment['issue_url']).group(1)

        # Check the cache for the associated issue.  If it's not present in the cache,
        # fetch it and then store it in the cache.
        # We query only for a specific version of the issue (fetched with a certain fetch index).
        issue_key = make_issue_key(project, issue_number)
        if issue_key not in issue_cache:
            latest_issue_version = (
                Issue
                .select()
                .join(GitHubProject)
                .where(
                    GitHubProject.repo == project.repo,
                    GitHubProject.owner == project.owner,
                    Issue.number == issue_number,
                    Issue.fetch_index == issue_fetch_index,
                )
            )
            issue_cache[issue_key] = latest_issue_version.first()\
                if latest_issue_version.count() != 0 else None

        # Retrive the issue from the cache.  If it is found, then create a comment
        # associated with this issue.
        issue = issue_cache[issue_key]
        if issue is not None:
            batch_inserter.insert({
                'fetch_index': fetch_index,
                'github_id': comment['id'],
                'issue': issue,
                'created_at': comment['created_at'],
                'updated_at': comment['updated_at'],
                'body': comment['body'],
            })


@lock_method(LOCK_FILENAME)
def main(show_progress, *args, **kwargs):
    get_issue_comments(show_progress)


def configure_parser(parser):
    parser.description = "Fetch all comments for the latest fetched issues."
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress of the number of projects for which issue comments have been saved."
    )
