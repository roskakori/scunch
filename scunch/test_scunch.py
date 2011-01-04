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
import shutil
import unittest

from urlparse import urljoin

import scunch

_log = logging.getLogger("test")

def makeEmptyFolder(folderPathToCreate):
    scunch.removeFolder(folderPathToCreate)
    scunch.makeFolder(folderPathToCreate)

_BaseTestFolder = os.path.abspath("test")

class _ScmTest(unittest.TestCase):
    def setUpProject(self, project, testFolderPath=_BaseTestFolder):
        """
        Create a local repository for ``project``, possibly removing any existing repository
        before. Next, checkout a working copy in ``testFolderPath``.
        """
        assert project
        assert testFolderPath
        
        self.project = project
        self.testFolderPath = testFolderPath
        self.scmWork = None

        _log.debug("clean up test folder at %r", self.testFolderPath)
        makeEmptyFolder(self.testFolderPath)

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

    def assertNonNormalStatus(self, expectedStatusToCountMap):
        # TODO: Move to some more appropriate place, for instance something like ``_ScmWorkTest``.
        assert self.scmWork is not None, "scmWork must be set"
        assert expectedStatusToCountMap is not None

        actualStatusToCountMap = {}        
        for statusInfo in self.scmWork.status(""):
            actualStatus = statusInfo.status
            if actualStatus != scunch.ScmStatus.Normal:
                if not actualStatus in expectedStatusToCountMap:
                    self.fail(u'status for "%s" is %r but must be one of: %s' % (statusInfo.path, actualStatus, expectedStatusToCountMap.keys()))
                existingCount = actualStatusToCountMap.get(actualStatus)
                if existingCount is None:
                    actualStatusToCountMap[actualStatus] = 1
                else:
                    actualStatusToCountMap[actualStatus] = existingCount + 1
        self.assertEqual(actualStatusToCountMap, expectedStatusToCountMap)
                
        
class _SvnTest(_ScmTest):
    def setUpProject(self, project, testFolderPath=_BaseTestFolder):
        """
        Create a Subversion repository containing a few files and a work copy with its current
        contents checked out.
        """
        super(_SvnTest, self).setUpProject(project, testFolderPath)
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
        self.writeTextFile(speechHtmlPath, ["<html><head><title>A great speech</title></head><body>", "<h1>A great speech</h1>", "<p>Uhm...</p>", "</body></html>"])
        # TODO: Add binary PNG test file.

        self.scmWork.addUnversioned("")
        self.scmWork.commit("", "Added test files")

class ScunchTest(_SvnTest):
    """
    TestCase for `scunch.scunch()`.
    """
    def testScunchWithClone(self):
        self.setUpProject("scunchWithClone")
        scmWork = self.scmWork

        testScunchWithClonePath = self.createTestFolder("testScunch")
        scmWork.exportTo(testScunchWithClonePath, clear=True)

        scunch.scunch(testScunchWithClonePath, scmWork)
        self.assertNonNormalStatus({})

    def testScunchWithChanges(self):
        self.setUpProject("scunchWithChanges")
        scmWork = self.scmWork

        testScunchWithChangesPath = self.createTestFolder("testScunch")
        scmWork.exportTo(testScunchWithChangesPath, clear=True)

        readMeTooPath = os.path.join(testScunchWithChangesPath, "ReadMeToo.txt")
        self.writeTextFile(readMeTooPath, ["You really should", "read me, too."])
        whilePyPath = os.path.join(testScunchWithChangesPath, "loops", "while.py")
        os.remove(whilePyPath)

        scunch.scunch(testScunchWithChangesPath, scmWork)
        self.assertNonNormalStatus({scunch.ScmStatus.Added: 1, scunch.ScmStatus.Removed: 1})

class ScmPuncherTest(_SvnTest):
    """
    TestCase for `scunch.ScmPuncher`.
    """
    def _testAfterPunch(self, externalFolderPath):
        """
        Test that previously punched changes can be committed and a re-punch results in no further changes.
        """
        assert self.scmWork is not None
        assert externalFolderPath is not None
        
        self.scmWork.commit([""], "Punched recent changes.")
        rePuncher = scunch.ScmPuncher(self.scmWork)
        rePuncher.punch(externalFolderPath)
        self.assertNonNormalStatus({})
        self.assertEqual(rePuncher.workItems, rePuncher.externalItems)

    def testPunchWithClone(self):
        self.setUpProject("punchWithClone")
        scmWork = self.scmWork

        testPunchWithClonePath = self.createTestFolder("testPunchWithClone")
        scmWork.exportTo(testPunchWithClonePath, clear=True)

        cloningPuncher = scunch.ScmPuncher(scmWork)
        cloningPuncher.punch(testPunchWithClonePath)

        self.assertEqual(cloningPuncher.workItems, cloningPuncher.externalItems)

        self.assertNonNormalStatus({})
        self._testAfterPunch(testPunchWithClonePath)

    def testPunchWithModify(self):
        self.setUpProject("punchWithModify")
        scmWork = self.scmWork

        testPunchWithModifyPath = self.createTestFolder("testPunchWithModify")
        scmWork.exportTo(testPunchWithModifyPath, clear=True)
        readMeTxtPath = os.path.join(testPunchWithModifyPath, "ReadMe.txt")
        self.writeTextFile(readMeTxtPath, ["This is an updated version of the file", "with a different text."])

        modifyingPuncher = scunch.ScmPuncher(scmWork)
        modifyingPuncher.punch(testPunchWithModifyPath)

        self.assertEqual(modifyingPuncher.workItems, modifyingPuncher.externalItems)

        self.assertNonNormalStatus({scunch.ScmStatus.Modified: 1})
        self._testAfterPunch(testPunchWithModifyPath)

    def testPunchWithAdd(self):
        self.setUpProject("punchWithAdd")
        scmWork = self.scmWork

        testPunchWithAddPath = self.createTestFolder("testPunchWithAdd")
        scmWork.exportTo(testPunchWithAddPath, clear=True)
        readMeTooPath = os.path.join(testPunchWithAddPath, "ReadMeToo.txt")
        self.writeTextFile(readMeTooPath, ["You really should", "read me, too."])

        addingPuncher = scunch.ScmPuncher(scmWork)
        addingPuncher.punch(testPunchWithAddPath)

        self.assertNonNormalStatus({scunch.ScmStatus.Added: 1})
        self._testAfterPunch(testPunchWithAddPath)

    def testPunchWithRemove(self):
        self.setUpProject("punchWithRemove")
        scmWork = self.scmWork

        testPunchWithRemovePath = self.createTestFolder("testPunchWithRemove")
        scmWork.exportTo(testPunchWithRemovePath, clear=True)
        readMeTxtPath = os.path.join(testPunchWithRemovePath, "ReadMe.txt")
        os.remove(readMeTxtPath)
        whilePyPath = os.path.join(testPunchWithRemovePath, "loops", "while.py")
        os.remove(whilePyPath)
        mediaPath = os.path.join(testPunchWithRemovePath, "media")
        scunch.removeFolder(mediaPath)

        addingPuncher = scunch.ScmPuncher(scmWork)
        addingPuncher.punch(testPunchWithRemovePath)

        self.assertNonNormalStatus({scunch.ScmStatus.Removed: 3})
        self._testAfterPunch(testPunchWithRemovePath)

    def testPunchWithMovedFiles(self):
        self.setUpProject("punchWithMovedFiles")
        scmWork = self.scmWork

        testPunchWithMovedFilesPath = self.createTestFolder("testPunchWithMovedFiles")
        scmWork.exportTo(testPunchWithMovedFilesPath, clear=True)
        oldReadMeTxtPath = os.path.join(testPunchWithMovedFilesPath, "ReadMe.txt")
        newReadMeTxtPath = os.path.join(testPunchWithMovedFilesPath, "loops", "ReadMe.txt")
        shutil.move(oldReadMeTxtPath, newReadMeTxtPath)
        oldWhilePyPath = os.path.join(testPunchWithMovedFilesPath, "loops", "while.py")
        newWhilePyPath = os.path.join(testPunchWithMovedFilesPath, "while.py")
        shutil.move(oldWhilePyPath, newWhilePyPath)

        movingPuncher = scunch.ScmPuncher(scmWork)
        movingPuncher.punch(testPunchWithMovedFilesPath)

        self.assertNonNormalStatus({scunch.ScmStatus.Added: 2, scunch.ScmStatus.Removed: 2})
        self._testAfterPunch(testPunchWithMovedFilesPath)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()

