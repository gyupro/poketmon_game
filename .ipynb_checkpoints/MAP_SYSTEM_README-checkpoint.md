# Pokemon Map System Documentation

## Overview

The map system implements a tile-based world similar to classic Pokemon games, featuring:
- Grid-based movement with smooth animations
- Multiple interconnected map areas
- Collision detection
- NPCs with dialogue
- Wild Pokemon encounter areas
- Map transitions (warps)

## Key Components

### 1. Map System (`src/map.py`)

**TileType Enum**: Defines all available tile types
- `GRASS` - Normal grass
- `TALL_GRASS` - Wild Pokemon encounters
- `PATH` - Walkable paths
- `WATER` - Non-walkable water
- `TREE` - Solid obstacle
- `BUILDING_WALL/FLOOR` - Building tiles
- `DOOR` - Entry points
- And more...

**Map Class**: Represents a single game area
- Tile-based grid system (32x32 pixel tiles)
- Collision detection
- Warp points for map transitions
- Interactive objects (signs, NPCs, items)
- Wild Pokemon encounter data

### 2. Player System (`src/player.py`)

**Enhanced Player Class**:
- Grid-based movement (moves one tile at a time)
- Smooth pixel interpolation during movement
- Running capability (hold Shift key)
- Direction facing (up, down, left, right)
- Proper collision checking
- Animation states

**Movement System**:
```python
# Grid position (tile coordinates)
player.grid_x, player.grid_y

# Pixel position (for smooth rendering)
player.pixel_x, player.pixel_y

# Movement is grid-based but rendered smoothly
player.start_move("up", is_running=True)
```

### 3. World Management (`src/world.py`)

**World Class**: Manages the entire game world
- Loads and manages all maps
- Handles map transitions
- NPC management and AI
- Dialogue system
- Camera following player
- Wild encounter triggers

**NPCs**:
- Static or wandering movement patterns
- Multi-line dialogue
- Can be trainers (trigger battles)
- Can give items
- Face player during interaction

## Controls

- **Arrow Keys / WASD**: Move player
- **Shift (hold)**: Run (2x speed)
- **Space**: Interact with NPCs/objects
- **ESC**: Pause menu
- **P**: Pokemon menu
- **I**: Inventory

## Map Features

### Sample Maps Included

1. **Pallet Town**
   - Starting town with buildings
   - Pokemon Center
   - Professor Oak NPC
   - Connected to Route 1

2. **Route 1**
   - Wild Pokemon in tall grass
   - Trainer battles
   - Connects Pallet Town to Viridian City
   - Ledges (one-way jumps)

3. **Pokemon Center**
   - Indoor map
   - Nurse Joy NPC (heals Pokemon)
   - Warp back to town

### Map Transitions

Maps are connected via warp points:
```python
warp = Warp(x=10, y=0, target_map="route_1", target_x=10, target_y=19)
```

Walking onto a warp tile automatically transitions to the target map.

## Creating New Maps

To create a new map:

```python
# Create map instance
new_map = Map("map_id", width=25, height=20, name="My Town")

# Set tiles
for y in range(20):
    for x in range(25):
        new_map.set_tile(x, y, TileType.GRASS)

# Add buildings, trees, etc.
new_map.set_tile(5, 5, TileType.TREE)

# Add warps
new_map.add_warp(Warp(12, 0, "other_map", 12, 19))

# Add objects
sign = MapObject(10, 10, "sign", {"text": "Welcome!"})
new_map.add_object(sign)
```

## Wild Pokemon Encounters

Tall grass tiles trigger random encounters:
- Base 10% chance per step
- Different Pokemon available per route
- Level ranges for variety

## Running the Demo

```bash
python demo_map_system.py
```

This showcases:
- Moving around Pallet Town
- Talking to NPCs
- Transitioning between maps
- Grid-based movement
- Running mechanics

## Integration with Main Game

The map system is fully integrated with the main game:
- Battle system triggers from trainer NPCs
- Wild encounters in tall grass
- Items can be found on maps
- Save/load system compatible

## Future Enhancements

Potential additions:
- Sprite-based tile rendering
- Day/night cycle
- Weather effects
- More tile types (ice, sand, etc.)
- Puzzle elements (strength boulders, cut trees)
- Indoor/outdoor lighting
- Map editor tool