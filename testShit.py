# Online Python compiler (interpreter) to run Python online.
# Write Python 3 code in this online editor and run it.
# skills = { 'fireball': {'level': 1, 'MPCost': 3, "Damage": 12}, 'gust': {'level': 5, 'MPCost': 6, "Damage": 22}}

# print(skills[fireball.level)
# test = ['fireball', 'gust']
# for ability in test:
#    print(ability)
#    print(skills[ability])
# print(skills['fireball']['level'])
# print(skills['gust'])

# for ability in skills:
#    print(skills[ability]['level'])
# print(skills['fireball']['level'])

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
                
                                       
class Enemy(Player):
    def supriseAttack(self, name, dmg):
        print(f"{self.name} got to you first!")   
    
# Kinda think about player classes?
class Mage(Player):
    def __init__(self, name, level, hp, mp, dmg, critDmg=1.25, critChance=100):
        super().__init__(name, level, hp, dmg, critDmg=1.25, critChance=100)
        self.mp = mp

    def magicAttack(self, player, enemy):
        print(f"{self.name} did ")

    def checkMP(self):
        return self.mp
    
    def describe(self):
        print(f"{self.name} is a level {self.level} character with {self.hp} hp and {self.mp} mp that does {self.dmg} damage")

from main import chooseSpell
Kennedy = Mage("Kennedy", 1, 80, 15, 50, critDmg=1.25)

skills = { 'fireball': {'level': 1, 'MPCost': 3, "Damage": 12}, 'gust': {'level': 5, 'MPCost': 6, "Damage": 22}}
    # Check level for spell availability
level = Kennedy.level
for ability in skills:
    levelReq = skills[ability]['level']
    print(levelReq)
    if Kennedy.level >= chooseSpell:
        print("okay to cast!")
