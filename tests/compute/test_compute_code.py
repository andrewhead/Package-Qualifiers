#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import unittest
from bs4 import BeautifulSoup

from compute.code import CodeExtractor


logging.basicConfig(level=logging.INFO, format="%(message)s")


class ExtractCodeTest(unittest.TestCase):

    def setUp(self):
        self.code_extractor = CodeExtractor()

    def _extract_code(self, document):
        return self.code_extractor.extract(document)

    def _make_document_with_body(self, body):
        return BeautifulSoup('\n'.join([
            "<html>",
            "  <body>",
            body,
            "  </body>",
            "</html>",
        ]), 'html.parser')

    def test_extract_valid_javascript(self):
        document = self._make_document_with_body("<code>var i = 0;</code")
        snippets = self.code_extractor.extract(document)
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0], "var i = 0;")

    def test_extract_valid_javascript_with_padding(self):
        # In the past, some parsers I have used have had trouble parsing with whitespace
        # surrounding the parsed content.  This is a sanity test to make sure that the
        # backend parser will still detect JavaScript padded with whitespace.
        document = self._make_document_with_body("<code>\n\n\t    var i = 0;\t  \n</code>")
        snippets = self.code_extractor.extract(document)
        self.assertEqual(snippets[0], "\n\n\t    var i = 0;\t  \n")

    def test_extract_valid_multiline_javascript(self):
        document = self._make_document_with_body('\n'.join([
            "<code>for (var i = 0; i < 2; i++) {",
            "    console.log(\"Hello, world!\");",
            "}</code>",
        ]))
        snippets = self.code_extractor.extract(document)
        self.assertEqual(snippets[0], '\n'.join([
            "for (var i = 0; i < 2; i++) {",
            "    console.log(\"Hello, world!\");",
            "}",
        ]))

    def test_extract_multiple_blocks(self):
        document = self._make_document_with_body('\n'.join([
            "<code>var i = 0;</code>",
            "<code>i = i + 1;</code>",
        ]))
        snippets = self.code_extractor.extract(document)
        self.assertEqual(len(snippets), 2)
        self.assertIn("var i = 0;", snippets)
        self.assertIn("i = i + 1;", snippets)

    def test_fail_to_detect_text_in_code_block(self):
        document = self._make_document_with_body("<code>This is a plain English sentence.</code>")
        snippets = self.code_extractor.extract(document)
        self.assertEqual(len(snippets), 0)

    def test_fail_to_detect_command_line(self):
        document = self._make_document_with_body("<code>npm install package</code>")
        snippets = self.code_extractor.extract(document)
        self.assertEqual(len(snippets), 0)

    def test_skip_whitespace_only(self):
        document = self._make_document_with_body("<code>\t \n</code>")
        snippets = self.code_extractor.extract(document)
        self.assertEqual(len(snippets), 0)

    # In practice I don't expect the next two scenarios to come up.  But the expected behavior of
    # the code extractor is to scan children of all nodes that are marked as invalid.  This
    # test makes sure that functionality is correct.
    def test_skip_child_of_code_block_parent(self):
        document = self._make_document_with_body('\n'.join([
            "<code>",
            "var outer = 0;",
            "<code>var inner = 1;</code>",
            "</code>",
        ]))
        snippets = self.code_extractor.extract(document)
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0], '\n'.join([
            "",
            "var outer = 0;",
            "var inner = 1;",
            "",
        ]))

    def test_detect_code_block_nested_inside_invalid_code_block(self):
        document = self._make_document_with_body('\n'.join([
            "<code>",
            " This plaintext invalidates this block as a whole.",
            " <code>var i = 0; // But this child will be valid</code>",
            "</code>",
        ]))
        snippets = self.code_extractor.extract(document)
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0], "var i = 0; // But this child will be valid")
