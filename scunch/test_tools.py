"""
Tests for `_tools`.
"""
# Copyright (C) 2011 - 2012 Thomas Aglassinger
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


class FolderTest(unittest.TestCase):
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


class HumanReadableListTest(unittest.TestCase):
    def testRendersEmptyListAsEmptyText(self):
        self.assertEqual(u'', _tools.humanReadableList([]))

    def testRendersSingleItemWithoutSeparator(self):
        self.assertEqual(u"'red'", _tools.humanReadableList(['red']))

    def testRendersTwoItemsWithOr(self):
        self.assertEqual(u"'red' or 'green'", _tools.humanReadableList(['red', 'green']))

    def testRendersMutipleItemsWithCommaAndOr(self):
        self.assertEqual(u"'red', 'green' or 'blue'", _tools.humanReadableList(['red', 'green', 'blue']))


class OneOrOtherTextTest(unittest.TestCase):
    def testShows0AsPlural(self):
        self.assertEqual(u'0 items', _tools.oneOrOtherText(0, 'item', 'items'))

    def testShows1AsSingular(self):
        self.assertEqual(u'1 item', _tools.oneOrOtherText(1, 'item', 'items'))

    def testShows2AsPlural(self):
        self.assertEqual(u'2 items', _tools.oneOrOtherText(2, 'item', 'items'))

if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    unittest.main()
