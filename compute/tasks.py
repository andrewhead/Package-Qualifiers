#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import subprocess
import sys
import os.path


logger = logging.getLogger('data')
TASK_PARSER_JAR = "task-parser-jar-with-dependencies.jar"
TASK_PARSER_BUCKET_URL = "https://s3-us-west-2.amazonaws.com/package-qualifiers-public/"
MODULE_DIRECTORY = '/'.join(__name__.split('.')[:-1])


def main(db_config, *args, **kwargs):

    # Fetch the JAR for task extraction, but only if it has been updated (-N flag)
    jar_url = TASK_PARSER_BUCKET_URL + TASK_PARSER_JAR
    logger.info("Downloading the task extractor from: %s", jar_url)
    subprocess.call(['wget', '-N', jar_url, '-P', MODULE_DIRECTORY], stdout=sys.stdout)

    # Launch the task extractor
    subprocess.call(['java', '-jar', os.path.join(MODULE_DIRECTORY, TASK_PARSER_JAR), db_config])


def configure_parser(parser):
    parser.description = "Extract and store programming tasks from web page content."
