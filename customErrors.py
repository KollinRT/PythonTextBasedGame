# Need to create a custom error by inheriting Error class
class Error(Exception):  # Need to inherit base class of exceptions for this to work
    """Base class for other exceptions"""
    pass


class ItemError(Error):
    """Raised when the Item key already exists in player inventory dictionarycc"""
    pass
