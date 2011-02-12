"""
Ant-like pattern matching and globbing with support for "**".

Ant-like includePatterns in their original form are described at
<http://ant.apache.org/manual/dirtasks.html>.
Patterns supported by this module also allow shell includePatterns using "[" and "]"
as supported by the `fnmatch` and `glob` module.

To sum it up:

* "/" or "\" separate folder names. Internally, "\" is unified to "/".
* "*" matches none or any amount of characters.
* "?" matches any single character.
* "[seq]" matches any character in sequence ``seq``.
* "[!seq]" matches any character not in sequence ``seq``.
* "**" matches none or any folder.
* If a pattern ends with "/" or "\", a "**" is automatically appended at the
  end of the pattern.
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
import errno
import fnmatch
import logging
import os
import re
import stat

_log = logging.getLogger("antglob")

_AntAllMagic = "**"
_AntMagicRegEx = re.compile('[*?[]')
# TODO: Use _NotFound = -1; or use ``None`` to indicate a "not found".

# Patterns to exclude by default similar to ant 1.8.2.
DefaultExcludes = (
     u"**/*~",
     u"**/#*#",
     u"**/.#*",
     u"**/%*%",
     u"**/._*",
     u"**/CVS",
     u"**/CVS/**",
     u"**/.cvsignore",
     u"**/SCCS",
     u"**/SCCS/**",
     u"**/vssver.scc",
     u"**/.svn",
     u"**/.svn/**",
     u"**/.DS_Store",
     u"**/.git",
     u"**/.git/**",
     u"**/.gitattributes",
     u"**/.gitignore",
     u"**/.gitmodules",
     u"**/.hg",
     u"**/.hg/**",
     u"**/.hgignore",
     u"**/.hgsub",
     u"**/.hgsubstate",
     u"**/.hgtags",
     u"**/.bzr",
     u"**/.bzr/**",
     u"**/.bzrignore"
)

def createAntPatterns(patternListText):
    """
    List of `AntPattern`s extracted from ``patternListText``, which should contain
    patterns separated by a comma (,) or blank ( ).
    """
    assert patternListText is not None
    result = []
    if u"," in patternListText:
        patternText = [part.strip() for part in patternListText.split(u",")]
    else:
        patternText = patternListText.split()
    for patternTextItem in patternText:
        result.append(AntPattern(patternTextItem))
    return result

def resolvedPathParts(parts=[]):
    assert parts is not None
    result = ""
    for element in parts:
        result = os.path.join(result, element)
    return result

def isFolderPath(pathToCheck):
    """
    ``True`` if ``pathToCheck`` indicates a folder path as returned by `AntPatternSet.find()`.
    """
    assert pathToCheck is not None
    return pathToCheck.endswith(os.sep)

def _asFolderPath(path):
    assert path is not None
    return path + os.sep

def _parentOfFolderPath(folderPath):
    """
    Like ``folderPath`` but without the trailing `os.sep`.
    """
    assert folderPath
    assert isFolderPath(folderPath)
    return os.path.dirname(folderPath[:-1])

class AntPatternError(Exception):
    """
    Error raised if an ant-like pattern is broken or cannot be processed.
    """
    pass

class FileSystemEntry(object):
    """
    Entry in a file system folder relative to a base folder. This typically is a file or folder.
    """
    File = 'file'
    Folder = 'folder'

    def __init__(self, baseFolderPath="", parts=[]):
        assert parts is not None
        assert baseFolderPath is not None
        
        self.parts = tuple(parts)
        if self.parts:
            self.name = self.parts[-1]
        else:
            self.name = ""
        self.relativePath = resolvedPathParts(self.parts)
        self.path = self.absolutePath(baseFolderPath)
        try:
            entryInfo = os.stat(self.path)
        except OSError, error:
            if error.errno == errno.ENOENT:
                raise AntPatternError("folder entry must remain during processing but was removed in the background: %r" % self.path)
            else:
                raise
        entryMode = entryInfo.st_mode
        if stat.S_ISDIR(entryMode):
            self.kind = FileSystemEntry.Folder
        elif stat.S_ISREG(entryMode):
            self.kind = FileSystemEntry.File
        else:
            raise AntPatternError("folder entry must be a folder or file: %r" % self.path)
        self.size = entryInfo.st_size
        self.timeModified = entryInfo.st_mtime

    def absolutePath(self, baseFolderPath):
        assert baseFolderPath is not None
        return os.path.join(baseFolderPath, self.relativePath)

    def __hash__(self):
        return self.parts.__hash__()

    def __cmp__(self, other):
        return cmp(self.parts, other.parts)

    def __eq__(self, other):
        return self.parts == other.parts

    def __unicode__(self):
        return u"<FileSystemEntry: kind=%s, parts=%s>" % (self.kind, self.parts)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __repr__(self):
        return self.__str__()

class AntPatternItem(object):
    """
    Ant-like pattern item able to match a single part of a path.
    """
    All = "all"
    Many = "many"
    One = "one"
    
    def __init__(self, text):
        assert text is not None
        self.pattern = text
        if text == _AntAllMagic:
            self.kind = AntPatternItem.All
        elif _AntMagicRegEx.search(text):
            self.kind = AntPatternItem.Many
        else:
            self.kind = AntPatternItem.One

    def matches(self, text):
        if self.kind == AntPatternItem.All:
            result = True
        else:
            assert self.kind in (AntPatternItem.Many, AntPatternItem.One) 
            result = fnmatch.fnmatch(text, self.pattern)
        return result

    def __cmp__(self, other):
        if isinstance(other, AntPatternItem):
            result = cmp(self.pattern, other.pattern)
        else:                                     
            result = cmp(self.pattern, other)
        return result    

    def __unicode__(self):
        return u"<AntPatternItem: kind=%s, pattern=%r>" % (self.kind, self.pattern)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __repr__(self):
        return self.__str__()

def _findItemInList(needle, haystack):
    return _findListInList([needle], haystack)

def _findListInList(needle, haystack):
    result = -1
    needleLength = len(needle)
    haystackLength = len(haystack)
    if needle:
        indexToCheck = 0
        while (result == -1) and (indexToCheck + needleLength <= haystackLength):
            haystackPartToCompareWithNeedle = haystack[indexToCheck:indexToCheck + needleLength]
            # TODO: Remove: print indexToCheck + needleLength, haystackLength, haystackPartToCompareWithNeedle
            if needle == haystackPartToCompareWithNeedle:
                result = indexToCheck
            else:
                indexToCheck += 1
    else:
        result = 0 
    return result

def _indexInTextItemsWherePatternPartsMatch(textParts, patternParts):
    """
    First index in ``textParts`` where a part of ``textParts`` with the same number of parts as
    ``patternParts`` matches ``patternParts``. 
    """
    assert textParts is not None
    assert patternParts is not None
    for patternItem in patternParts:
        assert patternItem.kind != AntPatternItem.All
    # This functions only is useful for ``patternParts`` between "** and another "**".
    assert patternParts

    result = -1
    textItemsCount = len(textParts)
    patternItemsCount = len(patternParts)
    indexToCheck = 0
    while (result == -1) and (indexToCheck + patternItemsCount <= textItemsCount):
        textItemsPartToCompareWithPatternItems = textParts[indexToCheck:indexToCheck + patternItemsCount]
        # TODO: Remove: print indexToCheck + patternItemsCount, textItemsCount, textItemsPartToCompareWithPatternItems
        if _textItemsMatchPatternItems(textItemsPartToCompareWithPatternItems, patternParts):
            result = indexToCheck
        else:
            indexToCheck += 1
    return result

def _findTextItemsInPatternItems(textItems, patternItems):
    """
    Index where ``textItems`` are found in ``patternItems`` or -1.
    """
    assert textItems is not None
    assert patternItems is not None
    for patternItem in patternItems:
        assert patternItem.kind != AntPatternItem.All

    result = -1
    textItemsLength = len(textItems)
    if textItemsLength:
        patternItemsLength = len(patternItems)
        patternItemIndexToStartSearchAt = 0
        while (result == -1) and (patternItemIndexToStartSearchAt + textItemsLength) <= patternItemsLength:
            patternItemsToMatch = patternItems[patternItemIndexToStartSearchAt:patternItemIndexToStartSearchAt + textItemsLength]
            if _textItemsMatchPatternItems(textItems, patternItemsToMatch):
                result = patternItemIndexToStartSearchAt
            else:
                patternItemIndexToStartSearchAt += 1
    elif not patternItem:
        result = 0
    return result

def _textItemsAreInPatternItems(textItems, patternItems):
    """
    ``True`` if a match for ``textItems`` can be found somewhere in ``patternItems``.
    """
    assert textItems is not None
    assert patternItems is not None
    for patternItem in patternItems:
        assert patternItem.kind != AntPatternItem.All

    return (_findTextItemsInPatternItems(textItems, patternItems) != -1)

def _textItemsAreAtEndOfPatternItems(textItems, patternItems):
    assert textItems is not None
    assert patternItems is not None
    for patternItem in patternItems:
        assert patternItem.kind != AntPatternItem.All

    patternItemsTail = patternItems[-len(textItems):]
    result = _textItemsMatchPatternItems(textItems, patternItemsTail)
    return result

def _textItemsMatchPatternItems(textItems, patternItems):
    assert textItems is not None
    assert patternItems is not None
    hasTextItems = (len(textItems) > 0)
    hasPatternItems = (len(patternItems) > 0)
    hasExactlyOnePatternItem = (len(patternItems) == 1)
    _log.debug("_textItemsMatchPatternItems:")
    _log.debug("  ti=%s", textItems)
    _log.debug("  pi=%s", patternItems)
    if hasPatternItems:
        firstPatternItem = patternItems[0]
        if hasTextItems:
            if firstPatternItem.kind == AntPatternItem.All:
                if hasExactlyOnePatternItem:
                    # "**" at end of pattern matches everything.
                    result = True
                else:
                    patternItemIndexOfNextAntAllMagic = _findItemInList(_AntAllMagic, patternItems[1:])
                    if patternItemIndexOfNextAntAllMagic != -1:
                        # Adjust for the fact that we started to search after the first pattern item.
                        patternItemIndexOfNextAntAllMagic += 1
                    assert patternItemIndexOfNextAntAllMagic != 1, "consecutive %r must be reduced to 1" % _AntAllMagic
                    _log.debug("    patternItemIndexOfNextAntAllMagic=%s", patternItemIndexOfNextAntAllMagic)
                    if patternItemIndexOfNextAntAllMagic == -1:
                        # Last "**" encountered; check that tail of text matches end of remaining pattern.
                        patternItemsAfterAllMagic = patternItems[1:]
                        _log.debug("    patternItemsAfterAllMagic=%s", patternItemsAfterAllMagic)
                        tailOfTextItems = textItems[-len(patternItemsAfterAllMagic):]
                        result = _textItemsAreAtEndOfPatternItems(tailOfTextItems, patternItemsAfterAllMagic)
                    else:
                        # "**" encountered with more "**" to come: check if and part of
                        # ``textItems`` matches the pattern between the two "**".
                        patternItemsBetweenAllMagic = patternItems[1:patternItemIndexOfNextAntAllMagic]
                        _log.debug("    patternItemsBetweenAllMagic=%s", patternItemsBetweenAllMagic)
                        indexOfTextItemsMatchingPatternItemsBetweenAll = _indexInTextItemsWherePatternPartsMatch(textItems, patternItemsBetweenAllMagic)
                        if indexOfTextItemsMatchingPatternItemsBetweenAll >= 0:
                            remainingTextItems = textItems[indexOfTextItemsMatchingPatternItemsBetweenAll + len(patternItemsBetweenAllMagic):]
                            remainingPatternItems = patternItems[patternItemIndexOfNextAntAllMagic:]
                            _log.debug("    remainingTextItems=%s", remainingTextItems)
                            _log.debug("    remainingPatternItems=%s", remainingPatternItems)
                            result = _textItemsMatchPatternItems(remainingTextItems, remainingPatternItems)
                        else:
                            # We cannot even find the current sub pattern anywhere in the
                            # remaining ``textItems``, so there is no need to process any
                            # further.
                            result = False
            else:
                if firstPatternItem.matches(textItems[0]):
                    result = _textItemsMatchPatternItems(textItems[1:], patternItems[1:])
                else:
                    # Text does not match pattern.
                    result = False
        else:
            # We have a pattern but no text.
            if len(patternItems) == 1:
                # Text matches if pattern is a single empty part or a single "*".
                if firstPatternItem.kind == AntPatternItem.One:
                    result = not firstPatternItem.pattern
                elif firstPatternItem.kind == AntPatternItem.Many:
                    result = (firstPatternItem.pattern == "*")
                else:
                    assert firstPatternItem.kind == AntPatternItem.All
                    result = True
            else:
                result = False
    else:
        # Text matches pattern if both do not contain even a single part.
        result = not hasTextItems
    return result

def _splitTextParts(text, fixAllMagicAtEnd=False):
    """
    List of string containing ``text`` split using a system independent path separator.
    
    Perform the following transformations on the text:

    * Unify "/" and "\\" to "/" to allow system independent path matching.
    * If ``fixAllMagicAtEnd`` is ``True`` and ``text`` ends in "/", append "**" to indicate that
      everything in the specified folder should match.
    """
    result = []
    pathSeperator = os.sep
    if pathSeperator == "/":
        remainingText = text.replace("\\", pathSeperator)
    elif pathSeperator == "\\":
        remainingText = text.replace("/", pathSeperator)
    else:
        raise NotImplementedError("cannot split unknown path separator: %r" % pathSeperator)
    if fixAllMagicAtEnd and remainingText.endswith(pathSeperator):
        remainingText += _AntAllMagic
    while remainingText and (remainingText != pathSeperator):
        remainingText, part = os.path.split(remainingText)
        result.insert(0, part)
    return result

class AntPattern(object):
    """
    Ant-like pattern representing a single path.
    """
    def __init__(self, patternText):
        assert patternText is not None
        self.patternItems = [AntPatternItem(itemText) for itemText in _splitTextParts(patternText, True)]

    def matches(self, text):
        assert text is not None
        textItems = _splitTextParts(text)
        return self.matchesParts(textItems)
    
    def matchesParts(self, textItems):
        assert textItems is not None
        return _textItemsMatchPatternItems(textItems, self.patternItems)

    def __unicode__(self):
        result = u"<AntPattern: %s>" % (self.patternItems)
        return result
        
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __repr__(self):
        return self.__str__()

class AntPatternSet(object):
    """
    A set of include and exclude patterns to decide whether a text should match.
    
    If no include pattern is specified, everything matches.
    
    As example, first create a pattern and specifiy which files to include and exclude. In this
    case, we want to include Python source code and documentation but exclude Python byte code:
    
    >>> pythonSet = AntPatternSet()
    >>> pythonSet.include("**/*.py, **/*.rst")
    >>> pythonSet.exclude("**/*.pyc, **/*.pyo")
    
    We can use this pattern set to check whether certain file paths would be part of it:
    >>> pythonSet.matches("some/module.py")
    True
    >>> pythonSet.matches("logo.gif")
    False
    
    The most useful method however is `AntPatternSet.find()`, which scans a folder for files and
    returns the files that match the pattern.
    """
    def __init__(self, useDefaultExcludes=True):
        """
        Create a new pattern set, which would include everything and exclude nothing apart from
        `DefaultExcludes`. To even consider files and folders in `DefaultExcludes`, specify
        `` useDefaultExcludes=False``.
        """
        self.includePatterns = []
        self.excludePatterns = []
        if useDefaultExcludes:
            for patternText in DefaultExcludes:
                self.exclude(patternText)
    
    def _addPatternDefinition(self, targetPatterns, patternDefinition):
        assert targetPatterns is not None
        assert patternDefinition is not None
        if isinstance(patternDefinition, basestring) : 
            for pattern in createAntPatterns(patternDefinition):
                targetPatterns.append(pattern)
        else:
            targetPatterns.append(patternDefinition)

    def include(self, patternDefinition):
        """
        Include ``patternDefinition``, which can be an ``AntPattern`` or a
        string possibly containing multiple patterns separated by a comma
        or space.
        """
        assert patternDefinition is not None
        self._addPatternDefinition(self.includePatterns, patternDefinition)

    def exclude(self, patternDefinition):
        """
        Exclude ``patternDefinition``, which can be an ``AntPattern`` or a
        string possibly containing multiple patterns separated by a comma
        or space.
        """
        assert patternDefinition is not None
        self._addPatternDefinition(self.excludePatterns, patternDefinition)

    def matches(self, text):
        textItems = _splitTextParts(text)
        return self.matchesParts(textItems)
    
    def _matchesAnyPatternIn(self, textItems, patterns):
        """
        ``True`` if ``textItems`` match any of the patterns in ``patterns``.
        """
        assert textItems is not None
        assert patterns is not None
        assert patterns, "empty patterns are special and must be handled before calling this"
        result = False
        patternIndex = 0
        while not result and (patternIndex < len(patterns)):
            pattern = patterns[patternIndex]
            if pattern.matchesParts(textItems):
                result = True
            else:
                patternIndex += 1
        return result
        
    def matchesParts(self, partsToMatch):
        assert partsToMatch is not None
        if self.includePatterns:
            result = self._matchesAnyPatternIn(partsToMatch, self.includePatterns)
        else:
            result = True
        if result and self.excludePatterns and self._matchesAnyPatternIn(partsToMatch, self.excludePatterns):
            result = False
        return result

    def _findFilesAndEmptyFolders(self, baseFolderPath, relativeFolderParts, relativeFolderPath, addFolders):
        """
        Find files and empty folders matching the pattern.
        """
        assert baseFolderPath is not None
        assert relativeFolderParts is not None
        assert relativeFolderPath is not None
        if relativeFolderPath.startswith(os.sep):
            raise ValueError("relative path must not start with %r: %r" % (os.sep, relativeFolderPath))
        folderToScanPath = os.path.join(baseFolderPath, relativeFolderPath)
        foundMatchingFilesOrSubFolders = False
        for nameToExamine in os.listdir(folderToScanPath):
            pathToExamine = os.path.join(relativeFolderPath, nameToExamine)
            if pathToExamine.startswith(os.sep):
                raise ValueError("pathToExamine must not start with %r: %r" % (os.sep, pathToExamine))
            pathToExamineParts = list(relativeFolderParts)
            pathToExamineParts.append(nameToExamine)
            if self.excludePatterns:
                isExcluded = self._matchesAnyPatternIn(pathToExamineParts, self.excludePatterns)
            else:
                isExcluded = False
            if not isExcluded:
                fullPathToExamine = os.path.join(baseFolderPath, pathToExamine)
                if os.path.isdir(fullPathToExamine):
                    # TODO: Scan into folder only if include patterns suggest there is a chance to
                    # actually find anything there.
                    for pathToExamine in self._findFilesAndEmptyFolders(baseFolderPath, pathToExamineParts, pathToExamine, addFolders):
                        if not foundMatchingFilesOrSubFolders:
                            foundMatchingFilesOrSubFolders = True
                        yield pathToExamine
                elif self.includePatterns:
                    if self._matchesAnyPatternIn(pathToExamineParts, self.includePatterns):
                        yield pathToExamine
                else:
                    # Without include pattern, yield everything.
                    yield pathToExamine
        if addFolders and not foundMatchingFilesOrSubFolders and self.matches(relativeFolderPath):
            # If no files or sub folders could be found but the folder itself matches, yield it.
            yield _asFolderPath(relativeFolderPath)

    def _findInFolder(self, baseFolderPath, addFolders):
        assert baseFolderPath is not None
        folderPathsYield = set()
        for pathToExamine in self._findFilesAndEmptyFolders(baseFolderPath, [], "", addFolders):
            if addFolders:
                # Yield all containing folders of `pathToExamine` that have not been yield yet.
                if isFolderPath(pathToExamine):
                    containingFolderPath = _parentOfFolderPath(pathToExamine)
                else:
                    containingFolderPath = os.path.dirname(pathToExamine)
                parentFolderPathsToYield = []
                if containingFolderPath:
                    assert containingFolderPath != os.sep
                    while containingFolderPath not in folderPathsYield:
                        parentFolderPathsToYield.insert(0, containingFolderPath)
                        folderPathsYield.update([containingFolderPath])
                    for containingFolderPath in parentFolderPathsToYield:
                        if containingFolderPath.startswith(os.sep):
                            raise ValueError("containingFolderPath must not start with %r: %r" % (os.sep, containingFolderPath))
                        yield _asFolderPath(containingFolderPath)
            yield pathToExamine

    def ifind(self, folderToScanPath=os.getcwdu(), addFolders=False):
        """
        Like `find()` but iterates over `folderToScanPath` instead of returning a list of paths.
        """
        assert folderToScanPath is not None
        for relativePath in self._findInFolder(folderToScanPath, addFolders):
            if relativePath.startswith(os.sep):
                assert not relativePath.startswith(os.sep), "relativePath=%r" % relativePath
            yield relativePath

    def find(self, folderToScanPath=os.getcwdu(), addFolders=False):
        """
        List of paths of files relative to ``folderPath`` matching the pattern set.
        """
        assert folderToScanPath is not None
        result = []
        for path in self.ifind(folderToScanPath, addFolders):
            result.append(path)
        return result

    def ifindEntries(self, folderToScanPath=os.getcwdu()):
        """
        Like `findEntries()` but iterates over ``folderToScanPath`` instead of returning a list of paths.
        """
        for path in self.ifind(folderToScanPath, True):
            parts = _splitTextParts(path)
            yield FileSystemEntry(folderToScanPath, parts)

    def findEntries(self, folderToScanPath=os.getcwdu()):
        """
        List containing a `FileSystemEntry` for each file matching the pattern set or any folder
        containing at least one such file.
        """
        result = []
        for entry in self.ifindEntries(folderToScanPath):
            _log.info("%s", entry)
            result.append(entry)
        return result

    def __unicode__(self):
        return u"<AntPatternSet: include=%s, exclude=%s>" % (self.includePatterns, self.excludePatterns)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __repr__(self):
        return self.__str__()

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    _log.info("running doctest")
    import doctest
    doctest.testmod()
