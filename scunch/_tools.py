"""
Various utility functions for scunch.
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
import errno
import logging
import os
import shutil
import string

_log = logging.getLogger("scunch")


def makeFolder(folderPathToMake):
    """
    Like `os.makedirs` but does nothing if the folder already exists.
    """
    try:
        os.makedirs(folderPathToMake)
    except OSError, error:
        if error.errno != errno.EEXIST:
            raise  # pragma: no cover


def removeFolder(folderPathToRemove):
    '''
    Attempt to remove the folder, ignoring any errors.
    '''
    _log.debug("remove folder \"%s\"", folderPathToRemove)
    shutil.rmtree(folderPathToRemove, True)
    if os.path.exists(folderPathToRemove):
        # If the folder still exists after the removal, try to remove it again but this
        # time with errors raised. In most cases, this will result in a proper error message
        # explaining why the folder could not be removed the first time.
        shutil.rmtree(folderPathToRemove)  # pragma: no cover


def makeEmptyFolder(folderPathToCreate):
    removeFolder(folderPathToCreate)
    makeFolder(folderPathToCreate)


def humanReadableList(items):
    """
    All values in ``items`` in a human readable form. This is meant to be used in error messages, where
    dumping '%r' to the user does not cut it.

    >>> humanReadableList(['red', 'green', 'blue'])
    u"'red', 'green' or 'blue'"
    """
    assert items is not None
    listItems = list(items)
    itemCount = len(listItems)
    if itemCount == 0:
        result = u''
    elif itemCount == 1:
        result = u'%r' % listItems[0]
    else:
        result = u''
        for itemIndex in range(itemCount):
            if itemIndex == itemCount - 1:
                result += u' or '
            elif itemIndex > 0:
                result += u', '
            result += u'%r' % listItems[itemIndex]
        assert result
    assert result is not None
    return result


def oneOrOtherText(count, oneText, otherText):
    """
    Text depending ``count`` to properly use singular and plural.

    >>> oneOrOtherText(2, 'item', 'items')
    u'2 items'
    """
    assert count >= 0
    if count == 1:
        text = oneText
    else:
        text = otherText
    result = u'%d %s' % (count, text)
    return result

if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    _log.info('running doctest')
    import doctest
    doctest.testmod()


# Maximum length of console commands. According to
# <http://support.microsoft.com/kb/830473/>, Windows NT and Windows 2000
# allow at most 2047. Later Windows versions would allow 8191.
_MAX_COMMAND_LENGTH = 2047

# Characters in filenames that for sure will not have to be escaped on any platform.
_UNESCAPED_CHARACTERS = set(string.ascii_letters + string.digits)
_MIN_BASE_COMMAND_AND_OPTIONS_LENGTH = 3  # 1 blank + 2 quotes


def bundledPathsToRun(baseCommandAndOptions, paths, maxCommandLenth=_MAX_COMMAND_LENGTH):
    assert baseCommandAndOptions
    assert paths is not None

    def escapedLength(text):
        '''
        Countable length for possibly escaped and quoted commands and options.

        This function aims to be platform independent and remains on the safe side when
        deciding which characters have to be quoted.
        '''
        result = _MIN_BASE_COMMAND_AND_OPTIONS_LENGTH
        for ch in text:
            if ch in _UNESCAPED_CHARACTERS:
                result += 1
            else:
                result += 2
        return result

    result = []
    resultLength = 0
    baseCommandAndOptionsLength = sum(escapedLength(option) for option in baseCommandAndOptions)
    maxPathsLength = maxCommandLenth - baseCommandAndOptionsLength
    if maxPathsLength < 1 + _MIN_BASE_COMMAND_AND_OPTIONS_LENGTH:
        raise EnvironmentError(u'command must have at most %d escapable characters instead of %d: %s' % (
            maxPathsLength - (1 + _MIN_BASE_COMMAND_AND_OPTIONS_LENGTH),
            baseCommandAndOptionsLength, u' '.join(baseCommandAndOptions)))
    pathIndex = 0
    pathCount = len(paths)

    while (pathIndex < pathCount):
        pathToAppend = paths[pathIndex]
        pathToAppendLength = escapedLength(pathToAppend)
        if resultLength + pathToAppendLength > maxPathsLength:
            if not result:
                raise EnvironmentError(u'path must have at most %d characters instead of %d to be processable by base command "%s": %s' % (
                    maxPathsLength, pathToAppendLength, u' '.join(baseCommandAndOptions), pathToAppend))
            yield result
            result = []
            resultLength = 0
        result.append(pathToAppend)
        resultLength += pathToAppendLength
        pathIndex += 1
    if result:
        yield result
