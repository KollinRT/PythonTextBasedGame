import random 
if __name__ == "__main__":
    from classes import Player, Mage
else:
    from classes.classes import Player, Mage

class HealingItems:
    def __init__(self, HPrest, MPrest):
        self.HPrest = HPrest
        self.MPrest = MPrest

    def healPlayer(self, player):
        if isinstance(player, Mage):
            player.mp += self.MPrest 
            player.hp += self.HPrest 
        else:
            player.hp += self.HPrest 



HPPot = HealingItems(25, 0)
MPPot = HealingItems(0, 25)

myplayer = Player("player", 1, 10, 5)
print(myplayer.hp)
HPPot.healPlayer(myplayer)
print(myplayer.hp)

mymage = Mage("mage", 1, 10, 15, 5)
print(mymage.mp)
MPPot.healPlayer(mymage)
print(mymage.mp)

# Have to check that the potion is actually in the player/mage's inventory 
# then look into the restoration value