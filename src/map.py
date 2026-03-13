"""
Map System - Tile-based maps with collision detection and transitions
"""

import pygame
import json
import os
import random
import math
import time
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

        # Current time for animations
        t = time.time()

        # Draw tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.tiles[y][x]
                if tile:
                    screen_x = x * self.tile_size - camera_x
                    screen_y = y * self.tile_size - camera_y
                    self._draw_tile_enhanced(screen, tile, screen_x, screen_y, t)

        # Draw tile border blending pass (softer edges between different types)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.tiles[y][x]
                if tile:
                    screen_x = x * self.tile_size - camera_x
                    screen_y = y * self.tile_size - camera_y
                    self._draw_tile_blending(screen, tile, x, y, screen_x, screen_y)

        # Draw objects
        for obj in self.objects:
            if start_x <= obj.x < end_x and start_y <= obj.y < end_y:
                screen_x = obj.x * self.tile_size - camera_x
                screen_y = obj.y * self.tile_size - camera_y
                self._draw_object(screen, obj, screen_x, screen_y)

    def _get_neighbor_type(self, x: int, y: int) -> Optional[int]:
        """Get the tile type at a neighbor position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            tile = self.tiles[y][x]
            return tile.type if tile else None
        return None

    def _draw_tile_blending(self, screen: pygame.Surface, tile: Tile,
                            grid_x: int, grid_y: int, sx: int, sy: int):
        """Draw subtle blending borders between different tile types."""
        ts = self.tile_size
        blend_size = 4

        # Only blend certain tile types
        blendable = {TileType.GRASS, TileType.TALL_GRASS, TileType.PATH,
                     TileType.WATER, TileType.FLOWER}
        if tile.type not in blendable:
            return

        neighbors = [
            (grid_x, grid_y - 1, "top"),
            (grid_x, grid_y + 1, "bottom"),
            (grid_x - 1, grid_y, "left"),
            (grid_x + 1, grid_y, "right"),
        ]

        for nx, ny, side in neighbors:
            n_type = self._get_neighbor_type(nx, ny)
            if n_type is not None and n_type != tile.type and n_type in blendable:
                blend_surf = pygame.Surface((ts, blend_size), pygame.SRCALPHA)
                blend_surf.fill((0, 0, 0, 0))
                # Create a gradient fade
                for i in range(blend_size):
                    alpha = int(40 * (1 - i / blend_size))
                    pygame.draw.line(blend_surf, (0, 0, 0, alpha), (0, i), (ts, i))

                if side == "top":
                    screen.blit(blend_surf, (sx, sy))
                elif side == "bottom":
                    flipped = pygame.transform.flip(blend_surf, False, True)
                    screen.blit(flipped, (sx, sy + ts - blend_size))
                elif side == "left":
                    rotated = pygame.transform.rotate(blend_surf, -90)
                    screen.blit(rotated, (sx, sy))
                elif side == "right":
                    rotated = pygame.transform.rotate(blend_surf, 90)
                    screen.blit(rotated, (sx + ts - blend_size, sy))

    def _draw_tile_enhanced(self, screen: pygame.Surface, tile: Tile,
                            x: int, y: int, t: float):
        """Draw a single tile with enhanced visuals and animation."""
        ts = self.tile_size
        rect = pygame.Rect(x, y, ts, ts)

        # Use tile grid position as a seed for consistent random variation
        seed_val = tile.x * 7919 + tile.y * 6271

        if tile.type == TileType.GRASS:
            self._draw_grass_tile(screen, x, y, ts, seed_val)
        elif tile.type == TileType.TALL_GRASS:
            self._draw_tall_grass_tile(screen, x, y, ts, seed_val, t)
        elif tile.type == TileType.WATER:
            self._draw_water_tile(screen, x, y, ts, seed_val, t)
        elif tile.type == TileType.PATH:
            self._draw_path_tile(screen, x, y, ts, seed_val)
        elif tile.type == TileType.TREE:
            self._draw_tree_tile(screen, x, y, ts, seed_val, t)
        elif tile.type == TileType.BUILDING_WALL:
            self._draw_building_wall_tile(screen, x, y, ts, seed_val)
        elif tile.type == TileType.BUILDING_FLOOR:
            self._draw_building_floor_tile(screen, x, y, ts)
        elif tile.type == TileType.DOOR:
            self._draw_door_tile(screen, x, y, ts)
        elif tile.type == TileType.FLOWER:
            self._draw_flower_tile(screen, x, y, ts, seed_val, t)
        elif tile.type == TileType.ROCK:
            self._draw_rock_tile(screen, x, y, ts, seed_val)
        elif tile.type == TileType.SIGN:
            self._draw_sign_tile(screen, x, y, ts)
        elif tile.type == TileType.STAIRS:
            self._draw_stairs_tile(screen, x, y, ts)
        elif tile.type in (TileType.LEDGE_DOWN, TileType.LEDGE_LEFT, TileType.LEDGE_RIGHT):
            self._draw_ledge_tile(screen, x, y, ts, tile.type)
        else:
            pygame.draw.rect(screen, (50, 50, 50), rect)

    def _draw_grass_tile(self, screen, x, y, ts, seed):
        """Grass tile with varied green shades, texture dots, and blade accents."""
        # Base color with subtle per-tile variation
        r_var = (seed % 11) - 5
        g_var = (seed % 17) - 8
        base_r = max(0, min(255, 34 + r_var))
        base_g = max(0, min(255, 139 + g_var))
        base_b = max(0, min(255, 34 + r_var))
        pygame.draw.rect(screen, (base_r, base_g, base_b),
                         pygame.Rect(x, y, ts, ts))

        # Lighter dappled patches for depth
        rng = random.Random(seed)
        for _ in range(3):
            px = rng.randint(3, ts - 6)
            py = rng.randint(3, ts - 6)
            pw = rng.randint(4, 8)
            ph = rng.randint(4, 8)
            patch_color = (max(0, min(255, base_r + 12)),
                           max(0, min(255, base_g + 18)),
                           max(0, min(255, base_b + 8)))
            patch_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.ellipse(patch_surf, (*patch_color, 60),
                                pygame.Rect(0, 0, pw, ph))
            screen.blit(patch_surf, (x + px, y + py))

        # Texture dots -- small lighter/darker green specks
        for _ in range(6):
            dx = rng.randint(2, ts - 3)
            dy = rng.randint(2, ts - 3)
            shade = rng.choice([-15, -10, 10, 15, 20])
            c = (max(0, min(255, base_r + shade)),
                 max(0, min(255, base_g + shade)),
                 max(0, min(255, base_b + shade)))
            pygame.draw.circle(screen, c, (x + dx, y + dy), 1)

        # Small grass blade accents (4 tiny lines with varied lean)
        for i in range(4):
            bx = x + 4 + i * 7 + (seed % 3)
            by = y + ts - 3
            blade_len = 4 + (seed + i) % 5
            lean = ((seed + i * 3) % 7) - 3
            tip_color = (max(0, base_r - 10),
                         max(0, min(255, base_g + 15)),
                         max(0, base_b - 10))
            pygame.draw.line(screen, tip_color,
                             (bx, by), (bx + lean, by - blade_len), 1)
            # Highlight blade beside it
            if i % 2 == 0:
                pygame.draw.line(screen, (min(255, base_r + 20),
                                          min(255, base_g + 25),
                                          min(255, base_b + 15)),
                                 (bx + 1, by), (bx + lean + 1, by - blade_len + 1), 1)

    def _draw_tall_grass_tile(self, screen, x, y, ts, seed, t):
        """Tall grass with animated swaying blades and layered depth."""
        # Darker green base
        pygame.draw.rect(screen, (28, 100, 28), pygame.Rect(x, y, ts, ts))

        # Texture variation -- ground patches
        rng = random.Random(seed)
        for _ in range(5):
            dx = rng.randint(1, ts - 2)
            dy = rng.randint(1, ts - 2)
            patch_shade = rng.choice([(24, 85, 24), (22, 78, 22), (30, 92, 30)])
            pygame.draw.rect(screen, patch_shade,
                             pygame.Rect(x + dx, y + dy, 3, 2))

        # Animated grass blades -- sway with time (two layers for depth)
        sway = math.sin(t * 2.0 + seed * 0.1) * 3
        sway2 = math.sin(t * 2.4 + seed * 0.15 + 1.0) * 2.5

        # Background blades (darker, shorter)
        for i in range(4):
            bx = x + 2 + i * 8 + (seed % 4)
            by = y + ts - 4
            blade_h = 7 + (seed + i * 3) % 4
            lean = sway2 + ((seed + i * 5) % 5) - 2
            pygame.draw.line(screen, (18, 60, 18),
                             (bx, by), (int(bx + lean), int(by - blade_h)), 2)

        # Foreground blades (brighter, taller, thicker sway)
        num_blades = 6
        for i in range(num_blades):
            bx = x + 2 + i * 5 + (seed % 2)
            by = y + ts - 2
            blade_h = 10 + (seed + i) % 7
            lean = sway + ((seed + i * 7) % 5) - 2

            # Main blade
            pygame.draw.line(screen, (22, 80, 22),
                             (bx, by), (int(bx + lean), int(by - blade_h)), 2)
            # Highlight blade
            pygame.draw.line(screen, (45, 120, 45),
                             (bx + 1, by), (int(bx + lean + 1), int(by - blade_h + 2)), 1)
            # Blade tip accent
            if i % 2 == 0:
                pygame.draw.circle(screen, (55, 130, 40),
                                   (int(bx + lean), int(by - blade_h)), 1)

        # Subtle dark border to distinguish from regular grass
        pygame.draw.rect(screen, (20, 80, 20), pygame.Rect(x, y, ts, ts), 1)

    def _draw_water_tile(self, screen, x, y, ts, seed, t):
        """Water tile with animated ripple rings, color-shifting, and sparkle spots."""
        # Time-based color shifting for shimmering water surface
        phase = t * 1.5 + seed * 0.05
        r_shift = int(math.sin(phase) * 10)
        g_shift = int(math.sin(phase + 1.0) * 10)
        b_shift = int(math.cos(phase) * 8)

        base_r = max(0, min(255, 55 + r_shift))
        base_g = max(0, min(255, 100 + g_shift))
        base_b = max(0, min(255, 215 + b_shift))

        pygame.draw.rect(screen, (base_r, base_g, base_b),
                         pygame.Rect(x, y, ts, ts))

        # Subtle wave lines across the tile
        rng = random.Random(seed)
        for i in range(3):
            wave_y = y + 6 + i * 10
            wave_offset = math.sin(t * 1.2 + seed * 0.3 + i) * 3
            points = []
            for wx in range(0, ts, 4):
                wy = wave_y + int(math.sin(t + wx * 0.15 + seed * 0.1) * 1.5 + wave_offset)
                points.append((x + wx, wy))
            if len(points) >= 2:
                wave_color = (min(255, base_r + 15), min(255, base_g + 20), min(255, base_b + 5))
                pygame.draw.lines(screen, wave_color, False, points, 1)

        # Animated concentric ripple rings
        ripple_phase = t * 2.0 + seed * 0.3
        cx, cy = x + ts // 2 + rng.randint(-3, 3), y + ts // 2 + rng.randint(-3, 3)

        for i in range(3):
            rr = int((math.sin(ripple_phase + i * 1.2) + 1) * 5 + 3 + i * 3)
            if rr > 1:
                ripple_color = (
                    min(255, base_r + 30 + i * 10),
                    min(255, base_g + 30 + i * 10),
                    min(255, base_b + 10)
                )
                pygame.draw.circle(screen, ripple_color, (cx, cy), rr, 1)

        # Multiple sparkle / shine spots
        for s in range(2):
            sparkle_phase = t * 3.0 + seed + s * 4.1
            sp_x = x + 5 + int(math.sin(sparkle_phase) * 8) + s * 7
            sp_y = y + 5 + int(math.cos(sparkle_phase * 0.7) * 8)
            sp_x = max(x + 1, min(x + ts - 2, sp_x))
            sp_y = max(y + 1, min(y + ts - 2, sp_y))
            sparkle_alpha = (math.sin(sparkle_phase * 2 + s) + 1) * 0.5
            if sparkle_alpha > 0.55:
                pygame.draw.circle(screen, (200, 230, 255), (sp_x, sp_y), 2)
                pygame.draw.circle(screen, (255, 255, 255), (sp_x, sp_y), 1)
                # Cross sparkle lines
                if sparkle_alpha > 0.8:
                    pygame.draw.line(screen, (240, 245, 255),
                                     (sp_x - 2, sp_y), (sp_x + 2, sp_y), 1)
                    pygame.draw.line(screen, (240, 245, 255),
                                     (sp_x, sp_y - 2), (sp_x, sp_y + 2), 1)

    def _draw_path_tile(self, screen, x, y, ts, seed):
        """Path tile with sandy/brown base, scattered pebble dots, and crack lines."""
        # Base sandy/brown color with variation
        rng = random.Random(seed)
        r_var = rng.randint(-8, 8)
        base = (139 + r_var, 119 + r_var, 101 + r_var)
        pygame.draw.rect(screen, base, pygame.Rect(x, y, ts, ts))

        # Lighter dirt patches for depth
        for _ in range(2):
            px = rng.randint(3, ts - 8)
            py = rng.randint(3, ts - 8)
            pw = rng.randint(5, 10)
            ph = rng.randint(4, 7)
            patch_color = (min(255, base[0] + 15), min(255, base[1] + 12),
                           min(255, base[2] + 10))
            patch_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.ellipse(patch_surf, (*patch_color, 50),
                                pygame.Rect(0, 0, pw, ph))
            screen.blit(patch_surf, (x + px, y + py))

        # Scattered pebbles / texture dots
        for _ in range(7):
            px = rng.randint(2, ts - 3)
            py = rng.randint(2, ts - 3)
            shade = rng.randint(-20, 15)
            peb_color = (
                max(0, min(255, base[0] + shade)),
                max(0, min(255, base[1] + shade)),
                max(0, min(255, base[2] + shade))
            )
            size = rng.choice([1, 1, 2])
            pygame.draw.circle(screen, peb_color, (x + px, y + py), size)
            # Highlight on larger pebbles
            if size == 2:
                pygame.draw.circle(screen, (min(255, peb_color[0] + 30),
                                            min(255, peb_color[1] + 25),
                                            min(255, peb_color[2] + 20)),
                                   (x + px - 1, y + py - 1), 1)

        # Crack lines (more frequent, with forking)
        if seed % 3 != 2:
            cx1 = x + rng.randint(4, ts - 4)
            cy1 = y + rng.randint(4, ts // 2)
            cx2 = cx1 + rng.randint(-6, 6)
            cy2 = cy1 + rng.randint(4, 10)
            crack_color = (max(0, base[0] - 20), max(0, base[1] - 20),
                           max(0, base[2] - 20))
            pygame.draw.line(screen, crack_color, (cx1, cy1), (cx2, cy2), 1)
            # Fork
            if seed % 5 == 0:
                cx3 = cx2 + rng.randint(-4, 4)
                cy3 = cy2 + rng.randint(2, 5)
                pygame.draw.line(screen, crack_color, (cx2, cy2), (cx3, cy3), 1)

    def _draw_tree_tile(self, screen, x, y, ts, seed, t):
        """Tree tile with trunk, bark detail, multi-layered canopy, and subtle sway."""
        # Ground underneath
        pygame.draw.rect(screen, (34, 120, 34), pygame.Rect(x, y, ts, ts))

        # Ground shadow beneath trunk
        shadow_surf = pygame.Surface((16, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (10, 50, 10, 80),
                            pygame.Rect(0, 0, 16, 6))
        screen.blit(shadow_surf, (x + (ts - 16) // 2, y + ts - 6))

        # Tree trunk
        trunk_w = 6 + (seed % 3)
        trunk_x = x + (ts - trunk_w) // 2
        trunk_rect = pygame.Rect(trunk_x, y + 18, trunk_w, 14)
        pygame.draw.rect(screen, (101, 67, 33), trunk_rect)
        # Bark detail lines
        pygame.draw.line(screen, (80, 50, 25),
                         (trunk_x + 2, y + 19), (trunk_x + 2, y + 31), 1)
        pygame.draw.line(screen, (120, 80, 40),
                         (trunk_x + trunk_w - 2, y + 21), (trunk_x + trunk_w - 2, y + 29), 1)
        # Bark knot
        if seed % 3 == 0:
            pygame.draw.circle(screen, (85, 55, 28),
                               (trunk_x + trunk_w // 2, y + 24), 2)

        # Root flare at base of trunk
        pygame.draw.line(screen, (90, 60, 30),
                         (trunk_x - 1, y + 31), (trunk_x + 2, y + 28), 1)
        pygame.draw.line(screen, (90, 60, 30),
                         (trunk_x + trunk_w + 1, y + 31), (trunk_x + trunk_w - 2, y + 28), 1)

        # Canopy layers (bottom to top, lighter on top)
        sway = math.sin(t * 0.8 + seed * 0.2) * 1.5
        cx = x + ts // 2 + int(sway)
        cy = y + 12

        # Deep shadow / bottom canopy layer
        pygame.draw.circle(screen, (18, 55, 18), (cx + 1, cy + 3), 15)
        # Shadow canopy
        pygame.draw.circle(screen, (22, 70, 22), (cx, cy + 2), 14)
        # Main canopy
        pygame.draw.circle(screen, (34, 100, 34), (cx, cy), 13)
        # Mid highlight layer
        pygame.draw.circle(screen, (50, 120, 50), (cx - 2, cy - 2), 9)
        # Light highlight layer
        pygame.draw.circle(screen, (65, 135, 55), (cx - 3, cy - 4), 6)
        # Top bright highlight
        pygame.draw.circle(screen, (80, 155, 65), (cx - 4, cy - 6), 3)

        # Leaf texture dots on canopy
        rng = random.Random(seed)
        for _ in range(5):
            lx = cx + rng.randint(-10, 8)
            ly = cy + rng.randint(-10, 6)
            dist = ((lx - cx) ** 2 + (ly - cy) ** 2) ** 0.5
            if dist < 12:
                shade = rng.choice([(25, 85, 25), (45, 115, 45), (55, 130, 50)])
                pygame.draw.circle(screen, shade, (lx, ly), 1)

    def _draw_building_wall_tile(self, screen, x, y, ts, seed):
        """Building wall with brick pattern, mortar lines, and optional window details."""
        # Base wall color with slight variation
        r_var = (seed % 7) - 3
        base = (115 + r_var, 115 + r_var, 120 + r_var)
        pygame.draw.rect(screen, base, pygame.Rect(x, y, ts, ts))

        # Brick pattern with individual brick color variation
        brick_h = 8
        rng = random.Random(seed)
        for row in range(ts // brick_h):
            row_y = y + row * brick_h
            # Horizontal mortar line
            pygame.draw.line(screen, (90, 90, 95),
                             (x, row_y), (x + ts, row_y), 1)
            # Vertical mortar lines (offset every other row)
            offset = (row % 2) * 8
            for col_x in range(offset, ts, 16):
                pygame.draw.line(screen, (90, 90, 95),
                                 (x + col_x, row_y), (x + col_x, row_y + brick_h), 1)
                # Subtle individual brick shade
                brick_shade = rng.randint(-6, 6)
                brick_rect = pygame.Rect(x + col_x + 1, row_y + 1,
                                         min(15, ts - col_x - 1), brick_h - 1)
                brick_surf = pygame.Surface((brick_rect.w, brick_rect.h), pygame.SRCALPHA)
                brick_surf.fill((
                    max(0, min(255, 128 + brick_shade)),
                    max(0, min(255, 128 + brick_shade)),
                    max(0, min(255, 133 + brick_shade)),
                    15
                ))
                screen.blit(brick_surf, brick_rect.topleft)

        # Border
        pygame.draw.rect(screen, (80, 80, 85), pygame.Rect(x, y, ts, ts), 1)

        # Window detail (on some wall tiles based on seed)
        if seed % 4 == 0:
            win_rect = pygame.Rect(x + 8, y + 6, 16, 14)
            # Window recess shadow
            pygame.draw.rect(screen, (60, 60, 70),
                             pygame.Rect(x + 7, y + 5, 18, 16))
            pygame.draw.rect(screen, (140, 180, 220), win_rect)  # Glass
            pygame.draw.rect(screen, (70, 70, 80), win_rect, 1)  # Frame
            # Window cross
            pygame.draw.line(screen, (70, 70, 80),
                             (x + 16, y + 6), (x + 16, y + 20), 1)
            pygame.draw.line(screen, (70, 70, 80),
                             (x + 8, y + 13), (x + 24, y + 13), 1)
            # Shine / reflection
            pygame.draw.line(screen, (200, 220, 255),
                             (x + 10, y + 8), (x + 13, y + 8), 1)
            pygame.draw.line(screen, (180, 210, 245),
                             (x + 10, y + 9), (x + 11, y + 9), 1)
            # Windowsill
            pygame.draw.line(screen, (100, 100, 110),
                             (x + 7, y + 20), (x + 25, y + 20), 2)

    def _draw_building_floor_tile(self, screen, x, y, ts):
        """Building floor with checkerboard tile pattern and polish shine."""
        pygame.draw.rect(screen, (168, 168, 174), pygame.Rect(x, y, ts, ts))

        # Checkerboard sub-tiles with subtle color difference
        half = ts // 2
        for i in range(2):
            for j in range(2):
                sub_rect = pygame.Rect(x + i * half, y + j * half, half, half)
                if (i + j) % 2 == 0:
                    pygame.draw.rect(screen, (152, 152, 158), sub_rect)
                else:
                    pygame.draw.rect(screen, (172, 172, 178), sub_rect)

        # Grid / grout lines
        pygame.draw.line(screen, (135, 135, 140),
                         (x, y + half), (x + ts, y + half), 1)
        pygame.draw.line(screen, (135, 135, 140),
                         (x + half, y), (x + half, y + ts), 1)
        pygame.draw.rect(screen, (140, 140, 145), pygame.Rect(x, y, ts, ts), 1)

        # Subtle floor shine / polish highlight
        shine_surf = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.ellipse(shine_surf, (255, 255, 255, 12),
                            pygame.Rect(4, 2, ts - 8, ts // 2))
        screen.blit(shine_surf, (x, y))

    def _draw_door_tile(self, screen, x, y, ts):
        """Door tile with wood grain, handle, and frame detail."""
        # Door frame (outer)
        pygame.draw.rect(screen, (85, 50, 18), pygame.Rect(x, y, ts, ts))
        # Door frame (inner recess)
        pygame.draw.rect(screen, (100, 60, 20), pygame.Rect(x + 1, y + 1, ts - 2, ts - 1))

        # Door panel
        panel = pygame.Rect(x + 3, y + 3, ts - 6, ts - 3)
        pygame.draw.rect(screen, (150, 85, 30), panel)

        # Raised panel inset
        inset = pygame.Rect(x + 6, y + 5, ts - 12, ts // 2 - 2)
        pygame.draw.rect(screen, (160, 95, 38), inset)
        pygame.draw.rect(screen, (130, 70, 25), inset, 1)

        # Wood grain lines
        for i in range(4):
            gy = y + 5 + i * 7
            grain_color = (135, 72, 27) if i % 2 == 0 else (140, 78, 30)
            pygame.draw.line(screen, grain_color,
                             (x + 5, gy), (x + ts - 5, gy), 1)

        # Door handle with metal shine
        handle_x = x + ts - 9
        handle_y = y + ts // 2
        pygame.draw.circle(screen, (180, 160, 50), (handle_x, handle_y), 3)
        pygame.draw.circle(screen, (220, 200, 80), (handle_x, handle_y), 2)
        pygame.draw.circle(screen, (240, 225, 120), (handle_x - 1, handle_y - 1), 1)

        # Top frame molding
        pygame.draw.rect(screen, (75, 45, 15), pygame.Rect(x, y, ts, 3))
        # Bottom threshold
        pygame.draw.rect(screen, (90, 55, 20), pygame.Rect(x, y + ts - 2, ts, 2))

    def _draw_flower_tile(self, screen, x, y, ts, seed, t):
        """Flower tile with multiple small colored flowers, stems, petals, and bobbing."""
        # Grass base
        pygame.draw.rect(screen, (34, 139, 34), pygame.Rect(x, y, ts, ts))

        # Grass texture under flowers
        rng = random.Random(seed + 999)
        for _ in range(3):
            gx = rng.randint(2, ts - 3)
            gy = rng.randint(2, ts - 3)
            pygame.draw.circle(screen, (30, 130, 30), (x + gx, y + gy), 1)

        rng = random.Random(seed)
        # Multiple small flowers with varied colors
        flower_colors = [
            (255, 100, 100), (255, 200, 100), (200, 100, 255),
            (255, 150, 200), (100, 200, 255), (255, 255, 100),
            (255, 130, 60), (180, 120, 255),
        ]

        num_flowers = 3 + rng.randint(0, 3)
        for i in range(num_flowers):
            fx = x + rng.randint(5, ts - 6)
            fy = y + rng.randint(5, ts - 6)
            color = flower_colors[rng.randint(0, len(flower_colors) - 1)]

            # Subtle bobbing animation per flower
            bob = math.sin(t * 1.5 + seed + i * 2.0) * 1.2
            fy_bob = int(fy + bob)

            # Stem (slightly curved)
            stem_lean = int(math.sin(t * 0.8 + i) * 0.5)
            pygame.draw.line(screen, (25, 110, 25),
                             (fx, fy_bob + 3), (fx + stem_lean, fy_bob + 8), 1)
            # Leaf on stem
            if i % 2 == 0:
                leaf_dir = 1 if i % 4 == 0 else -1
                pygame.draw.line(screen, (35, 120, 30),
                                 (fx, fy_bob + 5),
                                 (fx + leaf_dir * 3, fy_bob + 4), 1)

            # Petals (5 for a more realistic look)
            petal_r = 2
            num_petals = 5
            for p in range(num_petals):
                a = p * (2 * math.pi / num_petals)
                px = int(fx + math.cos(a) * petal_r)
                py = int(fy_bob + math.sin(a) * petal_r)
                # Slightly darker petal edge
                pygame.draw.circle(screen, (max(0, color[0] - 30),
                                            max(0, color[1] - 30),
                                            max(0, color[2] - 30)),
                                   (px, py), 2)
                pygame.draw.circle(screen, color, (px, py), 1)

            # Center pistil
            pygame.draw.circle(screen, (255, 255, 80), (fx, fy_bob), 1)

    def _draw_rock_tile(self, screen, x, y, ts, seed):
        """Rock tile with 3D shading, highlight spots, and cracks."""
        # Ground base
        pygame.draw.rect(screen, (34, 139, 34), pygame.Rect(x, y, ts, ts))

        cx, cy = x + ts // 2, y + ts // 2 + 2
        r = 11 + (seed % 3)

        # Ground shadow beneath rock
        shadow_surf = pygame.Surface((r * 2 + 4, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (15, 60, 15, 90),
                            pygame.Rect(0, 0, r * 2 + 4, 10))
        screen.blit(shadow_surf, (cx - r - 2, cy + r - 6))

        # Main rock body (darker base)
        pygame.draw.circle(screen, (95, 95, 100), (cx + 1, cy + 1), r)
        # Mid-tone layer
        pygame.draw.circle(screen, (115, 115, 120), (cx, cy), r)
        # Top highlight gradient
        pygame.draw.circle(screen, (140, 140, 145), (cx - 2, cy - 2), r - 3)
        # Upper-left bright highlight
        pygame.draw.circle(screen, (165, 165, 170), (cx - 4, cy - 4), r - 6)
        # Specular bright spot
        pygame.draw.circle(screen, (190, 190, 195), (cx - 5, cy - 6), 3)
        pygame.draw.circle(screen, (210, 210, 215), (cx - 5, cy - 6), 1)

        # Dark edge arc (bottom-right shadow)
        pygame.draw.arc(screen, (70, 70, 75),
                        pygame.Rect(cx - r, cy - r, r * 2, r * 2),
                        3.5, 5.5, 2)

        # Surface crack detail
        rng = random.Random(seed)
        if seed % 3 == 0:
            c1x = cx + rng.randint(-4, 2)
            c1y = cy + rng.randint(-3, 3)
            c2x = c1x + rng.randint(-3, 3)
            c2y = c1y + rng.randint(2, 5)
            pygame.draw.line(screen, (85, 85, 90), (c1x, c1y), (c2x, c2y), 1)

    def _draw_sign_tile(self, screen, x, y, ts):
        """Sign post tile with wooden post and sign board detail."""
        # Ground base
        pygame.draw.rect(screen, (34, 139, 34), pygame.Rect(x, y, ts, ts))

        # Post shadow
        shadow_surf = pygame.Surface((8, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (15, 70, 15, 70),
                            pygame.Rect(0, 0, 8, 4))
        screen.blit(shadow_surf, (x + 12, y + ts - 3))

        # Wooden post
        pygame.draw.rect(screen, (90, 58, 28), pygame.Rect(x + 14, y + 18, 5, 14))
        # Post grain
        pygame.draw.line(screen, (75, 48, 22), (x + 15, y + 20), (x + 15, y + 30), 1)
        pygame.draw.line(screen, (105, 70, 35), (x + 17, y + 19), (x + 17, y + 31), 1)

        # Sign board
        sign_rect = pygame.Rect(x + 3, y + 3, 26, 17)
        pygame.draw.rect(screen, (175, 135, 75), sign_rect)
        # Board edge highlight (top/left)
        pygame.draw.line(screen, (195, 155, 95),
                         (x + 3, y + 3), (x + 29, y + 3), 1)
        pygame.draw.line(screen, (195, 155, 95),
                         (x + 3, y + 3), (x + 3, y + 20), 1)
        # Board shadow edge (bottom/right)
        pygame.draw.line(screen, (130, 95, 55),
                         (x + 3, y + 20), (x + 29, y + 20), 1)
        pygame.draw.line(screen, (130, 95, 55),
                         (x + 29, y + 3), (x + 29, y + 20), 1)
        # Frame border
        pygame.draw.rect(screen, (110, 80, 45), sign_rect, 2)

        # Text lines on sign
        pygame.draw.line(screen, (95, 65, 35), (x + 7, y + 8), (x + 25, y + 8), 1)
        pygame.draw.line(screen, (95, 65, 35), (x + 7, y + 12), (x + 22, y + 12), 1)
        pygame.draw.line(screen, (95, 65, 35), (x + 7, y + 16), (x + 18, y + 16), 1)

    def _draw_stairs_tile(self, screen, x, y, ts):
        """Stairs tile."""
        pygame.draw.rect(screen, (150, 150, 155), pygame.Rect(x, y, ts, ts))
        step_h = ts // 4
        for i in range(4):
            sy = y + i * step_h
            shade = 140 + i * 8
            pygame.draw.rect(screen, (shade, shade, shade + 5),
                             pygame.Rect(x, sy, ts, step_h))
            pygame.draw.line(screen, (120, 120, 125), (x, sy), (x + ts, sy), 1)

    def _draw_ledge_tile(self, screen, x, y, ts, ledge_type):
        """Ledge tile with directional indicator."""
        # Grass base
        pygame.draw.rect(screen, (34, 139, 34), pygame.Rect(x, y, ts, ts))

        # Ledge edge
        edge_color = (100, 85, 60)
        shadow_color = (70, 60, 40)

        if ledge_type == TileType.LEDGE_DOWN:
            pygame.draw.rect(screen, edge_color, pygame.Rect(x, y + ts - 6, ts, 6))
            pygame.draw.line(screen, shadow_color, (x, y + ts - 6), (x + ts, y + ts - 6), 2)
            # Arrow indicator
            pygame.draw.polygon(screen, (60, 50, 35),
                                [(x + ts // 2, y + ts - 2),
                                 (x + ts // 2 - 4, y + ts - 6),
                                 (x + ts // 2 + 4, y + ts - 6)])
        elif ledge_type == TileType.LEDGE_LEFT:
            pygame.draw.rect(screen, edge_color, pygame.Rect(x, y, 6, ts))
            pygame.draw.line(screen, shadow_color, (x + 6, y), (x + 6, y + ts), 2)
        elif ledge_type == TileType.LEDGE_RIGHT:
            pygame.draw.rect(screen, edge_color, pygame.Rect(x + ts - 6, y, 6, ts))
            pygame.draw.line(screen, shadow_color,
                             (x + ts - 6, y), (x + ts - 6, y + ts), 2)
    
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
            
            # Add clear path to Route 1 exit
            if 18 <= x <= 22 and y <= 5:
                town.set_tile(x, y, TileType.PATH)
            
            # Add trees for natural borders (denser forest feel)
            # Leave gap for Route 1 exit at top
            if x <= 2 or x >= 37 or y >= 27:
                town.set_tile(x, y, TileType.TREE)
            elif y <= 2:
                # Only add trees at top if not in exit area
                if x < 17 or x > 23:
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
    
    town.set_tile(20, 3, TileType.SIGN)
    town.add_object(MapObject(20, 3, "sign", {
        "text": "Route 1 - North\nWild Pokemon in tall grass!"
    }))
    
    # Add warps
    # Exit to Route 1 (multiple tiles for wider exit)
    for x in range(18, 23):
        town.add_warp(Warp(x, 0, "route_1", x, 38))
    
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

    # Viridian City - 40x40 map with Pokemon Center and Poke Mart
    viridian = Map("viridian_city", 40, 40, "Viridian City")

    for y in range(40):
        for x in range(40):
            # Default to grass
            viridian.set_tile(x, y, TileType.GRASS)

            # Tree borders (leave gaps for south and north exits)
            if x <= 1 or x >= 38:
                viridian.set_tile(x, y, TileType.TREE)
            elif y <= 1:
                # North border - leave gap at x 18-22 for blocked north exit
                if x < 17 or x > 23:
                    viridian.set_tile(x, y, TileType.TREE)
            elif y >= 38:
                # South border - leave gap at x 18-22 for Route 1 exit
                if x < 17 or x > 23:
                    viridian.set_tile(x, y, TileType.TREE)

            # Main east-west road
            if 18 <= y <= 21 and 3 <= x <= 37:
                viridian.set_tile(x, y, TileType.PATH)

            # Main north-south road (center)
            if 18 <= x <= 21:
                if 2 <= y <= 38:
                    viridian.set_tile(x, y, TileType.PATH)

            # Path to Pokemon Center (left side)
            if 5 <= x <= 17 and 18 <= y <= 21:
                viridian.set_tile(x, y, TileType.PATH)
            if 8 <= x <= 11 and 15 <= y <= 18:
                viridian.set_tile(x, y, TileType.PATH)

            # Path to Poke Mart (right side)
            if 21 <= x <= 32 and 18 <= y <= 21:
                viridian.set_tile(x, y, TileType.PATH)
            if 27 <= x <= 30 and 15 <= y <= 18:
                viridian.set_tile(x, y, TileType.PATH)

            # Tall grass patches on eastern edge
            if 32 <= x <= 36 and 6 <= y <= 12:
                if random.random() > 0.2:
                    viridian.set_tile(x, y, TileType.TALL_GRASS)
            if 33 <= x <= 37 and 28 <= y <= 34:
                if random.random() > 0.2:
                    viridian.set_tile(x, y, TileType.TALL_GRASS)

            # Tree clusters for natural feel
            if (4 <= x <= 7 and 4 <= y <= 8):
                if random.random() > 0.3:
                    viridian.set_tile(x, y, TileType.TREE)
            if (4 <= x <= 6 and 28 <= y <= 33):
                if random.random() > 0.3:
                    viridian.set_tile(x, y, TileType.TREE)

    # Pokemon Center building (left side, ~8x6 area)
    for by in range(10, 16):
        for bx in range(5, 13):
            if by == 10 or by == 15 or bx == 5 or bx == 12:
                viridian.set_tile(bx, by, TileType.BUILDING_WALL)
            else:
                viridian.set_tile(bx, by, TileType.BUILDING_FLOOR)
    viridian.set_tile(9, 15, TileType.DOOR)
    # Roof decoration
    for bx in range(6, 12):
        viridian.set_tile(bx, 9, TileType.ROCK)

    # Poke Mart building (right side, ~6x5 area)
    for by in range(11, 16):
        for bx in range(26, 32):
            if by == 11 or by == 15 or bx == 26 or bx == 31:
                viridian.set_tile(bx, by, TileType.BUILDING_WALL)
            else:
                viridian.set_tile(bx, by, TileType.BUILDING_FLOOR)
    viridian.set_tile(28, 15, TileType.DOOR)
    # Roof decoration
    for bx in range(27, 31):
        viridian.set_tile(bx, 10, TileType.ROCK)

    # House 1 (upper left area)
    for by in range(5, 10):
        for bx in range(10, 16):
            if by == 5 or by == 9 or bx == 10 or bx == 15:
                viridian.set_tile(bx, by, TileType.BUILDING_WALL)
            else:
                viridian.set_tile(bx, by, TileType.BUILDING_FLOOR)
    viridian.set_tile(12, 9, TileType.DOOR)

    # House 2 (lower left area)
    for by in range(25, 30):
        for bx in range(8, 14):
            if by == 25 or by == 29 or bx == 8 or bx == 13:
                viridian.set_tile(bx, by, TileType.BUILDING_WALL)
            else:
                viridian.set_tile(bx, by, TileType.BUILDING_FLOOR)
    viridian.set_tile(10, 29, TileType.DOOR)

    # House 3 (right side, lower)
    for by in range(24, 29):
        for bx in range(24, 30):
            if by == 24 or by == 28 or bx == 24 or bx == 29:
                viridian.set_tile(bx, by, TileType.BUILDING_WALL)
            else:
                viridian.set_tile(bx, by, TileType.BUILDING_FLOOR)
    viridian.set_tile(26, 28, TileType.DOOR)

    # Small pond / water feature (south-east area)
    for by in range(30, 33):
        for bx in range(30, 34):
            viridian.set_tile(bx, by, TileType.WATER)

    # Flower beds around town
    flower_spots_v = [
        (7, 17), (8, 17), (12, 17), (13, 17),
        (27, 17), (28, 17), (30, 17),
        (15, 23), (16, 23), (22, 23), (23, 23),
    ]
    for fx, fy in flower_spots_v:
        viridian.set_tile(fx, fy, TileType.FLOWER)

    # Signs
    viridian.set_tile(8, 16, TileType.SIGN)
    viridian.add_object(MapObject(8, 16, "sign", {
        "text": "Viridian City Pokemon Center\nHeal your Pokemon for free!"
    }))

    viridian.set_tile(28, 16, TileType.SIGN)
    viridian.add_object(MapObject(28, 16, "sign", {
        "text": "Viridian City Poke Mart\nFor all your Pokemon needs!"
    }))

    viridian.set_tile(20, 22, TileType.SIGN)
    viridian.add_object(MapObject(20, 22, "sign", {
        "text": "Viridian City\nThe Eternally Green Paradise"
    }))

    viridian.set_tile(20, 3, TileType.SIGN)
    viridian.add_object(MapObject(20, 3, "sign", {
        "text": "Route 2 - North\n(Currently closed)"
    }))

    # Warps - south exit to Route 1
    for wx in range(18, 23):
        viridian.add_warp(Warp(wx, 39, "route_1", wx, 1))

    # Wild pokemon data for the tall grass patches
    viridian.wild_pokemon_data = {
        "grass": [
            {"species": "Pidgey", "levels": [3, 6]},
            {"species": "Rattata", "levels": [3, 5]},
            {"species": "Nidoran", "levels": [4, 6]},
        ]
    }

    maps["viridian_city"] = viridian

    return maps