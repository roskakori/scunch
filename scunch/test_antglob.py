"""
Tests for antglob.
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
import doctest
import errno
import logging
import os
import shutil
import tempfile
import unittest

import antglob

_log = logging.getLogger("test")

class DocTest(unittest.TestSuite):
    def __init__(self):
        super(DocTest, self).__init__()
        self.addTest(doctest.DocTestSuite(antglob))

class TestPrivateFunctions(unittest.TestCase):
    def testTextItemsAreInPatternItems(self):
        pattern = antglob.AntPattern("a/b/*_tmp/*.txt")
        patternItems = pattern.patternItems
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts("a"), patternItems))
        self.assertFalse(antglob._textItemsAreInPatternItems(antglob._splitTextParts("!"), patternItems))
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts("a/b"), patternItems))
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts("b"), patternItems))
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts("b/hugo_tmp"), patternItems))
        self.assertTrue(antglob._textItemsAreInPatternItems(antglob._splitTextParts("hugo.txt"), patternItems))

    def testTextItemsAreAtEndOfPatternItems(self):
        pattern = antglob.AntPattern("a/b/*_tmp/*.txt")
        patternItems = pattern.patternItems
        self.assertTrue(antglob._textItemsAreAtEndOfPatternItems(antglob._splitTextParts("hugo.txt"), patternItems))
        self.assertFalse(antglob._textItemsAreAtEndOfPatternItems(antglob._splitTextParts("a"), patternItems))
        self.assertFalse(antglob._textItemsAreAtEndOfPatternItems(antglob._splitTextParts("txt"), patternItems))

    def testFindTextItemsPartForPatternItems(self):
        pattern = antglob.AntPattern("a?c/d*")
        patternItems = pattern.patternItems
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts("abc/d"), patternItems), 0)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts("0/abc/d"), patternItems), 1)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts("abc/d/e"), patternItems), 0)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts("abc"), patternItems), -1)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts("cannot/find/me"), patternItems), -1)
        self.assertEqual(antglob._indexInTextItemsWherePatternPartsMatch(antglob._splitTextParts(""), patternItems), -1)

class AntPatternTest(unittest.TestCase):
    def testFindListInList(self):
        self.assertEqual(antglob._findListInList([2], [5, 4, 2, 7]), 2)
        self.assertEqual(antglob._findListInList([5], [5, 4, 2, 7]), 0)
        self.assertEqual(antglob._findListInList([7], [5, 4, 2, 7]), 3)
        self.assertEqual(antglob._findListInList([17], [5, 4, 2, 7]), -1)
        self.assertEqual(antglob._findListInList([5, 4], [5, 4, 2, 7]), 0)
        self.assertEqual(antglob._findListInList([4, 2], [5, 4, 2, 7]), 1)
        self.assertEqual(antglob._findListInList([2, 7], [5, 4, 2, 7]), 2)
        self.assertEqual(antglob._findListInList([4, 3], [5, 4, 2, 7]), -1)
     
    def testOnePatterns(self):
        pattern = antglob.AntPattern("hugo")
        self.assertTrue(pattern.matches("hugo"))
        self.assertFalse(pattern.matches("sepp"))
        self.assertFalse(pattern.matches(""))

        pattern = antglob.AntPattern("a/b/c")
        self.assertTrue(pattern.matches("a/b/c"))
        self.assertFalse(pattern.matches(""))
        self.assertFalse(pattern.matches("a"))
        self.assertFalse(pattern.matches("b"))
        self.assertFalse(pattern.matches("a/b"))
        self.assertFalse(pattern.matches("a/b/xxx"))
        self.assertFalse(pattern.matches("a/b/xxx/c"))
        self.assertFalse(pattern.matches("a/b/c/d"))

    def testManyPatterns(self):
        pattern = antglob.AntPattern("*.txt")
        self.assertTrue(pattern.matches("hugo.txt"))
        self.assertFalse(pattern.matches("hugo.txtx"))
        self.assertFalse(pattern.matches("sepp.png"))
        self.assertFalse(pattern.matches(""))

        pattern = antglob.AntPattern("*")
        self.assertTrue(pattern.matches("x"))
        self.assertTrue(pattern.matches(""))

    def testAllPatterns(self):
        pattern = antglob.AntPattern("**")
        self.assertTrue(pattern.matches("hugo.txt"))
        self.assertTrue(pattern.matches(""))

        pattern = antglob.AntPattern("**/*.txt")
        self.assertTrue(pattern.matches("hugo.txt"))
        self.assertTrue(pattern.matches("texts/hugo.txt"))
        self.assertTrue(pattern.matches("1/2/3/4/hugo.txt"))
        self.assertFalse(pattern.matches("hugo.png"))
        self.assertFalse(pattern.matches("hugo.txt/hugo.png"))
        self.assertFalse(pattern.matches(""))

    def testMultipleAllPatterns(self):
        pattern = antglob.AntPattern("**/b/**")
        self.assertTrue(pattern.matches("b"))
        self.assertTrue(pattern.matches("b/hugo.txt"))
        self.assertTrue(pattern.matches("a/b/hugo.txt"))
        self.assertTrue(pattern.matches("x/y/a/b/c/hugo.txt"))
        self.assertFalse(pattern.matches("bb/hugo.txt"))
        self.assertFalse(pattern.matches(""))

        pattern = antglob.AntPattern("**/data/2010*/**/some/*.csv")
        self.assertFalse(pattern.matches("x/data/20101130/projects/other/hugo.csv"))
        self.assertTrue(pattern.matches("x/data/20101130/projects/some/hugo.csv"))
        self.assertFalse(pattern.matches("x/dump/20101130/projects/some/hugo.csv"))
        self.assertFalse(pattern.matches(""))

        pattern = antglob.AntPattern("**/b?/**")
        self.assertTrue(pattern.matches("b1"))
        self.assertTrue(pattern.matches("a/b1/hugo.txt"))
        self.assertFalse(pattern.matches("a/b123/hugo.txt"))
        self.assertFalse(pattern.matches(""))

    def testAntPatternSet(self):
        patternSet = antglob.AntPatternSet()
        patternSet.include(antglob.AntPattern("*.png"))
        patternSet.include(antglob.AntPattern("*.jpg"))
        self.assertTrue(patternSet.matches("hugo.png"))
        self.assertTrue(patternSet.matches("hugo.jpg"))
        self.assertFalse(patternSet.matches("hugo.txt"))

class AntPatternSetFindTest(unittest.TestCase):
    def setUp(self):
        self._testFolderPath = tempfile.mkdtemp(prefix="test_antpattern_")
        self.ohsomeSourcePath = os.path.join("ohsome", "source")
        self.ohsomeSourceUiPath = os.path.join(self.ohsomeSourcePath, "ui")
        self.ohsomeManualPath = os.path.join("ohsome", "manual")
        self.makeFolder(os.path.join(self._testFolderPath, self.ohsomeSourcePath))
        self.makeFolder(os.path.join(self._testFolderPath, self.ohsomeSourceUiPath))
        self.makeFolder(os.path.join(self._testFolderPath, self.ohsomeManualPath))
        self.writeTestFile(os.path.join(self.ohsomeSourcePath, "ohsome.py"))
        self.writeTestFile(os.path.join(self.ohsomeSourcePath, "tools.py"))
        self.writeTestFile(os.path.join(self.ohsomeSourceUiPath, "login.py"))
        self.writeTestFile(os.path.join(self.ohsomeSourceUiPath, "mainwindow.py"))
        self.writeTestFile(os.path.join(self.ohsomeSourceUiPath, "splash.png"))
        self.writeTestFile(os.path.join(self.ohsomeManualPath, "tutorial.rst"))
        self.writeTestFile(os.path.join(self.ohsomeManualPath, "userguide.rst"))
        self.writeTestFile(os.path.join(self.ohsomeManualPath, "screenshot.png"))
        self.writeTestFile(os.path.join(self.ohsomeManualPath, "logo.png"))
    
    def tearDown(self):
        shutil.rmtree(self._testFolderPath)

    def makeFolder(self, folderPathToMake):
        """
        Like `os.makedirs` but does nothing if the folder already exists.
        """
        try:
            os.makedirs(folderPathToMake)
        except OSError, error:
            if error.errno !=  errno.EEXIST:
                raise
    
    def writeTestFile(self, relativePathOfFileToWrite, lines=[]):
        assert relativePathOfFileToWrite
        assert lines is not None
        testFilePath = os.path.join(self._testFolderPath, relativePathOfFileToWrite)
        testFile = open(testFilePath, "wb")
        try:
            for line in lines:
                testFile.write(line)
                testFile.write(os.linesep)
        finally:
            testFile.close()
        
    def testFindPatternSet(self):
        pythonSet = antglob.AntPatternSet()
        pythonSet.include("**/*.py, **/*.rst")
        pythonSet.exclude("**/*.pyc, **/*.pyo")
        filePathCount = 0
        folderPathCount = 0
        _log.info("find pattern set: %s", pythonSet)
        for path in pythonSet.find(self._testFolderPath, True):
            _log.info("  found: %s", path)
            if antglob.isFolderPath(path):
                folderPathCount += 1
            else:
                suffix = os.path.splitext(path)[1]
                self.assertTrue(suffix in (".py", ".rst"))
                filePathCount += 1
        self.assertTrue(filePathCount)
        self.assertTrue(folderPathCount)

    def testFindPatternSetWithoutFolders(self):
        pythonSet = antglob.AntPatternSet()
        pythonSet.include("**/*.py, **/*.rst")
        pythonSet.exclude("**/*.pyc, **/*.pyo")
        filePathCount = 0
        _log.info("find pattern set: %s", pythonSet)
        for path in pythonSet.find(self._testFolderPath):
            _log.info("  found: %s", path)
            self.assertFalse(antglob.isFolderPath(path), "path must noe be folder: %r" % path)
            suffix = os.path.splitext(path)[1]
            self.assertTrue(suffix in (".py", ".rst"))
            filePathCount += 1
        self.assertTrue(filePathCount)

    def testFindEntriesForPatternSet(self):
        pythonSet = antglob.AntPatternSet()
        pythonSet.include("**/*.py, **/*.rst")
        pythonSet.exclude("**/*.pyc, **/*.pyo")
        fileCount = 0
        folderCount = 0
        _log.info("find pattern set: %s", pythonSet)
        for entry in pythonSet.findEntries(self._testFolderPath):
            _log.info("  found: %s", entry)
            if entry.kind == antglob.FileSystemEntry.Folder:
                folderCount += 1
            else:
                self.assertEqual(entry.kind, antglob.FileSystemEntry.File)
                suffix = entry.parts[-1]
                self.assertTrue(suffix in (".py", ".rst"))
                fileCount += 1
        self.assertTrue(fileCount)
        self.assertTrue(folderCount)

class FolderEntryTest(unittest.TestCase):
    def testFileEntry(self):
        testFolderPath = tempfile.mkdtemp(prefix="test_antpattern_")
        testFilePath = os.path.join(testFolderPath, "test.txt")
        testText = "some test text"
        with open(testFilePath, "wb") as testFile:
            testFile.write(testText)
        
        folderEntry = antglob.FileSystemEntry(os.path.dirname(testFilePath), [os.path.basename(testFilePath)])
        self.assertEqual(folderEntry.kind, antglob.FileSystemEntry.File)
        self.assertEqual(folderEntry.size, len(testText))
        self.assertEqual(folderEntry.parts, tuple(["test.txt"]))
        shutil.rmtree(testFolderPath)

    def testFolderEntry(self):
        testFolderPath = tempfile.mkdtemp(prefix="test_antpattern_")
        folderEntry = antglob.FileSystemEntry(os.path.dirname(testFolderPath), [os.path.basename(testFolderPath)])
        self.assertEqual(folderEntry.kind, antglob.FileSystemEntry.Folder)
        self.assertEqual(folderEntry.parts, tuple([os.path.basename(testFolderPath)]))
        shutil.rmtree(testFolderPath)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
