"""
Map System - Tile-based maps with collision detection and transitions
"""

import pygame
import json
import os
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import IntEnum


class TileType(IntEnum):
    """Different types of tiles in the game."""
    EMPTY = 0
    GRASS = 1
    TALL_GRASS = 2
    PATH = 3
    WATER = 4
    TREE = 5
    BUILDING_WALL = 6
    BUILDING_FLOOR = 7
    DOOR = 8
    STAIRS = 9
    LEDGE_DOWN = 10
    LEDGE_LEFT = 11
    LEDGE_RIGHT = 12
    SIGN = 13
    ROCK = 14
    FLOWER = 15


@dataclass
class Warp:
    """Represents a warp/transition point between maps."""
    x: int
    y: int
    target_map: str
    target_x: int
    target_y: int
    transition_type: str = "fade"  # fade, stairs, door


@dataclass
class MapObject:
    """Represents an interactive object on the map."""
    x: int
    y: int
    object_type: str  # "npc", "item", "sign", etc.
    data: Dict[str, Any]
    solid: bool = True


class Tile:
    """Represents a single tile on the map."""
    
    def __init__(self, tile_type: TileType, x: int, y: int):
        self.type = tile_type
        self.x = x
        self.y = y
        self.solid = self._is_solid()
        self.wild_encounter = self._has_wild_encounters()
        
    def _is_solid(self) -> bool:
        """Check if this tile type blocks movement."""
        solid_tiles = {
            TileType.WATER,
            TileType.TREE,
            TileType.BUILDING_WALL,
            TileType.ROCK,
            TileType.SIGN
        }
        return self.type in solid_tiles
    
    def _has_wild_encounters(self) -> bool:
        """Check if this tile can trigger wild Pokemon encounters."""
        return self.type == TileType.TALL_GRASS


class Map:
    """Represents a game map with tiles and objects."""
    
    def __init__(self, map_id: str, width: int, height: int, name: str = ""):
        self.id = map_id
        self.name = name
        self.width = width
        self.height = height
        self.tile_size = 32
        
        # Initialize empty tile grid
        self.tiles: List[List[Optional[Tile]]] = [
            [None for _ in range(width)] for _ in range(height)
        ]
        
        # Map features
        self.warps: List[Warp] = []
        self.objects: List[MapObject] = []
        self.wild_pokemon_data: Optional[Dict] = None
        self.background_music: Optional[str] = None
        
        # Visual properties
        self.indoor = False
        self.dark = False
        
    def set_tile(self, x: int, y: int, tile_type: TileType):
        """Set a tile at the given position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = Tile(tile_type, x, y)
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Get the tile at the given position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None
    
    def add_warp(self, warp: Warp):
        """Add a warp point to the map."""
        self.warps.append(warp)
    
    def add_object(self, obj: MapObject):
        """Add an interactive object to the map."""
        self.objects.append(obj)
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable."""
        # Check bounds
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        
        # Check tile
        tile = self.tiles[y][x]
        if tile and tile.solid:
            return False
        
        # Check objects
        for obj in self.objects:
            if obj.x == x and obj.y == y and obj.solid:
                return False
        
        return True
    
    def get_warp_at(self, x: int, y: int) -> Optional[Warp]:
        """Get warp at the given position."""
        for warp in self.warps:
            if warp.x == x and warp.y == y:
                return warp
        return None
    
    def get_object_at(self, x: int, y: int) -> Optional[MapObject]:
        """Get object at the given position."""
        for obj in self.objects:
            if obj.x == x and obj.y == y:
                return obj
        return None
    
    def check_wild_encounter(self, x: int, y: int) -> bool:
        """Check if position can trigger wild encounters."""
        tile = self.get_tile(x, y)
        return tile.wild_encounter if tile else False
    
    def render(self, screen: pygame.Surface, camera_x: int = 0, camera_y: int = 0):
        """Render the map to the screen."""
        # Calculate visible tile range
        start_x = int(max(0, camera_x // self.tile_size))
        start_y = int(max(0, camera_y // self.tile_size))
        end_x = int(min(self.width, (camera_x + screen.get_width()) // self.tile_size + 1))
        end_y = int(min(self.height, (camera_y + screen.get_height()) // self.tile_size + 1))
        
        # Draw tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.tiles[y][x]
                if tile:
                    screen_x = x * self.tile_size - camera_x
                    screen_y = y * self.tile_size - camera_y
                    self._draw_tile(screen, tile, screen_x, screen_y)
        
        # Draw objects
        for obj in self.objects:
            if start_x <= obj.x < end_x and start_y <= obj.y < end_y:
                screen_x = obj.x * self.tile_size - camera_x
                screen_y = obj.y * self.tile_size - camera_y
                self._draw_object(screen, obj, screen_x, screen_y)
    
    def _draw_tile(self, screen: pygame.Surface, tile: Tile, x: int, y: int):
        """Draw a single tile."""
        rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
        
        # Enhanced color-based rendering with better visuals
        tile_colors = {
            TileType.EMPTY: (50, 50, 50),
            TileType.GRASS: (34, 139, 34),
            TileType.TALL_GRASS: (34, 100, 34),
            TileType.PATH: (139, 119, 101),
            TileType.WATER: (65, 105, 225),
            TileType.TREE: (34, 85, 34),
            TileType.BUILDING_WALL: (105, 105, 105),
            TileType.BUILDING_FLOOR: (160, 160, 160),
            TileType.DOOR: (139, 69, 19),
            TileType.STAIRS: (169, 169, 169),
            TileType.LEDGE_DOWN: (120, 100, 80),
            TileType.SIGN: (139, 90, 43),
            TileType.ROCK: (128, 128, 128),
            TileType.FLOWER: (255, 182, 193)
        }
        
        color = tile_colors.get(tile.type, (0, 0, 0))
        pygame.draw.rect(screen, color, rect)
        
        # Add enhanced visual details
        if tile.type == TileType.TALL_GRASS:
            # Draw animated grass blades
            for i in range(4):
                blade_x = x + 6 + i * 6
                blade_y = y + 24
                pygame.draw.line(screen, (20, 80, 20), 
                               (blade_x, blade_y), (blade_x - 2, blade_y - 10), 2)
                pygame.draw.line(screen, (40, 100, 40), 
                               (blade_x + 1, blade_y), (blade_x - 1, blade_y - 8), 1)
                               
            # Add grass texture
            pygame.draw.rect(screen, (28, 90, 28), rect, 1)
            
        elif tile.type == TileType.GRASS:
            # Add grass texture
            for i in range(3):
                dot_x = x + 10 + i * 6
                dot_y = y + 10 + (i % 2) * 8
                pygame.draw.circle(screen, (44, 154, 44), (dot_x, dot_y), 1)
                
        elif tile.type == TileType.WATER:
            # Draw water ripples and shine
            pygame.draw.circle(screen, (100, 149, 237), (x + 16, y + 16), 8, 1)
            pygame.draw.circle(screen, (120, 169, 255), (x + 12, y + 12), 4, 1)
            pygame.draw.circle(screen, (80, 120, 200), (x + 20, y + 20), 3, 1)
            
        elif tile.type == TileType.TREE:
            # Draw tree trunk and leaves
            trunk_rect = pygame.Rect(x + 12, y + 20, 8, 12)
            pygame.draw.rect(screen, (101, 67, 33), trunk_rect)
            # Tree canopy
            pygame.draw.circle(screen, (34, 85, 34), (x + 16, y + 16), 12)
            pygame.draw.circle(screen, (44, 95, 44), (x + 16, y + 16), 8)
            
        elif tile.type == TileType.PATH:
            # Add path texture
            pygame.draw.rect(screen, (159, 139, 121), rect, 1)
            for i in range(2):
                pebble_x = x + 8 + i * 12
                pebble_y = y + 12 + (i % 2) * 8
                pygame.draw.circle(screen, (119, 99, 81), (pebble_x, pebble_y), 1)
                
        elif tile.type == TileType.BUILDING_WALL:
            # Add brick texture
            pygame.draw.rect(screen, (125, 125, 125), rect, 1)
            # Draw brick lines
            for i in range(0, self.tile_size, 8):
                pygame.draw.line(screen, (85, 85, 85), (x, y + i), (x + self.tile_size, y + i), 1)
            for i in range(0, self.tile_size, 16):
                pygame.draw.line(screen, (85, 85, 85), (x + i, y), (x + i, y + self.tile_size), 1)
                
        elif tile.type == TileType.BUILDING_FLOOR:
            # Add floor tile pattern
            pygame.draw.rect(screen, (180, 180, 180), rect, 1)
            # Draw tile lines
            pygame.draw.line(screen, (140, 140, 140), (x, y + self.tile_size//2), (x + self.tile_size, y + self.tile_size//2), 1)
            pygame.draw.line(screen, (140, 140, 140), (x + self.tile_size//2, y), (x + self.tile_size//2, y + self.tile_size), 1)
            
        elif tile.type == TileType.FLOWER:
            # Draw flower petals
            center_x, center_y = x + 16, y + 16
            petal_color = (255, 192, 203)
            center_color = (255, 255, 0)
            
            # Draw petals
            for i in range(6):
                angle = i * 60
                petal_x = center_x + int(6 * (angle / 60))
                petal_y = center_y + int(6 * ((angle + 30) / 60))
                pygame.draw.circle(screen, petal_color, (petal_x, petal_y), 3)
            
            # Draw center
            pygame.draw.circle(screen, center_color, (center_x, center_y), 2)
            
        elif tile.type == TileType.ROCK:
            # Draw rock with shading
            pygame.draw.circle(screen, (108, 108, 108), (x + 16, y + 16), 12)
            pygame.draw.circle(screen, (148, 148, 148), (x + 12, y + 12), 6)
            pygame.draw.circle(screen, (88, 88, 88), (x + 20, y + 20), 4)
    
    def _draw_object(self, screen: pygame.Surface, obj: MapObject, x: int, y: int):
        """Draw an interactive object."""
        rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
        
        if obj.object_type == "npc":
            # Draw simple NPC representation
            pygame.draw.rect(screen, (255, 200, 100), rect)
            pygame.draw.circle(screen, (255, 150, 50), (x + 16, y + 12), 8)
        elif obj.object_type == "item":
            # Draw item ball
            pygame.draw.circle(screen, (255, 0, 0), (x + 16, y + 16), 10)
            pygame.draw.circle(screen, (255, 255, 255), (x + 16, y + 16), 6)
        elif obj.object_type == "sign":
            # Draw sign post
            pygame.draw.rect(screen, (139, 90, 43), pygame.Rect(x + 8, y + 8, 16, 16))
            pygame.draw.rect(screen, (101, 67, 33), pygame.Rect(x + 14, y + 24, 4, 8))


def create_sample_maps() -> Dict[str, Map]:
    """Create sample maps for the game."""
    maps = {}
    
    # Starting Town - Now larger and more detailed
    town = Map("pallet_town", 40, 30, "Pallet Town")
    
    # Create town layout with improved design
    for y in range(30):
        for x in range(40):
            # Default to grass
            town.set_tile(x, y, TileType.GRASS)
            
            # Add main paths (wider and more organic)
            # Horizontal main road
            if 12 <= y <= 17 and 5 <= x <= 34:
                town.set_tile(x, y, TileType.PATH)
            # Vertical paths connecting buildings
            if 15 <= x <= 17 or 22 <= x <= 24:
                if 5 <= y <= 25:
                    town.set_tile(x, y, TileType.PATH)
            
            # Add trees for natural borders (denser forest feel)
            if x <= 2 or x >= 37 or y <= 2 or y >= 27:
                town.set_tile(x, y, TileType.TREE)
            # Additional tree clusters
            if (3 <= x <= 6 and 3 <= y <= 8) or (33 <= x <= 36 and 20 <= y <= 25):
                if random.random() > 0.3:  # Random tree placement
                    town.set_tile(x, y, TileType.TREE)
    
    # Add Pokemon Center (larger building)
    for y in range(6, 12):
        for x in range(8, 15):
            if y == 6 or y == 11 or x == 8 or x == 14:
                town.set_tile(x, y, TileType.BUILDING_WALL)
            else:
                town.set_tile(x, y, TileType.BUILDING_FLOOR)
    town.set_tile(11, 11, TileType.DOOR)
    # Add roof decoration
    for x in range(9, 14):
        town.set_tile(x, 5, TileType.ROCK)  # Using rock as roof tiles
    
    # Add Player's House (cozy home with garden)
    for y in range(20, 25):
        for x in range(10, 16):
            if y == 20 or y == 24 or x == 10 or x == 15:
                town.set_tile(x, y, TileType.BUILDING_WALL)
            else:
                town.set_tile(x, y, TileType.BUILDING_FLOOR)
    town.set_tile(12, 24, TileType.DOOR)
    # Add small garden
    for y in range(25, 27):
        for x in range(11, 15):
            if random.random() > 0.4:
                town.set_tile(x, y, TileType.FLOWER)
    
    # Add Rival's House (matching player's house)
    for y in range(20, 25):
        for x in range(24, 30):
            if y == 20 or y == 24 or x == 24 or x == 29:
                town.set_tile(x, y, TileType.BUILDING_WALL)
            else:
                town.set_tile(x, y, TileType.BUILDING_FLOOR)
    town.set_tile(26, 24, TileType.DOOR)
    
    # Add Professor's Lab (important building)
    for y in range(7, 14):
        for x in range(18, 28):
            if y == 7 or y == 13 or x == 18 or x == 27:
                town.set_tile(x, y, TileType.BUILDING_WALL)
            else:
                town.set_tile(x, y, TileType.BUILDING_FLOOR)
    town.set_tile(22, 13, TileType.DOOR)
    town.set_tile(23, 13, TileType.DOOR)  # Double door for lab
    
    # Add decorative elements throughout town
    # Fountain in town center
    for y in range(14, 17):
        for x in range(19, 22):
            if (x == 19 or x == 21) and (y == 14 or y == 16):
                town.set_tile(x, y, TileType.ROCK)
            elif x == 20 and y == 15:
                town.set_tile(x, y, TileType.WATER)
    
    # Flower beds and decorations
    flower_spots = [(6, 18), (7, 19), (31, 15), (32, 16), (8, 23), (30, 8)]
    for x, y in flower_spots:
        town.set_tile(x, y, TileType.FLOWER)
    
    # Benches (using rocks as placeholder)
    bench_spots = [(13, 18), (26, 18), (16, 9), (23, 9)]
    for x, y in bench_spots:
        town.set_tile(x, y, TileType.ROCK)
    
    # Add signs
    town.set_tile(16, 19, TileType.SIGN)
    town.add_object(MapObject(16, 19, "sign", {
        "text": "Welcome to Pallet Town!\nA quiet town of new beginnings."
    }))
    
    town.set_tile(22, 6, TileType.SIGN)
    town.add_object(MapObject(22, 6, "sign", {
        "text": "Professor Oak's Pokemon Lab\nCutting-edge Pokemon research!"
    }))
    
    town.set_tile(11, 5, TileType.SIGN)
    town.add_object(MapObject(11, 5, "sign", {
        "text": "Pokemon Center\nHeal your Pokemon for free!"
    }))
    
    # Add warps
    # Exit to Route 1 (multiple tiles for wider exit)
    for x in range(18, 23):
        town.add_warp(Warp(x, 0, "route_1", x, 39))
    
    # NPCs are handled by World class, not added here
    
    maps["pallet_town"] = town
    
    # Route 1 - Much larger with varied terrain
    route = Map("route_1", 40, 40, "Route 1")
    
    # Create route layout with natural winding path
    for y in range(40):
        for x in range(40):
            # Default to grass
            route.set_tile(x, y, TileType.GRASS)
            
            # Create a winding path
            path_width = 4
            # Main path with curves
            if y < 10:
                if 18 <= x <= 21:  # Straight section
                    route.set_tile(x, y, TileType.PATH)
            elif 10 <= y < 15:
                if 18 - (y - 10) <= x <= 21 - (y - 10):  # Curve left
                    route.set_tile(x, y, TileType.PATH)
            elif 15 <= y < 25:
                if 13 <= x <= 16:  # Left path
                    route.set_tile(x, y, TileType.PATH)
            elif 25 <= y < 30:
                if 13 + (y - 25) <= x <= 16 + (y - 25):  # Curve right
                    route.set_tile(x, y, TileType.PATH)
            else:
                if 18 <= x <= 21:  # Back to center
                    route.set_tile(x, y, TileType.PATH)
            
            # Add extensive tall grass areas for encounters
            grass_areas = [
                (5, 5, 12, 15),    # Left upper area
                (25, 8, 35, 18),   # Right upper area
                (3, 20, 10, 30),   # Left lower area
                (28, 25, 37, 35),  # Right lower area
                (8, 32, 15, 38),   # Bottom left patch
                (23, 30, 30, 37),  # Bottom right patch
            ]
            
            for gx1, gy1, gx2, gy2 in grass_areas:
                if gx1 <= x <= gx2 and gy1 <= y <= gy2:
                    # Create patches with some normal grass mixed in
                    if random.random() > 0.2:
                        route.set_tile(x, y, TileType.TALL_GRASS)
            
            # Add tree borders and clusters
            if x <= 1 or x >= 38 or y <= 1 or y >= 38:
                route.set_tile(x, y, TileType.TREE)
            
            # Tree clusters for more natural look
            tree_clusters = [
                (22, 12, 5),  # (center_x, center_y, radius)
                (10, 18, 4),
                (30, 22, 4),
                (15, 35, 3),
            ]
            
            for cx, cy, radius in tree_clusters:
                if ((x - cx) ** 2 + (y - cy) ** 2) <= radius ** 2:
                    if random.random() > 0.3:
                        route.set_tile(x, y, TileType.TREE)
    
    # Add terrain features
    # Rocks scattered around
    rock_positions = [(6, 10), (14, 7), (25, 15), (32, 28), (8, 25), (20, 5)]
    for x, y in rock_positions:
        route.set_tile(x, y, TileType.ROCK)
    
    # Ledges for one-way movement
    for x in range(10, 15):
        route.set_tile(x, 18, TileType.LEDGE_DOWN)
    for x in range(24, 28):
        route.set_tile(x, 23, TileType.LEDGE_DOWN)
    
    # Small pond
    for y in range(12, 15):
        for x in range(31, 34):
            route.set_tile(x, y, TileType.WATER)
    
    # Flower patches
    flower_areas = [(7, 8), (12, 22), (26, 10), (33, 32)]
    for fx, fy in flower_areas:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if random.random() > 0.5:
                    route.set_tile(fx + dx, fy + dy, TileType.FLOWER)
    
    # Add warps
    # Multiple tiles for entrance from Pallet Town
    for x in range(18, 23):
        route.add_warp(Warp(x, 39, "pallet_town", x, 1))
    # Exit to Viridian City
    for x in range(18, 23):
        route.add_warp(Warp(x, 0, "viridian_city", x, 39))
    
    # Set wild Pokemon data
    route.wild_pokemon_data = {
        "grass": [
            {"species": "Pidgey", "levels": [2, 5]},
            {"species": "Rattata", "levels": [2, 4]},
            {"species": "Caterpie", "levels": [3, 5]}
        ]
    }
    
    maps["route_1"] = route
    
    # Pokemon Center Interior
    pokecenter = Map("pokecenter_1", 10, 8, "Pokemon Center")
    pokecenter.indoor = True
    
    # Create interior
    for y in range(8):
        for x in range(10):
            # Walls
            if x == 0 or x == 9 or y == 0 or y == 7:
                pokecenter.set_tile(x, y, TileType.BUILDING_WALL)
            else:
                pokecenter.set_tile(x, y, TileType.BUILDING_FLOOR)
    
    # Add door
    pokecenter.set_tile(5, 7, TileType.DOOR)
    pokecenter.add_warp(Warp(5, 7, "pallet_town", 5, 8))
    
    # Add healing station (Nurse Joy)
    pokecenter.add_object(MapObject(5, 2, "npc", {
        "name": "Nurse Joy",
        "dialogue": ["Welcome to the Pokemon Center!",
                    "Would you like me to heal your Pokemon?"],
        "healer": True
    }))
    
    maps["pokecenter_1"] = pokecenter
    
    return maps