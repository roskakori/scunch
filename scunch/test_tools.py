"""
Tests for `_tools`.
"""
# Copyright (C) 2011 - 2013 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import

import logging
import os
import tempfile
import unittest

from scunch import _tools

_log = logging.getLogger("test")


class FolderTest(_tools.LoggableTestCase):
    def testCanMessWithFolders(self):
        testFolderPath = tempfile.mkdtemp(prefix="scunch_test_")
        _tools.removeFolder(testFolderPath)
        self.assertFalse(os.path.exists(testFolderPath))

        _tools.makeFolder(testFolderPath)
        self.assertTrue(os.path.exists(testFolderPath))
        _tools.makeFolder(testFolderPath)

        _tools.removeFolder(testFolderPath)
        _tools.makeEmptyFolder(testFolderPath)
        _tools.makeEmptyFolder(testFolderPath)

        # Clean up.
        _tools.removeFolder(testFolderPath)


class HumanReadableListTest(_tools.LoggableTestCase):
    def testRendersEmptyListAsEmptyText(self):
        self.assertEqual(u'', _tools.humanReadableList([]))

    def testRendersSingleItemWithoutSeparator(self):
        self.assertEqual(u"'red'", _tools.humanReadableList(['red']))

    def testRendersTwoItemsWithOr(self):
        self.assertEqual(u"'red' or 'green'", _tools.humanReadableList(['red', 'green']))

    def testRendersMutipleItemsWithCommaAndOr(self):
        self.assertEqual(u"'red', 'green' or 'blue'", _tools.humanReadableList(['red', 'green', 'blue']))


class OneOrOtherTextTest(_tools.LoggableTestCase):
    def testShows0AsPlural(self):
        self.assertEqual(u'0 items', _tools.oneOrOtherText(0, 'item', 'items'))

    def testShows1AsSingular(self):
        self.assertEqual(u'1 item', _tools.oneOrOtherText(1, 'item', 'items'))

    def testShows2AsPlural(self):
        self.assertEqual(u'2 items', _tools.oneOrOtherText(2, 'item', 'items'))


class BundledPathsTest(_tools.LoggableTestCase):
    def testCanBundlePaths(self):
        self.assertEqual(
            list(_tools.bundledPathsToRun(['c'], ['1', '2', '3'])),
            [['1', '2', '3']])

    def testCanBundleEmptyPaths(self):
        self.assertEqual(
            list(_tools.bundledPathsToRun(['c'], [])),
            [])

    def testCanSplitBundle(self):
        manyPathsBundle = list(_tools.bundledPathsToRun(['c'], ['1', 'two.txt', 'three.jpeg', '0004.tmp', '5', 'six.six'], 15))
        logging.info(manyPathsBundle)
        self.assertEqual(
            manyPathsBundle,
            [['1'], ['two.txt'], ['three.jpeg'], ['0004.tmp'], ['5'], ['six.six']])

    def testCanSplitLargeBundle(self):
        manyPathsBundle = list(_tools.bundledPathsToRun(['c'], [(str(i) + '.txt') for i in xrange(100)], 15))
        self.assertNotEqual(len(manyPathsBundle), 1)


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    unittest.main()
