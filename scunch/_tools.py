"""
Various utility functions for scunch.
"""
import errno
import fnmatch
import logging
import os
import re
import shutil

_log = logging.getLogger("scunch")

def makeFolder(folderPathToMake):
    """
    Like `os.makedirs` but does nothing if the folder already exists.
    """
    try:
        os.makedirs(folderPathToMake)
    except OSError, error:
        if error.errno !=  errno.EEXIST:
            raise

def removeFolder(folderPathToRemove):
    # Attempt to remove the folder, ignoring any errors.
    _log.debug("remove folder \"%s\"", folderPathToRemove)
    shutil.rmtree(folderPathToRemove, True)
    if os.path.exists(folderPathToRemove):
        # If the folder still exists after the removal, try to remove it again but this
        # time with errors raised. In most cases, this will result in a proper error message
        # explaining why the folder could not be removed the first time.
        shutil.rmtree(folderPathToRemove)

def makeEmptyFolder(folderPathToCreate):
    removeFolder(folderPathToCreate)
    makeFolder(folderPathToCreate)

def antPatternList(patternText):
    assert patternText is not None
    if u"," in patternText:
        result = [item.strip() for item in patternText.split(",")]
    else:
        result = patternText.split()
    return result

_AntAllMagic = "**"
_AntMagicRegEx = re.compile('[*?[]')

class AntPatternError(Exception):
    pass

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
        elif self.kind == AntPatternItem.Many:
            result = fnmatch.fnmatch(text, self.pattern)
        else:
            assert self.kind == AntPatternItem.One
            result = (text == self.pattern)
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

def _findTextItemsPartForPatternItems(textItems, patternItems):
    """
    First index in ``textItems`` where a part of ``textItems`` with the same number of items as
    ``patternItems`` matches ``patternItems``. 
    """
    assert textItems is not None
    assert patternItems is not None
    for patternItem in patternItems:
        assert patternItem.kind != AntPatternItem.All
    # This functions only is useful for ``patternItems`` between "** and another "**".
    assert patternItems

    result = -1
    textItemsCount = len(textItems)
    patternItemsCount = len(patternItems)
    indexToCheck = 0
    while (result == -1) and (indexToCheck + patternItemsCount <= textItemsCount):
        textItemsPartToCompareWithPatternItems = textItems[indexToCheck:indexToCheck + patternItemsCount]
        # TODO: Remove: print indexToCheck + patternItemsCount, textItemsCount, textItemsPartToCompareWithPatternItems
        if _textItemsMatchPatternItems(textItemsPartToCompareWithPatternItems, patternItems):
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
    print "_textItemsMatchPatternItems:"
    print "  ti=", textItems
    print "  pi=", patternItems
    if hasPatternItems:
        firstPatternItem = patternItems[0]
        if hasTextItems:
            if firstPatternItem.kind == AntPatternItem.All:
                if hasExactlyOnePatternItem:
                    # "**" at end of pattern matches everything.
                    result = True
                else:
                    patternItemIndexOfCurrentAntAllMagic = 0
                    print "    patternItemIndexOfCurrentAntAllMagic=", patternItemIndexOfCurrentAntAllMagic
                    patternItemIndexOfNextAntAllMagic = _findItemInList(_AntAllMagic, patternItems[patternItemIndexOfCurrentAntAllMagic + 1:])
                    if patternItemIndexOfNextAntAllMagic != -1:
                        # Adjust for the fact that we started to search after the first pattern item.
                        patternItemIndexOfNextAntAllMagic += 1
                    assert patternItemIndexOfNextAntAllMagic != 1, "consecutive %r must be reduced to 1" % _AntAllMagic
                    print "    patternItemIndexOfNextAntAllMagic=", patternItemIndexOfNextAntAllMagic
                    if patternItemIndexOfNextAntAllMagic == -1:
                        # Last "**" encountered; check that tail of text matches end of remaining pattern.
                        patternItemsAfterAllMagic = patternItems[1:]
                        print "    patternItemsAfterAllMagic=", patternItemsAfterAllMagic
                        tailOfTextItems = textItems[-len(patternItemsAfterAllMagic):]
                        result = _textItemsAreAtEndOfPatternItems(tailOfTextItems, patternItemsAfterAllMagic)
                    else:
                        # "**" encountered with more "**" to come: check if and part of
                        # ``textItems`` matches the pattern between the two "**".
                        patternItemsBetweenAllMagic = patternItems[patternItemIndexOfCurrentAntAllMagic + 1:patternItemIndexOfNextAntAllMagic]
                        print "    patternItemsBetweenAllMagic=", patternItemsBetweenAllMagic
                        indexOfTextItemsMatchingPatternItemsBetweenAll = _findTextItemsPartForPatternItems(textItems, patternItemsBetweenAllMagic)
                        if indexOfTextItemsMatchingPatternItemsBetweenAll >= 0:
                            remainingTextItems = textItems[indexOfTextItemsMatchingPatternItemsBetweenAll + len(patternItemsBetweenAllMagic):]
                            remainingPatternItems = patternItems[patternItemIndexOfNextAntAllMagic:]
                            print "    remainingTextItems=", remainingTextItems
                            print "    remainingPatternItems=", remainingPatternItems
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
                # Text matches if pattern is a single empty item or a single "*".
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
        # Text matches pattern if both do not contain even a single item.
        result = not hasTextItems
    return result

def _splitTextItems(text):
    result = []
    pathSeperator = os.sep
    if pathSeperator == "/":
        remainingText = text.replace("\\", pathSeperator)
    elif pathSeperator == "\\":
        remainingText = text.replace("/", pathSeperator)
    else:
        raise NotImplementedError("cannot split unknown path separator: %r" % pathSeperator)
    if remainingText.endswith(pathSeperator):
        remainingText += _AntAllMagic
    while remainingText:
        remainingText, itemText = os.path.split(remainingText)
        result.insert(0, itemText)
    return result

class AntPattern(object):
    """
    Ant-like pattern representing a single path.
    """
    def __init__(self, patternText):
        self.patternItems = [AntPatternItem(itemText) for itemText in _splitTextItems(patternText)]

    def matches(self, text):
        textItems = _splitTextItems(text)
        return self.matchesItems(textItems)
    
    def matchesItems(self, textItems):
        assert textItems is not None
        return _textItemsMatchPatternItems(textItems, self.patternItems)

    def __unicode__(self):
        return u"<AntPattern: %s>" % (self.patternItems)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __repr__(self):
        return self.__str__()

class AntPatternSet(object):
    def __init__(self, patterns=()):
        self.patterns = []
        for pattern in patterns:
            self.add(pattern)
    
    def add(self, pattern):
        assert pattern is not None
        self.patterns.append(pattern)

    def matches(self, text):
        textItems = _splitTextItems(text)
        return self.matchesItems(textItems)
    
    def matchesItems(self, textItems):
        assert textItems is not None
        result = False
        patternIndex = 0
        while not result and (patternIndex < len(self.patterns)):
            pattern = self.patterns[patternIndex]
            if pattern.matchesItems(textItems):
                result = True
            else:
                patternIndex += 1
        return result

    def __unicode__(self):
        return u"<AntPatternSet: %s>" % (self.patterns)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __repr__(self):
        return self.__str__()

class AntGlob(object):
    """
    Glob using ant patterns as describe in
    <http://ant.apache.org/manual/dirtasks.html>.
    """
    def __init__(self, pattern):
        assert pattern is not None
        