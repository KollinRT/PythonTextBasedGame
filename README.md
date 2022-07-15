# Python Text-Based Adventure Game
This is the README.md file for the development of this project.

This game is a test-based python adventure game. This game came out of an interest in old-school text-based RPGs. My desire with this project is to implement the logic of python to create a game that mirrors what I have encountered before and maybe adds upon some features.

Game development is new to me, so bear with please. I am learning as I go in terms of how to structure this program based off of my knowledge and understanding of python but also trying to make it easily understood and extensible by others.

## Core Components:
**Logic**:   <br>
**Structure**: The structures follows the schematic that I have drawn below. This
### The files in this repo (and a description of what they do)
```
├── tests
│   ├── __init__.py (A file used to call tests as a module.)
│   │
│   └── test_maps.py (A file contained to test the functions
│                      implemented with graphAlgs)
│
├── classes
│   ├── __init__.py (A file used to call classes as a module.)
│   │
│   ├── Player.py (Consists of the base class Player, that is
│   │              extended upon by other classes.)
│   ├── Mage.py   (Consists of the Mage class which inherits from
│   │               Player and adds support for MP and spell logic.)
│   └ Enemy.py (Consists of the Enemy class which inherits from Player and isn't anything too special. Doesn't consist of any special methods )
│
├── maps
│   ├── __init__.py (A file used to call maps as a module.)
│   │
│   ├── beginner_map.py (Consists of the starting map which is just
│   │                    a basic map with a few different zones.)
│   └── intermediate_map.py (Not constructed yet but will be a map
│                             with additional zones.)
│                            
├── main.py (Consists of the logic that strings together the program)
│
├── graphAlgs.py (The module which contains the graph algorithms
│                 which will be
│                             
├── customErrors.py (A module which contains custom errors for
│              error handling for certain game-specific issues.)
│
│
└── train_mnist_model.pt (Trains the PyTorch model and saves the trained
                          parameters as pytorch_model.pt.)
```

<br>

**Map**: The game uses graphs implemented via a dict-of-dicts or dict-of-dicts-of-dicts with the construction being outsourced to the networkx module. This module provides me with the basics of graph construction and a few algorithms albeit I have chosen to implement those algorithms myself to more understand their logic and how they work and how to best integrate them in the future for additional game mechanics. <br>

## Goals:
### To Implement
- [ ] Finish basics of game logic  
  - [ ] Get the start of game setup
  - [ ] Integrate game with movement
  - [ ] Write some sorting algorithms for the inventory sorting  
  - [ ] Get the random encounters working
  - [ ] Write an exp level up function
  - [ ] Get the shop working
    - [ ] add gold acquisition methods
  - [ ] Add fishing
- [ ] Add more comprehensive documentation
- [ ] More comprehensive testing
  - [ ] determine how to best write the tests with pytest.  
  - [ ] test new functions as implemented

### Stretch implementations
- [ ] Additional functionalities  
  - [ ] Additional characters during battle
    - [ ] Maybe extend to allow a "companion" assistant during battle.
    - [ ] Add the capacity for multiple enemies as well
      - Would involve the need to implement logic for both targeting additional enemies and additional players.
- [ ] Additional Classes?
  - [ ] Ranger with a companion monster and advanced scouting?
    - [ ] Character pathfinding. Maybe this class has support for utilizing the graph pathfinding algorithms to find the closest path between current location and the next town or chest or something?
  - [ ] Cleric with heals?
- [ ] Get random item drops?
- [ ] Add AI/logic to enemies:
  - [ ] work with randomized enemy stats/levels.
  - [ ] Add more complex decision making and skills to enemies.

- [ ] Add more logic for map transition (i.e. beginner_map -> intermediate_map)

- [ ] Maybe fix
```
class Enemy(Player):
# Maybe fix this
def __init__(self, name, level, hp, dmg, critDmg=1.25, critChance=100, expWorth=500):
```



### Seeking Feedback
Please submit any pull requests or leave comments if you would like any features implemented!

If you have any ideas on how to better implement the logic or in adding additional features, please feel free to reach out to me via the contact form on my GitHub pages website at [KollinRT.github.io](https://kollinrt.github.io/).


<!-- ### Completed Column ✓
- [x] Completed task title  
 -->
<!-- ### To Implement
- [ ] Task title ~3d #type @name yyyy-mm-dd  
  - [ ] Sub-task or description   -->
