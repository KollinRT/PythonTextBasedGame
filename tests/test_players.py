# test_players.py
import pytest
from game_logic.core import *
from maps.beginner_map import *
from classes.items import HealingItems

# myPlayer = Player("Kollin", 1, 100, 50, critDmg=1.25)
# Alex = Enemy("Alex", 1, 70, 7)
# myplayer2 = Mage("Kennedy", 1, 80, 15, 50, critDmg=1.25)
# # dealDamage(myPlayer, Alex)
# print(myPlayer.level)

# while isCharacterAlive == True:
#     print("Woot, we in the game!")
#     isCharacterAlive = False

# start_battle(myplayer2, Alex)

# def test_movement():
#     movePath = [] # global for allowance of storage of movePath 
        
#     # Override the Python built-in input method 
#     monkeypatch.setattr('sys.stdin', '0')

#     initPos = 'A0' # initial start of map
#     movePath.append(initPos)
#     promptMovement()

#     assert movePath[-1] != 'A0'
    

def test_inventory_add():
    myplayer = Player("player", 1, 10, 5)
    currentInv = myplayer.inventory
    myplayer.obtainItem()



    # def obtainItem(self, item):
    #     self.inventory.update(item)
    #     # for ease of addition

    # def checkInv(self):
    #     return self.inventory


def test_healingPot():
    HPPot = HealingItems(25, 0)
    myplayer = Player("player", 1, 10, 5)
    playerHP = myplayer.hp
    HPPot.healPlayer(myplayer)
    postPotHP = myplayer.hp

    assert playerHP + HPPot.HPrest == postPotHP

def test_MPPot():
    MPPot = HealingItems(0, 25)
    mymage = Mage("mage", 1, 10, 15, 5)
    playerMP = mymage.mp
    MPPot.healPlayer(mymage)
    postPotMP = mymage.mp

    assert playerMP + MPPot.MPrest == postPotMP

