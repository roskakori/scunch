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
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging
import os
import subprocess
import shutil
import unittest

import scunch

from urlparse import urljoin

_log = logging.getLogger("test")

def makeEmptyFolder(folderPathToCreate):
    scunch.removeFolder(folderPathToCreate)
    scunch.makeFolder(folderPathToCreate)

_BaseTestFolder = os.path.abspath("test")

class _ScmTest(object):
    def __init__(self, project, testFolderPath=_BaseTestFolder):
        """
        Create a local repository for ``project``, possibly removing any existing repository
        before. Next, checkout a working copy in ``testFolderPath``.
        """
        assert project
        assert testFolderPath
        
        self.project = project
        self.testFolderPath = testFolderPath

        _log.info("clean up test folder at %r", self.testFolderPath)
        makeEmptyFolder(self.testFolderPath)

    def run(self, commandAndOptions):
        assert commandAndOptions
        _log.info("run: %s", " ".join(commandAndOptions))
        subprocess.check_call(commandAndOptions)

    def createTestFolder(self, name):
        """An empty folder named ``name`` in the test folder."""
        assert name

        result = os.path.join(self.testFolderPath, name)
        makeEmptyFolder(result)
        return result

    def writeTextFile(self, targetFilePath, lines):
        assert targetFilePath
        assert lines is not None
        with open(targetFilePath, 'wb') as targetFile:
            for line in lines:
                targetFile.write(line)
                targetFile.write(os.linesep)
        
class _SvnTest(_ScmTest):
    def __init__(self, project, testFolderPath=_BaseTestFolder):
        super(_SvnTest, self).__init__(project, testFolderPath)
        storagePath = os.path.join(self.testFolderPath, "svnRepository", self.project)
        storageQualifier = urljoin("file://localhost/", storagePath)
        self._scmStorage = scunch.ScmStorage(storageQualifier)
        os.makedirs(storagePath)
        self._trunkUri = self._scmStorage.absoluteQualifier("trunk")

        self._scmStorage.create(storagePath)
        self._scmStorage.mkdir(["branches", "tags", "trunk"], "Added project folders.")
        self.workBaseFolderPath = os.path.join(self.testFolderPath, "svnWork")
        self.workFolderPath = os.path.join(self.workBaseFolderPath, self.project)
        self.scmWork = scunch.ScmWork(self._scmStorage, "trunk", self.workFolderPath, scunch.ScmWork.CheckOutActionReset)

        # Create a few files in the project root folder.
        helloPyPath = self.scmWork.absolutePath("test file path", "hello.py")
        self.writeTextFile(helloPyPath, ["# A classic.", "print 'hello world!'"])
        readmeTxtPath = self.scmWork.absolutePath("test file path", "ReadMe.txt")
        self.writeTextFile(readmeTxtPath, ["Just a dummy project with some test file."])

        # Create a folder "loops" with a couple of Python source codes."
        loopsFolderPath = self.scmWork.absolutePath("test folder path", "loops")
        scunch.makeFolder(loopsFolderPath)
        forRangePyPath = os.path.join(loopsFolderPath, "forRange.py")
        whilePyPath = os.path.join(loopsFolderPath, "while.py")
        self.writeTextFile(forRangePyPath, ["for i in range(5):", "    print i"])
        self.writeTextFile(whilePyPath, ["i = 0", "while i < 5:", "     print i", "    i += 1"])

        # Create a folder "media" with a couple of files."
        mediaFolderPath = self.scmWork.absolutePath("test folder path", "media")
        scunch.makeFolder(mediaFolderPath)
        speechHtmlPath = os.path.join(loopsFolderPath, "speech.html")
        self.writeTextFile(speechHtmlPath, ["<html><head><title>A great speech</title></head><body>", "<h1>A great speech</h1>", "<p>Ahem...</p>", "</body></html>"])
        # TODO: Add binary PNG test file.

        self.scmWork.addUnversioned("")
        self.scmWork.commit("", "Added test files")

class ScmTest(unittest.TestCase):

    def testScm(self):
        scmTest = _SvnTest("hugo")
        scmWork = scmTest.scmWork

    def _assertNonNormalStatusCount(self, scmWork, expectedNonNormalStatus, expectedStatusCount):
        assert scmWork is not None
        assert expectedStatusCount is not None
        assert expectedStatusCount >= 0

        nonNormalStatusCount = 0
        for statusInfo in scmWork.status(""):
            actualStatus = statusInfo.status
            if actualStatus != scunch.ScmStatus.Normal:
                nonNormalStatusCount += 1
                self.assertEqual(actualStatus, expectedNonNormalStatus, u'status for "%s" is %r but must be %r' % (statusInfo.path, actualStatus, expectedNonNormalStatus))
        self.assertEqual(nonNormalStatusCount, expectedStatusCount)
                
    def _testAfterPunch(self, externalFolderPath, scmWork):
        """
        Test that previously punched changes can be committed and a re-punch results in no further changes.
        """
        assert externalFolderPath is not None
        assert scmWork is not None
        
        scmWork.commit([""], "Punched recent changes.")
        rePuncher = scunch.ScmPuncher(scmWork)
        rePuncher.punch(externalFolderPath)
        self._assertNonNormalStatusCount(scmWork, None, 0)
        self.assertEqual(rePuncher.workItems, rePuncher.externalItems)

    def testPunchWithClone(self):
        scmTest = _SvnTest("punchWithClone")
        scmWork = scmTest.scmWork

        testPunchWithClonePath = scmTest.createTestFolder("testPunchWithClone")
        scmWork.exportTo(testPunchWithClonePath, clear=True)

        cloningPuncher = scunch.ScmPuncher(scmWork)
        cloningPuncher.punch(testPunchWithClonePath)

        self.assertEqual(cloningPuncher.workItems, cloningPuncher.externalItems)

        self._assertNonNormalStatusCount(scmWork, None, 0)
        self._testAfterPunch(testPunchWithClonePath, scmWork)

    def testPunchWithModify(self):
        scmTest = _SvnTest("punchWithModify")
        scmWork = scmTest.scmWork

        testPunchWithModifyPath = scmTest.createTestFolder("testPunchWithModify")
        scmWork.exportTo(testPunchWithModifyPath, clear=True)
        readMeTxtPath = os.path.join(testPunchWithModifyPath, "ReadMe.txt")
        scmTest.writeTextFile(readMeTxtPath, ["This is an updated version of the file", "with a different text."])

        modifyingPuncher = scunch.ScmPuncher(scmWork)
        modifyingPuncher.punch(testPunchWithModifyPath)

        self.assertEqual(modifyingPuncher.workItems, modifyingPuncher.externalItems)

        self._assertNonNormalStatusCount(scmWork, scunch.ScmStatus.Modified, 1)
        self._testAfterPunch(testPunchWithModifyPath, scmWork)

    def testPunchWithAdd(self):
        scmTest = _SvnTest("punchWithAdd")
        scmWork = scmTest.scmWork

        testPunchWithAddPath = scmTest.createTestFolder("testPunchWithAdd")
        scmWork.exportTo(testPunchWithAddPath, clear=True)
        readMeTooPath = os.path.join(testPunchWithAddPath, "ReadMeToo.txt")
        scmTest.writeTextFile(readMeTooPath, ["You really should", "read me, too."])

        addingPuncher = scunch.ScmPuncher(scmWork)
        addingPuncher.punch(testPunchWithAddPath)

        self._assertNonNormalStatusCount(scmWork, scunch.ScmStatus.Added, 1)
        self._testAfterPunch(testPunchWithAddPath, scmWork)

    def testPunchWithRemove(self):
        scmTest = _SvnTest("punchWithRemove")
        scmWork = scmTest.scmWork

        testPunchWithRemovePath = scmTest.createTestFolder("testPunchWithRemove")
        scmWork.exportTo(testPunchWithRemovePath, clear=True)
        readMeTxtPath = os.path.join(testPunchWithRemovePath, "ReadMe.txt")
        os.remove(readMeTxtPath)
        whilePyPath = os.path.join(testPunchWithRemovePath, "loops", "while.py")
        os.remove(whilePyPath)
        mediaPath = os.path.join(testPunchWithRemovePath, "media")
        scunch.removeFolder(mediaPath)

        addingPuncher = scunch.ScmPuncher(scmWork)
        addingPuncher.punch(testPunchWithRemovePath)

        self._assertNonNormalStatusCount(scmWork, scunch.ScmStatus.Removed, 3)
        self._testAfterPunch(testPunchWithRemovePath, scmWork)

    def testIsInRemovedFolder(self):
        scmTest = _SvnTest("puncher")
        scmWork = scmTest.scmWork
        matcherPath = scmTest.createTestFolder("puncher")
        scmWork.exportTo(matcherPath, clear=True)
        
        identicalPuncher = scunch.ScmPuncher(scmWork)
        identicalPuncher.punch(matcherPath)
        
        scmWork.exportTo(matcherPath, clear=True)
        shutil.rmtree(os.path.join(matcherPath, "loops"))
        removingPuncher = scunch.ScmPuncher(scmWork)
        removingPuncher.punch(matcherPath)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()

