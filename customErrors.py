# Need to create a custom error by inheriting Error class
class Error(Exception):  # Need to inherit base class of exceptions for this to work
    """Base class for other exceptions"""
    pass


class ItemError(Error):
    """Raised when the Item key already exists in player inventory dictionarycc"""
    pass

# look @ https://www.programiz.com/python-programming/user-defined-exception
# https://www.programiz.com/python-programming/user-defined-exception


# Need to create a custom error by inheriting Error class
# class Error(Exception): # Need to inherit base class of exceptions for this to work
#     """Base class for other exceptions"""
#     pass

# class ItemError(Error):
#     """Raised when the Item key already exists in player inventory dictionarycc"""
#     pass

# def addToInv(player, name, level, dmg, slot):
#     if name in player.inventory:
#         raise ItemError("There is already an item with that name!")
#     if slot == 'w':
#         player.obtainItem({name: {'level': level, 'dmg': dmg, 'slot': 'weapon'}})
#     elif slot == 'a':
#         player.obtainItem({name: {'level': level, 'dmg': dmg, 'slot': 'armor'}})
#     elif slot == 's':
#         player.obtainItem({name: {'level': level, 'dmg': dmg, 'slot': 'shield'}})
