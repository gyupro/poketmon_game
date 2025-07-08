# Pokemon Game

A feature-rich Pokemon-style RPG game built with Python and Pygame, featuring turn-based battles, world exploration, and all the classic Pokemon mechanics you love!

![Pokemon Game Banner](screenshots/banner.png)

## Overview

This Pokemon Game is a comprehensive recreation of the classic Pokemon gaming experience. Explore a vibrant world, catch and train Pokemon, battle other trainers, and become the Pokemon Champion! The game features authentic Pokemon mechanics including type effectiveness, status conditions, experience systems, and more.

## Features

### Core Gameplay
- **Starter Pokemon Selection** - Choose between Bulbasaur, Charmander, or Squirtle
- **Turn-Based Battle System** - Authentic Pokemon battle mechanics with:
  - Type effectiveness system (18 types)
  - Physical/Special move split
  - Status conditions (Paralysis, Burn, Poison, Sleep, Freeze)
  - Stat modifications (Attack, Defense, Speed, etc.)
  - Critical hits and accuracy/evasion
  - Experience and leveling system

### World Exploration
- **Grid-Based Movement** - Classic Pokemon-style movement
- **Multiple Connected Maps** - Seamless transitions between areas
- **Different Terrain Types**:
  - Normal ground
  - Tall grass (wild Pokemon encounters)
  - Buildings with interiors
  - Water (Surf required - future feature)

### Pokemon Features
- **Comprehensive Pokemon System**:
  - Individual stats (HP, Attack, Defense, Sp. Attack, Sp. Defense, Speed)
  - Natures affecting stat growth
  - Abilities with in-battle effects
  - Move learning and PP system
  - Evolution (coming soon)

### NPCs and Interactions
- **Various NPC Types**:
  - Townspeople with helpful dialogue
  - Trainers for battles
  - Professor Oak for guidance
  - Nurse Joy for Pokemon healing
  - Item givers

### Items and Inventory
- **Item Categories**:
  - Healing items (Potions, Super Potions)
  - Poke Balls for catching Pokemon
  - Battle items (X Attack, X Defense)
  - Key items for progression

### Quality of Life Features
- **Pokemon Center Healing** - Full HP/PP restoration and status condition removal
- **Auto-Save** (coming soon)
- **Settings Menu** (coming soon)
- **Pokemon PC Storage** (coming soon)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pokemon_game
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download Pokemon sprites** (optional)
   ```bash
   python download_popular_sprites.py
   ```

5. **Run the game**
   ```bash
   python main.py
   ```

## How to Play

### Starting the Game
1. Run `python main.py` to start the game
2. Select "New Game" from the main menu
3. Choose your starter Pokemon (Bulbasaur, Charmander, or Squirtle)
4. Begin your adventure in Pallet Town!

### Game Objectives
- Build a strong team of Pokemon
- Defeat all 8 Gym Leaders (coming soon)
- Challenge the Elite Four (coming soon)
- Become the Pokemon Champion!
- Complete the Pokedex (coming soon)

### Tips for New Players
- Save your game frequently at Pokemon Centers
- Type effectiveness is crucial in battles - learn the type chart!
- Keep a balanced team with different Pokemon types
- Stock up on Potions and Poke Balls before leaving town
- Talk to all NPCs - they often give helpful items or information
- Train your Pokemon in tall grass before challenging trainers

## Controls

### World Exploration
| Key | Action |
|-----|--------|
| Arrow Keys / WASD | Move character |
| Hold Shift | Run (move faster) |
| Space | Interact with NPCs/Objects |
| I | Open Inventory |
| P | Open Pokemon Menu |
| ESC | Pause Menu |

### Battle Controls
| Key | Action |
|-----|--------|
| 1-4 | Select move (or click) |
| Arrow Keys | Navigate battle menu |
| Enter | Confirm selection |
| B | Back/Cancel |
| R | Run from wild Pokemon |

### Menu Navigation
| Key | Action |
|-----|--------|
| Arrow Keys | Navigate options |
| Enter | Select option |
| ESC | Back/Close menu |

## Game Mechanics

### Type Effectiveness
The game features the full Pokemon type chart with 18 types. Key interactions:
- **Super Effective** (2x damage): Fire → Grass, Water → Fire, etc.
- **Not Very Effective** (0.5x damage): Fire → Water, Grass → Fire, etc.
- **No Effect** (0x damage): Normal → Ghost, Electric → Ground, etc.

### Status Conditions
- **Burn**: Damage each turn, halves physical attack
- **Poison**: Damage each turn
- **Paralysis**: 25% chance to be unable to move, speed reduced
- **Sleep**: Cannot move for 1-3 turns
- **Freeze**: Cannot move until thawed

### Experience and Leveling
- Gain EXP by defeating Pokemon
- Level up to increase stats
- Learn new moves at certain levels
- Evolve at specific levels (coming soon)

## Project Structure

```
pokemon_game/
├── main.py                 # Game entry point
├── demo_full_game.py      # Comprehensive demo script
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── src/                   # Source code
│   ├── __init__.py
│   ├── game.py           # Main game loop and state management
│   ├── pokemon.py        # Pokemon classes and mechanics
│   ├── battle.py         # Battle system implementation
│   ├── player.py         # Player character management
│   ├── ui.py             # User interface components
│   ├── world.py          # World and NPC management
│   ├── map.py            # Map system and tiles
│   ├── encounters.py     # Wild Pokemon encounter system
│   └── items.py          # Item definitions and effects
├── assets/               # Game assets
│   ├── sprites/          # Pokemon sprite images
│   ├── maps/             # Map data files
│   └── sounds/           # Sound effects and music
└── utils/                # Utility modules
    ├── __init__.py
    └── downloader.py     # Sprite downloader utility
```

## Running the Demo

For a guided tour of all game features, run the comprehensive demo:

```bash
python demo_full_game.py
```

The demo will walk you through:
1. Starter selection process
2. Basic controls tutorial
3. World exploration basics
4. NPC interaction examples
5. Wild Pokemon encounters
6. Battle system demonstration
7. Item usage
8. Pokemon Center healing

## Development

### Adding New Pokemon
1. Define the Pokemon in `src/pokemon.py`
2. Add sprite images to `assets/sprites/`
3. Configure encounter data in `src/encounters.py`

### Creating New Maps
1. Create map data in `assets/maps/`
2. Define warps and connections
3. Add NPCs in `src/world.py`

### Implementing New Features
The codebase is modular and extensible. Key extension points:
- `src/pokemon.py` - Add new moves, abilities, or Pokemon
- `src/items.py` - Create new item types
- `src/battle.py` - Extend battle mechanics
- `src/ui.py` - Customize UI components

## Troubleshooting

### Common Issues

**Game won't start**
- Ensure Python 3.8+ is installed
- Check all dependencies are installed: `pip install -r requirements.txt`
- Verify Pygame is properly installed

**No sprites showing**
- Run `python download_popular_sprites.py` to download sprites
- Check `assets/sprites/` directory exists

**Performance issues**
- Lower the FPS in `src/game.py` (default is 60)
- Close other applications
- Update graphics drivers

## Future Features

- [ ] Pokemon catching mechanics with different Poke Ball types
- [ ] Full evolution system
- [ ] Pokemon breeding
- [ ] Day/night cycle
- [ ] Weather effects affecting battles
- [ ] Gym Leaders and badges
- [ ] Elite Four and Champion
- [ ] Post-game content
- [ ] Trading system
- [ ] Online battles
- [ ] Full Pokedex with detailed entries
- [ ] Berry growing system
- [ ] Pokemon abilities in battle
- [ ] Mega Evolution
- [ ] Save/Load system
- [ ] Sound effects and music
- [ ] Animated sprites
- [ ] Cutscenes and story events

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Guidelines
1. Follow the existing code style
2. Test your changes thoroughly
3. Update documentation as needed
4. Submit clear pull request descriptions

## Credits

- Game developed using Python and Pygame
- Inspired by the Pokemon game series by Game Freak and Nintendo
- Pokemon sprites from PokeAPI
- Special thanks to the Python and Pygame communities

## License

This is a fan-made game for educational purposes. Pokemon is a trademark of Nintendo/Game Freak. This project is not affiliated with or endorsed by Nintendo, Game Freak, or The Pokemon Company.

---

**Enjoy your Pokemon adventure!** 🎮

For questions or support, please open an issue on the repository.