#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from progressbar import ProgressBar, Percentage, Bar, ETA, Counter, RotatingMarker
from slimit.parser import Parser as JavaScriptParser
from bs4 import BeautifulSoup, Tag
from peewee import fn
import re

from models import WebPageContent, Code


logger = logging.getLogger('data')


class CodeExtractor(object):
    '''
    This code has been written by consulting the code for scanning HTML
    documents for source code from the Tutorons server project:
    https://github.com/andrewhead/tutorons-server
    '''

    def __init__(self):
        # We only extract code from 'pre' and 'code' elements.
        self.TAGS = ['pre', 'code']

    def extract(self, node):
        '''
        Given a BeautifulSoup representation of an HTML document,
        return a list of all code snippets in that document.
        '''

        node_code = None
        code_snippets = []

        # Attempt to parse content for a code node as JavaScript.
        # Mark the content as a code snippet if it is parsed successfully.
        # Skip nodes with nothing but whitespace content.
        if type(node) is Tag and node.name in self.TAGS:
            if node.text.strip() != '':
                try:
                    js_parser = JavaScriptParser()
                    js_parser.parse(node.text)
                except (SyntaxError, TypeError, AttributeError):
                    logging.debug("Code content could not be parsed as JavaScript.")
                else:
                    node_code = node.text
                    code_snippets.append(node_code)

        # If this node did not contain valid code, then visit all children
        # and check them for code.
        if node_code is None and hasattr(node, 'children'):
            for child_element in node.children:
                code_snippets.extend(self.extract(child_element))

        return code_snippets


def main(show_progress, *args, **kwargs):

    if show_progress:
        web_page_count = WebPageContent.select().count()
        progress_bar = ProgressBar(maxval=web_page_count, widgets=[
            'Progress: ', Percentage(),
            ' ', Bar(marker=RotatingMarker()),
            ' ', ETA(),
            ' Processing web page ', Counter(), ' / ' + str(web_page_count) + '.'
        ])
        progress_bar.start()

    # Create a new index for this computation
    last_compute_index = Code.select(fn.Max(Code.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # For each web page, we extract all code snippets and create a new record
    # for each snippet, saving the code's plaintext.
    code_extractor = CodeExtractor()
    for web_page_index, web_page in enumerate(WebPageContent.select(), start=1):

        document = BeautifulSoup(web_page.content, 'html.parser')
        snippets = code_extractor.extract(document)

        for snippet in snippets:

            # Screen snippets to those that have more than one space-delimited word.
            # This is to avoid storing single words referring to entities in code examples.
            word_count = len(re.split('\s', snippet.strip()))
            if word_count > 1:
                Code.create(
                    compute_index=compute_index,
                    code=snippet,
                    web_page=web_page,
                )

        if show_progress:
            progress_bar.update(web_page_index)

    if show_progress:
        progress_bar.finish()


def configure_parser(parser):
    parser.description =\
        "Extract JavaScript code snippets from web documents.  Note that you'll see output " +\
        "junk from the slimit parser as it tries to lex and parse web page content.  " +\
        "This is expected and, at the moment, unavoidable if you want to see progress output."
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help="Show progress of the number of web pages scanned."
    )
