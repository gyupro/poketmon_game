"""
Map System - Tile-based maps with collision detection and transitions
"""

import pygame
import json
import os
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
        start_x = max(0, camera_x // self.tile_size)
        start_y = max(0, camera_y // self.tile_size)
        end_x = min(self.width, (camera_x + screen.get_width()) // self.tile_size + 1)
        end_y = min(self.height, (camera_y + screen.get_height()) // self.tile_size + 1)
        
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
        
        # Simple color-based rendering for now
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
        
        # Add some visual details
        if tile.type == TileType.TALL_GRASS:
            # Draw grass blades
            for i in range(3):
                blade_x = x + 8 + i * 8
                blade_y = y + 20
                pygame.draw.line(screen, (20, 80, 20), 
                               (blade_x, blade_y), (blade_x - 2, blade_y - 8), 2)
        elif tile.type == TileType.WATER:
            # Draw water ripples
            pygame.draw.circle(screen, (100, 149, 237), (x + 16, y + 16), 8, 1)
        elif tile.type == TileType.TREE:
            # Draw tree trunk
            trunk_rect = pygame.Rect(x + 12, y + 20, 8, 12)
            pygame.draw.rect(screen, (101, 67, 33), trunk_rect)
    
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
    
    # Starting Town
    town = Map("pallet_town", 20, 20, "Pallet Town")
    
    # Create town layout
    for y in range(20):
        for x in range(20):
            # Default to grass
            town.set_tile(x, y, TileType.GRASS)
            
            # Add paths
            if 8 <= x <= 11 or 8 <= y <= 11:
                town.set_tile(x, y, TileType.PATH)
            
            # Add trees around edges
            if x == 0 or x == 19 or y == 0 or y == 19:
                town.set_tile(x, y, TileType.TREE)
    
    # Add Pokemon Center
    for y in range(4, 8):
        for x in range(3, 8):
            if y == 4 or y == 7 or x == 3 or x == 7:
                town.set_tile(x, y, TileType.BUILDING_WALL)
            else:
                town.set_tile(x, y, TileType.BUILDING_FLOOR)
    town.set_tile(5, 7, TileType.DOOR)
    
    # Add Player's House
    for y in range(12, 16):
        for x in range(4, 9):
            if y == 12 or y == 15 or x == 4 or x == 8:
                town.set_tile(x, y, TileType.BUILDING_WALL)
            else:
                town.set_tile(x, y, TileType.BUILDING_FLOOR)
    town.set_tile(6, 15, TileType.DOOR)
    
    # Add Rival's House
    for y in range(12, 16):
        for x in range(12, 17):
            if y == 12 or y == 15 or x == 12 or x == 16:
                town.set_tile(x, y, TileType.BUILDING_WALL)
            else:
                town.set_tile(x, y, TileType.BUILDING_FLOOR)
    town.set_tile(14, 15, TileType.DOOR)
    
    # Add some flowers and rocks for decoration
    town.set_tile(2, 10, TileType.FLOWER)
    town.set_tile(3, 11, TileType.FLOWER)
    town.set_tile(15, 8, TileType.ROCK)
    
    # Add sign
    town.set_tile(10, 14, TileType.SIGN)
    town.add_object(MapObject(10, 14, "sign", {
        "text": "Welcome to Pallet Town!\nA quiet town of new beginnings."
    }))
    
    # Add warp to route
    town.add_warp(Warp(10, 0, "route_1", 10, 19))
    
    # Add NPC
    town.add_object(MapObject(9, 9, "npc", {
        "name": "Professor Oak",
        "dialogue": ["Hello there! Welcome to the world of Pokemon!",
                    "My name is Oak. People call me the Pokemon Professor!"]
    }))
    
    maps["pallet_town"] = town
    
    # Route 1
    route = Map("route_1", 20, 20, "Route 1")
    
    # Create route layout
    for y in range(20):
        for x in range(20):
            # Default to grass
            route.set_tile(x, y, TileType.GRASS)
            
            # Add path through middle
            if 8 <= x <= 11:
                route.set_tile(x, y, TileType.PATH)
            
            # Add tall grass patches for wild encounters
            if ((4 <= x <= 7 or 12 <= x <= 15) and 
                (4 <= y <= 8 or 12 <= y <= 16)):
                route.set_tile(x, y, TileType.TALL_GRASS)
            
            # Add trees on sides
            if x <= 1 or x >= 18:
                route.set_tile(x, y, TileType.TREE)
    
    # Add some rocks and ledges
    route.set_tile(6, 10, TileType.ROCK)
    route.set_tile(14, 7, TileType.ROCK)
    route.set_tile(7, 15, TileType.LEDGE_DOWN)
    route.set_tile(8, 15, TileType.LEDGE_DOWN)
    
    # Add warps
    route.add_warp(Warp(10, 19, "pallet_town", 10, 1))
    route.add_warp(Warp(10, 0, "viridian_city", 10, 19))
    
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