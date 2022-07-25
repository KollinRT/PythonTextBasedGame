from customErrors import *
from classes.classes import *

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

# Initialize potion types
potionTypes = {'basicHPPot': {'level': 1, 'hp': 25, 'mp': 0}, 'basicMPPot': {'level': 1, 'hp': 0, 'mp': 25}, 'nextTierHPPots': {'level': 1, 'hp': 50, 'mp':0}, 'nextTierMPPots':{'level': 5, 'hp': 0, 'mp': 50}}
basicHPPot = {'basicHPPot': {'level': 1, 'hp': 25, 'mp': 0}}
basicMPPot = {'basicMPPot': {'level': 1, 'hp': 0, 'mp': 25}}
nextTierHPPot = {'nextTierHPPot': {'level': 5, 'hp': 50, 'mp':0}}
nextTierMPPot = {'nextTierMPPot': {'level': 5, 'hp': 0, 'mp':50}}
potionTypesList = ['basicHPPot', 'basicMPPot', 'nextTierHPPot', 'nextTierMPPot']

def addToPotions(player, name, hp, mp, level):
    # # Initialize potion types
    # potionTypes = {{'basicHPPot': {'level': 1, 'hp': 25, 'mp': 0}}, {'basicMPPot': {'level': 1, 'hp': 0, 'mp': 25}}}
    potionTypesList = ['basicHPPot', 'basicMPPot', 'nextTierHPPot','nextTierMPPot' ]
    player.obtainItem({name: {'level': level, 'hp': hp, 'mp': mp}})
# potionTypes = {'basicHPPot': {'level': 1, 'hp': 25, 'mp': 0}, 'basicMPPot': {'level': 1, 'hp': 0, 'mp': 25}, 'nextTierHPPots': {'level': 1, 'hp': 50, 'mp':0}, 'nextTierMPPots':{'level': 5, 'hp': 0, 'mp': 50}}

def get_all_main_keys(d):
    for key, value in d.items():
        yield key


for x in get_all_main_keys(potionTypes):
    print(x)


myplayer = Mage("player", 1, 10,15, 5)
myplayer.checkInv()
print("prior to add")
addToPotions(myplayer, 'basicHPPot', 25, 0, 1)
print("after to add")
myplayer.checkInv()
# potionTypes['']

def obtainItem(player, item):
    player.inventory.update(item)

print("prior to add")
obtainItem(myplayer, {'basicHPPot': {'level': 1, 'hp': 25, 'mp': 0}})
print("after to add")
myplayer.checkInv()

obtainItem(myplayer, basicHPPot)
obtainItem(myplayer, basicMPPot)
obtainItem(myplayer, nextTierHPPot)
obtainItem(myplayer, nextTierMPPot)
myplayer.checkInv()
print(myplayer.inventory['basicHPPot']['hp'])
# print(myplayer.inventory)

def drinkPotion(player):
    for potion in potionTypesList:
        if player.level >= player.inventory[potion]['level'] and str(potion) in player.inventory:
            print(f"allow this potion {potion}")
            

# def drinkPotion(player, potion):
#     if player.level >= player.inventory[potion]['level']:
#         print(f"{player.name} drank the potion and is now at {player.hp}/{player.maxHP}")

drinkPotion(myplayer)

# drinkPotion(myplayer, basicHPPot)
# print(f"What is this? \n {basicHPPot['basicHPPot']['level']}")
# print(myplayer.inventory['basicHPPot'])
# print(basicHPPot.items())
# print(basicHPPot['basicHPPot']['level'])

# how to figure out the quantity issue of the dictionary then also how to
# remove quantity as well. How to remove dict entry if 'qty': 0 of potion
# I imagine just searching by that item then there has to be some dict
# entry remove method built-in to the class?