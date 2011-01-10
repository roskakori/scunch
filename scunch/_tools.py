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

    def __unicode__(self):
        return u"<AntPatternItem: kind=%s, pattern=%r>" % (self.kind, self.pattern)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __repr__(self):
        return self.__str__()

def _textItemsMatchPatternItems(textItems, patternItems):
    assert textItems is not None
    assert patternItems is not None
    hasTextItems = (len(textItems) > 0)
    hasPatternItems = (len(patternItems) > 0)
    hasExactlyOnePatternItem = (len(patternItems) == 1)
    if hasPatternItems:
        print "%r" % patternItems
        firstPatternItem = patternItems[0]
        if hasTextItems:
            if firstPatternItem.kind == AntPatternItem.All:
                if hasExactlyOnePatternItem:
                    # "**" at end of pattern matches everything.
                    result = True
                else:
                    raise NotImplementedError()
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
                else:
                    assert firstPatternItem.kind == AntPatternItem.Many
                    result = (firstPatternItem.pattern == "*")
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
        