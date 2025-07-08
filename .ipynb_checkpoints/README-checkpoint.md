# Pokemon Game

A simple Pokemon-style game built with Python and Pygame.

## Directory Structure

```
pokemon_game/
├── main.py                 # Main game entry point
├── requirements.txt        # Python dependencies
├── src/                    # Source code
│   ├── __init__.py
│   ├── pokemon.py         # Pokemon class with stats and moves
│   ├── battle.py          # Turn-based battle system
│   ├── player.py          # Player character management
│   ├── game.py            # Main game loop and state management
│   └── ui.py              # UI rendering components
├── assets/                 # Game assets
│   ├── sprites/           # Pokemon sprite images
│   ├── maps/              # Game world maps
│   └── sounds/            # Sound effects and music
└── utils/                  # Utility modules
    ├── __init__.py
    └── downloader.py      # Sprite downloader utility
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the game:
   ```bash
   python main.py
   ```

## Features

- **Pokemon System**: Complete Pokemon class with stats, types, and moves
- **Battle System**: Turn-based battles with type effectiveness
- **Player Character**: Movement, inventory, and Pokemon team management
- **UI Components**: Battle screens, inventory, and status displays
- **Sprite Downloader**: Utility to download Pokemon sprites from PokeAPI

## Game Controls

### World Exploration
- Arrow Keys: Move player
- SPACE: Interact
- I: Open inventory
- P: Pokemon menu (not yet implemented)

### Battle
- 1-4: Select moves
- R: Run from battle
- SPACE: Continue after battle ends

### Inventory
- ESC or I: Close inventory

## Extending the Game

### Adding New Pokemon
Modify the `Pokemon` class in `src/pokemon.py` to add new Pokemon species or moves.

### Creating Maps
Add map data to `assets/maps/` and update the `load_map_data()` method in `src/game.py`.

### Downloading Sprites
Use the sprite downloader utility:
```python
from utils.downloader import SpriteDownloader

downloader = SpriteDownloader()
downloader.download_starter_sprites()
```

## Development Notes

- The game currently uses placeholder rectangles for Pokemon sprites
- Map rendering is simplified (solid color background)
- Save/load functionality not yet implemented
- Pokemon catching mechanics not yet implemented

## Future Enhancements

- [ ] Implement actual sprite rendering
- [ ] Add Pokemon catching with Pokeballs
- [ ] Create proper tile-based maps
- [ ] Add NPCs and trainers
- [ ] Implement save/load system
- [ ] Add more Pokemon species and moves
- [ ] Include sound effects and music
- [ ] Create Pokemon evolution system
- [ ] Add Pokemon Center healing
- [ ] Implement Pokedex