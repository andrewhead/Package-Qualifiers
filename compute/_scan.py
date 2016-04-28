#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from bs4 import Tag
import copy


logger = logging.getLogger('data')


class NodeScanner(object):
    '''
    Scans HTML document (as BeautifulSoup object) for text fragments matching some criteria.
    This criteria is defined by an extractor.  The extractor is applied to each node
    in a post-order traversal.  It takes a node and produces a set of "snippets".
    This class was reused from the Tutorons server code:
    https://github.com/andrewhead/tutorons-server
    '''

    def __init__(self, extractor, tags):
        ''' The scanner only inspects elements with tags specified by the list `tags` '''
        self.extractor = extractor
        self.tags = tags

    def scan(self, document):
        return self.visit(document)

    def visit(self, node):

        snippets = []
        children_with_snippets = []

        # Do a post-order traversal of the nodes in the tree
        if hasattr(node, 'children'):
            for c in node.children:
                child_snippets = self.visit(c)
                snippets.extend(child_snippets)
                if len(child_snippets) >= 1:
                    children_with_snippets.append(c)

        # To avoid sensing the same snippet twice, we 'blank out' elements in which
        # snippets have been detected so that the same snippet can't be detected in its parent.
        if type(node) is Tag and node.name in self.tags:
            node_clone = copy.copy(node)
            for c in node_clone.children:
                if c in children_with_snippets:
                    c.replace_with(' ' * len(c.text))

            # We apply the extractor to the current node to find its snippets
            node_snippets = self.extractor.extract(node_clone)
            snippets.extend(node_snippets)

        return snippets
