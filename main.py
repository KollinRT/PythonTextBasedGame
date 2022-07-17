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

if __name__ == "__main__":
    startGame()
    # Start playing loop
    while isCharacterAlive == True:
    # Character is initialized now from above. Now we need to start the movement.
        promptMovement()
    # enemyDmg(Alex, myCharacter)
