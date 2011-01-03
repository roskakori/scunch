#!/usr/bin/env python
"""
Scunch
======

Scunch is a tool to "punch" the files from an unversioned folder into a
working copy of a software configuration management system (SCM) and apply the
necessary SCM operations such as "add" and "remove".

Intended scenarios of use are:

  * Automatic version management of external sources delivered by a third party.
  * Automatic version management of typically unversioned centralized resources such as server configuration files.
  * Pseudo version management for users that have issues with manual version management (usual suspects are: managers, graphical artists, mainframe elders, ...).

Currently supported SCM's are:

 * Subversion (svn)

Installation
------------

To install scunch, you need:

* Python 2.6 or any later 2.x version, available from
  <http://www.python.org/>.
* The ``distribute`` package, available from
  <http://packages.python.org/distribute/>.

Then you can simply run::

  easy_install scunch

If you prefer a manual installation, you can obtain the ZIP archive from
<http://pypi.python.org/pypi/scunch/>.  Furthermore the source code is
available from <https://github.com/roskakori/scunch>.

Basic usage
-----------

To read a summary of the available options, run::

  > scunch --help

To "punch" the folder ``/tmp/ohsome`` into the work copy ``~/projects/ohsome``, run::

  > scunch /tmp/ohsome ~/projects/ohsome

To do the same but also commit the changes, run::

  > scunch --commit --message "Punched version 1.3.8." /tmp/ohsome ~/projects/ohsome

To control how much details you can see during the punching, use ``--log.``. To see
only warnings and errors, use::

  > scunch --log=warning /tmp/ohsome ~/projects/ohsome

To see a lot of details about the inner workings, use::

  > scunch --log=debug /tmp/ohsome ~/projects/ohsome


Upgrading from old school version management
--------------------------------------------

Tim is a hobbyist developer who has been programming a nifty utility
program for a while called "nifti". Until recently he has not been using
any version management. If he thought it useful to keep a certain state of
the source code, he just copied it to a new folder and added a timestamp to
the folder name::

  > cd ~/projects
  > ls
  nifti
  nifti_2010-11-27
  nifti_2010-09-18
  nifti_2010-07-03
  nifti_2010-05-23

After having been enlightened, he decides to move the project to a
Subversion repository. Nevertheless he would like to have all his snapshots
available.

As a first step, Tim creates a local Subversion repository::

  > mkdir /home/tim/repositories
  > svnadmin create /home/tim/repositories

Next he adds the project folders using the ``file`` protocol::

  > svn mkdir file:///home/tim/repositories/nifti/trunk  file:///home/tim/repositories/nifti/tags  file:///home/tim/repositories/nifti/branches

No he can check out the ``trunk`` to a temporary folder::
  
  > cd /tmp
  > svn checkout --username tim file:///home/tim/repositories/nifti/trunk nifti

Now it is time to punch the oldest version into the still empty work copy::

  > scunch ~/projects/nifti_2010-05-23

Tim reviews the changes to be committed. Unsurprisingly, there are only
"add" operations::

  > svn status
  A   setup.py
  A   README.txt
  A   nifti/
  ...

To commit this, Tim runs::

  > svn commit --message "Added initial version."

Then he proceeds with the other versions, where he lets ``scunch`` handle
the commit all by itself::

  > scunch --commit ~/projects/nifti_2010-07-03
  > scunch --commit ~/projects/nifti_2010-08-18
  > scunch --commit ~/projects/nifti_2010-11-27
  > scunch --commit ~/projects/nifti

Now all the changes are nicely traceable in the repository. However, the
timestamps use the time of the commit instead of the date when the source
code was current. In order to fix that, Tim looks at the history log to
find out the revision number of his changes and notes which actual date the
are supposed to represent::

  r1 --> before 2010-05-23
  r2 --> 2010-05-23
  r3 --> 2010-07-03
  r4 --> 2010-08-18
  r5 --> 2010-11-27
  r6 --> today

To update the timestamp in the repository, Tim sets the revision property
``date`` accordingly::

  > svn propset svn:date --revprop --revision 2 "2010-05-23 12:00:00Z" file:///home/tim/repositories/nifti/trunk

Note that this only works with the ``file`` protocol. If you want to do the
same on a repository using the ``http`` protocol, you have to install a
proper post commit hook in the repository that allows you to change
properties even after they have been comitted. Refer to the Subversion
manual for details on how to do that.

Similarly, Tim can set the log comments to a more meaningful text using the
revision property ``log``.

Once the repository is in shape, Tim can remove his current source code and
replace it with the work copy::

  > cd ~/projects
  > mv nifti nifti_backup # Do not delete just yet in case something went wrong.
  > svn checkout file:///home/tim/repositories/nifti/trunk nifti

Now Tim has a version controlled project where he can commit changes any
time he wants.


Version management of third party source code
---------------------------------------------

Joe works in an IT department. One of his responsibilities to install
updates for a web application named "ohsome" developed and delivered by a
third party. The work flow for this is well defined:

  1. Vendor send the updated source code to Joe in a ZIP archive containing
     a mix of HTML, JavaScript and XML files, mixed in with a few server
     configuration files.

  2. Joe extracts the ZIP archive to a local folder.

  3. Joe moves the contents of local folder to the application folder on
     the server. In the process, he removes all previous files for the
     application.

This works well as long as the vendor managed to pack everything into the ZIP
archive. However, experience shows that the vendor sometimes forgets to
include necessary files in the ZIP archive or does include configurations
files intended for a different site. While these situations always could be
resolved, it took a long time to analyze what's wrong and find out which files
were effected. This resulted in delays of a release, reduced end user
satisfaction and large amount of phone calls being made and email being
sent - including summaries for the management.

Joe decides that it would be a good idea to take a look at the changes
before copying them to the web server. And even if he cannot spot a
mistake before installing an update, SCM should help him in his
analysis later on.

Joe's company already has a Subversion repository for various projects, so
as a first step he adds a new project to the repository and creates a new
work copy on his computer::

  > svn add --message "Added project folders for ohsome application by Vendor." http://svn.joescompany.com/ohsome http://svn.joescompany.com/ohsome/trunk http://svn.joescompany.com/ohsome/tags http://svn.joescompany.com/ohsome/branches

This creates a project folder and the usual trunk, tags and branches
folders. For the time being, Joe intends to use only the trunk to hold the
most current version of the "ohsome" application.

Next, Joe creates a yet empty work copy in a local folder on his computer::

  > cd ~/projects
  > svn checkout http://svn.joescompany.com/ohsome/trunk ohsome

Now he copies all the files from the web server to the work copy::

  > cp -r /web/ohsome/* ~/projects/ohsome 

Although the files are now in the work copy, the are not yet under version
management. So Joe adds almost all the files except one folder named "temp" that
according to his knowledge contains only temporary files generated by the
web application.

  > cd ~/projects/ohsome
  > svn propset svn:ignore temp .
  > svn add ...

After that, he manually commits the current state of the web server::

  > svn commit --message "Added initial application version 1.3.7."
  
For the time being, Joe is done.

A couple of weeks later, the vendor send a ZIP archive with the application
version 1.3.8. As usual, Joe extracts the archive::

  > cd /tmp
  > unzip ~/Downloads/ohsome_1.3.8.zip

The result of this is a folder /tmp/ohsome containing all the files and
folders to be copied to the web server under /web/ohsome/. However, this
time Joe wants to review the changes first by "punching" them into his
work copy. So he runs ``scunch`` with the following options::

  > scunch /tmp/ohsome ~/projects/ohsome

This "punches" all the changes from folder /tmp/ohsome (where the ZIP
archive got extracted) to the work copy in ~/projects/ohsome.

As a result Joe can review the changes. He uses TortoiseSVN for that, but
``svn status`` and ``svn diff`` would have worked too.

Once he finished his review without noticing any obvious issues, he
manually commits the changes::

  > cd ~/projects/ohsome
  > svn commit --message "Punched version 1.3.8."

When version 1.3.9 ships, Joe decides that he might as well review the
changes directly in the repository after the commit. So this time he simply
uses::

  > cd /tmp
  > unzip ~/Downloads/ohsome_1.3.9.zip
  > scunch --commit --message "Punched version 1.3.9."

Joe can then use ``svn log`` to look for particular points of interest.
For instance, to find modified configuration files (matching the pattern \*.cfg)::

  > svn log --verbose --limit 1 http://svn.joescompany.com/ohsome/trunk | grep "\\.cfg$"

To get a list of Removed files and folders::

  > svn log --verbose --limit 1 http://svn.joescompany.com/ohsome/trunk | grep "^   D" 

(Note: The ``grep`` looks for three blanks and a "D" for "deleted".)
 
 
.. Pseudo SCM for users with SCM issues
.. ------------------------------------
.. 
.. SCM in its current form approached the IT scene relatively late. Most
.. concepts for operating systems and file management already have been
.. established a long time ago. Consequently SCM has not been integrated well
.. in the users's work flow and ended up as optional add on instead of being
.. an integral part of it. Despite brave attempts like MULTICS, VMS, WebDAV
.. and Desktop integrations like TortoiseSVN, version managements remains a
.. mystery to many.
.. 
.. Although software developers profit enough from SCM to take the effort
.. learning to cope with them, people from other backgrounds keep stumbling
.. over the various idiosyncrasies and usability issues modern SCM's offer.
.. This is particular true for people who see computers as tools that help
.. them to get their job done and often limit their use to a single
.. application (for instance graphical artists) or people who at one time
.. decided that the know everything they need to know about computers and can
.. safely ignore everything that happened after the Disco movement (for
.. instance mainframe elders).
.. 
.. Continuous attempts to get such people to use an SCM only result in
.. increased frustration and waste of time for everybody involved.
.. 
.. TODO: Describe solution.
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

# Developer cheat sheet:
#
# Create the installer archive:
#
# > python setup.py sdist --formats=zip
#
# Upload release to PyPI:
#
# > python scunch/test_scunch.py
# > python setup.py sdist --formats=zip upload
import difflib
import errno
import logging
import optparse
import os.path
import shutil
import stat
import subprocess
import sys
import tempfile
import types
import urlparse
import xml.sax
from xml.sax.handler import ContentHandler

__version__ = "0.1"

_log = logging.getLogger("scunch")

def _humanReadableCommand(commandAndOptions):
    result = ""
    isFirstItem = True
    for commandItem in commandAndOptions:
        if " " in commandItem:
            commandItem = '"%s"' % commandItem
        if isFirstItem:
            isFirstItem = False
        else:
            result += " "
        result += commandItem
    return result

def run(commandAndOptions, returnStdout=False, cwd=None):
    assert commandAndOptions
    result = None
    commandName = commandAndOptions[0]
    commandText = _humanReadableCommand(commandAndOptions)
    _log.info("run: %s", commandText)
    with tempfile.TemporaryFile(prefix="scunch_stderr_") as stderrLines:
        if returnStdout:
            stdoutLines = tempfile.TemporaryFile(prefix="scunch_stdout_")
        else:
            stdoutLines = open(os.devnull, "wb")
        try:
            exitCode = subprocess.call(commandAndOptions, stdout=stdoutLines, stderr=stderrLines, cwd=cwd)
            if exitCode != 0:
                stderrLines.seek(0)
                errorMessage = stderrLines.readline().rstrip("\n\r")
                if errorMessage:
                    if errorMessage[-1] not in ".!?":
                        errorMessage += "."
                    errorMessage = " Error: " + errorMessage
                else:
                    errorMessage = "."
                raise ScmError("cannot perform shell command %r.%s Command:  %s" %(commandName, errorMessage, commandText))
        except OSError, error:
            raise ScmError("cannot perform shell command %r: %s. Command:  %s" %(commandName, error, commandText))
        finally:
            if returnStdout:
                result = []
                stdoutLines.seek(0)
                for line in stdoutLines:
                    result.append(line.rstrip('\n\r'))
            stdoutLines.close()
    return result

def removeFolder(folderPathToRemove):
    # Attempt to remove the folder, ignoring any errors.
    _log.info("remove folder \"%s\"", folderPathToRemove)
    shutil.rmtree(folderPathToRemove, True)
    if os.path.exists(folderPathToRemove):
        # If the folder still exists after the removal, try to remove it again but this
        # time with errors raised. In most cases, this will result in a proper error message
        # explaining why the folder could not be removed the first time.
        shutil.rmtree(folderPathToRemove)

def makeFolder(folderPathToMake):
    """
    Like `os.makedirs` but does nothing if the folder already exists.
    """
    try:
        os.makedirs(folderPathToMake)
    except OSError, error:
        if error.errno !=  errno.EEXIST:
            raise

class ScmError(Exception):
    pass

class ScmStatus(object):
    Added = "added"
    Conflicted = "conflicted"
    External = "external"
    Ignored = "ignored"
    Incomplete = "incomplete"
    Merged = "merged"
    Missing = "missing"
    Modified = "modified"
    None_ = "none"
    Normal = "normal"
    Obstructed = "obstructed"
    Removed = "deleted"
    Replaced = "replaced"
    Unversioned = "unversioned"
    
    _CleanStati = set([External, Ignored, None_, Normal])
    _ModifiedStati = set([Added, Merged, Modified, Removed])
    _CommitableStati = _CleanStati | _ModifiedStati

    _SvnStatusToStatusMap = {
        "added": Added,
        "conflicted": Conflicted,
        "deleted": Removed,
        "external": External,
        "ignored": Ignored,
        "incomplete": Incomplete,
        "merged": Merged,
        "missing": Missing,
        "modified": Modified,
        "none": None_,
        "normal": Normal,
        "obstructed": Obstructed,
        "replaced": Replaced,
        "unversioned": Unversioned
    }

    def __init__(self, path):
        if path is None:
            raise ScmError("status item path must not be None")
        if not path:
            raise ScmError("status item path must not be empty")
        self.path = path
        self.status = None
        self.propertiesStatus = None

    def _bothStatIn(self, possibleStati):
        result = (self.status in possibleStati) and (self.propertiesStatus in possibleStati) 
        return result
    
    def isClean(self):
        return self._bothStatIn(ScmStatus._CleanStati)

    def isModified(self):
        return self._bothStatIn(ScmStatus._ModifiedStati)

    def isCommitable(self):
        return self._bothStatIn(ScmStatus._CommitableStati)

    def __unicode__(self):
        return u"%s:%s,%s" % (self.path, self.status, self.propertiesStatus)
        
    def __str__(self):
        return unicode(self).encode('utf-8')

class _SvnStatusContentHandler(ContentHandler):
    _ElementsToIgnore = set(('author', 'commit', 'date', 'status', 'target'))
    def __init__(self):
        self.statusItems = []
        self.currentEntry = None

    def _svnStatusAsScmStatus(self, attributes, statusAttributeName):
        assert attributes is not None
        assert statusAttributeName
        svnStatus = attributes.get(statusAttributeName)
        if svnStatus is None:
            raise ScmError("attribute <wc-status %s=...> must be specified for <entry path=\"%s\">" % (statusAttributeName, self.currentEntry.path))
        result = ScmStatus._SvnStatusToStatusMap.get(svnStatus)
        if result is None:
            raise ScmError("cannot process unknown status: %r" % svnStatus)
        if result == ScmStatus.None_:
            result = None
        _log.debug("  status: svn=%r --> %r", svnStatus, result)
        return result

    def startElement(self, name, attributes):
        if name == "entry":
            entryPath = attributes.get("path")
            self.currentEntry = ScmStatus(entryPath)
        elif name == "wc-status":
            if not self.currentEntry:
                raise ScmError("<entry> must occur before <wc-props>")
            self.currentEntry.status = self._svnStatusAsScmStatus(attributes, "item")
            self.currentEntry.propertiesStatus = self._svnStatusAsScmStatus(attributes, "props")
        elif name not in _SvnStatusContentHandler._ElementsToIgnore:
            _log.warning("ignored <%s>", name)

    def endElement(self, name):
        if name == "entry":
            self.statusItems.append(self.currentEntry)
            self.currentEntry = None

class ScmStorage(object):
    """
    Abstract storage (repository) for a software configuration management system (SCMS).
    """
    def __init__(self, baseQualifier):
        """
        Create a storage at ``baseQualifier``. The syntax for the baseQualifier depends on the SCM used.
        If the storage does not yet physically exist, use `create` before calling any other commands.
        """
        self.checkAbsolteQualifier("base baseQualifier", baseQualifier)
        self.baseQualifier = baseQualifier
        if not self.baseQualifier.endswith("/"):
            self.baseQualifier += "/"

    def create(self, localTargetPath, reset=False):
        """
        Create a new repository at ``localTargetPath``.
        """
        scmCreateCommand = ['svnadmin', 'create', localTargetPath]
        if reset:
            raise NotImplementedError()
        run(scmCreateCommand)

    def checkAbsolteQualifier(self, name, qualifierToCheck):
        assert name
        ValidProtocols = ("file", "http", "https", "svn", "svn+ssh")
        if qualifierToCheck is None:
            raise ScmError("%s must not be None")
        if not qualifierToCheck:
            raise ScmError("%s must not be empty")
        hasValidProtocoll = False
        for validProtocoll in ValidProtocols:
            if qualifierToCheck.startswith(validProtocoll + ":"):
                hasValidProtocoll = True
        if not hasValidProtocoll:
            raise ScmError("%s must start with one of %s but is: %s", (name, str(ValidProtocols), qualifierToCheck))
            
    def checkRelativeQualifier(self, name, qualifierToCheck):
        assert name
        if qualifierToCheck is None:
            raise ScmError("%s must not be None" % name)
            
    def absoluteQualifier(self, relativeQualifier):
        self.checkRelativeQualifier("internal qualifier", relativeQualifier)
        result = urlparse.urljoin(self.baseQualifier, relativeQualifier)
        self.checkAbsolteQualifier("internal qualifier", result)
        return result

    def absoluteQualifiers(self, relativeQualifiers):
        result = []
        if isinstance(relativeQualifiers, types.StringTypes):
            actualRelativeQualifiers = [relativeQualifiers]
        else:
            actualRelativeQualifiers = relativeQualifiers
        for actualRelativeQualifierToCreate in actualRelativeQualifiers:
            result.append(self.absoluteQualifier(actualRelativeQualifierToCreate))
        return result
 
    def mkdir(self, relativeQualifiersToCreate, message):
        scmCommand = ["svn", "mkdir"]
        if message:
            scmCommand.extend(["--message", message])
        scmCommand.extend(self.absoluteQualifiers(relativeQualifiersToCreate)) 
        run(scmCommand)

class FolderItem(object):
    File = 'file'
    Folder = 'folder'

    def __init__(self, elements=[], name="", baseFolderPath=""):
        assert elements is not None
        assert name is not None
        assert baseFolderPath is not None
        
        itemElements = list(elements)
        if name:
            itemElements.append(name)
        self.elements = tuple(itemElements)
        self.relativePath = resolvedPathElements(self.elements)
        self.path = self.absolutePath(baseFolderPath)
        try:
            itemInfo = os.stat(self.path)
        except OSError, error:
            if error.errno == errno.ENOENT:
                raise ScmError("folder item must remain during processing but was removed in the background: %r" % self.path)
            else:
                raise
        itemMode = itemInfo.st_mode
        if stat.S_ISDIR(itemMode):
            self.kind = FolderItem.Folder
        elif stat.S_ISREG(itemMode):
            self.kind = FolderItem.File
        else:
            raise ScmError("folder item must be a folder or file: %r" % self.path)
        self.size = itemInfo.st_size
        self.timeModified = itemInfo.st_mtime

    def absolutePath(self, baseFolderPath):
        assert baseFolderPath is not None
        return os.path.join(baseFolderPath, self.relativePath)

    def __hash__(self):
        return self.elements.__hash__()

    def __cmp__(self, other):
        return cmp(self.elements, other.elements)

    def __eq__(self, other):
        return self.elements == other.elements

    def __unicode__(self):
        return u"FolderItem(kind=%s, elements=%s)" % (self.kind, self.elements)
        
    def __str__(self):
        return unicode(self).encode('utf-8')

def _sortedFolderItems(folderItemsToSort):
    def comparedFolderItems(some, other):
        assert some is not None
        assert other is not None
        
        # Sort folders before files, hence '-'.
        typeComparison = -cmp(some.kind, other.kind)
        if typeComparison:
            result = cmp(some.elements, other.elements)
        else:
            result = typeComparison
        return result

    assert folderItemsToSort is not None
    result = []
    for item in folderItemsToSort:
        result.append(item)
    result = sorted(result, comparedFolderItems)
    return result

def resolvedPathElements(elements=[]):
    assert elements is not None
    result = ""
    for element in elements:
        result = os.path.join(result, element)
    return result

def _listFolderItems(baseFolderPath, baseFolderItem, isAcceptable=None):
    """
    List of folder items starting with ``baseFolderPath`` joined according to the path elements
    of ``baseFolderItem``.
    """
    assert baseFolderItem.kind == FolderItem.Folder
    folderPath = baseFolderItem.absolutePath(baseFolderPath)
    _log.debug("  scan: %s", folderPath)
    for itemName in os.listdir(folderPath):
        item = FolderItem(baseFolderItem.elements, itemName, baseFolderPath)
        if (isAcceptable is None) or isAcceptable(item):
            yield item
            if item.kind == FolderItem.Folder:
                for nestedItem in _listFolderItems(baseFolderPath, item, isAcceptable):
                    yield nestedItem
        else:
            _log.debug("  reject: %s", item)

def listFolderItems(folderPathToList, isAcceptable=None):
    """
    List of folder items starting with ``folderPathToList``.
    """
    item = FolderItem(baseFolderPath=folderPathToList)
    if item.kind != FolderItem.Folder:
        # Note: We could easily "yield" a file too. The current design just does not require this
        # because a folder to punch cannot be meaningfully processed in case it is a file.
        raise ScmError("path to list must be a folder: %r" % folderPathToList)
    if isAcceptable and not isAcceptable(item):
        raise ScmError("folder to list must be acceptable: %r" % folderPathToList)
    for nestedItem in _listFolderItems(folderPathToList, item, isAcceptable):
        yield nestedItem

class ScmPuncher(object):
    """
    Puncher to transform a work copy according to the current state of an external folder.
    """
    def __init__(self, scmWork):
        assert scmWork is not None
        self.scmWork = scmWork
        self._clear()

    def _clear(self):
        self.externalItems = None
        self.workItems = None
        self._externalFolderPath = None
        self._addedItems = None
        self._modifiedItems = None
        self._removedItems = None

    def _isInLastRemovedFolder(self, itemToCheck):
        result = False
        if self._removedItems:
            lastRemovedItem = self._removedItems[-1]
            if lastRemovedItem.kind == FolderItem.Folder:
                if lastRemovedItem.elements == itemToCheck.elements[:len(lastRemovedItem.elements)]:
                    result = True
        return result

    def _workPathFor(self, folderItem):
        assert folderItem is not None
        return folderItem.absolutePath(self.scmWork.localTargetPath)

    def _externalPathFor(self, folderItem):
        assert folderItem is not None
        assert self._externalFolderPath is not None
        return folderItem.absolutePath(self._externalFolderPath)

    def _add(self, items):
        for itemToAdd in items:
            if not self._isInLastRemovedFolder(itemToAdd):
                _log.debug('schedule item for add: "%s"', itemToAdd.relativePath)
                self._addedItems.append(itemToAdd)
            else:
                _log.debug('skip added item in removed folder: "%s"', itemToAdd.relativePath)

    def _remove(self, items):
        for itemToRemove in items:
            if not self._isInLastRemovedFolder(itemToRemove):
                _log.debug('schedule item for remove: "%s"', itemToRemove.relativePath)
                self._removedItems.append(itemToRemove)
            else:
                _log.debug('skip removed item in removed folder: "%s"', itemToRemove.relativePath)
    
    def _modify(self, items):
        for itemToModify in items:
            if not self._isInLastRemovedFolder(itemToModify):
                # TODO: Add option to consider items modified by only checking their date.
                _log.debug('schedule item for copy: "%s"', itemToModify.relativePath)
                self._modifiedItems.append(itemToModify)
            else:
                _log.debug('skip modified item in removed folder: "%s"', itemToModify.relativePath)

    def _copyItem(self, itemToCopy):
        externalPathOfItemToCopy = self._externalPathFor(itemToCopy)
        workPathOfItemToCopy = self._workPathFor(itemToCopy)
        shutil.copy2(externalPathOfItemToCopy, workPathOfItemToCopy)

    def _setExternalAndWorkItems(self, externalFolderPath, relativeWorkFolderPath=""):
        assert externalFolderPath is not None
        assert relativeWorkFolderPath is not None

        self._externalFolderPath = externalFolderPath

        # Collect external items.
        self.externalItems = listFolderItems(externalFolderPath)
        self.externalItems = _sortedFolderItems(self.externalItems)
        _log.info("external items:")
        for item in self.externalItems:
            _log.debug('  %s', item)

        # Collect items in work copy.
        self.workItems = self.scmWork.listFolderItems(relativeWorkFolderPath)
        self.workItems = _sortedFolderItems(self.workItems)
        _log.debug("work items:")
        for item in self.workItems:
            _log.debug('  %s', item)
        
    def _setAddedModifiedRemovedItems(self):
        assert self._externalFolderPath is not None
        assert self.workItems is not None
        assert self.externalItems is not None

        matcher = difflib.SequenceMatcher(None, self.workItems, self.externalItems)
        _log.debug("matcher: %s", matcher.get_opcodes())
        self._addedItems = []
        self._modifiedItems = []
        self._removedItems = []

        for operation, i1, i2, j1, j2 in matcher.get_opcodes():
            _log.debug("%s: %d, %d; %d, %d", operation, i1, i2, j1, j2)
            if operation == 'insert':
                self._add(self.externalItems[j1:j2])
            elif operation == 'equal':
                self._modify(self.externalItems[i1:i2])
            elif operation == 'delete':
                self._remove(self.workItems[i1:i2])
            elif operation == 'replace':
                self._add(self.workItems[i1:i2])
                self._remove(self.externalItems[j1:j2])
            else:
                assert False, "operation=%r" % operation

    def _setCopiedAndMovedItems(self):
        assert self._externalFolderPath is not None
        assert self.workItems is not None
        assert self.externalItems is not None

        self._copiedItems = []
        self._movedItems = []

    def _applyAddedModifiedRemovedItems(self):
        _log.info("punch modifications into work copy")
        if self._removedItems:
            _log.info("remove %d items", len(self._removedItems))
            relativePathsToRemove = [itemToRemove.relativePath for itemToRemove in self._removedItems]
            self.scmWork.remove(relativePathsToRemove, recursive=True, force=True)
        if self._modifiedItems:
            _log.info("modify %d items", len(self._modifiedItems))
            for itemToModify in self._modifiedItems:
                if itemToModify.kind == FolderItem.Folder:
                    makeFolder(self._workPathFor(itemToModify))
                else:
                    self._copyItem(itemToModify)
        if self._addedItems:
            _log.info("add %d items", len(self._modifiedItems))
            # Create added folders and copy added files.
            for itemToAdd in self._addedItems:
                if itemToAdd.kind == FolderItem.Folder:
                    makeFolder(self._workPathFor(itemToAdd))
                else:
                    self._copyItem(itemToAdd)
            # Add folders and files to SCM.
            for itemToAdd in self._addedItems:
                _log.info('  add "%s"', itemToAdd.relativePath)
                relativePathsToAdd = [itemToAdd.relativePath for itemToAdd in self._addedItems]
                self.scmWork.add(relativePathsToAdd, recursive=False)

    def punch(self, externalFolderPath, relativeWorkFolderPath=""):
        try:
            self._setExternalAndWorkItems(externalFolderPath, relativeWorkFolderPath)
            self._setAddedModifiedRemovedItems()
            self._setCopiedAndMovedItems()
            self._applyAddedModifiedRemovedItems()
        finally:
            self._clear()

class ScmWork(object):
    """
    Abstract working copy with a software configuration management system (SCMS).
    """
    CheckOutActionReset = "reset"
    CheckOutActionSkip = "skip"
    CheckOutActionCreate = "create"
    CheckOutActionUpdate = "update"
    _ValidCheckOutActions = set((CheckOutActionCreate, CheckOutActionReset, CheckOutActionSkip, CheckOutActionUpdate))

    def __init__(self, storage, relativeQualifierInStorage, localTargetPath, checkOutAction=CheckOutActionSkip):
        assert storage is not None
        assert relativeQualifierInStorage is not None
        assert localTargetPath is not None
        if checkOutAction not in ScmWork._ValidCheckOutActions:
            raise ScmError("check out action is %r but must be one of: %s", str(sorted(ScmWork._ValidCheckOutActions)))
        self.storage = storage
        self.relativeQualifierInStorage = relativeQualifierInStorage
        self.baseWorkQualifier = self.storage.absoluteQualifier(self.relativeQualifierInStorage)
        self.localTargetPath = localTargetPath

        hasExistingWork = os.path.exists(self.localTargetPath)
        if hasExistingWork and (checkOutAction == ScmWork.CheckOutActionReset):
            self.clear()
        
        if checkOutAction in (ScmWork.CheckOutActionCreate, ScmWork.CheckOutActionReset):
            self.checkout()
        elif checkOutAction == ScmWork.CheckOutActionUpdate:
            self.update()
        else:
            assert checkOutAction == ScmWork.CheckOutActionSkip, 'checkOutAction=%r' % checkOutAction

    def clear(self):
        """
        Remove work copy folder and all its contents.
        """
        _log.info("remove work copy at \"%s\"", self.localTargetPath)
        removeFolder(self.localTargetPath)
        
    def checkout(self):
        _log.info("check out work copy at \"%s\"", self.localTargetPath)
        scmCommand = ["svn", "checkout", self.baseWorkQualifier, self.localTargetPath]
        run(scmCommand)

    def update(self, relativePathToUpdate=""):
        _log.info("update out work copy at \"%s\"", self.localTargetPath)
        pathToUpdate = os.path.join(self.localTargetPath, relativePathToUpdate)
        scmCommand = ["svn", "update", "--non-interactive", pathToUpdate]
        run(scmCommand, cwd=self.localTargetPath)

    def absolutePath(self, name, relativePath):
        assert name
        if relativePath is None:
            raise ScmError("%s must not be None" % relativePath)
        result = os.path.join(self.localTargetPath, relativePath)
        return result

    def absolutePaths(self, name, relativePaths):
        result = []
        isSingleRelativePathString = isinstance(relativePaths, types.StringTypes)
        if isSingleRelativePathString:
            actualRelativePaths = [relativePaths]
        else:
            actualRelativePaths = relativePaths
        for relativePath in actualRelativePaths:
            result.append(self.absolutePath(name, relativePath))
        if not result:
            raise ScmError("at least 1 %s must be specified")
        return result

    def add(self, relativePathsToAdd, recursive=True):
        _log.info("add: %s", str(relativePathsToAdd))
        assert relativePathsToAdd is not None
        svnAddCommand = ["svn", "add", "--non-interactive"]
        if not recursive:
            svnAddCommand.append("--non-recursive")
        if isinstance(relativePathsToAdd, types.StringTypes):
            svnAddCommand.append(relativePathsToAdd)
        else:
            svnAddCommand.extend(relativePathsToAdd)
        run(svnAddCommand, cwd=self.localTargetPath)

    def addUnversioned(self, relativePathsToExamine):
        # TODO: For unversioned folders, add only the folder without recursing and adding all the files in it.
        pathsToAdd = []
        for statusInfo in self.status(relativePathsToExamine, True):
            if statusInfo.status == ScmStatus.Unversioned:
                pathsToAdd.append(statusInfo.path)
            else:
                _log.debug("add unversioned: ignore: %r; %r", statusInfo.status, statusInfo.path)
        if pathsToAdd:
            self.add(pathsToAdd, True)

    def mkdir(self, relativeFolderPathToCreate):
        _log.info("mkdir: %s", relativeFolderPathToCreate)
        absoluteFolderPathToCreate = self.absolutePath("folder to create", relativeFolderPathToCreate)
        svnMkdirCommand = ["svn", "mkdir", "--non-interactive", absoluteFolderPathToCreate]
        run(svnMkdirCommand, cwd=self.localTargetPath)

    def remove(self, relativePathsToRemove, recursive=True, force=False):
        _log.info("remove: %s", str(relativePathsToRemove))
        assert relativePathsToRemove is not None
        svnAddCommand = ["svn", "remove", "--non-interactive"]
        if force:
            svnAddCommand.append("--force")
        if not recursive:
            svnAddCommand.append("--non-recursive")
        if isinstance(relativePathsToRemove, types.StringTypes):
            svnAddCommand.append(relativePathsToRemove)
        else:
            svnAddCommand.extend(relativePathsToRemove)
        run(svnAddCommand, cwd=self.localTargetPath)

    def commit(self, relativePathsToCommit, message, recursive=True):
        assert relativePathsToCommit is not None
        assert message is not None
        _log.info("commit: %s", str(relativePathsToCommit))
        svnCommitCommand = ["svn", "commit", "--non-interactive"]
        if not recursive:
            svnCommitCommand.append("--non-recursive")
        svnCommitCommand.extend(["--message", message])
        svnCommitCommand.extend(self.absolutePaths("paths to commit", relativePathsToCommit))
        run(svnCommitCommand, cwd=self.localTargetPath)
        
    def isSpecialPath(self, path):
        name = os.path.basename(path)
        return (name.lower() in [".svn", "_svn"])

    def listStorage(self, relativePathsToList, recursive=True):
        absolutePathsToList = self.absolutePaths("paths to list", relativePathsToList)
        scmListCommand = ["svn", "list"]
        if recursive:
            scmListCommand.append("--recursive")
        scmListCommand.extend(absolutePathsToList)
        result = run(scmListCommand, returnStdout=True)
        return result

    def list(self, relativePathsToList, recursive=True, onlyFiles=True):
        """
        List of all files and folders found in the local working copy including ignored files but
        excluding special files used by the SCM (for instance ".svn" for Subversion).
        """
        absolutePathsToList = self.absolutePaths("paths to list", relativePathsToList)
        for pathToList in absolutePathsToList:
            for listedPath in self._list(pathToList, recursive, onlyFiles):
                yield listedPath

    def _list(self, folderPathToList, recursive, onlyFiles):
        for path in os.listdir(folderPathToList):
            if not self.isSpecialPath(path):
                if os.path.isdir(path):
                    if not onlyFiles:
                        yield path
                    for recursedPath in self._list(path, recursive, onlyFiles):
                        yield recursedPath
                else:
                    yield path

    def listFolderItems(self, relativeFolderToList=""):
        """
        List of folder items starting with ``relativeFolderPathToList`` excluding special items
        used internally by the SCM (such as for example ".svn" for Subversion).
        """
        def isAcceptable(folderItem):
            return not self.isSpecialPath(folderItem.elements[-1])

        if relativeFolderToList:
            raise NotImplementedError
        folderPathToList = self.localTargetPath
        item = FolderItem(baseFolderPath=folderPathToList)
        if item.kind != FolderItem.Folder:
            raise ScmError("work copy path to list must be a folder: %r" % folderPathToList)
        for nestedItem in _listFolderItems(folderPathToList, item, isAcceptable=isAcceptable):
            yield nestedItem

    def status(self, relativePathsToExamine, recursive=True):
        absolutePathsToExamine = self.absolutePaths("paths to examine", relativePathsToExamine)
        svnStatusCommand = ["svn", "status",  "--non-interactive", "--verbose", "--xml"]
        if not recursive:
            svnStatusCommand.append("--non-recursive")
        svnStatusCommand.extend(absolutePathsToExamine)
        statusXml = ""
        for statusLine in run(svnStatusCommand, returnStdout=True, cwd=self.localTargetPath):
            statusXml += statusLine + os.linesep
        statusHandler = _SvnStatusContentHandler()
        xml.sax.parseString(statusXml, statusHandler)
        for statusItem in statusHandler.statusItems:
            yield statusItem

    def exportTo(self, targetFolderPath, relativePathToExport="", clear=False):
        """
        Export contents of work copy to ``targetFolderPath``. If ``clear`` is ``True``,
        remove a possibly existing target folder.
        """
        assert targetFolderPath
        folderPathToExport = self.absolutePath("export path", relativePathToExport)
        if clear:
            removeFolder(targetFolderPath)
        _log.info("export \"%s\" to \"%s\"", folderPathToExport, targetFolderPath)
        shutil.copytree(folderPathToExport, targetFolderPath, ignore=shutil.ignore_patterns(".svn", "_svn"))

def createScmWork(workFolderPath):
    SvnUrlKey = "URL: "
    scmStorageQualifier = None
    for svnName in [".svn", "_svn"]:
        svnFolderToCheckFor = os.path.join(workFolderPath, svnName)
        _log.debug("check for %s", svnFolderToCheckFor)
        if os.path.exists(svnFolderToCheckFor):
            svnInfoLines = run(["svn", "info", workFolderPath], returnStdout=True)
            for infoLine in svnInfoLines:
                _log.debug("  analyze: %s", infoLine)
                if infoLine.startswith(SvnUrlKey):
                    scmStorageQualifier = infoLine[len(SvnUrlKey):]
                    _log.info("found svn work copy stored at %s", scmStorageQualifier)
    if scmStorageQualifier is None:
        raise ScmError("folder must be a working copy: \"%s\"" % workFolderPath)
    scmStorage = ScmStorage(scmStorageQualifier)
    result = ScmWork(scmStorage, "", workFolderPath, ScmWork.CheckOutActionSkip)
    return result

def listRelativePaths(folderToListPath, elements=[]):
    for folderItem in os.listdir(folderToListPath):
        itemElements = list(elements)
        itemElements.append(folderItem)
        itemPath = os.path.join(folderToListPath, folderItem)
        # TODO: Ignore special paths such as ".svn"
        if os.path.isdir(itemPath):
            yield ('folder', tuple(itemElements))
            for itemTypeAndElements in listRelativePaths(itemPath, itemElements):
                yield itemTypeAndElements
        else:
                yield ('file', tuple(itemElements))

def scunch(sourceFolderPath, scmWork):
    assert sourceFolderPath is not None
    _log.info("punch %r", sourceFolderPath)
    print sorted(scmWork.list(""))
    raise NotImplementedError()

_LogLevelNameMap = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR
}

_Usage = """%prog [options] FOLDER [WORK-FOLDER]
    
  Punch files and folders from an unversioned FOLDER into a SCM's
  work copy at WORK-FOLDER and perform the required add and remove
  operations."""

def main(arguments=None):
    if arguments == None:
        actualArguments = sys.argv
    else:
        actualArguments = arguments

    parser = optparse.OptionParser(usage=_Usage, version="%prog " + __version__)
    parser.add_option("-c", "--commit", action="store_true", dest="isCommit", help="after punching the changes into the work copy, commit them")
    parser.add_option("-L", "--log", default='info', dest="logLevel", metavar="LEVEL", type="choice", choices=_LogLevelNameMap.keys(), help='logging level (default: "%default")')
    parser.add_option("-m", "--message", default="Scunched.", dest="commitMessage", metavar="TEXT", help='text for commit message (default: "%default")')
    (options, others) = parser.parse_args(actualArguments[1:])
    othersCount = len(others)
    if othersCount == 0:
        parser.error("FOLDER to punch into work copy must be specified")
    elif othersCount == 1:
        sourceFolderPath = others[0]
        workFolderPath = os.getcwd()
    elif othersCount == 2:
        sourceFolderPath = others[0]
        workFolderPath = others[1]
    else:
        parser.error("unrecognized options must be removed: %s" % others[2:])

    logging.basicConfig(level=_LogLevelNameMap[options.logLevel])
   
    exitCode = 1
    try:
        scmWork = createScmWork(workFolderPath)
        scunch(sourceFolderPath, scmWork)
        if options.isCommit:
            scmWork.commit("", options.commitMessage)
        exitCode = 0
    except (EnvironmentError, ScmError), error:
        _log.error("%s", error)
    except Exception, error:
        _log.exception("%s", error)
    return exitCode

if __name__ == "__main__":
    sys.exit(main())
