# 🎮 Pokemon Game

A feature-rich Pokemon-style RPG game built with uv run and Pygame, featuring turn-based battles, world exploration, and all the classic Pokemon mechanics you love!

## 🎯 Overview

This Pokemon Game is a comprehensive recreation of the classic Pokemon gaming experience. Explore a vibrant tile-based world, catch and train Pokemon, battle other trainers, and become the Pokemon Champion!

## ✨ Features

### Core Gameplay
- **Starter Pokemon Selection** - Choose between Bulbasaur, Charmander, or Squirtle
- **Turn-Based Battle System** with:
  - Type effectiveness system (18 types)
  - Physical/Special move split
  - Status conditions (Paralysis, Burn, Poison, Sleep, Freeze)
  - Stat modifications
  - Critical hits and accuracy/evasion
  - Experience and leveling system

### World Exploration
- **Grid-Based Movement** - Classic Pokemon-style with smooth animations
- **Multiple Connected Maps** - Seamless transitions between areas
- **Different Terrain Types**:
  - Normal ground and paths
  - Tall grass (wild Pokemon encounters - 10% chance per step)
  - Buildings with interiors
  - Trees and obstacles
  - Water (Surf required - future feature)

### Pokemon System
- **Comprehensive Pokemon Mechanics**:
  - Individual stats (HP, Attack, Defense, Sp. Attack, Sp. Defense, Speed)
  - Natures affecting stat growth
  - Abilities with in-battle effects
  - Move learning and PP system
  - Shiny Pokemon (0.1% chance)
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


### Setup Instructions


3. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```
   Dependencies:
   - pygame==2.5.2
   - requests==2.31.0
   - pillow==10.2.0

4. **Run the game**
   ```bash
   # Option 1: Game launcher (recommended)
   uv run run_game.py
   
   # Option 2: Full version
   uv run main.py
   
   # Option 3: Simple version
   uv run simple_game.py
   ```

## 🎮 How to Play

### Starting the Game
1. Run the game using one of the methods above
2. If using `run_game.py`, select between full or simple version
3. Choose your starter Pokemon
4. Begin your adventure in Pallet Town!

### Controls

#### World Exploration
| Key | Action |
|-----|--------|
| Arrow Keys / WASD | Move character |
| Hold Shift | Run (move faster) |
| Space | Interact with NPCs/Objects |
| I | Open Inventory |
| P | Open Pokemon Menu |
| ESC | Pause Menu |

#### Battle Controls
| Key | Action |
|-----|--------|
| 1-4 / A | Attack/Select move |
| C | Catch Pokemon (uses Poke Ball) |
| R | Run from wild Pokemon |
| Arrow Keys | Navigate battle menu |
| Enter | Confirm selection |
| B | Back/Cancel |

### Game Objectives
- Build a strong team of Pokemon
- Explore all areas and talk to NPCs
- Catch different types of Pokemon
- Train your team in wild encounters
- Heal at Pokemon Centers
- Become the ultimate Pokemon trainer!

### Tips for New Players
- Type effectiveness is crucial - learn the type chart!
- Lower a Pokemon's HP before trying to catch it
- Keep a balanced team with different types
- Talk to all NPCs for items and information
- Save frequently (when implemented)
- Explore tall grass for wild Pokemon

## 🗺️ Map System

### Tile Types
- `T` = Trees (solid obstacles)
- `.` = Path/Ground (walkable)
- `#` = Tall Grass (wild Pokemon encounters)
- `~` = Water (requires Surf)
- `B` = Buildings
- `D` = Doors (entry points)

### Sample Maps
1. **Pallet Town** - Starting town with Pokemon Center and Professor Oak
2. **Route 1** - Wild Pokemon area connecting to other towns
3. **Pokemon Center** - Heal your Pokemon team

### Map Features
- Grid-based movement (32x32 pixel tiles)
- Smooth movement animations
- Collision detection
- Warp points for transitions
- Interactive objects (signs, NPCs)
- Wild Pokemon encounter areas

## 📁 Project Structure

```
pokemon_game/
├── main.py              # Full game entry point
├── simple_game.py       # Simplified standalone version
├── run_game.py         # Game launcher
├── requirements.txt     # Dependencies
├── README.md           # This file
├── src/                # Source code
│   ├── game.py        # Main game loop
│   ├── pokemon.py     # Pokemon classes
│   ├── battle.py      # Battle system
│   ├── player.py      # Player management
│   ├── ui.py          # User interface
│   ├── world.py       # World management
│   ├── map.py         # Map system
│   ├── encounters.py  # Wild encounters
│   └── items.py       # Item definitions
├── assets/            # Game assets
│   ├── sprites/       # Pokemon sprites
│   ├── maps/          # Map data
│   └── sounds/        # Audio files
└── utils/             # Utilities
    └── downloader.py  # Sprite downloader
```

## 🔧 Technical Details

### Game Versions
1. **Full Version** (`main.py`) - Complete Pokemon experience with all features
2. **Simple Version** (`simple_game.py`) - Lightweight, self-contained version

### Known Issues & Fixes
- **Audio on WSL**: Audio is disabled in WSL environments to prevent crashes
- **Missing Sprites**: Game displays colored shapes as fallback graphics
- **Performance**: Lower FPS in settings if experiencing lag

## 🚀 Future Features

- [ ] Pokemon catching with different ball types
- [ ] Full evolution system
- [ ] Save/Load functionality
- [ ] Gym Leaders and badges
- [ ] Pokemon PC storage system
- [ ] Trading system
- [ ] Day/night cycle
- [ ] Weather effects
- [ ] Sound effects and music
- [ ] Animated sprites
- [ ] Berry growing
- [ ] Breeding system
- [ ] Online features

## 🤝 Contributing

Contributions are welcome! Please:
1. Follow existing code style
2. Test changes thoroughly
3. Update documentation
4. Submit clear pull requests

## ⚠️ Notes

- This is a fan-made game for educational purposes
- Pokemon is a trademark of Nintendo/Game Freak
- Not affiliated with or endorsed by Nintendo
- Sprites from PokeAPI (when downloaded)

## 📝 License

Educational project - see repository for license details.

---

**Enjoy your Pokemon adventure!** 🎮✨

For support, please open an issue on the repository.