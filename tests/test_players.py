# test_players.py

from game_logic.core import *
from maps.beginner_map import *

Kollin = Player("Kollin", 1, 100, 50, critDmg=1.25)
Alex = Enemy("Alex", 1, 70, 7)
Kennedy = Mage("Kennedy", 1, 80, 15, 50, critDmg=1.25)
# dealDamage(Kollin, Alex)
print(Kollin.level)

while isCharacterAlive == True:
    print("Woot, we in the game!")
    isCharacterAlive = False

start_battle(Kennedy, Alex)

def test_movement():
    movePath = [] # global for allowance of storage of movePath 
    initPos = 'A0' # initial start of map
    movePath.append(initPos)
    promptMovement()
