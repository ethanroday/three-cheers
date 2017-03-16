'''
A module containing a variety of utility functions in a single location.
'''

import os
import json
import glob


def debug(func, args, dbg):
    """Wrap a function call with an additional debug argument, which is some string to be printed.
    Useful when calling when calling functions from list comprehensions, lambda expressions, etc.
    Attempts to print debug, then returns the result of calling func with arguments args (must be
    passed as a list).
    Example: Assume we have a list l = [1,2,3,4]. Then debug(sum, [l], len(l)) will print 4 and
    return 10."""

    print(dbg)
    return func(*args)


def makeFilename(filepath, filename, ext):
    """Create a filename from a path, basename, and extension."""
    if ext[0] != '.':
        ext = "." + ext
    return os.path.join(filepath, str(filename) + ext)


def makeJSONFilename(filepath, filename):
    """Create a JSON filename from a path and basename."""
    return makeFilename(filepath, filename, "json")


def getText(filename, encoding='latin1'):
    """Get the raw text of a file with an optionally specified encoding."""
    with open(filename, 'r', encoding=encoding) as file:
        return file.read()


def getJSON(filename, encoding='latin1'):
    """Given a JSON filename, load the contents of that file into a dictionary.
    Optionally, specify an encoding."""
    with open(filename, 'r', encoding=encoding) as file:
        return json.load(file)


def writeJSON(data, filename):
    """Given a dictionary and a filename, write that dictionary to the filename as JSON."""
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def getFilenames(directory, ext=None):
    """Return an iterable of the files in a given directory. If ext is specified, returns
    only those files with the extension ext."""
    ext = "*" if ext is None else ext
    return glob.glob(os.path.normpath(directory) + "/*." + ext)


def getBaseFilename(filepath, stripExt=True):
    """Return the basename of a file given its full path. If stripExt is true, also
    strip the extension."""
    return os.path.basename(filepath).split('.')[0] if stripExt else os.path.basename(filepath)
