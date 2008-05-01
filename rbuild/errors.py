#
# Copyright (c) 2006-2008 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

"""
rBuild-specific errors.
"""
from conary.lib import util

# make ParseError available from here as well
# pylint: disable-msg=W0611
from conary.errors import ParseError

class InternalError(Exception):
    """
    B{C{InternalError}} - superclass for all errors that are not meant to be
    seen.

    Errors deriving from InternalError should never occur, but when they do
    they indicate a failure within the code to handle some unexpected case.
    """
    pass

class BaseError(Exception):
    """
    B{C{BaseError}} - superclass for all well-defined errors.

    If you create an error in rBuild, it should derive from this class,
    and have a str() that is acceptable output for the command line,
    with the string "C{error: }" prepended to it.

    Any relevant data for this error should be stored outside of the
    string so it can be accessed from non-command-line interfaces.
    """

class RbuildError(BaseError):
    """
    B{C{RbuildError}} - Internal rBuild errors

    This error may be raised directly only by rBuild internals,
    not by plugins.
    """
    pass

class BadParameters(BaseError):
    """
    Raised when a command is given bad parameters at the command line.
    """
    pass

#: error that is output when a Python exception makes it to the command 
#: line.
_ERROR_MESSAGE = '''
ERROR: An unexpected condition has occurred in rBuild.  This is
most likely due to insufficient handling of erroneous input, but
may be some other bug.  In either case, please report the error at
https://issues.rpath.com/ and attach to the issue the file
%(stackfile)s

To get a debug prompt, rerun the command with the --debug-all argument.

For more information, go to:
http://wiki.rpath.com/wiki/Conary:How_To_File_An_Effective_Bug_Report
For more debugging help, please go to #conary on freenode.net
or email conary-list@lists.rpath.com.

Error details follow:

%(filename)s:%(lineno)s
%(errtype)s: %(errmsg)s

The complete related traceback has been saved as %(stackfile)s
'''

def genExcepthook(*args, **kw):
    """
    Generates an exception handling hook that brings up a debugger.

    Example::
        sys.excepthook = genExceptHook(debugAll=True)
    """
    return util.genExcepthook(error=_ERROR_MESSAGE,
                              prefix='rbuild-error-', *args, **kw)

#pylint: disable-msg=C0103
# this shouldn't be upper case.
_uncatchableExceptions = (KeyboardInterrupt, SystemExit)
