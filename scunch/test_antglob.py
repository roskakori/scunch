"""
Tests for `antglob`.
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

import errno
import logging
import os
import shutil
import tempfile
import unittest

from scunch import antglob

_log = logging.getLogger('test')


class TextItemsTest(unittest.TestCase):
    def testCanFindTextItemsInPatternItems(self):
        pattern = antglob.AntPattern('a/b/*_tmp/*.txt')
        patternItems = pattern.patternItems
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts('a'), patternItems))
        self.assertFalse(antglob._textItemsAreInPatternItems(antglob._splitTextParts('!'), patternItems))
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts('a/b'), patternItems))
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts('b'), patternItems))
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts('b/hugo_tmp'), patternItems))
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts('hugo.txt'), patternItems))

    def testCanFindTextItemsAtEndOfPatternItems(self):
        pattern = antglob.AntPattern('a/b/*_tmp/*.txt')
        patternItems = pattern.patternItems
        self.assertTrue(antglob._textItemsAreAtEndOfPatternItems(antglob._splitTextParts('hugo.txt'), patternItems))
        self.assertFalse(antglob._textItemsAreAtEndOfPatternItems(antglob._splitTextParts('a'), patternItems))
        self.assertFalse(antglob._textItemsAreAtEndOfPatternItems(antglob._splitTextParts('txt'), patternItems))

    def testCanFindTextItemsPartForPatternItems(self):
        pattern = antglob.AntPattern('a?c/d*')
        patternItems = pattern.patternItems
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts('abc/d'), patternItems), 0)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts('0/abc/d'), patternItems), 1)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts('abc/d/e'), patternItems), 0)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts('abc'), patternItems), None)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts('cannot/find/me'), patternItems), None)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts(''), patternItems), None)


class AntPatternTest(unittest.TestCase):
    def testShowsAsString(self):
        def _assertShows(self, pattern):
            assert pattern is not None
            self.assertTrue(unicode(pattern))
            self.assertTrue(str(pattern))
            self.assertTrue(repr(pattern))

        _assertShows(self, antglob.AntPattern('hugo'))
        _assertShows(self, antglob.AntPattern('hugo/sepp'))
        _assertShows(self, antglob.AntPattern('hugo/*.png'))
        _assertShows(self, antglob.AntPattern('**/*.png'))
        _assertShows(self, antglob.AntPattern(''))
        _assertShows(self, antglob.AntPattern('folder/'))

    def testCanFindListInList(self):
        self.assertEqual(antglob._findListInList([2], [5, 4, 2, 7]), 2)
        self.assertEqual(antglob._findListInList([5], [5, 4, 2, 7]), 0)
        self.assertEqual(antglob._findListInList([7], [5, 4, 2, 7]), 3)
        self.assertEqual(antglob._findListInList([17], [5, 4, 2, 7]), None)
        self.assertEqual(antglob._findListInList([5, 4], [5, 4, 2, 7]), 0)
        self.assertEqual(antglob._findListInList([4, 2], [5, 4, 2, 7]), 1)
        self.assertEqual(antglob._findListInList([2, 7], [5, 4, 2, 7]), 2)
        self.assertEqual(antglob._findListInList([4, 3], [5, 4, 2, 7]), None)

    def testCanMatchPatternsWithoutPlaceholders(self):
        pattern = antglob.AntPattern('hugo')
        self.assertTrue(pattern.matches('hugo'))
        self.assertFalse(pattern.matches('sepp'))
        self.assertFalse(pattern.matches(''))

        pattern = antglob.AntPattern('a/b/c')
        self.assertTrue(pattern.matches('a/b/c'))
        self.assertFalse(pattern.matches(''))
        self.assertFalse(pattern.matches('a'))
        self.assertFalse(pattern.matches('b'))
        self.assertFalse(pattern.matches('a/b'))
        self.assertFalse(pattern.matches('a/b/xxx'))
        self.assertFalse(pattern.matches('a/b/xxx/c'))
        self.assertFalse(pattern.matches('a/b/c/d'))

    def testCanMatchPatternsWithPlaceHolders(self):
        pattern = antglob.AntPattern('*.txt')
        self.assertTrue(pattern.matches('hugo.txt'))
        self.assertFalse(pattern.matches('hugo.txtx'))
        self.assertFalse(pattern.matches('sepp.png'))
        self.assertFalse(pattern.matches(''))

        pattern = antglob.AntPattern('*')
        self.assertTrue(pattern.matches('x'))
        self.assertTrue(pattern.matches(''))

    def testCanMatchPatternsWithAllMagic(self):
        pattern = antglob.AntPattern('**')
        self.assertTrue(pattern.matches('hugo.txt'))
        self.assertTrue(pattern.matches(''))

        pattern = antglob.AntPattern('**/*.txt')
        self.assertTrue(pattern.matches('hugo.txt'))
        self.assertTrue(pattern.matches('texts/hugo.txt'))
        self.assertTrue(pattern.matches('1/2/3/4/hugo.txt'))
        self.assertFalse(pattern.matches('hugo.png'))
        self.assertFalse(pattern.matches('hugo.txt/hugo.png'))
        self.assertFalse(pattern.matches(''))

    def testCanMatchPatternsWithMultipleAllMagics(self):
        pattern = antglob.AntPattern('**/b/**')
        self.assertTrue(pattern.matches('b'))
        self.assertTrue(pattern.matches('b/hugo.txt'))
        self.assertTrue(pattern.matches('a/b/hugo.txt'))
        self.assertTrue(pattern.matches('x/y/a/b/c/hugo.txt'))
        self.assertFalse(pattern.matches('bb/hugo.txt'))
        self.assertFalse(pattern.matches(''))

        pattern = antglob.AntPattern('**/data/2010*/**/some/*.csv')
        self.assertFalse(pattern.matches('x/data/20101130/projects/other/hugo.csv'))
        self.assertTrue(pattern.matches('x/data/20101130/projects/some/hugo.csv'))
        self.assertFalse(pattern.matches('x/dump/20101130/projects/some/hugo.csv'))
        self.assertFalse(pattern.matches(''))

        pattern = antglob.AntPattern('**/b?/**')
        self.assertTrue(pattern.matches('b1'))
        self.assertTrue(pattern.matches('a/b1/hugo.txt'))
        self.assertFalse(pattern.matches('a/b123/hugo.txt'))
        self.assertFalse(pattern.matches(''))

    def testCanMatchAntPatternSet(self):
        patternSet = antglob.AntPatternSet()
        patternSet.include(antglob.AntPattern('*.png'))
        patternSet.include(antglob.AntPattern('*.jpg'))
        self.assertTrue(patternSet.matches('hugo.png'))
        self.assertTrue(patternSet.matches('hugo.jpg'))
        self.assertFalse(patternSet.matches('hugo.txt'))


class AntPatternSetTest(unittest.TestCase):
    def setUp(self):
        self._testFolderPath = tempfile.mkdtemp(prefix='test_antpattern_')
        self.ohsomeSourcePath = os.path.join('ohsome', 'source')
        self.ohsomeSourceUiPath = os.path.join(self.ohsomeSourcePath, 'ui')
        self.ohsomeManualPath = os.path.join('ohsome', 'manual')
        self.makeFolder(os.path.join(self._testFolderPath, self.ohsomeSourcePath))
        self.makeFolder(os.path.join(self._testFolderPath, self.ohsomeSourceUiPath))
        self.makeFolder(os.path.join(self._testFolderPath, self.ohsomeManualPath))
        self.writeTestFile(os.path.join(self.ohsomeSourcePath, 'ohsome.py'))
        self.writeTestFile(os.path.join(self.ohsomeSourcePath, 'tools.py'))
        self.writeTestFile(os.path.join(self.ohsomeSourceUiPath, 'login.py'))
        self.writeTestFile(os.path.join(self.ohsomeSourceUiPath, 'mainwindow.py'))
        self.writeTestFile(os.path.join(self.ohsomeSourceUiPath, 'splash.png'))
        self.writeTestFile(os.path.join(self.ohsomeManualPath, 'tutorial.rst'))
        self.writeTestFile(os.path.join(self.ohsomeManualPath, 'userguide.rst'))
        self.writeTestFile(os.path.join(self.ohsomeManualPath, 'screenshot.png'))
        self.writeTestFile(os.path.join(self.ohsomeManualPath, 'logo.png'))

    def tearDown(self):
        shutil.rmtree(self._testFolderPath)

    def makeFolder(self, folderPathToMake):
        """
        Like `os.makedirs` but does nothing if the folder already exists.
        """
        try:
            os.makedirs(folderPathToMake)
        except OSError, error:  # pragma: no cover
            if error.errno != errno.EEXIST:
                raise

    def writeTestFile(self, relativePathOfFileToWrite, lines=[], baseFolderPath=None):
        assert relativePathOfFileToWrite
        assert lines is not None

        if baseFolderPath is None:
            actualBaseFolderPath = self._testFolderPath
        else:
            actualBaseFolderPath = baseFolderPath
        testFilePath = os.path.join(actualBaseFolderPath, relativePathOfFileToWrite)
        testFile = open(testFilePath, 'wb')
        try:
            for line in lines:
                testFile.write(line)
                testFile.write(os.linesep)
        finally:
            testFile.close()

    def testShowsAsString(self):
        patternSet = antglob.AntPatternSet()

        def _assertShows(self):
            self.assertTrue(unicode(patternSet))
            self.assertTrue(str(patternSet))
            self.assertTrue(repr(patternSet))

        _assertShows(self)
        patternSet.include('hugo, *.png, **/.py,')
        _assertShows(self)
        patternSet.include('sepp, *.gif, **/test*')
        _assertShows(self)

    def testDoesFindFolderOnlyOnce(self):
        textSet = antglob.AntPatternSet()
        textSet.include('**/*.txt')
        testFolderPath = tempfile.mkdtemp(prefix='test_antpattern_')
        someFolderPath = os.path.join(testFolderPath, 'some')
        os.mkdir(someFolderPath)
        self.writeTestFile('other.txt', baseFolderPath=someFolderPath)
        self.writeTestFile('some.txt', baseFolderPath=someFolderPath)
        entries = textSet.findEntries(testFolderPath)
        actualRelativeEntryPaths = sorted([entry.relativePath for entry in entries])
        expectedRelativeEntryPaths = sorted([
            'some' + os.sep,
            os.path.join('some', 'other.txt'),
            os.path.join('some', 'some.txt')
        ])
        self.assertEqual(expectedRelativeEntryPaths, actualRelativeEntryPaths)

    def testCanFindFilesAndfFolders(self):
        pythonSet = antglob.AntPatternSet()
        pythonSet.include('**/*.py, **/*.rst')
        pythonSet.exclude('**/*.pyc, **/*.pyo')
        filePathCount = 0
        folderPathCount = 0
        _log.info('find pattern set: %s', pythonSet)
        for path in pythonSet.find(self._testFolderPath, True):
            _log.info('  found: %s', path)
            if antglob.isFolderPath(path):
                folderPathCount += 1
            else:
                suffix = os.path.splitext(path)[1]
                self.assertTrue(suffix in ('.py', '.rst'))
                filePathCount += 1
        self.assertTrue(filePathCount)
        self.assertTrue(folderPathCount)

    def testCanFindFileIn3NestedFolders(self):
        # Regression test for #21: Fix adding of files within 3 nested otherwise empty folders.
        pythonSet = antglob.AntPatternSet()
        pythonSet.include('**/test.txt')
        nestedFolderPath = os.path.join(self._testFolderPath, '1', '2', '3')
        self.makeFolder(nestedFolderPath)
        self.writeTestFile('test.txt', baseFolderPath=nestedFolderPath)
        filePathCount = 0
        folderPathCount = 0
        for entry in pythonSet._findInFolder(self._testFolderPath, True):
            _log.info(u'  found: %s', entry)
        for entry in pythonSet.findEntries(self._testFolderPath):
            _log.info(u'  found: %s', entry.relativePath)
            if entry.kind == antglob.FileSystemEntry.Folder:
                folderPathCount += 1
            else:
                filePathCount += 1
        self.assertEqual(filePathCount, 1)
        self.assertEqual(folderPathCount, 3)

    def testCanFindFilesInRootFolder(self):
        pythonSet = antglob.AntPatternSet()
        pythonSet.include('**/*.py, **/*.rst')
        pythonSet.exclude('**/*.pyc, **/*.pyo')
        filePathCount = 0
        _log.info('find pattern set: %s', pythonSet)
        for path in pythonSet.find(self._testFolderPath):
            _log.info('  found: %s', path)
            self.assertFalse(antglob.isFolderPath(path), 'path must not be folder: %r' % path)
            suffix = os.path.splitext(path)[1]
            self.assertTrue(suffix in ('.py', '.rst'))
            filePathCount += 1
        self.assertTrue(filePathCount)

    def testCanFindEmptyFolder(self):
        pythonSet = antglob.AntPatternSet()

        # Create a test folder containing exactly 1 empty sub folder.
        testFolderPath = tempfile.mkdtemp(prefix='test_antpattern_')
        emptyFolderPath = os.path.join(testFolderPath, 'emptyFolder')
        os.mkdir(emptyFolderPath)

        pathCount = 0
        for path in pythonSet.find(testFolderPath, True):
            _log.info('  found: %s', path)
            pathCount += 1
            self.assertTrue(antglob.isFolderPath(path), 'path must be a folder: %r' % path)
        self.assertEqual(pathCount, 1)

    def testCanFindEntriesForPatternSet(self):
        pythonSet = antglob.AntPatternSet()
        pythonSet.include('**/*.py, **/*.rst')
        pythonSet.exclude('**/*.pyc, **/*.pyo')
        fileCount = 0
        folderCount = 0
        _log.info('find pattern set: %s', pythonSet)
        for entry in pythonSet.findEntries(self._testFolderPath):
            _log.info('  found: %s', entry)
            if entry.kind == antglob.FileSystemEntry.Folder:
                folderCount += 1
            else:
                self.assertEqual(entry.kind, antglob.FileSystemEntry.File)
                lastPart = entry.parts[-1]
                suffix = os.path.splitext(lastPart)[1]
                self.assertTrue(suffix in ('.py', '.rst'), 'suffix=%r, lastPart=%r' % (suffix, lastPart))
                fileCount += 1
        self.assertTrue(fileCount)
        self.assertTrue(folderCount)


class FileSystemEntryTest(unittest.TestCase):
    def testCanProcessFileEntry(self):
        testFolderPath = tempfile.mkdtemp(prefix='test_antpattern_')
        testFilePath = os.path.join(testFolderPath, 'test.txt')
        testText = 'some test text'
        with open(testFilePath, 'wb') as testFile:
            testFile.write(testText)

        entry = antglob.FileSystemEntry(os.path.dirname(testFilePath), [os.path.basename(testFilePath)])
        self.assertEqual(entry.kind, antglob.FileSystemEntry.File)
        self.assertEqual(entry.size, len(testText))
        self.assertEqual(entry.parts, tuple(['test.txt']))

        # Just exercise methods to render entry.
        self.assertTrue(repr(entry))
        self.assertTrue(str(entry))
        self.assertTrue(unicode(entry))

        shutil.rmtree(testFolderPath)

    def testCanProcessFolderEntry(self):
        testFolderPath = tempfile.mkdtemp(prefix='test_antpattern_')
        entry = antglob.FileSystemEntry(os.path.dirname(testFolderPath), [os.path.basename(testFolderPath)])
        self.assertEqual(entry.kind, antglob.FileSystemEntry.Folder)
        self.assertEqual(entry.parts, tuple([os.path.basename(testFolderPath)]))

        # Just exercise methods to render entry.
        self.assertTrue(repr(entry))
        self.assertTrue(str(entry))
        self.assertTrue(unicode(entry))

        shutil.rmtree(testFolderPath)


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    unittest.main()
