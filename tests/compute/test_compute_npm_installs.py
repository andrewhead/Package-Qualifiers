#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from tests.base import TestCase
from tests.modelfactory import create_post, create_tag
from compute.npm_packages import extract_npm_install_packages
from models import Post, PostTag, Tag, PostNpmInstallPackage


logger = logging.getLogger('data')


class ExtractNpmInstallsTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(ExtractNpmInstallsTest, self).__init__(
            [Post, PostTag, Tag, PostNpmInstallPackage],
            *args, **kwargs
        )

    def _extract(self):
        extract_npm_install_packages(0)

    def _create_post(self, body, tag_name='node.js'):
        post = create_post(body=self._make_post_body(body))
        tag = create_tag(tag_name=tag_name)
        PostTag.create(post_id=post.id, tag_id=tag.id)
        return post

    def _make_post_body(self, code):
        return '\n'.join([
            '<div>',
            '  <pre>',
            '    <code>' + code + '</code>',
            '  </pre>',
            '</div>',
        ])

    def test_extract_package_from_simple_npm_install(self):

        post = self._create_post('npm install coffee-script')
        self._extract()

        # We should have found one package that was npm-installed.
        # This package should maintain a link back to the post it was found in
        self.assertEqual(PostNpmInstallPackage.select().count(), 1)
        package = PostNpmInstallPackage.select().first()
        self.assertEqual(package.package, 'coffee-script')
        self.assertEqual(package.post, post)

    def test_extract_package_for_node_js_and_npm_tags_only(self):
        self._create_post('npm install found1', tag_name='node.js')
        self._create_post('npm install found2', tag_name='npm')
        self._create_post('npm install not-found', tag_name='irrelevanttag')
        self._extract()
        package_names = [package.package for package in PostNpmInstallPackage.select()]
        self.assertIn('found1', package_names)
        self.assertIn('found2', package_names)
        self.assertNotIn('not-found', package_names)

    def test_extract_multiple_packages_from_one_npm_install(self):
        self._create_post('npm install coffee-script browserify')
        self._extract()
        self.assertEqual(PostNpmInstallPackage.select().count(), 2)
        package_names = [package.package for package in PostNpmInstallPackage.select()]
        self.assertIn('coffee-script', package_names)
        self.assertIn('browserify', package_names)

    def test_skip_npm_install_if_not_left_aligned(self):
        self._create_post('ls && npm install coffee-script')
        self._extract()
        self.assertEqual(PostNpmInstallPackage.select().count(), 0)

    def test_extract_package_if_npm_install_after_newline(self):
        self._create_post('\n'.join([
            'cd directory/',
            'npm install coffee-script'
        ]))
        self._extract()
        self.assertEqual(PostNpmInstallPackage.select().count(), 1)

    def test_extract_packages_from_multiple_npm_installs(self):
        self._create_post('\n'.join([
            'npm install browserify',
            'ls directory/',
            'npm install coffee-script'
        ]))
        self._extract()
        self.assertEqual(PostNpmInstallPackage.select().count(), 2)

    def test_ignore_npm_options(self):
        # This command line includes short options, long options, and option-value pairs
        self._create_post('npm install -g --nodedir=/tmp/ --only production coffee-script')
        self._extract()
        self.assertEqual(PostNpmInstallPackage.select().count(), 1)
        self.assertEqual(PostNpmInstallPackage.select().first().package, 'coffee-script')

    def test_ignore_scope_and_versions_and_tags_in_package_name(self):
        # At the time of writing this test, the npm-install man page stated that npm install could
        # strings of any of the following formats:
        #
        # npm install
        # npm install [<@scope>/]<name>
        # npm install [<@scope>/]<name>@<tag>
        # npm install [<@scope>/]<name>@<version>
        # npm install [<@scope>/]<name>@<version range>
        # npm install <tarball file>
        # npm install <tarball url>
        # npm install <folder>
        #
        # For formats 2-5, we make sure to extract only the part of the argument that corresponds
        # to an actual package name, and not its scope, tag or version name
        self._create_post('\n'.join([
            'npm install @myorg/coffee-script',  # scope
            'npm install coffee-script@latest',  # tag
            'npm install coffee-script@0.1.1',  # version
            'npm install coffee-script@">=0.1.0 <0.2.0"',  # version range
            'npm install @myorg/coffee-script@0.1.1',  # scope and version
        ]))
        self._extract()
        self.assertEqual(PostNpmInstallPackage.select().count(), 5)
        package_names = [package.package for package in PostNpmInstallPackage.select()]
        distinct_package_names = list(set(package_names))
        self.assertEqual(len(distinct_package_names), 1)
        self.assertEqual(distinct_package_names[0], 'coffee-script')
