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
import sys
from unittest import TestCase

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


def _maximumCommandLength():
    '''
    Maximum length of console commands.
    '''
    try:
        result = os.sysconf('SC_ARG_MAX')
    except OSError:
        #  Assume windows. According to
        # <http://support.microsoft.com/kb/830473/>, Windows NT and Windows 2000
        # allow at most 2047. Later Windows versions would allow 8191.
        result = 2047
    return result


_MAX_COMMAND_LENGTH = _maximumCommandLength()

# Characters in filenames that for sure will not have to be escaped on any platform.
_UNESCAPED_CHARACTERS = set(string.ascii_letters + string.digits)
_MIN_BASE_COMMAND_AND_OPTIONS_LENGTH = 3  # 1 blank + 2 quotes


def configConsoleLogging():
    '''
    Configure console logging so that non ASCII characters can be printed under
    Windows without causing `UnicodeError`s.

    Source: http://stackoverflow.com/questions/878972/windows-cmd-encoding-change-causes-python-crash
    '''
    if sys.platform == 'win32':
        import codecs
        from ctypes import WINFUNCTYPE, windll, POINTER, byref, c_int
        from ctypes.wintypes import BOOL, HANDLE, DWORD, LPWSTR, LPCWSTR, LPVOID

        original_stderr = sys.stderr

        # If any exception occurs in this code, we'll probably try to print it on stderr,
        # which makes for frustrating debugging if stderr is directed to our wrapper.
        # So be paranoid about catching errors and reporting them to original_stderr,
        # so that we can at least see them.
        def _complain(message):
            print >> original_stderr, message if isinstance(message, str) else repr(message)

        # Work around <http://bugs.python.org/issue6058>.
        codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

        # Make Unicode console output work independently of the current code page.
        # This also fixes <http://bugs.python.org/issue1602>.
        # Credit to Michael Kaplan <http://blogs.msdn.com/b/michkap/archive/2010/04/07/9989346.aspx>
        # and TZOmegaTZIOY
        # <http://stackoverflow.com/questions/878972/windows-cmd-encoding-change-causes-python-crash/1432462#1432462>.
        try:
            # <http://msdn.microsoft.com/en-us/library/ms683231(VS.85).aspx>
            # HANDLE WINAPI GetStdHandle(DWORD nStdHandle);
            # returns INVALID_HANDLE_VALUE, NULL, or a valid handle
            #
            # <http://msdn.microsoft.com/en-us/library/aa364960(VS.85).aspx>
            # DWORD WINAPI GetFileType(DWORD hFile);
            #
            # <http://msdn.microsoft.com/en-us/library/ms683167(VS.85).aspx>
            # BOOL WINAPI GetConsoleMode(HANDLE hConsole, LPDWORD lpMode);

            GetStdHandle = WINFUNCTYPE(HANDLE, DWORD)(("GetStdHandle", windll.kernel32))
            STD_OUTPUT_HANDLE = DWORD(-11)
            STD_ERROR_HANDLE = DWORD(-12)
            GetFileType = WINFUNCTYPE(DWORD, DWORD)(("GetFileType", windll.kernel32))
            FILE_TYPE_CHAR = 0x0002
            FILE_TYPE_REMOTE = 0x8000
            GetConsoleMode = WINFUNCTYPE(BOOL, HANDLE, POINTER(DWORD))(("GetConsoleMode", windll.kernel32))
            INVALID_HANDLE_VALUE = DWORD(-1).value

            def not_a_console(handle):
                if handle == INVALID_HANDLE_VALUE or handle is None:
                    return True
                return ((GetFileType(handle) & ~FILE_TYPE_REMOTE) != FILE_TYPE_CHAR
                        or GetConsoleMode(handle, byref(DWORD())) == 0)

            old_stdout_fileno = None
            old_stderr_fileno = None
            if hasattr(sys.stdout, 'fileno'):
                old_stdout_fileno = sys.stdout.fileno()
            if hasattr(sys.stderr, 'fileno'):
                old_stderr_fileno = sys.stderr.fileno()

            STDOUT_FILENO = 1
            STDERR_FILENO = 2
            real_stdout = (old_stdout_fileno == STDOUT_FILENO)
            real_stderr = (old_stderr_fileno == STDERR_FILENO)

            if real_stdout:
                hStdout = GetStdHandle(STD_OUTPUT_HANDLE)
                if not_a_console(hStdout):
                    real_stdout = False

            if real_stderr:
                hStderr = GetStdHandle(STD_ERROR_HANDLE)
                if not_a_console(hStderr):
                    real_stderr = False

            if real_stdout or real_stderr:
                # BOOL WINAPI WriteConsoleW(HANDLE hOutput, LPWSTR lpBuffer, DWORD nChars,
                #                           LPDWORD lpCharsWritten, LPVOID lpReserved);

                WriteConsoleW = WINFUNCTYPE(BOOL, HANDLE, LPWSTR, DWORD, POINTER(DWORD), LPVOID)(("WriteConsoleW", windll.kernel32))

                class UnicodeOutput:
                    def __init__(self, hConsole, stream, fileno, name):
                        self._hConsole = hConsole
                        self._stream = stream
                        self._fileno = fileno
                        self.closed = False
                        self.softspace = False
                        self.mode = 'w'
                        self.encoding = 'utf-8'
                        self.name = name
                        self.flush()

                    def isatty(self):
                        return False

                    def close(self):
                        # don't really close the handle, that would only cause problems
                        self.closed = True

                    def fileno(self):
                        return self._fileno

                    def flush(self):
                        if self._hConsole is None:
                            try:
                                self._stream.flush()
                            except Exception as e:
                                _complain("%s.flush: %r from %r" % (self.name, e, self._stream))
                                raise

                    def write(self, text):
                        try:
                            if self._hConsole is None:
                                if isinstance(text, unicode):
                                    text = text.encode('utf-8')
                                self._stream.write(text)
                            else:
                                if not isinstance(text, unicode):
                                    text = str(text).decode('utf-8')
                                remaining = len(text)
                                while remaining:
                                    n = DWORD(0)
                                    # There is a shorter-than-documented limitation on the
                                    # length of the string passed to WriteConsoleW (see
                                    # <http://tahoe-lafs.org/trac/tahoe-lafs/ticket/1232>.
                                    retval = WriteConsoleW(self._hConsole, text, min(remaining, 10000), byref(n), None)
                                    if retval == 0 or n.value == 0:
                                        raise IOError("WriteConsoleW returned %r, n.value = %r" % (retval, n.value))
                                    remaining -= n.value
                                    if not remaining:
                                        break
                                    text = text[n.value:]
                        except Exception as e:
                            _complain("%s.write: %r" % (self.name, e))
                            raise

                    def writelines(self, lines):
                        try:
                            for line in lines:
                                self.write(line)
                        except Exception as e:
                            _complain("%s.writelines: %r" % (self.name, e))
                            raise

                if real_stdout:
                    sys.stdout = UnicodeOutput(hStdout, None, STDOUT_FILENO, '<Unicode console stdout>')
                else:
                    sys.stdout = UnicodeOutput(None, sys.stdout, old_stdout_fileno, '<Unicode redirected stdout>')

                if real_stderr:
                    sys.stderr = UnicodeOutput(hStderr, None, STDERR_FILENO, '<Unicode console stderr>')
                else:
                    sys.stderr = UnicodeOutput(None, sys.stderr, old_stderr_fileno, '<Unicode redirected stderr>')
        except Exception as e:
            _complain("exception %r while fixing up sys.stdout and sys.stderr" % (e,))

        # While we're at it, let's unmangle the command-line arguments:

        # This works around <http://bugs.python.org/issue2128>.
        GetCommandLineW = WINFUNCTYPE(LPWSTR)(("GetCommandLineW", windll.kernel32))
        CommandLineToArgvW = WINFUNCTYPE(POINTER(LPWSTR), LPCWSTR, POINTER(c_int))(("CommandLineToArgvW", windll.shell32))

        argc = c_int(0)
        argv_unicode = CommandLineToArgvW(GetCommandLineW(), byref(argc))
        argv = [argv_unicode[i].encode('utf-8') for i in xrange(0, argc.value)]

        if not hasattr(sys, 'frozen'):
            # If this is an executable produced by py2exe or bbfreeze, then it will
            # have been invoked directly. Otherwise, unicode_argv[0] is the Python
            # interpreter, so skip that.
            argv = argv[1:]

            # Also skip option arguments to the Python interpreter.
            while len(argv) > 0:
                arg = argv[0]
                if not arg.startswith(u"-") or arg == u"-":
                    break
                argv = argv[1:]
                if arg == u'-m':
                    # sys.argv[0] should really be the absolute path of the module source,
                    # but never mind
                    break
                if arg == u'-c':
                    argv[0] = u'-c'
                    break

        sys.argv = argv


class LoggableTestCase(TestCase):
    '''
    Test case that initializes console logging properly.
    '''
    def setUp(self):
        configConsoleLogging()


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


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    _log.info('running doctest')
    import doctest
    doctest.testmod()
