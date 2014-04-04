"""
Exceptions for the package go here

"""

class Error(Exception):
    pass

class OpenidResolutionError(Error):
    pass

class DuplicateHashError(Error):
    pass
