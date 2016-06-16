#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import json
import functools
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker

from fetch.api import github_get, GITHUB_API_URL
from models import GitHubProject, Issue
from lock import lock_method


logger = logging.getLogger('data')


LOCK_FILENAME = '/tmp/issues-fetcher.lock'


def get_issues_for_projects(projects, show_progress):

    if show_progress:
        progress_bar = ProgressBar(maxval=len(projects), widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Processing project ', Counter(), ' / ' + str(len(projects)) + '.'
        ])
        progress_bar.start()

    # Create a new fetch index
    last_fetch_index = GitHubProject.select(fn.Max(GitHubProject.fetch_index)).scalar() or 0
    fetch_index = last_fetch_index + 1

    for project_index, project in enumerate(projects, start=1):

        # Create a new record for the project based on the JSON specification
        project = GitHubProject.create(
            fetch_index=fetch_index,
            name=project['name'],
            owner=project['owner'],
            repo=project['repo'],
        )

        # Wrap a callback that will save issues associated to this project and fetch index.
        save_issues_callback = functools.partial(
            save_issues,
            project=project,
            fetch_index=fetch_index,
        )

        # Fetch all issues for the project from GitHub
        github_get(
            start_url=GITHUB_API_URL + '/repos/' + project.owner + '/' + project.repo + '/issues',
            results_callback=save_issues_callback,
            params={
                'state': 'all',
            }
        )

        if show_progress:
            progress_bar.update(project_index)

    if show_progress:
        progress_bar.finish()


def save_issues(issues, project, fetch_index):
    for issue in issues:
        Issue.create(
            fetch_index=fetch_index,
            github_id=issue['id'],
            project=project,
            number=issue['number'],
            created_at=issue['created_at'],
            updated_at=issue['updated_at'],
            closed_at=issue['closed_at'],
            state=issue['state'],
            body=issue['body'],
            comments=issue['comments'],
        )


@lock_method(LOCK_FILENAME)
def main(projects, show_progress, *args, **kwargs):

    # Fetch autocomplete results
    with open(projects) as projects_file:
        project_list = json.load(projects_file)
        get_issues_for_projects(project_list, show_progress)


def configure_parser(parser):
    parser.description = "Fetch GitHub issues for a set of GitHub projects."
    parser.add_argument(
        'projects',
        help="a JSON file containing records of project names, owners, and repository names."
    )
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress of the number of projects for which issues have been saved."
    )
