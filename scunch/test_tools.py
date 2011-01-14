"""
Tests for scunch.
"""
# Copyright (C) 2011 Thomas Aglassinger
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
import logging
import os
import tempfile
import unittest

import _tools

_log = logging.getLogger("test")

class FolderTest(unittest.TestCase):
    def testFolderFunctions(self):
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

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
