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
import shutil
import unicodedata
import unittest

from urlparse import urljoin

import scunch
import _tools
from scunch import ScmPendingChangesError

_log = logging.getLogger("test")

_BaseTestFolder = os.path.abspath("test")


class ToolsTest(unittest.TestCase):
    def testRunWithAsciiEcho(self):
        scunch.run([u"echo", u"hello"])

    def testRunWithUmlautEcho(self):
        scunch.run([u"echo", u'h\xe4ll\xf6'])

    def testRunWithUmlautEchoResult(self):
        hello = u'h\xe4ll\xf6'
        helloWithUmlauts = scunch.run([u'echo', hello], returnStdout=True)
        normalizedHelloPy = [unicodedata.normalize(scunch._consoleNormalization, hello)]
        self.assertEqual( helloWithUmlauts, normalizedHelloPy)
        
class _ScmTest(unittest.TestCase):
    def setUp(self):
        scunch._setUpEncoding()

    def setUpEmptyProject(self, project, testFolderPath=_BaseTestFolder):
        """
        Create a local repository for ``project``, possibly removing any existing repository
        before.
        """
        assert project
        assert testFolderPath
        
        self.project = project
        self.testFolderPath = testFolderPath
        self.scmWork = None

        _log.debug("clean up test folder at %r", self.testFolderPath)
        _tools.makeEmptyFolder(self.testFolderPath)

    def createTestFolder(self, name):
        """An empty folder named ``name`` in the test folder."""
        assert name

        result = os.path.join(self.testFolderPath, name)
        _tools.makeEmptyFolder(result)
        return result

    def writeBinaryFile(self, targetFilePath, data):
        assert targetFilePath
        assert data is not None
        _log.debug("write binary file \"%s\"", targetFilePath)
        with open(targetFilePath, 'wb') as targetFile:
                targetFile.write(data)

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
    def setUpEmptyProject(self, project, testFolderPath=_BaseTestFolder):
        """
        Create an empty Subversion repository and an empty work copy with its current contents
        checked out.
        """
        super(_SvnTest, self).setUpEmptyProject(project, testFolderPath)
        storagePath = os.path.join(self.testFolderPath, "svnRepository", self.project)
        self.scmDepotQualifier = urljoin("file://localhost/", storagePath)
        self.scmDepot = scunch.ScmStorage(self.scmDepotQualifier)
        os.makedirs(storagePath)
        self.scmDepotTrunkQualifier = self.scmDepot.absoluteQualifier("trunk")

        self.scmDepot.create(storagePath)
        self.scmDepot.mkdir(["branches", "tags", "trunk"], "Added project folders.")
        self.workBaseFolderPath = os.path.join(self.testFolderPath, "svnWork")
        self.workFolderPath = os.path.join(self.workBaseFolderPath, self.project)
        self.scmWork = scunch.ScmWork(self.scmDepot, "trunk", self.workFolderPath, scunch.ScmWork.CheckOutActionReset)

    def setUpProject(self, project, testFolderPath=_BaseTestFolder):
        """
        Create a Subversion repository containing a few files and a work copy with its current
        contents checked out.
        """
        self.setUpEmptyProject(project, testFolderPath)
        # Create a few files in the project root folder.
        helloPyPath = self.scmWork.absolutePath("test file path", "hello.py")
        self.writeTextFile(helloPyPath, ["# A classic.", "print 'hello world!'"])
        readmeTxtPath = self.scmWork.absolutePath("test file path", "ReadMe.txt")
        self.writeTextFile(readmeTxtPath, ["Just a dummy project with some test file."])

        # Create a folder "loops" with a couple of Python source codes."
        loopsFolderPath = self.scmWork.absolutePath("test folder path", "loops")
        _tools.makeFolder(loopsFolderPath)
        forRangePyPath = os.path.join(loopsFolderPath, "forRange.py")
        whilePyPath = os.path.join(loopsFolderPath, "while.py")
        self.writeTextFile(forRangePyPath, ["for i in range(5):", "    print i"])
        self.writeTextFile(whilePyPath, ["i = 0", "while i < 5:", "    print i", "    i += 1"])

        # Create a folder "media" with a couple of files."
        mediaFolderPath = self.scmWork.absolutePath("test folder path", "media")
        _tools.makeFolder(mediaFolderPath)
        speechHtmlPath = os.path.join(loopsFolderPath, "speech.html")
        self.writeTextFile(speechHtmlPath, ["<html><head><title>A great speech</title></head><body>", "<h1>A great speech</h1>", "<p>Uhm...</p>", "</body></html>"])
        # TODO: Add binary PNG test file.

        self.scmWork.addUnversioned("")
        self.scmWork.commit("", "Added test files")

class BasicTest(_SvnTest):
    def testAddWithNonAsciiFileName(self):
        self.setUpProject("basic")
        scmWork = self.scmWork
        hello = unicodedata.normalize("NFD", u'h\xe4ll\xf6.py')
        helloWithUmlautPath = scmWork.absolutePath('test file path with umlauts', hello)
        self.writeTextFile(helloWithUmlautPath, ["print u'h\\xe4ll\\xf6'"])
        self.assertNonNormalStatus({scunch.ScmStatus.Unversioned: 1})
        scmWork.add(helloWithUmlautPath)
        for statusInfo in scmWork.status(""):
            _log.debug("  status=%s", statusInfo)
        self.assertNonNormalStatus({scunch.ScmStatus.Added: 1})
        scmWork.commit("", "Added file with umlauts in name.")
        self.assertNonNormalStatus({})

    def testPurge(self):
        self.setUpProject("testPurge")
        self.assertTrue(os.path.exists(self.scmWork.localTargetPath))
        self.scmWork.purge()
        self.assertFalse(os.path.exists(self.scmWork.localTargetPath))
        
    def testReset(self):
        self.setUpProject("testReset")
        
        # Modify a few files.
        addedPyPath = self.scmWork.absolutePath("test file to add", os.path.join("loops", "added.py"))
        forRangePyPath = self.scmWork.absolutePath("test file to remove", os.path.join("loops", "forRange.py"))
        whilePyPath = self.scmWork.absolutePath("test file to change", os.path.join("loops", "while.py"))
        self.writeTextFile(addedPyPath, ["# Just some added file."])
        os.remove(forRangePyPath)
        self.writeTextFile(whilePyPath, ["# Just some changed file."])

        self.scmWork.reset()
        self.assertFalse(os.path.exists(addedPyPath))
        self.assertTrue(os.path.exists(forRangePyPath))
        self.assertTrue(os.path.exists(whilePyPath))
        self.assertNonNormalStatus({})
        
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

    def _testMain(self, cliOptions, currentFolderPathToSet=None, expectedExitCode=0):
        logLevelAtStartOfTest = _log.level
        currentFolderPathAtStartOfTest = os.getcwdu()
        try:
            arguments = ["scunch.test"]
            arguments.extend(cliOptions)
            if currentFolderPathToSet:
                os.chdir(currentFolderPathToSet)
            exitCode, exitError = scunch.main(arguments)
            if not expectedExitCode and exitError:
                raise exitError
            self.assertEqual(exitCode, expectedExitCode)
        finally:
            os.chdir(currentFolderPathAtStartOfTest)
            _log.setLevel(logLevelAtStartOfTest)

    def _testMainWithSystemExit(self, cliOptions, expectedExitCode=0):
        oldLogLevel = _log.level
        try:
            arguments = ["scunch.test"]
            arguments.extend(cliOptions)
            scunch.main(arguments)
            self.fail("expected SystemExit with code=%d" % expectedExitCode)
        except SystemExit, error:
            if expectedExitCode:
                self.assertEqual(error.code, expectedExitCode)
        finally:
            _log.setLevel(oldLogLevel)

    def testMainHelp(self):
        self._testMainWithSystemExit(["--help"])

    def testMainVersion(self):
        self._testMainWithSystemExit(["--version"])
        
    def testMainBrokenOption(self):
        self._testMainWithSystemExit(["--no-such-option"], 2)

    def testMainBrokenAfterAction(self):
        self._testMainWithSystemExit(["--after", "broken", "external_folder", "work_folder"], 2)

    def testMainWithImplicitWork(self):
        self.setUpProject("mainWithImplicitWork")
        scmWork = self.scmWork

        testScunchWithImplicitWorkPath = self.createTestFolder("testMainWithImplicitWork")
        scmWork.exportTo(testScunchWithImplicitWorkPath, clear=True)
        
        implicitWorkPath = scmWork.absolutePath("implicit work folder", "")
        # Assertion to make sure that major screw ups will not destroy scunch's source code.
        queriedWorkName = os.path.basename(os.path.dirname(implicitWorkPath))
        self.assertTrue(queriedWorkName == "mainWithImplicitWork", "queriedWorkName=%r, implicitWorkPath=%r" % (queriedWorkName, implicitWorkPath))
        
        self._testMain([testScunchWithImplicitWorkPath], implicitWorkPath)

    def testMainWithWorkOnlyPattern(self):
        self.setUpProject("mainWithWorkOnlyPattern")
        scmWork = self.scmWork

        testScunchWithWorkOnlyPatternPath = self.createTestFolder("testMainWorkOnlyPattern")
        scmWork.exportTo(testScunchWithWorkOnlyPatternPath, clear=True)
        
        workOnlyPath = scmWork.absolutePath("work only folder", "")
        makefilePath = os.path.join(workOnlyPath, "Makefile")
        self.writeTextFile(makefilePath, ["# Dummy Makefile that could call scunch and what not."])
        
        self._testMain(["--before", "none", "--work-only", "Makefile", testScunchWithWorkOnlyPatternPath], workOnlyPath)
        self.assertTrue(os.path.exists(makefilePath))

        # Try again, but this time without ``--work-only``.
        self._testMain(["--before", "none", testScunchWithWorkOnlyPatternPath], workOnlyPath)
        self.assertFalse(os.path.exists(makefilePath))

    def testMainWithIncludeAndExcludePattern(self):
        self.setUpProject("mainWithIncludeAndExcludePattern")
        scmWork = self.scmWork

        testScunchWithIncludeAndExcludePatternPath = self.createTestFolder("testMainIncludeAndExcludePattern")
        scmWork.exportTo(testScunchWithIncludeAndExcludePatternPath, clear=True)
        
        workFolderPath = scmWork.absolutePath("work folder", "")
        helloPyWorkPath = scmWork.absolutePath("included Python source file", "hello.py")
        self.assertTrue(os.path.getsize(helloPyWorkPath))
        whilePyWorkPath = scmWork.absolutePath("excluded Python source file", os.path.join("loops", "while.py"))
        self.assertTrue(os.path.exists(whilePyWorkPath))

        # Clear included file in work copy to test that it will be transferred again with content.
        with open(helloPyWorkPath, "wb"):
            pass
        self.assertEqual(os.path.getsize(helloPyWorkPath), 0)
        
        # Remove excluded file from work copy to make sure that it will not be transferred.
        os.remove(whilePyWorkPath)
        
        self._testMain(["--before", "none", "--include", "**/*.py", "--exclude", "loops/while.py", testScunchWithIncludeAndExcludePatternPath], workFolderPath)
        self.assertTrue(os.path.getsize(helloPyWorkPath))
        self.assertFalse(os.path.exists(whilePyWorkPath))

    def testMainWithCommit(self):
        self.setUpProject("mainWithComit")
        scmWork = self.scmWork

        testScunchWithCommitPath = self.createTestFolder("testMainWithCommit")
        scmWork.exportTo(testScunchWithCommitPath, clear=True)
        
        workFolderPath = scmWork.absolutePath("work folder", "")
        workReadmeTxtPath = self.scmWork.absolutePath("test file path", "ReadMe.txt")
        externalReadmeTxtPath = os.path.join(testScunchWithCommitPath, "ReadMe.txt")
        os.remove(externalReadmeTxtPath)

        self._testMain(["--after", "commit", testScunchWithCommitPath, workFolderPath])
        self.assertNonNormalStatus({})
        self.assertFalse(os.path.exists(workReadmeTxtPath))

    def testMainWithCheckAndPendingChanges(self):
        self.setUpProject("mainCheckAndPendingChanges")
        scmWork = self.scmWork

        testScunchWithCheckAndPendingChangesPath = self.createTestFolder("testMainWithCheckAndPendingChanges")
        scmWork.exportTo(testScunchWithCheckAndPendingChangesPath, clear=True)
        
        # Enforce a change by removing a file under version control.
        workFolderPath = scmWork.absolutePath("work folder", "")
        workReadmeTxtPath = self.scmWork.absolutePath("test file path", "ReadMe.txt")
        os.remove(workReadmeTxtPath)

        self.assertRaises(ScmPendingChangesError, self._testMain, [testScunchWithCheckAndPendingChangesPath, workFolderPath])

    def testMainWithCheckout(self):
        self.setUpProject("mainWithCheckout")
        scmWork = self.scmWork

        testScunchWithCheckoutPath = self.createTestFolder("testMainWithCheckout")
        scmWork.exportTo(testScunchWithCheckoutPath, clear=True)

        self.assertTrue(os.path.exists(scmWork.localTargetPath))
        self._testMain(["--before", "checkout", "--depot", self.scmDepotTrunkQualifier, testScunchWithCheckoutPath, scmWork.localTargetPath])
        self.assertTrue(os.path.exists(scmWork.localTargetPath))

        _tools.removeFolder(scmWork.localTargetPath)
        self.assertFalse(os.path.exists(scmWork.localTargetPath))
        self._testMain(["--before", "checkout", "--depot", self.scmDepotTrunkQualifier, testScunchWithCheckoutPath, scmWork.localTargetPath])
        self.assertTrue(os.path.exists(scmWork.localTargetPath))

    def testMainWithPurge(self):
        self.setUpProject("mainWithPurge")
        scmWork = self.scmWork

        testScunchWithPurgePath = self.createTestFolder("testMainWithPurge")
        scmWork.exportTo(testScunchWithPurgePath, clear=True)

        self.assertTrue(os.path.exists(scmWork.localTargetPath))
        self._testMain(["--after", "purge", testScunchWithPurgePath, scmWork.localTargetPath])
        self.assertFalse(os.path.exists(scmWork.localTargetPath))

    def testMainWithUpdate(self):
        self.setUpProject("mainWithUpdate")
        scmWork = self.scmWork

        testScunchWithUpdatePath = self.createTestFolder("testMainWithUpdate")
        scmWork.exportTo(testScunchWithUpdatePath, clear=True)

        # TODO: Improve test for "--before=update" by creating a second working copy and committing a change from it.        
        self._testMain(["--before", "update", testScunchWithUpdatePath, scmWork.localTargetPath])

    def testMainWithResetCommit(self):
        self.setUpProject("mainWithReset")
        scmWork = self.scmWork

        testScunchWithResetPath = self.createTestFolder("testMainWithReset")
        scmWork.exportTo(testScunchWithResetPath, clear=True)

        # TODO: Improve test for "--before=reset" by messing up a few files to that reset does something useful.
        # Note: We are doing an --after commit in order to ensure that the work copy is still consistent after the reset.        
        self._testMain(["--before", "reset", "--after", "commit", testScunchWithResetPath, scmWork.localTargetPath])

    def testMainWithResetUpdateCommitPurge(self):
        # This test just exercises many --after and --before actions in combination.
        self.setUpProject("mainWithResetUpdateCommitPurge")
        scmWork = self.scmWork

        testScunchWithResetUpdateCommitPurgePath = self.createTestFolder("testMainWithResetUpdateCommitPurge")
        scmWork.exportTo(testScunchWithResetUpdateCommitPurgePath, clear=True)

        self._testMain(["--before", "reset, update", "--after", "commit, purge", testScunchWithResetUpdateCommitPurgePath, scmWork.localTargetPath])
        self.assertFalse(os.path.exists(scmWork.localTargetPath))

class ScmPuncherTest(_SvnTest):
    """
    TestCase for `scunch.ScmPuncher`.
    """
    def setUp(self):
        scunch._setUpEncoding()

    def _testAfterPunch(self, externalFolderPath, textOptions=None, names=scunch._Names.Preserve):
        """
        Test that previously punched changes can be committed and a re-punch results in no further changes.
        """
        assert self.scmWork is not None
        assert externalFolderPath is not None
        
        self.scmWork.commit([""], "Punched recent changes.")
        rePuncher = scunch.ScmPuncher(self.scmWork)
        rePuncher.punch(externalFolderPath, textOptions=textOptions, names=names)
        self.assertNonNormalStatus({})
        self.assertEqual(rePuncher.workEntries, rePuncher.externalEntries)

    def testPunchWithClone(self):
        self.setUpProject("punchWithClone")
        scmWork = self.scmWork

        testPunchWithClonePath = self.createTestFolder("testPunchWithClone")
        scmWork.exportTo(testPunchWithClonePath, clear=True)

        cloningPuncher = scunch.ScmPuncher(scmWork)
        cloningPuncher.punch(testPunchWithClonePath)

        self.assertEqual(cloningPuncher.workEntries, cloningPuncher.externalEntries)

        self.assertNonNormalStatus({})
        self._testAfterPunch(testPunchWithClonePath)

    def testPunchWithLowerCopy(self):
        self.setUpEmptyProject("punchWithLowerCopy")
        externalPunchWithLowerCopyPath = self.createTestFolder("externalPunchWithLowerCopy")

        def writeEmptyTxtFile(relativeFilePath):
            fullFilePath = os.path.join(externalPunchWithLowerCopyPath, relativeFilePath)
            self.writeTextFile(fullFilePath, [])

        def writeLowerTxtFile(relativeFolderPath=""):
            relativeFilePath = os.path.join(relativeFolderPath, "lower.txt")
            writeEmptyTxtFile(relativeFilePath)

        def writeMixedTxtFile(relativeFolderPath=""):
            relativeFilePath = os.path.join(relativeFolderPath, "MiXeD.tXt")
            writeEmptyTxtFile(relativeFilePath)

        def writeUpperTxtFile(relativeFolderPath=""):
            relativeFilePath = os.path.join(relativeFolderPath, "UPPER.TXT")
            writeEmptyTxtFile(relativeFilePath)

        def writeAllTxtFiles(relativeFolderPath=''):
            writeLowerTxtFile(relativeFolderPath)
            writeMixedTxtFile(relativeFolderPath)
            writeUpperTxtFile(relativeFolderPath)

        # Create test files and folders with names with different cases.
        writeAllTxtFiles()
        _tools.makeEmptyFolder(os.path.join(externalPunchWithLowerCopyPath, "lower"))
        writeAllTxtFiles('lower')
        _tools.makeEmptyFolder(os.path.join(externalPunchWithLowerCopyPath, "MiXeD"))
        writeAllTxtFiles('MiXeD')
        _tools.makeEmptyFolder(os.path.join(externalPunchWithLowerCopyPath, "UPPER"))
        writeAllTxtFiles('UPPER')
        
        modifyingPuncher = scunch.ScmPuncher(self.scmWork)
        modifyingPuncher.punch(externalPunchWithLowerCopyPath, names=scunch._Names.Lower)

        self.assertEqual(modifyingPuncher.workEntries, modifyingPuncher.externalEntries)

        self.assertNonNormalStatus({scunch.ScmStatus.Added: 15})
        self._testAfterPunch(externalPunchWithLowerCopyPath, names=scunch._Names.Lower)

    def testPunchWithLowerNameClash(self):
        self.setUpEmptyProject("punchWithLowerNameClash")
        externalPunchWithLowerNameClashPath = self.createTestFolder("externalPunchWithLowerNameClash")

        def writeEmptyTxtFile(relativeFilePath):
            fullFilePath = os.path.join(externalPunchWithLowerNameClashPath, relativeFilePath)
            self.writeTextFile(fullFilePath, [])

        # Create test files and folders with names with different cases.
        writeEmptyTxtFile("some.txt")
        writeEmptyTxtFile("SoMe.TxT")
        
        hasLowerSomeTxt = False
        hasMixedSomeTxt = False
        for name in os.listdir(externalPunchWithLowerNameClashPath):
            if name == 'some.txt':
                hasLowerSomeTxt = True
            elif name == 'SoMe.TxT':
                hasMixedSomeTxt = True

        if hasLowerSomeTxt and hasMixedSomeTxt:
            clashingPuncher = scunch.ScmPuncher(self.scmWork)
            self.assertRaises(scunch.ScmNameClashError, clashingPuncher.punch, externalPunchWithLowerNameClashPath, names=scunch._Names.Lower)
        else:
            _log.info('skipping test on case insensitive file system: %s', 'testPunchWithLowerNameClash')

    def testPunchWithModify(self):
        self.setUpProject("punchWithModify")
        scmWork = self.scmWork

        testPunchWithModifyPath = self.createTestFolder("testPunchWithModify")
        scmWork.exportTo(testPunchWithModifyPath, clear=True)
        readMeTxtPath = os.path.join(testPunchWithModifyPath, "ReadMe.txt")
        self.writeTextFile(readMeTxtPath, ["This is an updated version of the file", "with a different text."])

        modifyingPuncher = scunch.ScmPuncher(scmWork)
        modifyingPuncher.punch(testPunchWithModifyPath)

        self.assertEqual(modifyingPuncher.workEntries, modifyingPuncher.externalEntries)

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
        _tools.removeFolder(mediaPath)

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

    def testPunchWithMovedRoot(self):
        self.setUpProject("punchWithMovedRoot")
        scmWork = self.scmWork

        testPunchWithMovedRootPath = self.createTestFolder("testPunchWithMovedRoot")
        scmWork.exportTo(os.path.join(testPunchWithMovedRootPath, "subFolder"), clear=True)

        movingPuncher = scunch.ScmPuncher(scmWork)
        movingPuncher.punch(testPunchWithMovedRootPath)

        self.assertNonNormalStatus({scunch.ScmStatus.Added: 8, scunch.ScmStatus.Removed: 7})
        self._testAfterPunch(testPunchWithMovedRootPath)

    def _assertWorkTextFileEquals(self, correspondingExternalTextFilePath, expectedContent):
        assert correspondingExternalTextFilePath is not None
        assert expectedContent is not None
        
        correspondingExternalTextFileName = os.path.basename(correspondingExternalTextFilePath)
        relativeWorkFileToTestPath = os.path.join("texts", correspondingExternalTextFileName)
        workFileToTestPath = self.scmWork.absolutePath("work text file", relativeWorkFileToTestPath)
        with open(workFileToTestPath, "rb") as fileToTest:
            actualContent = ""
            hasDataLeftToRead = True
            while hasDataLeftToRead:
                data = fileToTest.read()
                hasDataLeftToRead = len(data)
                if hasDataLeftToRead:
                    actualContent += data
        self.assertEqual(actualContent, expectedContent, 'content of "%s" must match: %r != %r' % (workFileToTestPath, actualContent, expectedContent))

    def _setTextFilePaths(self):
        self.textsFolderPath = os.path.join(self.testPunchTextPath, "texts")
        self.dosNewLineTxtPath = os.path.join(self.textsFolderPath, "dosNewLine.txt")
        self.tabAndTrailingSpaceTxtPath = os.path.join(self.textsFolderPath, "tabAndTrailingSpace.txt")
        self.unixNewLineTxtPath = os.path.join(self.textsFolderPath, "unixNewLine.txt")
        self.mixedNewLineTxtPath = os.path.join(self.textsFolderPath, "mixedNewLine.txt")
        self.noNewLineTxtPath = os.path.join(self.textsFolderPath, "noNewLine.txt")
        self.emptyTxtPath = os.path.join(self.textsFolderPath, "empty.txt")

    def _testTextOptions(self, textOptions=None, expectedTextFileContents={}):
        scmWork = self.scmWork
        # Create a folder with a couple of messed up text files.
        _tools.makeFolder(self.textsFolderPath)
        self.writeBinaryFile(self.dosNewLineTxtPath, "1\r\n2\r\n")
        self.writeBinaryFile(self.unixNewLineTxtPath, "1\n2\n")
        self.writeBinaryFile(self.mixedNewLineTxtPath, "1\r\n2\n3\r")
        self.writeBinaryFile(self.mixedNewLineTxtPath, "1\r\n2\n3\r\n4\n")
        self.writeBinaryFile(self.noNewLineTxtPath, "1")
        self.writeBinaryFile(self.tabAndTrailingSpaceTxtPath, ".\t1 \n")
        self.writeBinaryFile(self.emptyTxtPath, "")

        scunch.scunch(self.testPunchTextPath, scmWork, textOptions=textOptions)

        for filePathToTest, expectedContent in expectedTextFileContents.items():
            self._assertWorkTextFileEquals(filePathToTest, expectedContent)

        scmWork.addUnversioned("")
        self.assertNonNormalStatus({scunch.ScmStatus.Added: 1 + len(expectedTextFileContents)})
        self._testAfterPunch(self.testPunchTextPath, textOptions)

    def testTextOptionsNative(self):
        self.setUpProject("punchTextNative")
        self.testPunchTextPath = self.createTestFolder("testPunchTextNative")
        self.scmWork.exportTo(self.testPunchTextPath, clear=True)
        self._setTextFilePaths()
        self._testTextOptions(
            scunch.TextOptions("**/*.txt"),
            {
                self.dosNewLineTxtPath: "1%s2%s" % (os.linesep, os.linesep),
                self.unixNewLineTxtPath: "1%s2%s"  % (os.linesep, os.linesep),
                self.mixedNewLineTxtPath: "1%s2%s3%s4%s" % (os.linesep, os.linesep, os.linesep, os.linesep),
                self.noNewLineTxtPath: "1%s" % os.linesep,
                self.emptyTxtPath: "",
                self.tabAndTrailingSpaceTxtPath: ".\t1 %s" % os.linesep,
            }
        )

    def testTextOptionsUnixSpaceStrip(self):
        self.setUpProject("punchTextNativeSpaceStrip")
        self.testPunchTextPath = self.createTestFolder("testPunchTextNativeSpaceStrip")
        self.scmWork.exportTo(self.testPunchTextPath, clear=True)
        self._setTextFilePaths()
        self._testTextOptions(
            scunch.TextOptions("**/*.txt", scunch.TextOptions.Unix, 4, True),
            {
                self.dosNewLineTxtPath: "1\n2\n",
                self.unixNewLineTxtPath: "1\n2\n",
                self.mixedNewLineTxtPath: "1\n2\n3\n4\n",
                self.noNewLineTxtPath: "1\n",
                self.emptyTxtPath: "",
                self.tabAndTrailingSpaceTxtPath: ".   1\n",
            }
        )

    def testPunchWithPattern(self):
        IncludePatternText="**/*.py **/*.html"
        ExcludePatternText = "**/*i*.py"
        WorkOnlyPatternText="build.xml"

        self.setUpProject("punchWithPattern")
        scmWork = self.scmWork

        testPunchWithPatternPath = self.createTestFolder("testPunchWithPattern")
        scmWork.exportTo(testPunchWithPatternPath, clear=True)
        buildXmlWorkPath = scmWork.absolutePath("added build.xml in work", "build.xml")
        helloPyWorkPath = scmWork.absolutePath("removed hello.py in work", "hello.py")
        readMeTxtWorkPath = scmWork.absolutePath("removed ReadMe.txt in work", "ReadMe.txt")
        whilePyExternalPath = os.path.join(testPunchWithPatternPath, "loops", "while.py")
        os.remove(helloPyWorkPath)
        os.remove(readMeTxtWorkPath)
        os.remove(whilePyExternalPath)
        self.writeTextFile(buildXmlWorkPath, "<!-- This would normally contain some ant target for scunch. -->")
        patternPuncher = scunch.ScmPuncher(scmWork)
        patternPuncher.punch(testPunchWithPatternPath, includePatternText=IncludePatternText, excludePatternText=ExcludePatternText, workOnlyPatternText=WorkOnlyPatternText)

        self.assertTrue(os.path.exists(helloPyWorkPath))
        self.assertTrue(os.path.exists(buildXmlWorkPath))
        self.assertFalse(os.path.exists(readMeTxtWorkPath))

        self.assertNonNormalStatus({scunch.ScmStatus.Unversioned: 1, scunch.ScmStatus.Missing: 1})
        # TODO: Remove: self._testAfterPunch(testPunchWithPatternPath)


if __name__ == '__main__':
    scunch._setUpLogging(logging.DEBUG)
    logging.getLogger("antglob").setLevel(logging.INFO)
    unittest.main()
