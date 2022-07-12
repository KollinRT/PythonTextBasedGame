

class Player:
    
    inventory = {}
    
    following = {}
    
    def __init__(self, name, level, hp, dmg, critDmg=1.25, critChance=100):
        self.name = name
        self.level = level
        self.hp = hp
        self.dmg = dmg
        self.critDmg = critDmg # 1 is default
        self.critChance = critChance # 100% default
        
    def describe(self):
        print(f"{self.name} is a level {self.level} character with {self.hp} that does {self.dmg} damage")

    def takeDamage(self):
        currentHP = self.hp
        print(f"{self.name} took xxx damage! Down to xxx hp! Current HP is {currentHP}")
    
    def levelUp(self):
        self.level += 1
        self.hp += random.randint(0,11)
        self.dmg += random.randint(0,5)
        
    def obtainItem(self, item):
        self.inventory.update(item)
        # for ease of addition
        
    def checkInv(self):
        return self.inventory
    
    def equipItem(self):
        # iterator through items in inventory...
        for items in self.inventory:
            if self.level >= self.inventory[item]['level']:
                pass
        pass
        
Kollin = Player("Kollin", 1, 100, 50, critDmg=1.25)
# Kollin.describe()

Kollin.obtainItem({ 'Sword': {'level': 1, 'dmg': 12, 'slot': 'weapon'}})
Kollin.obtainItem({'Rod': {'level': 1, 'dmg': 22, 'slot': 'weapon'}})
# print(Kollin.checkInv())

# { 'Sword': {'level': 1, 'Damage': 12}, 'Rod': {'level': 1, 'Damage': 22}}

# print(Kollin.inventory['Sword']['level'])

# Way to cycle through items for level requirements
def cycleInv(player):
    for item in player.checkInv():
        print(player.inventory[item]['slot'])
        # return player.inventory[item]['dmg']
        
#def addToInv(player, item):
    # (name, level, dmg, slot)
 #   player.obtainItem(item):
     #   item = {name : {'level': level, 'dmg': dmg, 'slot': slot}}
        
        
#def addToInv(player, item):
    # (name, level, dmg, slot)
        #player.obtainItem(item):
     #   item = {name : {'level': level, 'dmg': dmg, 'slot': slot}}

# Need to create a custom error by inheriting Error class
class Error(Exception): # Need to inherit base class of exceptions for this to work
    """Base class for other exceptions"""
    pass
    
class ItemError(Error):
    """Raised when the Item key already exists in player inventory dictionarycc"""
    pass        

def addToInv(player, name, level, dmg, slot):
    if name in player.inventory:
        raise ItemError("There is already an item with that name!")
    if slot == 'w':
        player.obtainItem({name: {'level': level, 'dmg': dmg, 'slot': 'weapon'}})
    elif slot == 'a':
        player.obtainItem({name: {'level': level, 'dmg': dmg, 'slot': 'armor'}})   
    elif slot == 's':
        player.obtainItem({name: {'level': level, 'dmg': dmg, 'slot': 'shield'}})
   

             
    
