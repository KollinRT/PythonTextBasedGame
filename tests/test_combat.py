import pytest
from classes.classes import Player, Enemy
from game_logic.core import dealDamage, roll

def test_roll():
    decider = roll()
    assert decider >= 0 and decider <= 100

def test_dealDamage():
    # Initialize Player and Enemy
    myCharacter = Player("player", 1, 100, 50, critDmg=125)
    enemy = Enemy("enemy", 1, 10, 5)

    # Get starting HP
    initHP = enemy.hp
    
    # call dealDamage fxn and update hp variable for enemy
    dealDamage(myCharacter, enemy)
    currHP = enemy.hp

    assert initHP != currHP # verify that enemy loses hp!

def test_deal():
    pass
