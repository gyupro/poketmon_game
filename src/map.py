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
from collections import deque
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
    COUNTER = 16  # Indoor furniture: shop counters, shelves, tables, beds
    ROOF = 17     # The body of an overworld building, seen from above


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
            TileType.SIGN,
            TileType.COUNTER,
            TileType.ROOF,
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

        # Per-tile render cache -- tiles are static after map construction, so most
        # tiles only need to be drawn (many primitives + RNG-derived detail) once and
        # then blitted every frame. Animated tile types (water/tall grass/flowers/trees)
        # are regenerated on a throttled interval instead of every frame. Without this,
        # a full map redraw (1000+ tiles, each several draw calls plus a fresh
        # random.Random(seed) object) costs ~70ms/frame -- far above a 16ms budget.
        # Animated tiles are refreshed round-robin under a per-frame budget
        # rather than all at once on a shared interval: refreshing every visible
        # animated tile on the same frame cost ~25ms and dropped a frame several
        # times a second, which read as the world hitching while walking.
        self._static_tile_cache: Dict[Tuple[int, int], pygame.Surface] = {}
        self._static_layer: Optional[pygame.Surface] = None
        self._anim_tile_cache: Dict[Tuple[int, int], pygame.Surface] = {}
        self._anim_cursor = 0
        
    def set_tile(self, x: int, y: int, tile_type: TileType):
        """Set a tile at the given position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = Tile(tile_type, x, y)
            self._static_layer = None  # must be recomposited
            self._static_tile_cache.pop((x, y), None)
            self._anim_tile_cache.pop((x, y), None)
            # A changed tile can also affect a neighbor's cached edge-blending
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                self._static_tile_cache.pop((nx, ny), None)
                self._anim_tile_cache.pop((nx, ny), None)
    
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
    
    # Tile types whose visuals change over time (sway/shimmer/bob) and therefore
    # can't be cached forever -- everything else is drawn once and reused.
    _ANIMATED_TYPES = {TileType.TALL_GRASS, TileType.WATER, TileType.FLOWER, TileType.TREE}

    # Animated tiles re-rendered per frame (~0.05ms each, so ~2ms of budget).
    _ANIM_REFRESH_BUDGET = 40

    def render(self, screen: pygame.Surface, camera_x: int = 0, camera_y: int = 0):
        """Render the map to the screen."""
        # Calculate visible tile range
        start_x = int(max(0, camera_x // self.tile_size))
        start_y = int(max(0, camera_y // self.tile_size))
        end_x = int(min(self.width, (camera_x + screen.get_width()) // self.tile_size + 1))
        end_y = int(min(self.height, (camera_y + screen.get_height()) // self.tile_size + 1))

        # Current time for animations
        t = time.time()
        ts = self.tile_size

        # The static tiles are pre-composited into one map-sized surface, so the
        # whole non-animated layer costs a single blit per frame instead of the
        # ~600 the viewport used to need.
        static_layer = self._get_static_layer(t)
        screen.blit(static_layer, (-camera_x, -camera_y))

        visible_animated = []

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.tiles[y][x]
                if not tile or tile.type not in self._ANIMATED_TYPES:
                    continue
                key = (x, y)
                visible_animated.append((key, tile))

                surf = self._anim_tile_cache.get(key)
                if surf is None:
                    surf = self._render_tile_surface(tile, x, y, t)
                    self._anim_tile_cache[key] = surf

                screen.blit(surf, (x * ts - camera_x, y * ts - camera_y))

        # Draw objects
        for obj in self.objects:
            if start_x <= obj.x < end_x and start_y <= obj.y < end_y:
                screen_x = obj.x * self.tile_size - camera_x
                screen_y = obj.y * self.tile_size - camera_y
                self._draw_object(screen, obj, screen_x, screen_y)

        self._refresh_animated_tiles(visible_animated, t)

    def _get_static_layer(self, t: float) -> pygame.Surface:
        """Build (once) a surface holding every non-animated tile of the map."""
        if self._static_layer is not None:
            return self._static_layer

        ts = self.tile_size
        layer = pygame.Surface((self.width * ts, self.height * ts), pygame.SRCALPHA)
        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                if not tile or tile.type in self._ANIMATED_TYPES:
                    continue
                key = (x, y)
                surf = self._static_tile_cache.get(key)
                if surf is None:
                    surf = self._render_tile_surface(tile, x, y, t)
                    self._static_tile_cache[key] = surf
                layer.blit(surf, (x * ts, y * ts))

        self._static_layer = layer.convert_alpha()
        return self._static_layer

    def _refresh_animated_tiles(self, visible_animated, t: float):
        """Re-render a bounded slice of the visible animated tiles.

        A viewport on a grassy route holds 400-500 animated tiles at ~0.05ms
        each, so refreshing them all on one frame costs 20-25ms and drops a
        frame. Instead a fixed number are refreshed per frame, round-robin, so
        the per-frame cost stays flat no matter how dense the map is. The tiles
        sway slightly out of phase with each other as a result, which reads as
        a wave rather than a glitch.
        """
        total = len(visible_animated)
        if total == 0:
            self._anim_cursor = 0
            return

        budget = min(self._ANIM_REFRESH_BUDGET, total)
        cursor = self._anim_cursor % total
        for i in range(budget):
            key, tile = visible_animated[(cursor + i) % total]
            self._anim_tile_cache[key] = self._render_tile_surface(tile, key[0], key[1], t)
        self._anim_cursor = (cursor + budget) % total

    def _render_tile_surface(self, tile: "Tile", grid_x: int, grid_y: int, t: float) -> pygame.Surface:
        """Render one tile (base art + edge blending) onto a small cacheable surface."""
        ts = self.tile_size
        surf = pygame.Surface((ts, ts), pygame.SRCALPHA)
        self._draw_tile_enhanced(surf, tile, 0, 0, t)
        self._draw_tile_blending(surf, tile, grid_x, grid_y, 0, 0)
        return surf

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
        elif tile.type == TileType.COUNTER:
            self._draw_counter_tile(screen, x, y, ts)
        elif tile.type == TileType.ROOF:
            self._draw_roof_tile(screen, x, y, ts, seed_val)
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
        """Tall grass with animated swaying blades and layered depth.

        Deliberately a distinctly richer/more saturated green than plain grass
        (rather than just darker) so encounter zones are unmistakable at a
        glance -- this tile is where wild Pokemon battles trigger.
        """
        # Vivid, saturated base -- clearly distinct from plain grass (34,139,34)
        pygame.draw.rect(screen, (46, 158, 42), pygame.Rect(x, y, ts, ts))

        # Texture variation -- ground patches
        rng = random.Random(seed)
        for _ in range(5):
            dx = rng.randint(1, ts - 2)
            dy = rng.randint(1, ts - 2)
            patch_shade = rng.choice([(38, 140, 34), (34, 130, 30), (52, 168, 46)])
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
            pygame.draw.line(screen, (26, 100, 24),
                             (bx, by), (int(bx + lean), int(by - blade_h)), 2)

        # Foreground blades (brighter, taller, thicker sway) -- denser than
        # before so the tile reads as a leafy patch, not just a green square
        num_blades = 8
        for i in range(num_blades):
            bx = x + 1 + i * 4 + (seed % 2)
            by = y + ts - 2
            blade_h = 11 + (seed + i) % 8
            lean = sway + ((seed + i * 7) % 5) - 2

            # Main blade
            pygame.draw.line(screen, (34, 120, 30),
                             (bx, by), (int(bx + lean), int(by - blade_h)), 2)
            # Highlight blade
            pygame.draw.line(screen, (90, 200, 60),
                             (bx + 1, by), (int(bx + lean + 1), int(by - blade_h + 2)), 1)
            # Blade tip accent
            if i % 2 == 0:
                pygame.draw.circle(screen, (110, 210, 70),
                                   (int(bx + lean), int(by - blade_h)), 1)

        # Strong dark border so the encounter-zone boundary is unmistakable
        pygame.draw.rect(screen, (14, 66, 16), pygame.Rect(x, y, ts, ts), 2)

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

    def _draw_roof_tile(self, screen, x, y, ts, seed):
        """Roof shingles for the body of an overworld building.

        Buildings used to be drawn with walkable floor tiles inside their
        footprint, which read as a room you ought to be able to walk into and
        left dead space on the map. The body is now solid roof, and the way in
        is the door on the front wall.
        """
        base = (176, 74, 66)
        pygame.draw.rect(screen, base, pygame.Rect(x, y, ts, ts))

        # Shingle courses, offset every other row so they interlock
        shade = (150, 60, 54)
        light = (198, 96, 86)
        row_h = ts // 4
        for row in range(4):
            ry = y + row * row_h
            offset = (row % 2) * (ts // 6)
            pygame.draw.line(screen, shade, (x, ry), (x + ts, ry), 1)
            for col in range(3):
                cx = x + offset + col * (ts // 3)
                if x <= cx <= x + ts:
                    pygame.draw.line(screen, shade, (cx, ry), (cx, ry + row_h), 1)
            pygame.draw.line(screen, light, (x, ry + 1), (x + ts, ry + 1), 1)

        # Slight per-tile weathering so a large roof isn't perfectly flat
        if seed % 4 == 0:
            weather = pygame.Surface((ts, ts), pygame.SRCALPHA)
            weather.fill((0, 0, 0, 18))
            screen.blit(weather, (x, y))

    def _draw_counter_tile(self, screen, x, y, ts):
        """Indoor furniture: a wooden counter/table sitting on the room floor.

        Interiors used to reuse ROCK for furniture, which drew boulders on a
        patch of grass in the middle of a Pokemon Center.
        """
        self._draw_building_floor_tile(screen, x, y, ts)

        top = pygame.Rect(x + 1, y + 4, ts - 2, ts - 10)
        pygame.draw.rect(screen, (150, 105, 62), top, border_radius=3)
        # Lit top surface
        pygame.draw.rect(screen, (178, 130, 82),
                         pygame.Rect(top.x + 2, top.y + 2, top.width - 4, top.height // 2),
                         border_radius=2)
        # Wood grain
        for i in range(2):
            gy = top.y + 6 + i * 6
            pygame.draw.line(screen, (128, 88, 50),
                             (top.x + 4, gy), (top.right - 4, gy), 1)
        # Front edge shadow and outline
        pygame.draw.rect(screen, (104, 70, 38),
                         pygame.Rect(top.x, top.bottom - 3, top.width, 3),
                         border_radius=2)
        pygame.draw.rect(screen, (86, 58, 32), top, 1, border_radius=3)

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



# ===========================================================================
# Map construction
#
# Every map is laid down in the same order: terrain, scenery, tree border,
# then roads, then buildings, then signs. Carving the roads after the border
# is what keeps entrances open -- the previous generator painted the tree
# border after the paths and so sealed Route 1's own exits shut.
#
# Doors are never placed by hand: _place_building puts the door on the front
# wall, _link_building wires it to an interior in both directions, and
# _connect_down carves a stub from it until it meets a road. validate_maps()
# re-checks all of it on every build.
# ===========================================================================

# Maps are generated from a fixed seed so a given build is always identical.
# They used to use the global RNG, so scenery landed differently on every
# launch and a tree could randomly close off a path.
MAP_SEED = 20240521

# Shared road geometry. The main north-south road occupies these columns on
# every outdoor map, so a town's exit always lines up with the route it leads
# to and the player walks through in a straight line.
GATE_COLS = range(18, 22)
GATE_X = 18
ROAD_W = 4

# Where a new game starts, and where a whited-out player is sent back to:
# the middle of Pallet Town's main road, in sight of the lab and the Center.
START_MAP = "pallet_town"
START_X = 20
START_Y = 20


def _fill(m: Map, x1: int, y1: int, x2: int, y2: int, tile: TileType):
    """Fill an inclusive rectangle, clipped to the map."""
    for y in range(max(0, y1), min(m.height, y2 + 1)):
        for x in range(max(0, x1), min(m.width, x2 + 1)):
            m.set_tile(x, y, tile)


def _scatter(m: Map, rng: random.Random, x1: int, y1: int, x2: int, y2: int,
             tile: TileType, density: float):
    """Randomly sprinkle a tile through a rectangle."""
    for y in range(max(0, y1), min(m.height, y2 + 1)):
        for x in range(max(0, x1), min(m.width, x2 + 1)):
            if rng.random() < density:
                m.set_tile(x, y, tile)


def _blob(m: Map, rng: random.Random, cx: int, cy: int, radius: int,
          tile: TileType, density: float = 0.75):
    """Sprinkle a tile inside a circle, for natural-looking clusters."""
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2 and rng.random() < density:
                m.set_tile(x, y, tile)


def _tree_border(m: Map, thickness: int = 2):
    """Ring the map in trees. Gates are carved back out by the roads."""
    _fill(m, 0, 0, m.width - 1, thickness - 1, TileType.TREE)
    _fill(m, 0, m.height - thickness, m.width - 1, m.height - 1, TileType.TREE)
    _fill(m, 0, 0, thickness - 1, m.height - 1, TileType.TREE)
    _fill(m, m.width - thickness, 0, m.width - 1, m.height - 1, TileType.TREE)


def _road(m: Map, points, width: int = ROAD_W, tile: TileType = TileType.PATH):
    """Carve a road along an axis-aligned polyline.

    A point is the top-left corner of the road band, so consecutive segments
    that share a corner always overlap -- the road cannot come out in
    disconnected pieces.
    """
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x1 == x2:
            _fill(m, x1, min(y1, y2), x1 + width - 1, max(y1, y2), tile)
        elif y1 == y2:
            _fill(m, min(x1, x2), y1, max(x1, x2), y1 + width - 1, tile)
        else:
            raise ValueError(
                f"road segment {(x1, y1)}->{(x2, y2)} is not axis aligned")


def _connect_down(m: Map, x: int, y: int, limit: int = 16) -> bool:
    """Carve straight down from (x, y) until an existing road is reached."""
    for step in range(limit):
        ty = y + step
        if ty >= m.height:
            return False
        tile = m.get_tile(x, ty)
        if tile and tile.type == TileType.PATH:
            return True
        m.set_tile(x, ty, TileType.PATH)
    return False


def _seal_pockets(m: Map, start: Tuple[int, int], fill: TileType = TileType.TREE):
    """Close off outdoor ground the player can never actually reach.

    Scenery clusters inevitably fence off the odd tile of grass. Left as-is
    those read as somewhere you ought to be able to walk to, so they are turned
    back into scenery. Building interiors are left alone -- they are meant to
    be sealed, and are entered through their door.
    """
    reachable = flood_fill(m, start)
    outdoor = {TileType.GRASS, TileType.TALL_GRASS, TileType.PATH, TileType.FLOWER}
    for y in range(m.height):
        for x in range(m.width):
            tile = m.tiles[y][x]
            if tile and tile.type in outdoor and (x, y) not in reachable:
                m.set_tile(x, y, fill)


def _place_building(m: Map, x: int, y: int, w: int, h: int, door_dx: int):
    """Draw a building: roof over the body, front wall along the bottom.

    The whole footprint is solid -- the only way in is the door, which leads to
    the building's interior map.
    """
    _fill(m, x, y, x + w - 1, y + h - 2, TileType.ROOF)
    _fill(m, x, y + h - 1, x + w - 1, y + h - 1, TileType.BUILDING_WALL)
    door = (x + door_dx, y + h - 1)
    m.set_tile(door[0], door[1], TileType.DOOR)
    return door


def _add_sign(m: Map, x: int, y: int, text: str):
    """Place a readable sign beside a road.

    Signs are solid, so one dropped onto a road narrows or blocks it. Refusing
    that here catches the mistake while the map is being built rather than
    leaving the player wedged against a signpost.
    """
    tile = m.get_tile(x, y)
    if tile is not None and tile.type == TileType.PATH:
        raise ValueError(f"{m.id}: sign at ({x},{y}) would block a road")
    if not any(m.is_walkable(x + dx, y + dy)
               for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))):
        raise ValueError(f"{m.id}: sign at ({x},{y}) cannot be reached to read")

    m.set_tile(x, y, TileType.SIGN)
    m.add_object(MapObject(x, y, "sign", {"text": text}))


def _build_interior(map_id: str, name: str, kind: str,
                    exit_map: str, exit_x: int, exit_y: int,
                    width: int = 11, height: int = 9) -> Map:
    """Build a room interior with a door back out onto the overworld.

    Furniture is kept off the door column so the way in and out is always
    clear, and shopkeepers stand at the head of that column where the player
    walks straight up to them.
    """
    room = Map(map_id, width, height, name)
    room.indoor = True

    _fill(room, 0, 0, width - 1, height - 1, TileType.BUILDING_WALL)
    _fill(room, 1, 1, width - 2, height - 2, TileType.BUILDING_FLOOR)

    door_x = width // 2
    room.set_tile(door_x, height - 1, TileType.DOOR)
    room.add_warp(Warp(door_x, height - 1, exit_map, exit_x, exit_y, "door"))

    if kind == "pokecenter":
        _fill(room, 2, 2, door_x - 1, 2, TileType.COUNTER)          # healing counter
        _fill(room, door_x + 1, 2, width - 3, 2, TileType.COUNTER)  # storage PC
    elif kind == "mart":
        _fill(room, 2, 2, door_x - 1, 2, TileType.COUNTER)          # shop counter
        _fill(room, door_x + 2, 2, width - 3, 3, TileType.COUNTER)  # shelves
    elif kind == "lab":
        _fill(room, 1, 2, door_x - 1, 2, TileType.COUNTER)          # bookshelves
        _fill(room, door_x + 1, 2, width - 2, 2, TileType.COUNTER)
        _fill(room, 2, 5, 3, 5, TileType.COUNTER)                   # research tables
        _fill(room, width - 4, 5, width - 3, 5, TileType.COUNTER)
    else:  # generic house
        _fill(room, 1, 2, 2, 3, TileType.COUNTER)                   # bed
        room.set_tile(width - 3, 2, TileType.COUNTER)               # table
        room.set_tile(width - 3, height - 3, TileType.COUNTER)      # dresser

    return room


def _link_building(overworld: Map, interiors: Dict[str, Map], door,
                   interior_id: str, name: str, kind: str, **room_kwargs) -> Map:
    """Wire a door on the overworld to a freshly built interior, both ways."""
    door_x, door_y = door
    step_out = (door_x, door_y + 1)

    room = _build_interior(interior_id, name, kind, overworld.id,
                           step_out[0], step_out[1], **room_kwargs)
    # Land one tile above the room's own exit door, so walking in doesn't drop
    # the player straight back onto the warp they just came through.
    overworld.add_warp(Warp(door_x, door_y, interior_id,
                            room.width // 2, room.height - 2, "door"))
    interiors[interior_id] = room
    return room


def _link_edges(a: Map, b: Map, columns, a_y: int, b_y: int,
                a_land_y: int, b_land_y: int):
    """Join two overworld maps along a shared edge, in both directions.

    The landing row sits one tile inside the destination's own gate row:
    landing straight onto the return warp would bounce the player back.
    """
    for x in columns:
        a.add_warp(Warp(x, a_y, b.id, x, b_land_y))
        b.add_warp(Warp(x, b_y, a.id, x, a_land_y))


# ---------------------------------------------------------------------------
# Individual maps
# ---------------------------------------------------------------------------

def _build_pallet_town(rng: random.Random) -> Tuple[Map, Dict[str, Map]]:
    """Pallet Town: a high street with buildings along it, gate north."""
    m = Map("pallet_town", 40, 30, "Pallet Town")
    interiors: Dict[str, Map] = {}

    # 1. terrain + scenery
    _fill(m, 0, 0, 39, 29, TileType.GRASS)
    _blob(m, rng, 6, 25, 4, TileType.TREE, 0.7)
    _blob(m, rng, 34, 25, 4, TileType.TREE, 0.7)
    _blob(m, rng, 35, 5, 3, TileType.TREE, 0.6)
    _fill(m, 8, 19, 10, 21, TileType.WATER)                    # village pond
    m.set_tile(7, 19, TileType.ROCK)
    m.set_tile(11, 21, TileType.ROCK)
    _scatter(m, rng, 5, 18, 15, 18, TileType.FLOWER, 0.25)
    _scatter(m, rng, 30, 19, 36, 22, TileType.FLOWER, 0.2)

    # 2. border, then 3. roads carved through it
    _tree_border(m, thickness=2)
    _road(m, [(GATE_X, 0), (GATE_X, 27)])                      # gate -> south
    _road(m, [(3, 14), (36, 14)])                              # high street
    _road(m, [(6, 24), (33, 24)], 3)                           # south lane

    # 4. buildings, each fronting a street
    pc_door = _place_building(m, 4, 6, 8, 7, 3)
    _link_building(m, interiors, pc_door, "pokecenter_1", "Pokemon Center", "pokecenter")
    _connect_down(m, pc_door[0], pc_door[1] + 1)

    lab_door = _place_building(m, 24, 5, 11, 8, 5)
    _link_building(m, interiors, lab_door, "oak_lab", "Prof. Oak's Lab", "lab",
                   width=13, height=10)
    _connect_down(m, lab_door[0], lab_door[1] + 1)

    home_door = _place_building(m, 12, 8, 6, 5, 2)
    _link_building(m, interiors, home_door, "player_house", "Your House", "house")
    _connect_down(m, home_door[0], home_door[1] + 1)

    rival_door = _place_building(m, 24, 18, 6, 5, 2)
    _link_building(m, interiors, rival_door, "rival_house", "Rival's House", "house")
    _connect_down(m, rival_door[0], rival_door[1] + 1)

    # 5. signs, placed beside a road so they can always be read
    _add_sign(m, pc_door[0] + 2, pc_door[1] + 1,
              "Pokemon Center\nRest and heal your Pokemon for free!")
    _add_sign(m, lab_door[0] + 2, lab_door[1] + 1,
              "Prof. Oak's Pokemon Lab\nWhere every journey begins.")
    _add_sign(m, 17, 4, "North: Route 1\nWild Pokemon hide in the tall grass.")
    _add_sign(m, 17, 18, "Welcome to Pallet Town!\nA quiet town of new beginnings.")

    _seal_pockets(m, (GATE_X, 20))
    m.background_music = "pallet_town.mp3"
    return m, interiors


def _build_route_1(rng: random.Random) -> Map:
    """Route 1: one continuous road from the Pallet gate to the Viridian gate."""
    m = Map("route_1", 40, 40, "Route 1")

    _fill(m, 0, 0, 39, 39, TileType.GRASS)

    # Tall grass for encounters, off to either side of where the road will run
    for x1, y1, x2, y2 in [(4, 4, 14, 14), (25, 6, 35, 17),
                           (3, 22, 11, 32), (26, 24, 36, 35),
                           (6, 34, 15, 37)]:
        _scatter(m, rng, x1, y1, x2, y2, TileType.TALL_GRASS, 0.82)

    _fill(m, 30, 11, 33, 14, TileType.WATER)                   # pond
    for cx, cy, r in [(23, 13, 4), (9, 18, 3), (31, 22, 3), (15, 33, 3)]:
        _blob(m, rng, cx, cy, r, TileType.TREE, 0.7)
    for x, y in [(6, 10), (14, 7), (26, 19), (33, 28), (8, 26), (17, 5)]:
        m.set_tile(x, y, TileType.ROCK)
    for fx, fy in [(7, 8), (12, 21), (27, 9), (34, 33)]:
        _blob(m, rng, fx, fy, 1, TileType.FLOWER, 0.6)

    _tree_border(m, thickness=2)

    # The road, carved last so neither gate can be closed off by the border or
    # by a scenery cluster. It runs gate to gate in one unbroken line.
    _road(m, [(GATE_X, 39), (GATE_X, 26), (13, 26), (13, 12),
              (GATE_X, 12), (GATE_X, 0)])

    _add_sign(m, 22, 36, "Route 1\nPallet Town is south, Viridian City is north.")
    _add_sign(m, 12, 16, "Tall grass ahead!\nWild Pokemon live in it.")

    _seal_pockets(m, (GATE_X, 30))
    m.wild_pokemon_data = {
        "grass": [
            {"species": "Pidgey", "levels": [2, 5]},
            {"species": "Rattata", "levels": [2, 4]},
            {"species": "Caterpie", "levels": [3, 5]},
        ]
    }
    m.background_music = "route_1.mp3"
    return m


def _build_viridian_city(rng: random.Random) -> Tuple[Map, Dict[str, Map]]:
    """Viridian City: three streets off one avenue, gate south to Route 1."""
    m = Map("viridian_city", 40, 40, "Viridian City")
    interiors: Dict[str, Map] = {}

    _fill(m, 0, 0, 39, 39, TileType.GRASS)
    _scatter(m, rng, 31, 24, 36, 28, TileType.TALL_GRASS, 0.8)
    _scatter(m, rng, 4, 33, 14, 36, TileType.TALL_GRASS, 0.8)
    _fill(m, 34, 10, 37, 13, TileType.WATER)                   # pond
    _blob(m, rng, 5, 22, 3, TileType.TREE, 0.6)
    _blob(m, rng, 36, 34, 3, TileType.TREE, 0.6)

    _tree_border(m, thickness=2)

    # The avenue stops short of the north border: Route 2 isn't in the game
    # yet, so there is deliberately no gap up there pretending to be an exit.
    _road(m, [(GATE_X, 39), (GATE_X, 6)])                      # main avenue
    _road(m, [(4, 18), (35, 18)])                              # central street
    _road(m, [(4, 6), (35, 6)], 3)                             # north street
    _road(m, [(6, 30), (33, 30)], 3)                           # south street

    buildings = [
        (5, 11, 9, 7, 4, "viridian_pokecenter", "Pokemon Center", "pokecenter"),
        (26, 11, 8, 7, 3, "viridian_mart", "Poke Mart", "mart"),
        (6, 2, 6, 4, 2, "viridian_house_1", "Viridian House", "house"),
        (26, 2, 6, 4, 2, "viridian_house_2", "Viridian House", "house"),
        (8, 25, 6, 5, 2, "viridian_house_3", "Viridian House", "house"),
        (24, 25, 6, 5, 2, "viridian_house_4", "Viridian House", "house"),
    ]
    doors = {}
    for bx, by, bw, bh, ddx, interior_id, name, kind in buildings:
        door = _place_building(m, bx, by, bw, bh, ddx)
        _link_building(m, interiors, door, interior_id, name, kind)
        _connect_down(m, door[0], door[1] + 1)
        doors[interior_id] = door

    # Signs sit on the grass strip beside each building, facing the street
    _add_sign(m, 14, 17, "Viridian City Pokemon Center\nHeal your Pokemon for free!")
    _add_sign(m, 25, 17, "Viridian City Poke Mart\nFor all your Pokemon needs!")
    _add_sign(m, 22, 22, "Viridian City\nThe Eternally Green Paradise.")
    _add_sign(m, 22, 10, "Route 2 is closed for now.\nCome back another day.")
    _add_sign(m, 17, 36, "South: Route 1\nPallet Town lies beyond.")

    _seal_pockets(m, (GATE_X, 20))
    m.wild_pokemon_data = {
        "grass": [
            {"species": "Pidgey", "levels": [3, 6]},
            {"species": "Rattata", "levels": [3, 5]},
            {"species": "Zubat", "levels": [4, 6]},
        ]
    }
    m.background_music = "viridian_city.mp3"
    return m, interiors


def create_sample_maps() -> Dict[str, Map]:
    """Build every map in the game.

    Tile layouts live here rather than in assets/maps/*.json -- the JSON files
    carry only metadata (NPCs, wild Pokemon, and a mirror of the connections
    for reference).
    """
    rng = random.Random(MAP_SEED)
    maps: Dict[str, Map] = {}

    town, town_interiors = _build_pallet_town(rng)
    route = _build_route_1(rng)
    viridian, viridian_interiors = _build_viridian_city(rng)

    # Gates line up column for column, and each landing row sits one tile
    # inside the destination's own gate row.
    _link_edges(town, route, GATE_COLS, a_y=0, b_y=39, a_land_y=1, b_land_y=38)
    _link_edges(route, viridian, GATE_COLS, a_y=0, b_y=39, a_land_y=1, b_land_y=38)

    for built in (town, route, viridian):
        maps[built.id] = built
    maps.update(town_interiors)
    maps.update(viridian_interiors)

    problems = validate_maps(maps)
    if problems:
        raise AssertionError(
            "map generation produced broken maps:\n  " + "\n  ".join(problems))
    return maps


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_maps(maps: Dict[str, Map]) -> List[str]:
    """Report the mistakes that break navigation.

    Run on every build so a broken layout fails loudly instead of shipping as
    a door that opens onto nothing or an exit walled in behind trees.
    """
    problems: List[str] = []

    def check(condition: bool, message: str):
        if not condition:
            problems.append(message)

    for map_id, m in maps.items():
        for warp in m.warps:
            check(m.is_walkable(warp.x, warp.y),
                  f"{map_id}: warp at ({warp.x},{warp.y}) sits on a solid tile")

            target = maps.get(warp.target_map)
            check(target is not None,
                  f"{map_id}: warp at ({warp.x},{warp.y}) targets unknown map "
                  f"'{warp.target_map}'")
            if target is None:
                continue

            check(target.is_walkable(warp.target_x, warp.target_y),
                  f"{map_id}: warp at ({warp.x},{warp.y}) lands on a solid tile in "
                  f"{warp.target_map} at ({warp.target_x},{warp.target_y})")
            check(target.get_warp_at(warp.target_x, warp.target_y) is None,
                  f"{map_id}: warp at ({warp.x},{warp.y}) lands on another warp in "
                  f"{warp.target_map} -- the player would bounce straight back")
            check(any(back.target_map == map_id for back in target.warps),
                  f"{map_id}: warp at ({warp.x},{warp.y}) to {warp.target_map} is "
                  f"one-way -- there is no way back")

        for y in range(m.height):
            for x in range(m.width):
                tile = m.tiles[y][x]
                if tile and tile.type == TileType.DOOR:
                    check(m.get_warp_at(x, y) is not None,
                          f"{map_id}: door at ({x},{y}) has no warp behind it")

        for obj in m.objects:
            if obj.object_type != "sign":
                continue
            tile = m.get_tile(obj.x, obj.y)
            check(tile is not None and tile.type == TileType.SIGN,
                  f"{map_id}: sign object at ({obj.x},{obj.y}) is not on a sign tile")
            check(any(m.is_walkable(obj.x + dx, obj.y + dy)
                      for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))),
                  f"{map_id}: sign at ({obj.x},{obj.y}) cannot be read from anywhere")

        # Every entrance must be reachable from every other one, or the player
        # can walk through a door and be unable to get back to the rest of the
        # map.
        entrances = [(w.x, w.y) for w in m.warps]
        if entrances:
            reachable = flood_fill(m, entrances[0])
            for x, y in entrances[1:]:
                check((x, y) in reachable,
                      f"{map_id}: warp at ({x},{y}) is cut off from the other exits")

    return problems


def flood_fill(m: Map, start: Tuple[int, int]) -> set:
    """Every tile walkable from `start`, treating warp tiles as walkable."""
    def passable(x: int, y: int) -> bool:
        return m.is_walkable(x, y) or m.get_warp_at(x, y) is not None

    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nxt = (x + dx, y + dy)
            if nxt not in seen and 0 <= nxt[0] < m.width and 0 <= nxt[1] < m.height \
                    and passable(*nxt):
                seen.add(nxt)
                queue.append(nxt)
    return seen
