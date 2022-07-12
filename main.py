# import dependencies
import random
from customErrors import ItemError  # custom errors python file I made

# Lets start this project!

# Condition for the game
isCharacterAlive = True
movePath = [] # global for allowance of storage of movePath 
initPos = 'A0' # initial start of map
movePath.append(initPos)
ableToCast = [] # For mages to be able to cast. See chooseSpell()


# Some starting parameters for the adventurer
# playerHP = 100
# playerDmg = 10
# playerGold = 0
# playerLevel = 1
# playerFollowing = [{'name': 'Adventure', 'level': playerLevel}]
# playerInventory = {}


# Should wrap the above into a class and export to an external file?


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

    def __init__(self, name, level, hp, dmg, critDmg=1.25, critChance=100, exp=0):
        self.name = name
        self.level = level
        self.hp = hp
        self.dmg = dmg
        self.critDmg = critDmg  # 1 is default
        self.critChance = critChance  # 100% default
        self.exp = exp

    def describe(self):
        print(
            f"{self.name} is a level {self.level} character with {self.hp} that does {self.dmg} damage")

    def takeDamage(self):
        currentHP = self.hp
        print(f"{self.name} took xxx damage! Down to xxx hp! Current HP is {currentHP}")

    def levelUp(self):
        self.level += 1
        self.hp += random.randint(0, 11)
        self.dmg += random.randint(0, 5)

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
    
    ableToCast = []
    skills = {'fireball': {'level': 1, 'MPCost': 3, "Damage": 12},
              'gust': {'level': 5, 'MPCost': 6, "Damage": 22},
              'blizzard': {'level': 10, 'MPCost': 10, "Damage": 30}}

    
    def __init__(self, name, level, hp, mp, dmg, critDmg=1.25, critChance=100, exp=0):
        # not sure if this super init is needed...
        super().__init__(name, level, hp, dmg, critDmg=1.25, critChance=100)
        self.mp = mp

    def magicAttack(self, player, enemy):
        print(f"{self.name} did ")

    def checkMP(self):
        return self.mp

    def describe(self):
        print(f"{self.name} is a level {self.level} character with {self.hp} hp and {self.mp} mp that does {self.dmg} damage")

    def levelUp(self):
        self.level += 1
        self.hp += random.randint(0, 6)
        self.dmg += random.randint(0, 5)
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
        print("You a mage boo")
        skills = self.skills
        for ability in self.skills:
            print(f"{ability} has a level requirement of {skills[ability]['level']} ")
            levelReq = skills[ability]['level']
            if self.level >= levelReq:
                print(f"okay to cast {ability}!")
                if f"{ability}" not in self.ableToCast:
                    self.ableToCast.append(ability)
        return self.ableToCast
        
    def chooseSpell(self, spell):
        if spell in self.ableToCast:
            print("Can cast!")
            return True

    # include mana in their stats!
    # Include spells at certain levels?
        # like fireball at level 1, gust at level 5, blizzard at level 10?
        # Blizzard something to make enemy have a chance to get frozen and lose a turn?




# Some actions that can be carried out
def roll():
    global decider
    decider = int(random.random()*100)
    return decider


def determineBattleOrder(player, enemy):
    roll()
    global turn_order
    turn_order = []
    if decider > 50:
        # print(decider)
        print("You go first!")
        turn_order = [player, enemy]
        print(f"[{turn_order[0].name}, {turn_order[1].name}]")
        return turn_order
    else:
        # print(decider)
        print("Enemy goes first!")
        turn_order = [enemy, player]
        print(f"[{turn_order[0].name}, {turn_order[1].name}]")
        return turn_order


def initCombat(player, enemy):
    # If we go first
    if turn_order[0] == player:
        print("Hell yes!")
        print("This from initCombat()")

    # If enemy goes first
    elif turn_order[0] == enemy:
        print("You too slow!")
        print("This from initCombat()")


def start_battle(player, enemy):
    """
    Takes two entities (typically an instance of Player and Enemy) and initiates and carries out the combat phase
    """
    # determine turn order
    determineBattleOrder(player, enemy)

    # check turn order and then initiate combat
    initCombat(player, enemy)

    # Decide Combat Logic!
    bothAlive = True
    # battle shit...
    while bothAlive == True:
        battling(player, enemy)

        if player.hp <= 0:
            print(f"{player.name} has died!")
            bothAlive = False
            # elif action == "magic":
            #    Magic(player, enemy)
            # elif action == "escape"
            #     escape(player)
        elif enemy.hp <= 0:
            print(f"{player.name} has killed {enemy.name}")
            print(f"Remaining HP {player.hp}")
            bothAlive = False

    # Transition back to moving interaction! How to do so? Need to create a function!
    print("We get to transition back to moving!")

    # go back to traversing the map!!!

    # bothAlive = False

    # start combat
    # print(decider)
    # roll()


def battling(player, enemy):
    """
    Takes two instances (typically an instance of Player and Enemy) and carries out the logic of the combat phase
    """
    # First calculate difference in damage from enemy levels
    # print(f"The turn order is [{turn_order[0].name}, {turn_order[1].name}]")
    # print(f"[{turn_order[0].name}, {turn_order[1].name}]")
    
    # if Mage class
    if isinstance(player, Mage):
        # You go first/next
        if turn_order[0] == player:
            action = input("What action would you like to do? \n 0)'attack' \n 1)'magic' \n ")
            if action == 'attack' or action == str(0):
                dealDamage(player, enemy)
                print(enemy.hp)
                turn_order.reverse()
                print(f"The turn order is [{turn_order[0].name}, {turn_order[1].name}]")
            elif action == 'magic' or action == str(1):
                dealMagicDamage(player, enemy)
                print(enemy.hp)
                print(f"remaining mp {player.mp}")
                turn_order.reverse()
                print(f"The turn order is [{turn_order[0].name}, {turn_order[1].name}]")
        # Enemy goes first/next
        elif turn_order[0] == enemy:
            enemyDmg(enemy, player)
            turn_order.reverse()
            print(
                f"The turn order is [{turn_order[0].name}, {turn_order[1].name}]")
    # if Player base class
    else:
        if turn_order[0] == player:
            action = input("What action would you like to do? \n 0)'attack' \n ")
            if action == "attack":
                dealDamage(player, enemy)
                print(enemy.hp)
                turn_order.reverse()
                print(f"The turn order is [{turn_order[0].name}, {turn_order[1].name}]")

            elif turn_order[0] == enemy:
                enemyDmg(enemy, player)
                turn_order.reverse()
                print(f"The turn order is [{turn_order[0].name}, {turn_order[1].name}]")


def dealDamage(player, enemy):
    """
    Functions takes an instance of a Player and Enemy and deals with the logic behind crits or weak hits.
    """
    # Determine hp and figure out damage dealt!

    # roll() # I don't think this is needed...

    # Roll for Crit Hit Chance
    if roll() > 80:
        print("Critical Hit!")
        enemy.hp = enemy.hp - player.dmg*player.critDmg
        # not sure if this works...
        print(
            f"{player.name} hit {enemy.name} for {player.dmg*player.critDmg}. Health remaining: {enemy.hp}")
    elif roll() < 80 and roll() > 20:
        enemy.hp = enemy.hp - player.dmg
        print(
            f"{player.name} hit {enemy.name} for {player.dmg}. Health remaining: {enemy.hp}")
    else:
        print("Swing a lil harder!")
        enemy.hp = enemy.hp - player.dmg * 0.75
        print(
            f"{player.name} hit {enemy.name} for {player.dmg*0.75}. Health remaining: {enemy.hp}")

def chooseSpell(player):
    skills = {'fireball': {'level': 1, 'MPCost': 3, "Damage": 12},
              'gust': {'level': 5, 'MPCost': 6, "Damage": 22}}
    # Check level for spell availability
    level = player.level
    for ability in skills:
        levelReq = skills[ability]['level']
        print(levelReq)
        if player.level >= levelReq:
            print("okay to cast!")


def dealMagicDamage(player, enemy):
    """
    Takes an instance of Player(Mage subclass) and Enemy and deals with the combat logic for the Mage class.
    """
    # Determine hp and figure out damage dealt!
    if isinstance(player, Mage):
        mp = player.mp
        player.checkSpellLevels()
        for idx, spell in enumerate(player.ableToCast):
            if player.mp >= player.skills[spell]['MPCost']:
                print(f"{idx}) {spell} MPCost: {player.skills[spell]['MPCost']}")
        print("3) attack")
        spell = input("Which spell would you like to cast?")
        if spell == "fireball" or spell == str(0):
            if player.mp >= player.skills['fireball']['MPCost']:
            # Roll for Crit Hit Chance
                if roll() > 80:
                    print("Critical Hit!")
                    enemy.hp = enemy.hp - player.skills['fireball']['Damage']*player.critDmg
                    player.mp -= player.skills['fireball']['MPCost']
                    # not sure if this works...
                    print(f"{player.name} hit {enemy.name} for {player.skills['fireball']['Damage']}. Health remaining: {enemy.hp}")
                elif roll() < 80 and roll() > 20:
                    enemy.hp = enemy.hp - player.skills['fireball']['Damage']
                    player.mp -= player.skills['fireball']['MPCost']
                    print(f"{player.name} hit {enemy.name} for {player.skills['fireball']['Damage']}. Health remaining: {enemy.hp}")
                else:
                    print("Swing a lil harder!")
                    enemy.hp = enemy.hp - player.skills['fireball']['Damage'] * 0.75
                    player.mp -= player.skills['fireball']['MPCost']
                    print(f"{player.name} hit {enemy.name} for {player.skills['fireball']['Damage']}. Health remaining: {enemy.hp}")
        
        elif spell == 'gust' or spell == str(1):
            if player.mp >= player.skills['gust']['MPCost']:
                # Roll for Crit Hit Chance
                if roll() > 80:
                    print("Critical Hit!")
                    enemy.hp = enemy.hp - player.skills['gust']['Damage']*player.critDmg
                    player.mp -= player.skills['gust']['MPCost']
                    # not sure if this works...
                    print(f"{player.name} hit {enemy.name} for {player.skills['gust']['Damage']}. Health remaining: {enemy.hp}")
                elif roll() < 80 and roll() > 20:
                    enemy.hp = enemy.hp - player.skills['gust']['Damage']
                    player.mp -= player.skills['gust']['MPCost']
                    print(f"{player.name} hit {enemy.name} for {player.skills['gust']['Damage']}. Health remaining: {enemy.hp}")
                else:
                    print("Swing a lil harder!")
                    enemy.hp = enemy.hp - player.skills['gust']['Damage'] * 0.75
                    player.mp -= player.skills['gust']['MPCost']
                    print(f"{player.name} hit {enemy.name} for {player.skills['gust']['Damage']}. Health remaining: {enemy.hp}")
        
        elif spell == 'blizzard' or spell == str(2):
            if player.mp >= player.skills['blizzard']['MPCost']:
                # Roll for Crit Hit Chance
                if roll() > 80:
                    print("Critical Hit!")
                    enemy.hp = enemy.hp - player.skills['blizzard']['Damage']*player.critDmg
                    player.mp -= player.skills['blizzard']['MPCost']
                    # not sure if this works...
                    print(f"{player.name} hit {enemy.name} for {player.skills['blizzard']['Damage']}. Health remaining: {enemy.hp}")
                elif roll() < 80 and roll() > 20:
                    enemy.hp = enemy.hp - player.skills['blizzard']['Damage']
                    player.mp -= player.skills['blizzard']['MPCost']
                    print(f"{player.name} hit {enemy.name} for {player.skills['blizzard']['Damage']}. Health remaining: {enemy.hp}")
                else:
                    print("Swing a lil harder!")
                    enemy.hp = enemy.hp - player.skills['blizzard']['Damage'] * 0.75
                    player.mp -= player.skills['blizzard']['MPCost']
                    print(f"{player.name} hit {enemy.name} for {player.skills['blizzard']['Damage']}. Health remaining: {enemy.hp}")
        if spell == 'attack' or spell == str(3):
            if roll() > 80:
                print("Critical Hit!")
                enemy.hp = enemy.hp - player.dmg*player.critDmg
                # not sure if this works...
                print(
                    f"{player.name} hit {enemy.name} for {player.dmg}. Health remaining: {enemy.hp}")
            elif roll() < 80 and roll() > 20:
                enemy.hp = enemy.hp - player.dmg
                print(
                    f"{player.name} hit {enemy.name} for {player.dmg}. Health remaining: {enemy.hp}")
            else:
                print("Swing a lil harder!")
                enemy.hp = enemy.hp - player.dmg * 0.75
                print(
                    f"{player.name} hit {enemy.name} for {player.dmg}. Health remaining: {enemy.hp}")
    else:
        print("Player is not a mage!")

def enemyDmg(enemy, player):
    player.hp = player.hp - enemy.dmg
    print(f"{enemy.name} hit {player.name} for {enemy.dmg}. Health remaining: {player.hp}")
    # roll into deal dealDamage and let the enemy also do critical damage!!!
    # maybe change enemy into opponent here? But enemy is the class name so it is easier to think about also... So, shrug?


def saveProgress():
    # writing to a file that can then have a loadProgress to load into current env...
    pass


def loadProgress():
    pass


def fishing():
    # Fishing skill? Time start then input in time less then? 20% chance not to catch? Idk
    # bigger if caught earlier??
    pass


def escape():
    # combat escape
    # think about breaking from the current loop of the battle and back to moving...
    # add a percent chance?
    pass


def addToInv(player, name, level, dmg, slot):
    if name in player.inventory:
        raise ItemError("There is already an item with that name!")
    if slot == 'w':
        player.obtainItem(
            {name: {'level': level, 'dmg': dmg, 'slot': 'weapon'}})
    elif slot == 'a':
        player.obtainItem(
            {name: {'level': level, 'dmg': dmg, 'slot': 'armor'}})
    elif slot == 's':
        player.obtainItem(
            {name: {'level': level, 'dmg': dmg, 'slot': 'shield'}})

def movement(dir):
    pass
    

def checkNeighbors(n1, n2):
    if n2 in G[n1]:
        return True
# Woot woot! This works right here! Works?
# then append this to nodeMove list then call a function that checks the label of the node moved to and if it one 
# of the labeled 'special' nodes have it trigger a event!!
def movement(n1,n2):
    if checkNeighbors(n1,n2): # check that it is true
        print(G[n1])
        print("YASSS") # just a print statement to see that it works...
        movePath.append(n2)
        return movePath # not sure if this'll wipe out the 'A1' or not....
    
def checkForEncounterNode(G): # do I need player, enemy in the params for this? hmm....
    encounterZones = nx.get_node_attributes(G, "encounterArea")
    for i in range(0, G.size()):
        if f"A{i}" in encounterZones.keys():
            print(f"['A{i}']", "nodes")
            
def checkForBattle(player, enemy):    
    roll()
    if decider > 70: # 30% chance to start combat on any node there is an encounter zone...
        start_battle(player, enemy) # 30% chance to start combat! 
            # think of how to get the (player, enemy) here...
    else:
        pass
    
def cycleNodeTypes(G, player, enemy):
    nodeTypes = ['encounterArea', 'cityArea', 'shopArea', 'fishingArea']
    zoneTypes = ['encounterZones', 'cityZones', 'shopZones', 'fishingZones']
    for i in range(0,4):
        zoneTypes[i] = nx.get_node_attributes(G, nodeTypes[i]) # get zone of node label
    for j in range(0, G.size()): # iterate over the size of the graph
        if f"A{j}" in movePath[-1]:
            if movePath[-1] in list(zoneTypes[0].keys()) and movePath[-1] == f'A{j}':
    #           print("This is encounter")
                print(f"this is {list(zoneTypes[0].values())[0]}")
            elif movePath[-1] in list(zoneTypes[1].keys()) and movePath[-1] == f'A{j}':
    #             print("You are in the city!")
                print(f"this is {list(zoneTypes[1].values())[0]}")
                print(f"This is A{j}")
            elif movePath[-1] in list(zoneTypes[2].keys()) and movePath[-1] == f'A{j}':
                print("Feel free to shop around!")
                print("ADD IN SHOP FEATURE!")
                print(f"this is {list(zoneTypes[2].values())[0]}")
            elif movePath[-1] in list(zoneTypes[3].keys()) and movePath[-1] == f'A{j}':
                print("Drop a line and relax, it's fishing time!")# Think how to chain these functions together... wtf?
                print(f"this is {list(zoneTypes[3].values())[0]}")# Maybe over thinking this logic... Maybe separate them?

# Then can combine these into a logic loop!

# while on an encounter zone we can check for encounter node then check for battle condition?
# then when we leave the encounter nodes we just switch it to false? Hmm?

# then make a similar scanning for while in town and let it scan for each location? Generalize encounterZones
# to be a parameter that we can also do cities with? Hmm?
# specific nodes for certain implications in towns?

# maybe make a list of particular areas? encounterArea, cityArea, etc... 
# if in some particular one like if it is encounterArea we will trigger checkForBattle and shizz...
# cityArea we will see if in there and also on a shop tile to be able to buy from a shop?
# think about a currency from monsters... like create a gold gain from when battle ends?

def promptMovement():
    if len(list(G[movePath[-1]])) == 1:
        print(f"current location: {movePath[-1]} \n 0) {list(G[movePath[-1]])[0]}")
        choice = input("Where do you want to move?")
        if choice == "0":
            movement(movePath[-1], list(G[movePath[-1]])[0])
        else:
            print("not a valid choice, please reselect")
    elif len(list(G[movePath[-1]])) == 2:
        print(f"current location: {movePath[-1]} \n 0) {list(G[movePath[-1]])[0]} \n 1) {list(G[movePath[-1]])[1]}")
        choice = input("Where do you want to move?")
        if choice == "0":
            movement(movePath[-1], list(G[movePath[-1]])[0])
        elif choice == "1":
#             print((movePath[-1], list(G[movePath[-1]])[1]))
            movement(movePath[-1], list(G[movePath[-1]])[1])
        else:
            print("not a valid choice, please reselect")
    elif len(list(G[movePath[-1]])) == 3:
        print(f"current location: {movePath[-1]} \n 0) {list(G[movePath[-1]])[0]} \n 1) {list(G[movePath[-1]])[1]} \n 2) {list(G[movePath[-1]])[2]}")
        choice = input("Where do you want to move?")
        if choice == "0":
            movement(movePath[-1], list(G[movePath[-1]])[0])
        elif choice == "1":
            movement(movePath[-1], list(G[movePath[-1]])[1])
        elif choice == "2":
            movement(movePath[-1], list(G[movePath[-1]])[2])
        else:
            print("not a valid choice, please reselect")
    elif len(list(G[movePath[-1]])) == 4:
        print(f"current location: {movePath[-1]} \n 0) {list(G[movePath[-1]])[0]} \n 1) {list(G[movePath[-1]])[1]} \n 2) {list(G[movePath[-1]])[2]} \n 3) {list(G[movePath[-1]])[3]}")
        choice = input("Where do you want to move?")
        if choice == "0":
            movement(movePath[-1], list(G[movePath[-1]])[0])
        elif choice == "1":
            movement(movePath[-1], list(G[movePath[-1]])[1])
        elif choice == "2":
            movement(movePath[-1], list(G[movePath[-1]])[2])
        elif choice == "3":
            movement(movePath[-1], list(G[movePath[-1]])[3])
        else:
            print("not a valid choice, please reselect")
    elif len(list(G[movePath[-1]])) == 5:
        print(f"current location: {movePath[-1]} \n 0) {list(G[movePath[-1]])[0]} \n 1) {list(G[movePath[-1]])[1]} \n 2) {list(G[movePath[-1]])[2]} \n 3) {list(G[movePath[-1]])[3]} \n 4) {list(G[movePath[-1]])[4]}")
        choice = input("Where do you want to move?")
        if choice == "0":
            movement(movePath[-1], list(G[movePath[-1]])[0])
        elif choice == "1":
            movement(movePath[-1], list(G[movePath[-1]])[1])
        elif choice == "2":
            movement(movePath[-1], list(G[movePath[-1]])[2])
        elif choice == "3":
            movement(movePath[-1], list(G[movePath[-1]])[3])
        elif choice == "4":
            movement(movePath[-1], list(G[movePath[-1]])[4])
        else:
            print("not a valid choice, please reselect")


# THINK EVENTUALLY HOW TO SEPARATE THIS ALL!


# Lets instantiate a test character
Kollin = Player("Kollin", 1, 100, 50, critDmg=1.25)
Kollin.describe()
Kollin.takeDamage()
Alex = Enemy("Alex", 1, 70, 7)
Kennedy = Mage("Kennedy", 1, 80, 15, 50, critDmg=1.25)
# dealDamage(Kollin, Alex)
Alex.describe()
while isCharacterAlive == True:
    print("Woot, we in the game!")
    isCharacterAlive = False

start_battle(Kennedy, Alex)

print("Now we dead...")
# print(playerFollowing[0]['level'])


# Still need to add exp, levels, and gold currency for shops!