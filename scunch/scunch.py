#!/usr/bin/env python
"""
======
Scunch
======

Scunch updates a working copy of a source code management (SCM) system
from an external folder and copies, adds and removes files and folders as
necessary.

Intended scenarios of use are:

* Automatic version management of external sources delivered by a third
  party.
* Automatic version management of typically unversioned centralized
  resources such as server configuration files.
* Migration of projects using folder based version management to a proper
  SCM.

.. TODO: Elaborate the below scenario.
.. Pseudo version management for users that have issues with manual version
.. management (usual suspects are: managers, graphical artists, mainframe
.. elders, ...).

Currently supported SCM systems are:

* Subversion (svn)

The name "scunch" is a combination of the acronym "SCM" and the word
"punch" with letters removed to make it easy to pronounce. (The initial
name used during early development was "scmpunch").


Installation
============

To install ``scunch``, you need:

* Python 2.6 or any later 2.x version, available from
  <http://www.python.org/>.
* The ``distribute`` package, available from
  <http://packages.python.org/distribute/>.

Then you can simply run::

  $ easy_install scunch

If you prefer a manual installation, you can obtain the ZIP archive from
<http://pypi.python.org/pypi/scunch/>.  Furthermore the source code is
available from <https://github.com/roskakori/scunch>.

To actually use ``scunch``, you lso need an SCM tool. In particular,
you need the SCM's command line client to be installed and located in the
shell's search path. Installing a desktop plug-in such as `TortoiseSVN
<http://tortoisesvn.tigris.org/>`_ is not enough because it does not
install a command line client.

Here are some hints to install a command line client on popular platforms:

* Mac OS X: ``svn`` is included in Leopard. Alternatively you can use
  `MacPorts <http://www.macports.org/>`_.
* Linux: Use your package manager, for example:
  ``apt-get install subversion``.
* Windows: Use `Slik SVN <http://www.sliksvn.com/en/download>`_.


Usage
=====

This section gives a short description of the available command line
options together with simple examples.

To read a summary of the available options, run::

  $ scunch --help

For more detailed usage in real world scenarios, read the section on
"<Scenarios scenarios>_".

Basic usage
-----------

To "punch" the folder ``/tmp/ohsome`` into the work copy ``~/projects/ohsome``, run::

  $ scunch /tmp/ohsome ~/projects/ohsome

To do the same but also commit the changes, run::

  $ scunch --after=commit --message "Punched version 1.3.8." /tmp/ohsome ~/projects/ohsome


Controlling the output
----------------------

To control how much details you can see during the punching, use ``--log.``. To see
only warnings and errors, use::

  $ scunch --log=warning /tmp/ohsome ~/projects/ohsome

To see a lot of details about the inner workings, use::

  $ scunch --log=debug /tmp/ohsome ~/projects/ohsome

Possible values for ``--log`` are: ``debug``, ``info`` (the default),
``warning`` and ``error``.


Specifying which files to process
---------------------------------

By default, ``scunch`` considers almost all files and folders
in the external folder for transfer, excluding:

* internal files and folders used by popular SCM systems, for example
  ``.svn`` and ``.gitignore``.
* internal system files, for example MacOS X's ``.DS_Store``.
* apparent temporary files, for example ``#*#``.

To ignore additional files use ``--exclude=PATTERN`` with ``PATTERN`` using
the popular `ant pattern syntax <http://ant.apache.org/manual/dirtasks.html>`_.
Ant patters are similar to shell patterns and support the "*" and "?" place
holder as usual. In addition to that, "**" stands for any amount of folders
and sub folders matching any folder nesting level.

For example, to exclude all Python byte code files, use::

  $ scunch --exclude "**/*.pyc, **/*.pyo" ...

In case you want to punch only Python and files and ignore everything
else, use ``--include``::

  $ scunch --include "**/*.py" ...

Of course you can combine both options to for example punch all Python
files except test cases::

  $ scunch --include "**/*.py" --exclude "**/test_*.py" ...

Sometimes the work copy includes files that will never exist in the
external folder. For example, the work copy might contain a script
to run ``scunch`` with all options set up already. Because this script
does not exist in the external folder, it would be removed as soon as
``scunch`` is run. To prevent this from happening, use
``--work-only=PATTERN``. For example::

  $ scunch --work-only "run_scunch.sh" ...

Note that this example does not use the "**" place holder because only
files in the work copy's top folder are of interest.

Preparing the work copy
-----------------------

When punching any changes from the external folder the current state of the
work copy influences what actually is going to happen.

``Scunch`` works best on a clean work copy without any pending changes and
messed up files. If this is not the case, ``scunch`` refuses to continue
announcing:

  Pending changes in "..." must be committed, use "svn status" for details.
  To resolve this, '--before=reset' to discard the changes or
  '--before=none' to ignore them.

In case you are sure the changes are irrelvant and intend to discard them,
use::

  $ scunch --before reset ...

This reverts all changes and removes files not under version control.

In case you prefer a clean check out, use::

  $ scunch --before checkout --depot http://example.com/ohsome/trunk ...

where ``http://example.com/ohsome/trunk`` represents the project's depot
qualifier. Note that a ``before=checkout`` usually takes longer than a
``--before=reset`` because a checkout needs to obtain all files again
where else a ``--before=checkout`` needs to obtain every file in the depot.

In case you are happy with the current pending changes and want to preserve
them even after punching the external changes, use::

  $ scunch --before none ...

The result might or might not be what you want, though.


Committing punched changes
--------------------------

To automatically commit the changes ``scunch`` just punched into your work
copy, use::

  $ scunch --after commit ...

To do the same with a meaningful log message, use::

  $ scunch --after commit --message "Punched version 1.3.8." ...

In case you use a script to launch ``scunch`` and want to get rid of the
work copy once it is done, you can specify multiple actions for ``--after``
separated by a comma::

  $ scunch --after "commit, purge" ...

The actions are performed in the given order so make sure to use ``purge``
last. Also notice the double quotes (") around ``"commit, purge"``. They
ensure that the shell does not consider ``purge`` a command line option of
its own.
 

Moving or renaming files
------------------------

By default, ``scunch`` checks for files added and removed with the same
name but located in a different folder. For example::

  Added  : source/tools/uitools.py
  Removed: source/uitools.py

With Subversion, ``scunch`` will internally run::

  $ svn move ... source/uitools.py source/tools

instead of::

  $ svn add ... source/tools/uitools.py
  $ svn remove ... source/uitools.py

The advantage of moving files instead of adding/removing them is that the
version history remains attached to the new file.

Note that this only works for files but not for folders. Furthermore, the
file names must be identical including upper/lower case and suffix.

If you rather want to add/remove files instead of moving them, you can
specify the move mode using the ``--move=MODE``::

  $ scunch --move=none /tmp/ohsome ~/projects/ohsome

Possible move modes are:

* ``name`` (the default): move files with identical names.
* ``none``: use add/remove instead if move.


Dealing with non ASCII file names
---------------------------------

To perform SCM operations, ``scunch`` simply runs the proper SCM command
line client as a shell process in the background. This typically works nice
and dandy as long as all files to be processed have names that solely
consist of ASCII characters. As soon as you have names in Kanji or with
Umlauts, trouble can ensue.

By default, ``scunch`` attempts to figure out proper settings for such a
situation by itself. However, this might fail and the result typically is a
``UnicodeEncodeError``.

The first sign of trouble is when ``scunch`` logs the following warning message:

  LC_CTYPE should be set to for example 'en_US;UTF-8' to allow processing of file names with non-ASCII characters

This indicates that the console encoding is set to ASCII and any non ASCII
characters in file names will result in a ``UnicodeEncodeError``. To fix
this, you can tell the console the file name encoding by setting the
environment variable ``LC_CTYPE``. For Mac OS X and most modern Linux
systems, the following command should do the trick::

  $ export LC_CTYPE=en_US;UTF-8

For Windows 7 you can use::

  > set LC_CTYPE=en_US;UTF-8

Note that this can have implications for other command line utilities, so
making this a permanent setting in ``.profile`` or ``.bashrc`` might not
be a good idea. Alternatively you can specify the proper encoding every
time you run ``scunch`` (upper/lower case does not matter here)::

  $ scunch --encoding=utf-8 /tmp/ohsome ~/projects/ohsome

For other platforms, you can try the values above. If they do not work as
intended, you need to dive into the documentation of your file system and
find out which encoding it uses.

But even if the encoding is correct, ``scunch`` and the file system still
might disagree on how to normalize Unicode characters. Again, ``scunch``
attempts to figure out the proper normalization but in case it is wrong
you can specify it using ``--normalize``.  Possible value are: ``auto``
(the default), ``nfc``, ``nfkc``, ``nfd`` and ``nfkd``. To understand the
meaning of these values, check the Unicode Consortium's `FAQ on normalization <http://unicode.org/faq/normalization.html>`_.

As a complete example, the proper options for Mac OS X with a HFS volume
are::

  $ scunch --encoding=utf-8 --normalize=nfd /tmp/ohsome ~/projects/ohsome

Incidentally, these are the values ``scunch`` would have used already, so
in practice there is not need to explicitly state them.

If however the files reside on a UDF volume, the proper settings would be::

  $ scunch --normalize=nfc /tmp/ohsome ~/projects/ohsome

In case the external files to punch into the work copy reside on a volume
with different settings than the work copy, or you cannot figure them out
at all, try to copy the files to a Volume with know settings and run
``scunch`` on this copy.

.. scenarios:

Scenarios
=========

This section describes common scenarios where ``scunch`` can be put to
good use.

Upgrading from old school version management
--------------------------------------------

Tim is a hobbyist developer who has been programming a nifty utility
program for a while called "nifti". Until recently he has not been using
any version management. If he deemed it useful to keep a certain state of
the source code, he just copied it to a new folder and added a timestamp to
the folder name::

  $ cd ~/projects
  $ ls
  nifti
  nifti_2010-11-27
  nifti_2010-09-18
  nifti_2010-07-03
  nifti_2010-05-23

After having been enlightened, he decides to move the project to a
Subversion repository. Nevertheless he would like to have all his snapshots
available.

As a first step, Tim creates a local Subversion repository::

  $ mkdir /Users/tim/repositories
  $ svnadmin create /Users/tim/repositories/nifti

Next he adds the project folders using the ``file`` protocol::

  $ svn mkdir file:///Users/tim/repositories/nifti/trunk  file:///Users/tim/repositories/nifti/tags  file:///Users/tim/repositories/nifti/branches

No he can check out the ``trunk`` to a temporary folder::

  $ cd /tmp
  $ svn checkout --username tim file:///Users/tim/repositories/nifti/trunk nifti

Now it is time to punch the oldest version into the still empty work copy::

  $ cd /tmp/nifti
  $ scunch ~/projects/nifti_2010-05-23

Tim reviews the changes to be committed. Unsurprisingly, there are only
"add" operations::

  $ svn status
  A   setup.py
  A   README.txt
  A   nifti/
  ...

To commit this, Tim runs::

  $ svn commit --message "Added initial version."

Then he proceeds with the other versions, where he lets ``scunch`` handle
the commit all by itself::

  $ scunch --commit ~/projects/nifti_2010-07-03
  $ scunch --commit ~/projects/nifti_2010-08-18
  $ scunch --commit ~/projects/nifti_2010-11-27
  $ scunch --commit ~/projects/nifti

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

  $ svn propset svn:date --revprop --revision 2 "2010-05-23 12:00:00Z" file:///Users/tim/repositories/nifti/trunk

Note that this only works with the ``file`` protocol. If you want to do the
same on a repository using the ``http`` protocol, you have to install a
proper post commit hook in the repository that allows you to change
properties even after they have been committed. Refer to the Subversion
manual for details on how to do that.

Similarly, Tim can set the log comments to a more meaningful text using the
revision property ``log``.

Once the repository is in shape, Tim can remove his current source code and
replace it with the work copy::

  $ cd ~/projects
  $ mv nifti nifti_backup # Do not delete just yet in case something went wrong.
  $ svn checkout file:///Users/tim/repositories/nifti/trunk nifti

Now Tim has a version controlled project where he can commit changes any
time he wants.


Version management of third party source code
---------------------------------------------

Joe works in an IT department. One of his responsibilities to install
updates for a web application named "ohsome" developed and delivered by a
third party. The work flow for this is well defined:

1. Vendor send the updated source code to Joe in a ZIP archive containing a
   mix of HTML, JavaScript and XML files, mixed in with a few server
   configuration files.

2. Joe extracts the ZIP archive to a local folder.

3. Joe moves the contents of local folder to the application folder on the
   server. In the process, he removes all previous files for the application.

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

  $ svn add --message "Added project folders for ohsome application by Vendor." http://svn.example.com/ohsome http://svn.example.com/ohsome/trunk http://svn.example.com/ohsome/tags http://svn.example.com/ohsome/branches

This creates a project folder and the usual trunk, tags and branches
folders. For the time being, Joe intends to use only the trunk to hold the
most current version of the "ohsome" application.

Next, Joe creates a yet empty work copy in a local folder on his computer::

  $ cd ~/projects
  $ svn checkout http://svn.example.com/ohsome/trunk ohsome

Now he copies all the files from the web server to the work copy::

  $ cp -r /web/ohsome/* ~/projects/ohsome

Although the files are now in the work copy, the are not yet under version
management. So Joe adds almost all the files except one folder named "temp" that
according to his knowledge contains only temporary files generated by the
web application::

  $ cd ~/projects/ohsome
  $ svn propset svn:ignore temp .
  $ svn add ...

After that, he manually commits the current state of the web server::

  $ svn commit --message "Added initial application version 1.3.7."

For the time being, Joe is done.

A couple of weeks later, the vendor send a ZIP archive with the application
version 1.3.8. As usual, Joe extracts the archive::

  $ cd /tmp
  $ unzip ~/Downloads/ohsome_1.3.8.zip

The result of this is a folder /tmp/ohsome containing all the files and
folders to be copied to the web server under /web/ohsome/. However, this
time Joe wants to review the changes first by "punching" them into his
work copy. So he runs ``scunch`` with the following options::

  $ scunch /tmp/ohsome ~/projects/ohsome

This "punches" all the changes from folder /tmp/ohsome (where the ZIP
archive got extracted) to the work copy in ~/projects/ohsome.

As a result Joe can review the changes. He uses TortoiseSVN for that, but
``svn status`` and ``svn diff`` would have worked too.

Once he finished his review without noticing any obvious issues, he
manually commits the changes::

  $ cd ~/projects/ohsome
  $ svn commit --message "Punched version 1.3.8."

When version 1.3.9 ships, Joe decides that he might as well review the
changes directly in the repository after the commit. So this time he simply
uses::

  $ cd /tmp
  $ unzip ~/Downloads/ohsome_1.3.9.zip
  $ scunch --commit --message "Punched version 1.3.9."

Joe can then use ``svn log`` to look for particular points of interest.
For instance, to find modified configuration files (matching the pattern \*.cfg)::

  $ svn log --verbose --limit 1 http://svn.example.com/ohsome/trunk | grep "\\.cfg$"

To get a list of Removed files and folders::

  $ svn log --verbose --limit 1 http://svn.example.com/ohsome/trunk | grep "^   D"

(Note: Here, ``grep`` looks for three blanks and a "D" for "deleted" at the beginning of a line.)


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


License
=======

Copyright (C) 2011 Thomas Aglassinger

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Version history
===============

**Version 0.5.1, 2011-02-xx**

* #10: Added command line option ``--before`` to specify action to be taken
  before punching.
* Added check that no changes are pending before copying files from the
  external folder. Use ``--before=none`` to skip this.
* #11: Added command line option ``--after`` to specify actions to be taken
  after punching.
* Removed command line option ``--commit``, use ``--after=commit``
  instead.

**Version 0.5.0, 2011-02-12**

* #12: Added options ``--include`` and ``--exclude`` to specify which
  files in the external folder should be punched. These options take a
  list of ant patterns separated by a comma (,) or blank space.
* #13: Added option ``--work-only`` to specify files and folders that
  only exist in the work copy but not in the external folder but should be
  preserved nevertheless. This is useful if the work copy contains helper
  scripts, ``build.xml`` for ant, Makefiles and so on that call scunch or
  other tools but will never be part of the external folder.
* Changed ``--text`` to use ant-like pattern instead of a suffix list. For
  example now use ``--text="**/*.txt" instead of ``text=txt``.

**Version 0.4.1, 2011-01-09**

* Fixed ``AssertionError`` if no explicit ``--encoding`` was specified.
* Cleaned up command line help and code.

**Version 0.4, 2011-01-08**

Added options to normalize text files and fixed some critical bugs.

* #4: Added command line option ``--text`` to specify which files should be
  considered text and normalized concerning end of line characters.
* #5: Added command line option ``--newline`` to specify which end of line
  characters should be used for text files.
* #6: Added command line option ``--tabsize`` to specify that tabs should
  be aligned on a certain number of spaces in text files.
* #7: Added command line option ``--strip-trailing`` to remove trailing
  white space in text files.
* Fixed sorting of file names which could result into inconsistent work
  copies.
* Fixed processing of internal file name diff sequences of type 'replace',
  which could result in inconsistent work copies.

**Version 0.3, 2011-01-05**

* Fixed processing of file names with non ASCII characters for Mac OS X
  and possibly other platforms.
* Added command lines options ``--encoding`` and ``--normalize`` to
  specify how to deal with non ASCII characters.

**Version 0.2, 2011-01-04**

* Fixed ``NotImplementedError``.
* Added support for moving files with same name instead of performing a
  simple add/remove. This preserves the version history on the new file.
  Use ``--move=none`` to get the old behavior.
* Cleaned up logging output.

**Version 0.1, 2011-01-03**

* Initial release.
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
import codecs
import difflib
import locale
import logging
import optparse
import os.path
import platform
import shutil
import subprocess
import sys
import tempfile
import types
import unicodedata
import urlparse
import xml.sax
from xml.sax.handler import ContentHandler

import antglob
import _tools

__version_info__ = (0, 5, 1)
__version__ = '.'.join(unicode(item) for item in __version_info__)

_log = logging.getLogger("scunch")

_consoleEncoding = None
_consoleNormalization = None

class _Actions(object):
    """
    Pseudo class to collect possible actions for ``--before`` and ``--after``.
    """
    Checkout = 'checkout'
    Check = 'check'
    Commit = 'commit'
    None_ = 'none'
    Purge = 'purge'
    Update = 'update'
    Reset = 'reset'
    
_ValidAfterActions = set([_Actions.Commit, _Actions.None_, _Actions.Purge])
_ValidBeforeActions = set([_Actions.Check, _Actions.Checkout, _Actions.None_, _Actions.Reset, _Actions.Update])
_ValidConsoleNormalizations = set(['auto', 'nfc', 'nfkc', 'nfd', 'nfkd'])

def _setUpLogging(level=logging.INFO):
    """
    Set up logging with ``level`` being the initial minimum logging level.
    """
    assert level is not None
    logging.basicConfig(level=level)

def _setUpEncoding(consoleEncoding='auto', consoleNormalization='auto'):
    """
    * consoleEncoding - the encoding used by shell commands when writing to ``stdout``.

    * consoleNormalization - Unicode normalization for console output which in turn decides the
      normalization of file names. For Mac OS X HFS, this is "NFD". See Technical Q&A QA1173,
      "Text Encodings in VFS", available from
      <http://developer.apple.com/library/mac/#qa/qa2001/qa1173.html>.
    """
    assert consoleEncoding is not None
    assert consoleNormalization in _ValidConsoleNormalizations, "consoleNormalization=%r" % consoleNormalization

    # TODO: #9: Redesign console encoding to get rid of ugly globals.
    global _consoleEncoding
    global _consoleNormalization

    if consoleEncoding == 'auto':
        _consoleEncoding = locale.getpreferredencoding()
    else:
        _consoleEncoding = consoleEncoding
    if consoleNormalization == 'auto':
        if platform.system() == 'Darwin':
            # HACK: Assume NFD, which wil be fine for HFS. However, UDF and SMB would expect NFC.
            # Furthermore, NFS is utterly undeterministic.
            _consoleNormalization = 'nfd'
        else:
            # TODO: Try this with Windows and Linux.
            _consoleNormalization = 'nfc'
    _consoleNormalization = _consoleNormalization.upper()

    if _consoleEncoding.lower() in ("ascii", "us-ascii"):
        _log.warning("LC_CTYPE should be set to for example 'en_US;UTF-8' to allow processing of file names with non-ASCII characters")
    sys.stdout = codecs.getwriter(_consoleEncoding)(sys.stdout)
    sys.stdin = codecs.getreader(_consoleEncoding)(sys.stdin)

def _humanReadableCommand(commandAndOptions):
    result = ""
    isFirstItem = True
    for commandItem in commandAndOptions:
        if (" " in commandItem) or not commandItem:
            commandItem = '"%s"' % commandItem
        if isFirstItem:
            isFirstItem = False
        else:
            result += " "
        result += commandItem
    return result

def run(commandAndOptions, returnStdout=False, cwd=None):
    assert _consoleEncoding is not None
    assert _consoleNormalization is not None
    assert commandAndOptions
    result = None
    encoding = _consoleEncoding
    normalizedCommandAndOptions = []
    for commandItem in commandAndOptions:
        if isinstance(commandItem, types.UnicodeType):
            commandItem = unicodedata.normalize(_consoleNormalization, commandItem)
        normalizedCommandAndOptions.append(commandItem)
    commandName = normalizedCommandAndOptions[0]
    commandText = _humanReadableCommand(normalizedCommandAndOptions)
    _log.debug(u"run: %s", commandText)
    stderrFd, stderrPath = tempfile.mkstemp(prefix="scunch_stderr_")
    try:
        os.close(stderrFd)
        with codecs.open(stderrPath, "w+b", encoding) as stderrLines:
            if returnStdout:
                stdoutFd, stdoutPath = tempfile.mkstemp(prefix="scunch_stdout_")
                os.close(stdoutFd)
                stdoutFile = codecs.open(stdoutPath, "w+b", encoding)
            else:
                # No need to set encoding "w+b" here because nothing can be read or written.
                stdoutFile = open(os.devnull, "wb")
            try:
                exitCode = subprocess.call(normalizedCommandAndOptions, stdout=stdoutFile, stderr=stderrLines, cwd=cwd)
                if exitCode != 0:
                    stderrLines.seek(0)
                    errorMessage = stderrLines.readline().rstrip("\n\r")
                    if errorMessage:
                        if errorMessage[-1] not in ".!?":
                            errorMessage += "."
                        errorMessage = " Error: " + errorMessage
                    else:
                        errorMessage = "."
                    raise ScmError(u"cannot perform shell command %r.%s Command:  %s" %(commandName, errorMessage, commandText))
            except OSError, error:
                raise ScmError(u"cannot perform shell command %r: %s. Command:  %s" %(commandName, error, commandText))
            finally:
                if returnStdout:
                    result = []
                    stdoutFile.seek(0)
                    for line in stdoutFile:
                        line = line.rstrip('\n\r')
                        line = unicodedata.normalize(_consoleNormalization, line)
                        result.append(line)
                stdoutFile.close()
    finally:
        os.remove(stderrPath)
    return result

class ScmError(Exception):
    """
    Error related to performing an SCM operation.
    """
    pass

class ScmPendingChangesError(Exception):
    """
    Error indicating that an SCM operation could not be performed due to
    pending. To solve this, either commit or discard the changes and try
    again.
    """
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
    _None = "none"
    Normal = "normal"
    Obstructed = "obstructed"
    Removed = "deleted"
    Replaced = "replaced"
    Unversioned = "unversioned"

    _CleanStati = set([External, Ignored, None, Normal])
    _ModifiedStati = set([Added, Merged, Modified, Removed])
    _CommitableStati = _CleanStati | _ModifiedStati
    _StatiNotToReset = set([Ignored, None, Normal])

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
        # Note: status 'none' is not mapped to `None` directly because this
        # would prevent us from detecting unknown stati (which return `None`
        # when looked up.
        #
        # Nevertheless, `ScmStatus` uses `None` to represent a 'none' status
        "none": _None,
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

    def isResetable(self):
        """
        ``True`` if the status indicates that the path should be removed by
        `ScmWork.reset()`.
        """
        resetBacauseOfEntryStatus = self.status not in ScmStatus._StatiNotToReset
        resetBecauseOfPropertiesStatus = self.propertiesStatus not in ScmStatus._StatiNotToReset
        return resetBacauseOfEntryStatus or resetBecauseOfPropertiesStatus

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
        if result == ScmStatus._None:
            result = None
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
        self.checkAbsoluteQualifier("base baseQualifier", baseQualifier)
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

    def checkAbsoluteQualifier(self, name, qualifierToCheck):
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
        self.checkAbsoluteQualifier("internal qualifier", result)
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

def _sortedFileSystemEntries(folderItemsToSort):
    def comparedFileSystemEntries(some, other):
        assert some is not None
        assert other is not None

        # Sort folders before files, hence '-'.
        typeComparison = -cmp(some.kind, other.kind)
        if typeComparison:
            result = typeComparison
        else:
            result = cmp(some.parts, other.parts)
        return result

    assert folderItemsToSort is not None
    result = []
    for item in folderItemsToSort:
        result.append(item)
    result = sorted(result, comparedFileSystemEntries)
    return result

class TextOptions(object):
    """
    Options describing how to convert punched text files.
    """

    # Special tab size indicating that tabs should be preserved.
    PreserveTabs = 0

    # Possible values for property ``newLine``..
    Dos = '\r\n'
    Native = os.linesep
    Unix = '\n'

    _ValidNewLines = set((Dos, Native, Unix))

    def __init__(self, antPatternText=None, newLine=Native, tabSize=PreserveTabs, stripTrailing=False):
        assert newLine in TextOptions._ValidNewLines
        assert tabSize is not None
        assert tabSize >= TextOptions.PreserveTabs

        self._trailingCharactersToStrip = '\n\r'
        if stripTrailing:
                self._trailingCharactersToStrip += "\t "
        self.newLine = newLine
        assert self.newLine
        self.tabSize = tabSize
        if antPatternText:
            self.textPatternSet = antglob.AntPatternSet()
            self.textPatternSet.include(antPatternText)
        else:
            self.textPatternSet = None

    def isText(self, folderItemToCheck):
        """
        ``True`` if ``folderItemToCheck`` indicates a text file according to the suffixes specified in the constructor.
        """
        # Note: We do not even accept an empty ``folderItemsToCheck`` because this must only be called for
        # file names always have at least 1 character, and not folders (which can be empty
        # when referring to the current working folder).
        assert folderItemToCheck

        if self.textPatternSet:
            result = self.textPatternSet.matchesParts(folderItemToCheck.parts)
        else:
            result = False
        return result

    def convertedLine(self, line):
        """
        Similar to ``line`` but with the conversion decribed by this `TextOptions` applied.
        """
        assert line is not None

        result = line.rstrip(self._trailingCharactersToStrip)
        if self.tabSize:
            result = result.expandtabs(self.tabSize)
        result += self.newLine
        return result

    def __unicode__(self):
        return u"<TextOptions: newLine=%r, charactersToStrip=%r, tabSize=%d, texts=%s>" % (self.newLine, self._trailingCharactersToStrip, self.tabSize, self.textPatternSet)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return self.__str__()


class ScmPuncher(object):
    """
    Puncher to update a work copy according from a folder performing the following changes on the
    work copy:

    * Add files that do not exist in the work copy but the folder.
    * Remove files that exist in the work copy but not the folder.
    * Copy other files that exist in both from the folder to the work copy.
    """
    MoveName = "name"
    MoveNone = "none"
    _ValidMoveModes = set((MoveName, MoveNone))

    def __init__(self, scmWork):
        assert scmWork is not None
        self.scmWork = scmWork
        self._clear()

    def _clear(self):
        self.externalItems = None
        self.workItems = None
        self._externalFolderPath = None
        self._addedItems = None
        self._copiedItems = None
        self._transferedItems = None
        self._movedItems = None
        self._removedItems = None
        self._filesToPunchPatternSet = None
        self._workFilesToPreservePatternSet = None

    def _isInLastRemovedFolder(self, itemToCheck):
        result = False
        if self._removedItems:
            lastRemovedItem = self._removedItems[-1]
            if lastRemovedItem.kind == antglob.FileSystemEntry.Folder:
                if lastRemovedItem.parts == itemToCheck.parts[:len(lastRemovedItem.parts)]:
                    result = True
        return result

    def _workPathFor(self, folderItem):
        assert folderItem is not None
        return folderItem.absolutePath(self.scmWork.localTargetPath)

    def _externalPathFor(self, folderItem):
        assert folderItem is not None
        assert self._externalFolderPath is not None
        return folderItem.absolutePath(self._externalFolderPath)

    def _assertScheduledItemIsUnique(self, itemToSchedule, operation):
        """
        Assert that a folder item ``itemToSchedule` scheduled for ``operation`` has not been
        scheduled for any other operation so far.
        """
        assert itemToSchedule is not None
        assert operation in ('add', 'copy', 'move', 'remove', 'transfer')
        # TODO: Change self._*Items from list to set for faster lookup.
        assert (self._addedItems is None) or (itemToSchedule not in self._addedItems, "item scheduled to %s has already been added: %s" % (operation, itemToSchedule))
        assert (self._copiedItems is None) or (itemToSchedule not in self._copiedItems, "item scheduled to %s has already been copied: %s" % (operation, itemToSchedule))
        assert (self._transferedItems is None) or (itemToSchedule not in self._transferedItems, "item scheduled to %s has already been transferred: %s" % (operation, itemToSchedule))
        assert (self._movedItems is None) or (itemToSchedule not in self._movedItems, "item scheduled to %s has already been moved: %s" % (operation, itemToSchedule))
        assert (self._removedItems is None) or (itemToSchedule not in self._removedItems, "item scheduled to %s has already been removed: %s" % (operation, itemToSchedule))

    def _add(self, items):
        for itemToAdd in items:
            if not self._isInLastRemovedFolder(itemToAdd):
                _log.debug('schedule item for add: "%s"', itemToAdd.relativePath)
                self._assertScheduledItemIsUnique(itemToAdd, 'add')
                self._addedItems.append(itemToAdd)
            else:
                _log.debug('skip added item in removed folder: "%s"', itemToAdd.relativePath)

    def _remove(self, items):
        for itemToRemove in items:
            if not self._isInLastRemovedFolder(itemToRemove):
                _log.debug('schedule item for remove: "%s"', itemToRemove.relativePath)
                self._assertScheduledItemIsUnique(itemToRemove, 'remove')
                self._removedItems.append(itemToRemove)
            else:
                _log.debug('skip removed item in removed folder: "%s"', itemToRemove.relativePath)

    def _transfer(self, items):
        for itemToTransfer in items:
            if not self._isInLastRemovedFolder(itemToTransfer):
                # TODO: Add option to consider items modified by only checking their date.
                _log.debug('schedule item for transfer: "%s"', itemToTransfer.relativePath)
                self._assertScheduledItemIsUnique(itemToTransfer, 'transfer')
                self._transferedItems.append(itemToTransfer)
            else:
                _log.debug('skip transferable item in removed folder: "%s"', itemToTransfer.relativePath)

    def _copyTextFile(self, sourceFilePath, targetFilePath, textOptions):
        assert textOptions is not None
        with open(sourceFilePath, "rb") as sourceFile:
            with open(targetFilePath, "wb") as targetFile:
                for line in sourceFile:
                    lineToWrite = textOptions.convertedLine(line)
                    targetFile.write(lineToWrite)
        # TODO: Copy attributes similar to `shutil.copy2()`.

    def _transferItemFromExternalToWork(self, itemToTransfer, textOptions):
        assert itemToTransfer is not None
        externalPathOfItemToTransferFrom = self._externalPathFor(itemToTransfer)
        workPathOfItemToTransferTo = self._workPathFor(itemToTransfer)
        if textOptions and textOptions.isText(itemToTransfer):
            self._copyTextFile(externalPathOfItemToTransferFrom, workPathOfItemToTransferTo, textOptions)
        else:
            shutil.copy2(externalPathOfItemToTransferFrom, workPathOfItemToTransferTo)

    def _setExternalAndWorkItems(self, externalFolderPath, relativeWorkFolderPath, includePatternText, excludePatternText, workOnlyPatternText):
        assert externalFolderPath is not None
        assert relativeWorkFolderPath is not None

        self._externalFolderPath = externalFolderPath
        # Compute file name patterns.
        filesToPunchPatternSet = antglob.AntPatternSet()
        if includePatternText:
            filesToPunchPatternSet.include(includePatternText)
        if excludePatternText:
            filesToPunchPatternSet.exclude(excludePatternText)

        # Collect external items.
        self.externalItems = filesToPunchPatternSet.findEntries(externalFolderPath)
        self.externalItems = _sortedFileSystemEntries(self.externalItems)
        _log.info('found %d external items in "%s"', len(self.externalItems), self._externalFolderPath)

        # Check that external items do not contain any work only items.
        if workOnlyPatternText:
            workFilesToPreservePatternSet = antglob.AntPatternSet(False)
            workFilesToPreservePatternSet.include(workOnlyPatternText)
        for item in self.externalItems:
            _log.debug('  %s', item)
            if workOnlyPatternText and workFilesToPreservePatternSet.matchesParts(item.parts):
                raise ScmError('entry in folder to punch must exist only in work copy: "%s"' % item.relativePath)

        # Collect items in work copy.
        if workOnlyPatternText:
            filesToPunchPatternSet.exclude(workOnlyPatternText)
        self.workItems = self.scmWork.listFolderItems(relativeWorkFolderPath, filesToPunchPatternSet)
        self.workItems = _sortedFileSystemEntries(self.workItems)
        _log.info('found %d work items in "%s"', len(self.workItems), self.scmWork.absolutePath("work path", relativeWorkFolderPath))
        for item in self.workItems:
            _log.debug('  %s', item)

    def _setAddedModifiedRemovedItems(self):
        assert self._externalFolderPath is not None
        assert self.workItems is not None
        assert self.externalItems is not None

        matcher = difflib.SequenceMatcher(None, self.workItems, self.externalItems)
        _log.debug("matcher: %s", matcher.get_opcodes())
        self._addedItems = []
        self._transferedItems = []
        self._removedItems = []

        for operation, i1, i2, j1, j2 in matcher.get_opcodes():
            _log.debug("%s: %d, %d; %d, %d", operation, i1, i2, j1, j2)
            if operation == 'insert':
                self._add(self.externalItems[j1:j2])
            elif operation == 'equal':
                self._transfer(self.externalItems[j1:j2])
            elif operation == 'delete':
                self._remove(self.workItems[i1:i2])
            elif operation == 'replace':
                externalItemsToReplace = self.externalItems[j1:j2]
                _log.debug("  external to replace: %s", externalItemsToReplace)
                workItemsToReplace = self.workItems[i1:i2]
                _log.debug("  work to replace: %s", workItemsToReplace)
                allItems = set(self.workItems[i1:i2]) | set(self.externalItems[j1:j2])
                for replaceditem in allItems:
                    replacedWorkItems = set(self.workItems[i1:i2])
                    replacedExternalItems = set(self.externalItems[j1:j2])
                    if replaceditem in replacedExternalItems:
                        if replaceditem in replacedWorkItems:
                            self._transfer([replaceditem])
                        else:
                            self._add([replaceditem])
                    else:
                        assert replaceditem in replacedWorkItems, "item must be at least in external or work items: %s" % replaceditem
                        self._remove([replaceditem])
            else:
                assert False, "operation=%r" % operation

    def _createNameAndKindToListOfFolderItemsMap(self, items):
        result = {}
        for item in items:
            itemName = item.name
            itemKind = item.kind
            itemKey = (itemName, itemKind)
            existingItems = result.get(itemKey)
            if existingItems is None:
                result[itemKey] = [item]
            else:
                existingItems.append(item)
        return result

    def _setCopiedAndMovedItems(self):
        assert self._externalFolderPath is not None
        assert self.workItems is not None
        assert self.externalItems is not None

        self._copiedItems = []
        self._movedItems = []
        removedNameMap = self._createNameAndKindToListOfFolderItemsMap(self._removedItems)
        addedNameMap = self._createNameAndKindToListOfFolderItemsMap(self._addedItems)

        for possiblyMovedItemKey, possiblyMovedItems in addedNameMap.items():
            possiblyMovedItemKind = possiblyMovedItemKey[1]
            correspondingRemovedItems = removedNameMap.get(possiblyMovedItemKey)
            if correspondingRemovedItems:
                # TODO: Process all moved items of the same name as long as there is both an added and removed item.
                if possiblyMovedItemKind == antglob.FileSystemEntry.File:
                        sourceItem = correspondingRemovedItems[0]
                        targetItem = possiblyMovedItems[0]
                        _log.debug('schedule for move: "%s" to "%s"', sourceItem.relativePath, targetItem.relativePath)
                        self._removedItems.remove(sourceItem)
                        self._addedItems.remove(targetItem)
                        self._movedItems.append((sourceItem, targetItem))
                else:
                    # TODO: Move folders in case the new folder contains all the item from the old folder (and possibly some more).
                    pass

    def _applyChangedItems(self, textOptions):
        _log.info("punch modifications into work copy")
        if self._removedItems:
            _log.info("remove %d items", len(self._removedItems))
            relativePathsToRemove = []
            for itemToRemove in self._removedItems:
                relativePathToRemove = itemToRemove.relativePath
                _log.info('  remove "%s"', relativePathToRemove)
                relativePathsToRemove.append(relativePathToRemove)
            # Remove folder and files  using a single command call.
            self.scmWork.remove(relativePathsToRemove, recursive=True, force=True)
        if self._transferedItems:
            _log.info("transfer %d items", len(self._transferedItems))
            for itemToTransfer in self._transferedItems:
                if itemToTransfer.kind == antglob.FileSystemEntry.Folder:
                    _tools.makeFolder(self._workPathFor(itemToTransfer))
                else:
                    _log.info('  transfer "%s"', itemToTransfer.relativePath)
                    self._transferItemFromExternalToWork(itemToTransfer, textOptions)
        if self._addedItems:
            _log.info("add %d items", len(self._addedItems))
            relativePathsToAdd = []
            # Create added folders and copy added files.
            for itemToAdd in self._addedItems:
                relativePathToAdd = itemToAdd.relativePath
                _log.info('  add "%s"', relativePathToAdd)
                relativePathsToAdd.append(relativePathToAdd)
                if itemToAdd.kind == antglob.FileSystemEntry.Folder:
                    _tools.makeFolder(self._workPathFor(itemToAdd))
                else:
                    self._transferItemFromExternalToWork(itemToAdd, textOptions)
            # Add folders and files to SCM using a single command call.
            self.scmWork.add(relativePathsToAdd, recursive=False)
        if self._movedItems:
            _log.info("move %d items", len(self._movedItems))
            for sourceItemToMove, targetItemToMove in self._movedItems:
                sourcePath = sourceItemToMove.relativePath
                targetPath = os.path.dirname(targetItemToMove.relativePath)
                _log.info('  move "%s" from "%s" to "%s"', os.path.basename(sourcePath), os.path.dirname(sourcePath), targetPath)
                self.scmWork.move(sourcePath, targetPath, force=True)
                self._transferItemFromExternalToWork(targetItemToMove, textOptions)

    def punch(self, externalFolderPath, relativeWorkFolderPath="", textOptions=None, move=MoveName, includePatternText=None, excludePatternText=None, workOnlyPatternText=None):
        assert externalFolderPath is not None
        assert relativeWorkFolderPath is not None
        try:
            self._setExternalAndWorkItems(externalFolderPath, relativeWorkFolderPath, includePatternText, excludePatternText, workOnlyPatternText)
            self._setAddedModifiedRemovedItems()
            if move != ScmPuncher.MoveNone:
                self._setCopiedAndMovedItems()
            self._applyChangedItems(textOptions)
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
            raise ScmError("check out action is %r but must be one of: %s", _tools.humanReadableList(sorted(ScmWork._ValidCheckOutActions)))
        self.storage = storage
        self.relativeQualifierInStorage = relativeQualifierInStorage
        self.baseWorkQualifier = self.storage.absoluteQualifier(self.relativeQualifierInStorage)
        self.localTargetPath = localTargetPath

        hasExistingWork = os.path.exists(self.localTargetPath)
        if hasExistingWork and (checkOutAction == ScmWork.CheckOutActionReset):
            self.purge()

        if checkOutAction in (ScmWork.CheckOutActionCreate, ScmWork.CheckOutActionReset):
            self.checkout()
        elif checkOutAction == ScmWork.CheckOutActionUpdate:
            self.update()
        else:
            assert checkOutAction == ScmWork.CheckOutActionSkip, 'checkOutAction=%r' % checkOutAction
        self.specialPathPatternSet = antglob.AntPatternSet(False)
        self.specialPathPatternSet.include("**/.svn, **/_svn")

    def check(self,relativePath=u""):
        """
        Check that work copy is up to date and no pending changes or messed
        up files are flowing around; otherwise, raise an `ScmError`. To remedy
        the conditons `check()` complains about, use `reset()`.
        """
        assert relativePath is not None
        for statusEntry in self.status(relativePath):
            if statusEntry.isResetable():
                raise ScmPendingChangesError("pending changes in \"%s\" must be committed, use \"svn status\" for details." % self.localTargetPath)

    def checkout(self, purge=False):
        """
        Check out a work copy to ``localTargetPath``.
        """
        _log.info("check out work copy at \"%s\"", self.localTargetPath)
        if purge and os.path.exists(self.localTargetPath):
            self.purge()
        scmCommand = ["svn", "checkout", self.baseWorkQualifier, self.localTargetPath]
        run(scmCommand)

    def purge(self):
        """
        Remove work copy folder and all its contents. If the folder does not exist, do nothing.
        """
        _log.info("purge work copy at \"%s\"", self.localTargetPath)
        _tools.removeFolder(self.localTargetPath)

    def reset(self):
        """
        Reset the work copy to its baseline. This cleans up any locks, reverts
        changes and removes any files not under version control.
        """
        _log.info("reset work copy at \"%s\"", self.localTargetPath)
        _log.debug("  clean up pending locks")
        scmCommand = ["svn", "cleanup", "--non-interactive", self.localTargetPath]
        run(scmCommand)
        _log.debug("  revert uncommited changes")
        scmCommand = ["svn", "revert", "--recursive", "--non-interactive", self.localTargetPath]
        run(scmCommand)
        _log.debug("  remove unversioned files and folders")
        folderPathsToRemove = []
        for statusItem in self.status(""):
            pathToRemove = statusItem.path
            if statusItem.isResetable():
                if os.path.isfile(pathToRemove):
                    _log.debug("    remove file \"%s\"", pathToRemove)
                    os.remove(pathToRemove)
                elif os.path.isdir(pathToRemove):
                    folderPathsToRemove.append(pathToRemove)
                else:
                    raise ScmError(u"path to reset must be either a file or directory: \"%s\"" % pathToRemove)
        for folderPathToRemove in folderPathsToRemove:
            _log.debug("    remove folder \"%s\"", folderPathToRemove)
            # TODO: shutil.rmtree(folderPathToRemove)

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
        _log.debug(u"add: %r", relativePathsToAdd)
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
        _log.debug("mkdir: %s", relativeFolderPathToCreate)
        absoluteFolderPathToCreate = self.absolutePath("folder to create", relativeFolderPathToCreate)
        svnMkdirCommand = ["svn", "mkdir", "--non-interactive", absoluteFolderPathToCreate]
        run(svnMkdirCommand, cwd=self.localTargetPath)

    def move(self, relativeSourcePaths, relativeTargetPath, force=False):
        _log.debug('move: %s to "%s"', str(relativeSourcePaths), relativeTargetPath)
        assert relativeSourcePaths is not None
        assert relativeTargetPath is not None
        svnAddCommand = ["svn", "move", "--non-interactive"]
        if force:
            svnAddCommand.append("--force")
        if isinstance(relativeSourcePaths, types.StringTypes):
            svnAddCommand.append(relativeSourcePaths)
        else:
            svnAddCommand.extend(relativeSourcePaths)
        svnAddCommand.append(relativeTargetPath)
        run(svnAddCommand, cwd=self.localTargetPath)

    def remove(self, relativePathsToRemove, recursive=True, force=False):
        _log.debug("remove: %s", str(relativePathsToRemove))
        assert relativePathsToRemove is not None
        svnRemoveCommand = ["svn", "remove", "--non-interactive"]
        if force:
            svnRemoveCommand.append("--force")
        if not recursive:
            svnRemoveCommand.append("--non-recursive")
        if isinstance(relativePathsToRemove, types.StringTypes):
            svnRemoveCommand.append(relativePathsToRemove)
        else:
            svnRemoveCommand.extend(relativePathsToRemove)
        run(svnRemoveCommand, cwd=self.localTargetPath)

    def commit(self, relativePathsToCommit, message, recursive=True):
        assert relativePathsToCommit is not None
        assert message is not None
        _log.debug("commit: %s", str(relativePathsToCommit))
        svnCommitCommand = ["svn", "commit", "--non-interactive"]
        if not recursive:
            svnCommitCommand.append("--non-recursive")
        svnCommitCommand.extend(["--message", message])
        svnCommitCommand.extend(self.absolutePaths("paths to commit", relativePathsToCommit))
        run(svnCommitCommand, cwd=self.localTargetPath)

    def isSpecialPath(self, path):
        name = os.path.basename(path)
        return self.specialPathPatternSet.matches(name)

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

    def listFolderItems(self, relativeFolderToList="", patternSetToMatch=None):
        """
        List of folder items starting with ``relativeFolderPathToList`` excluding special items
        used internally by the SCM (such as for example ".svn" for Subversion).
        """
        if patternSetToMatch:
            actualPatternSetToMatch = patternSetToMatch
        else:
            actualPatternSetToMatch = antglob.AntPatternSet()
        folderPathToList = self.absolutePath("folder to list", relativeFolderToList)
        for entry in actualPatternSetToMatch.ifindEntries(folderPathToList):
            yield entry

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
            _tools.removeFolder(targetFolderPath)
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

def scunch(sourceFolderPath, scmWork, textOptions=None, move=ScmPuncher.MoveName, includePatternText=None, excludePatternText=None, workOnlyPatternText=None):
    assert sourceFolderPath is not None
    puncher = ScmPuncher(scmWork)
    puncher.punch(sourceFolderPath, "", textOptions, move=move, includePatternText=includePatternText, excludePatternText=excludePatternText, workOnlyPatternText=workOnlyPatternText)

_NameToLogLevelMap = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR
}

_NameToNewLineMap = {
    'native': os.linesep,
    'dos': TextOptions.Dos,
    'unix': '\n',
    'crlf': '\r\n',
    'lf': '\n'
}

def _createTextOptions(commandLineOptions):
    assert commandLineOptions is not None
    assert commandLineOptions.tabSize is not None
    assert commandLineOptions.tabSize >= 0
    assert commandLineOptions.newLine in _NameToNewLineMap.keys(), 'newLine=%r' % commandLineOptions.newLine

    result = TextOptions(
        commandLineOptions.textPatternSet,
        _NameToNewLineMap[commandLineOptions.newLine],
        commandLineOptions.tabSize,
        commandLineOptions.isStripTrailing
    )
    return result

_Usage = "%prog [options] FOLDER [WORK-FOLDER]"
_Description = "Update svn work copy from folder applying add and remove."

def _parsedActions(optionsParser, actionName, actionsText, validActions):
    assert optionsParser
    assert actionsText is not None
    assert validActions
    result = []
    actionsFoundSoFar = set()
    for action in actionsText.split(','):
        action = action.strip()
        if action in actionsFoundSoFar:
            optionsParser.error("option %s must contain action %r only once but is: %s" % (actionName, action, actionsText))
        actionsFoundSoFar.update([action])
        if action not in validActions:
            optionsParser.error("%s action %r must be changed to %s" % (actionName, action, _tools.humanReadableList(validActions)))
        result.append(action)
    return result

def parsedOptions(arguments):
    assert arguments is not None

    parser = optparse.OptionParser(usage=_Usage, description=_Description, version="%prog " + __version__)
    punchGroup = optparse.OptionGroup(parser, u"Punching options")
    punchGroup.add_option("-a", "--after", default=_Actions.None_, dest="actionsToPerformAfterPunching", metavar="ACTION", help=u'action(s) to perform after punching (default: "%default")')
    punchGroup.add_option("-b", "--before", default=_Actions.Check, dest="actionsToPerformBeforePunching", metavar="ACTION", help=u'action(s) to perform before punching (default: "%default")')
    punchGroup.add_option("-d", "--depot", dest="depotQualifier", metavar="QUALIFIER", help=u'qualifier for source code depot when using --before=checkout')
    punchGroup.add_option("-i", "--include", dest="includePattern", metavar="PATTERN", help=u'ant pattern for file to include (default: all files)')
    punchGroup.add_option("-m", "--message", default="Punched recent changes.", dest="commitMessage", metavar="TEXT", help=u'text for commit message (default: "%default")')
    punchGroup.add_option("-M", "--move", default=ScmPuncher.MoveName, dest="moveMode", metavar="MODE", type="choice", choices=sorted(list(ScmPuncher._ValidMoveModes)), help=u'criteria to detect moved files (default: "%default")')
    punchGroup.add_option("-w", "--work-only", dest="workOnlyPattern", metavar="PATTERN", help=u'ant pattern for files that only reside in work copy but still should remain (default: none)')
    punchGroup.add_option("-x", "--exclude", dest="excludePattern", metavar="PATTERN", help=u'ant pattern for file to exclude (default: exclude no files but the default excludes)')
    parser.add_option_group(punchGroup)
    textGroup = optparse.OptionGroup(parser, u"Text file conversion options")
    textGroup.add_option("-N", "--newline", dest="newLine", metavar="KIND", type="choice", choices=sorted(_NameToNewLineMap.keys()), help=u'separator at the end of line in --text files (default: "native")')
    textGroup.add_option("-S", "--strip-trailing", action="store_true", dest="isStripTrailing", help=u"strip trailing white space from --text files")
    textGroup.add_option("-t", "--text", dest="textPatternSet", metavar="PATTERN", help=u'ant pattern for files to be considered text files (default: none)')
    textGroup.add_option("-T", "--tabsize", default=TextOptions.PreserveTabs, dest="tabSize", metavar="NUMBER", type=long, help=u'number of spaces to allign tabs with in --text files; %d=keep tab (default: %%default)' % TextOptions.PreserveTabs)
    parser.add_option_group(textGroup)
    consoleGroup = optparse.OptionGroup(parser, u"Console and logging options")
    consoleGroup.add_option("-e", "--encoding", default='auto', help=u'encoding to use for running console commands (default: "%default")')
    consoleGroup.add_option("-L", "--log", default='info', dest="logLevel", metavar="LEVEL", type="choice", choices=sorted(_NameToLogLevelMap.keys()), help=u'logging level (default: "%default")')
    consoleGroup.add_option("-n", "--normalize", default='auto', dest="unicodeNormalization", metavar="FORM", type="choice", choices=sorted(_ValidConsoleNormalizations), help=u'uncode normalization to use for running console commands (default: "%default")')
    parser.add_option_group(consoleGroup)

    # Parse and validate command line options.
    (options, others) = parser.parse_args(arguments[1:])
    if options.tabSize < TextOptions.PreserveTabs:
        parser.error("value for --tabsize is %d but must be at least %d" % (options.tabSize, TextOptions.PreserveTabs))
    if options.textPatternSet is None:
        if options.newLine:
            parser.error("option --text must be set to enable option --newline")
        if options.isStripTrailing:
            parser.error("option --text must be set to enable option --strip-trailing")
        if options.tabSize:
            parser.error("option --text must be set to enable option --tabsize")
        options.newLine = 'native'
    othersCount = len(others)
    if othersCount == 0:
        parser.error("FOLDER to punch into work copy must be specified")
    elif othersCount == 1:
        sourceFolderPath = others[0]
        workFolderPath = os.getcwdu()
    elif othersCount == 2:
        sourceFolderPath = others[0]
        workFolderPath = others[1]
    else:
        parser.error("unrecognized options must be removed: %s" % others[2:])

    # Validate actions for option ``--before``.
    actionsToPerformBeforePunching = _parsedActions(parser, '--before', options.actionsToPerformBeforePunching, _ValidBeforeActions)
    # 10: Consider Actions.Checkout to be destructive
    destructiveActions = set([_Actions.Reset])
    previousDestructiveAction = None
    previousAction = None
    for action in actionsToPerformBeforePunching:
        if action in destructiveActions:
            if previousDestructiveAction:
                parser.error("action %r in option --before must not appear together with action %r: %s" % (action, previousDestructiveAction, options.actionsToPerformBeforePunching))
            if previousAction:
                parser.error("action %r in option --before must appear before action %r: %s" % (action, previousAction, options.actionsToPerformBeforePunching))
            if (action == _Actions.Checkout) and not options.depotQualifier:
                parser.error('--depot must be specified for --before=%s' % _Actions.Checkout)
            previousDestructiveAction = action
        else:
            previousAction = action
            
    # Validate actions for option ``--after``.
    actionsToPerformAfterPunching = _parsedActions(parser, '--after', options.actionsToPerformAfterPunching, _ValidAfterActions)
    foundPurgeAction = False
    for action in actionsToPerformAfterPunching:
        if action == _Actions.Purge:
            assert not foundPurgeAction
            foundPurgeAction = True
        elif foundPurgeAction:
            parser.error("action %r in option --after must appear before action %r but is: %s" % (action, _Actions.Purge, options.actionsToPerformAfterPunching))
            
    return (options, sourceFolderPath, workFolderPath, actionsToPerformBeforePunching, actionsToPerformAfterPunching)

def main(arguments=None):
    """
    Main function for command line call returning a tuple
    ``(exitCode, error)``. In cause everything worked out, the result is
    ``(0, None)``. 
    """
    if arguments == None:
        actualArguments = sys.argv
    else:
        actualArguments = arguments

    # Parse and validate command line options.
    options, sourceFolderPath, workFolderPath, actionsToPerformBeforePunching, actionsToPerformAfterPunching = parsedOptions(actualArguments)

    # Set up logging and encoding.
    _setUpLogging(_NameToLogLevelMap[options.logLevel])
    _setUpEncoding(options.encoding, options.unicodeNormalization)

    # Do the actual work and log any errors.
    exitCode = 1
    exitError = None
    try:
        if _Actions.Checkout in actionsToPerformBeforePunching:
            assert actionsToPerformBeforePunching[0] == _Actions.Checkout
            scmStorage = ScmStorage(options.depotQualifier)
            scmWork = ScmWork(scmStorage, "", workFolderPath, ScmWork.CheckOutActionReset)
        else:
            scmWork = createScmWork(workFolderPath)
        textOptions = _createTextOptions(options)
        
        # Perform actions before punching.
        for action in actionsToPerformBeforePunching:
            assert action in _ValidBeforeActions
            if action == _Actions.Check:
                scmWork.check()
            elif action == _Actions.Checkout:
                scmWork.checkout(True)
            elif action == _Actions.Reset:
                scmWork.reset()
            elif action == _Actions.Update:
                scmWork.update()
            else:
                assert action == _Actions.None_, "action=%r" % action

        # Actually punch work copy.
        scunch(sourceFolderPath, scmWork, textOptions, move=options.moveMode, includePatternText=options.includePattern, excludePatternText=options.excludePattern, workOnlyPatternText=options.workOnlyPattern)

        # Perform actions after punching.
        for action in actionsToPerformAfterPunching:
            assert action in _ValidAfterActions
            if action == _Actions.Commit:
                scmWork.commit("", options.commitMessage)
            elif action == _Actions.Purge:
                scmWork.purge()
            else:
                assert action == _Actions.None_
                
        exitCode = 0
    except ScmPendingChangesError, error:
        _log.error("%s To resolve this, '--before=reset' to discard the changes or '--before=none' to ignore them." % error)
        exitError = error
    except (EnvironmentError, ScmError), error:
        _log.error("%s", error)
        exitError = error
    except Exception, error:
        _log.exception("%s", error)
        exitError = error
    if exitCode:
        assert exitError
    return (exitCode, exitError)

if __name__ == "__main__":
    exitCode, _ = main()
    sys.exit(exitCode)
