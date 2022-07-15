# import dependencies
import random
from customErrors import ItemError  # custom errors python file I made
from classes.classes import *
from game_logic.core import *
from maps.beginner_map import G
import networkx as nx
# Lets start this project!

# Condition for the game
isCharacterAlive = True
movePath = [] # global for allowance of storage of movePath 
initPos = 'A0' # initial start of map
movePath.append(initPos)
ableToCast = [] # For mages to be able to cast. See chooseSpell()

# Should wrap the above into a class and export to an external file?




# THINK EVENTUALLY HOW TO SEPARATE THIS ALL!


# Lets instantiate a test character
# Kollin = Player("Kollin", 1, 100, 50, critDmg=1.25)
# Kollin.describe()
# Kollin.takeDamage()
# Alex = Enemy("Alex", 1, 70, 7)
# Kennedy = Mage("Kennedy", 1, 80, 15, 50, critDmg=1.25)
# dealDamage(Kollin, Alex)
# Alex.describe()

# start_battle(Kennedy, Alex)

# print("Now we dead...")


# print(playerFollowing[0]['level'])


# Still need to add exp, levels, and gold currency for shops!

# Start the game!
# Initialize the character needs to be alive!
print("Woot, we in the game!")
# classChoices = ["Player", "Mage"]
# playerClass = input('Are you going to be a Player or a Mage?: ')
# while playerClass not in classChoices:
#     print("Please reselect your class!")
#     playerClass = input('Are you going to be a Player or a Mage?: ')
# playerName = input("What is your character's name?: ")
# print(f"{playerName} is a {playerClass}")
# if playerClass == "Player":
#     exec(f"myCharacter = {playerClass}('{playerName}', 1, 100, 50, critDmg=125)")
# elif playerClass == "Mage":
#     exec(f"myCharacter = {playerClass}('{playerName}', 1, 100, 15, 50, critDmg=125)")

# # Start playing loop
while isCharacterAlive == True:
# Character is initialized now from above. Now we need to start the movement.
    promptMovement()
# # enemyDmg(Alex, myCharacter)

# print(myCharacter)
# print(myCharacter.level)
# print(f"{myCharacter.hp}, {myCharacter.mp}")
# myCharacter.levelUp
# print(myCharacter.level)
# print(f"{myCharacter.hp}/{myCharacter.maxHP}; {myCharacter.mp}/{myCharacter.maxMP}")
# print(myCharacter.exp)
# print(myCharacter.level)
# print(f"{myCharacter.hp}/{myCharacter.maxHP}; {myCharacter.mp}/{myCharacter.maxMP}")
# myCharacter.exp += 200
# myCharacter.checkLevel()
# print(myCharacter.exp)
# print(myCharacter.level)

# myCharacter.checkLevel()

# print(myCharacter.exp)
# print(myCharacter.level)

# print(myCharacter)
# print(f"{myCharacter.hp}/{myCharacter.maxHP}; {myCharacter.mp}/{myCharacter.maxMP}")

