import random 

class Player:
    """
    class Player:
    A class to represent a player in the game.

    ...

    Attributes
    ----------
    name : str
        name of the person.
    level : int
        level of the player.
    hp : int
        hp of the player
    dmg : int
        dmg of the player
    critDmg : int
        Critical damage modifier of the player.
    critChance : int
        Critical hit chance of the player.

    Methods
    -------
    describe():
        Describes the player's name, level, hp, and damage.
    takeDamage():
        Triggered when the player takes damage from environmental triggers.  
    levelUp():
        Increases the player's level along with increasing hp and dmg.
    obtainItem(item):
        Adds an item to the player's inventory. Must be in a dictionary format 
        and reference OTHER FUNCTION here for more details.
    MORE TO TRULY ADD HERE!!!!


    """

    inventory = {}

    following = {}
    
    expToLevel = [0, 200, 500, 900, 1400, 2000, 2700, 3500, 4400, 5400, 6500, 7700, 9000, 10400, 11900]

    levelsAttained = []

    equipment = {}

    def __init__(self, name, level, hp, dmg, critDmg=1.25, critChance=100, exp=0, gp=0):
        self.name = name
        self.level = level
        self.hp = hp
        self.dmg = dmg
        self.critDmg = critDmg  # 1 is default
        self.critChance = critChance  # 100% default
        self.exp = exp
        self.maxHP = hp
        self.gp = gp

    def __str__(self):
        return (f"{self.name} is a level {self.level} character with {self.hp} that does {self.dmg} damage")

    def takeDamage(self):
        currentHP = self.hp
        print(f"{self.name} took xxx damage! Down to xxx hp! Current HP is {currentHP}")

    def levelUp(self):
        self.level += 1
        self.maxHP += random.randint(0, 11)
        self.hp += random.randint(0, 11)
        self.dmg += random.randint(0, 5)

    # def movementRestoreHP(self):
    #     self.hp += 0.1*self.maxHP

    def obtainItem(self, item):
        self.inventory.update(item)
        # for ease of addition

    def checkInv(self):
        print(self.inventory)

    def checkEquipped(self):
        ### Double check that only so much of certain types of equipment is equippment.
        print(self.equipment)


    def equipItem(self):
        # iterator through items in inventory...
        for items in self.inventory:
            if self.level >= self.inventory[items]['level']:
                pass
        pass

    def maxHP(self):
        self.maxHP = self.hp

    def checkLevel(self):
        for i in range(0,15):
            if self.exp > self.expToLevel[i]:
                self.levelsAttained.append(i)
                if self.level < self.levelsAttained[-1]+1:
                    print(f"level {i+1}: True")
                    self.levelUp()
                    self.level = self.levelsAttained[-1]+1


class Enemy(Player):
    # Maybe fix this!
    def __init__(self, name, level, hp, dmg, critDmg=1.25, critChance=100, expWorth=500, gpWorth=10, maxHP=10, exp=0):
        self.name = name
        self.level = level
        self.hp = hp
        self.dmg = dmg
        self.critDmg = critDmg  # 1 is default
        self.critChance = critChance  # 100% default
        self.expWorth = expWorth
        self.gpWorth = gpWorth
        self.maxHP = maxHP
        self.exp = exp
    
    def levelUp(self):
        self.level += 1
        self.maxHP += random.randint(0, 11)
        self.hp += random.randint(0, 11)
        self.dmg += random.randint(0, 5)
        self.expWorth += 50
        self.gpWorth += 25

    def supriseAttack(self, name, dmg):
        print(f"{self.name} got to you first!")

    def regenHP(self):
        self.hp = self.maxHP

# Kinda think about player classes?

class Mage(Player):    
    
    ableToCast = []
    skills = {'fireball': {'level': 1, 'MPCost': 3, "Damage": 12},
              'gust': {'level': 5, 'MPCost': 6, "Damage": 22},
              'blizzard': {'level': 10, 'MPCost': 10, "Damage": 30}}

    
    def __init__(self, name, level, hp, mp, dmg, critDmg=1.25, critChance=100, exp=0):
        # not sure if this super init is needed...
        super().__init__(name, level, hp, dmg, critDmg=1.25, critChance=100)
        self.mp = mp
        self.maxHP = hp
        self.maxMP = mp

    def magicAttack(self, player, enemy):
        print(f"{self.name} did ")

    def checkMP(self):
        return self.mp

    def __str__ (self):
        return (f"{self.name} is a level {self.level} character with {self.hp} hp and {self.mp} mp that does {self.dmg} damage")

    def levelUp(self):
        self.level += 1
        self.maxHP += random.randint(0, 6)
        self.hp += random.randint(0, 6)
        self.dmg += random.randint(0, 5)
        self.maxMP += random.randint(0, 6)
        self.mp += random.randint(0, 6)

#     def chooseSpell(self):
#         if isinstance(self, Mage):
#             checkSpellLevels(self)
#             print("You a mage boo")
#             # Check level for spell availability
#             level = self.level
#             for ability in self.skills:
#                 levelReq = self.skills[ability]['level']
# #                 print(f"{list(self.skills)[ability]} has a levelReq of {levelReq}")
#     #             if mage.level >= levelReq:
#     #                 print("okay to cast!")
#         else:
#             print("You don't have spells!")

    def checkSpellLevels(self):
        # print("You a mage boo")
        skills = self.skills
        for ability in self.skills:
            # print(f"{ability} has a level requirement of {skills[ability]['level']} ")
            levelReq = skills[ability]['level']
            if self.level >= levelReq:
                # print(f"okay to cast {ability}!")
                if f"{ability}" not in self.ableToCast:
                    self.ableToCast.append(ability)
        return self.ableToCast
        
    def chooseSpell(self, spell):
        if spell in self.ableToCast:
            # print("Can cast!")
            return True

    # include mana in their stats!
    # Include spells at certain levels?
        # like fireball at level 1, gust at level 5, blizzard at level 10?
        # Blizzard something to make enemy have a chance to get frozen and lose a turn?

    def maxMP(self):
        self.maxMP = self.mp

