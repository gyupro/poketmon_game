"""
World Management - Handles maps, NPCs, and world interactions
"""

import pygame
import random
import math
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .map import Map, TileType, Warp, MapObject, create_sample_maps
from .player import Player
from .pokemon import Pokemon, PokemonType
from .encounters import EncounterSystem


@dataclass
class NPC:
    """Represents a Non-Player Character."""
    name: str
    x: int
    y: int
    sprite: str
    dialogue: List[str]
    facing_direction: str = "down"
    movement_type: str = "static"  # static, wander, patrol
    movement_range: int = 2
    is_trainer: bool = False
    trainer_data: Optional[Dict] = None
    defeated: bool = False
    item_gift: Optional[str] = None
    given_item: bool = False
    is_healer: bool = False  # For Pokemon Center healing

    def __post_init__(self):
        # Store original position for wander range checks
        self.origin_x = self.x
        self.origin_y = self.y


class World:
    """Manages the game world, maps, and interactions."""
    
    def __init__(self):
        # Load all maps
        self.maps: Dict[str, Map] = create_sample_maps()
        self.current_map_id = "pallet_town"
        self.current_map = self.maps[self.current_map_id]
        
        # Camera settings (smooth lerp)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.camera_target_x = 0.0
        self.camera_target_y = 0.0
        self.camera_lerp_speed = 6.0  # Higher = snappier, lower = smoother
        self.screen_width = 1280
        self.screen_height = 800

        # Map transition effect
        self.map_transition_active = False
        self.map_transition_phase = "none"  # "fade_out", "fade_in", "none"
        self.map_transition_alpha = 0
        self.map_transition_speed = 600  # alpha per second
        self.pending_warp = None  # Warp to execute after fade-out

        # Area name banner
        self.area_banner_text = ""
        self.area_banner_timer = 0.0
        self.area_banner_duration = 3.0
        self.area_banner_active = False
        self.last_area_name = ""

        # Ambient effects
        self.ambient_particles = []  # grass particles, water sparkles
        self.ambient_timer = 0.0

        # Day/night tint
        self.day_night_enabled = True
        
        # NPCs for each map
        self.npcs: Dict[str, List[NPC]] = {
            "pallet_town": self._create_pallet_town_npcs(),
            "route_1": self._create_route_1_npcs(),
            "pokecenter_1": self._create_pokecenter_npcs()
        }
        
        # Interaction state
        self.current_dialogue: Optional[List[str]] = None
        self.dialogue_index = 0
        self.interaction_cooldown = 0.0
        
        # Wild encounter system
        self.encounter_system = EncounterSystem()
        self.steps_in_grass = 0  # Consecutive steps in tall grass
        self.last_encounter_position = None
        
    def _create_pallet_town_npcs(self) -> List[NPC]:
        """Create NPCs for Pallet Town."""
        npcs = []
        
        # Professor Oak
        oak = NPC(
            name="Professor Oak",
            x=9, y=9,
            sprite="prof_oak",
            dialogue=[
                "Hello there! Welcome to the world of Pokemon!",
                "My name is Oak. People call me the Pokemon Professor!",
                "This world is inhabited by creatures called Pokemon!",
                "For some people, Pokemon are pets. Others use them for fights.",
                "Myself... I study Pokemon as a profession."
            ],
            item_gift="pokedex",
            movement_type="wander",
            movement_range=2
        )
        npcs.append(oak)
        
        # Rival
        rival = NPC(
            name="Gary",
            x=14, y=13,
            sprite="rival",
            dialogue=[
                "Hey! I'm Gary, Professor Oak's grandson!",
                "I'm going to be the world's greatest Pokemon trainer!",
                "You better not get in my way!"
            ],
            is_trainer=True,
            trainer_data={
                "team": [
                    {"species": "Eevee", "level": 5}
                ],
                "reward_money": 100
            }
        )
        npcs.append(rival)
        
        # Town Kid
        kid = NPC(
            name="Young Boy",
            x=6, y=10,
            sprite="youngster",
            dialogue=[
                "Technology is amazing!",
                "You can now store and recall Pokemon from PCs!"
            ]
        )
        npcs.append(kid)
        
        return npcs
    
    def _create_route_1_npcs(self) -> List[NPC]:
        """Create NPCs for Route 1."""
        npcs = []
        
        # Bug Catcher
        bug_catcher = NPC(
            name="Bug Catcher Rick",
            x=10, y=8,
            sprite="bug_catcher",
            dialogue=[
                "Hey! You can't just walk past a trainer!",
                "Let's battle!"
            ],
            is_trainer=True,
            trainer_data={
                "team": [
                    {"species": "Pikachu", "level": 4},
                    {"species": "Bulbasaur", "level": 4}
                ],
                "reward_money": 50
            }
        )
        npcs.append(bug_catcher)
        
        # Item NPC
        item_guy = NPC(
            name="Helpful Man",
            x=9, y=15,
            sprite="gentleman",
            dialogue=[
                "Are you going to Viridian City?",
                "Here, take this Potion. It might help you!"
            ],
            item_gift="potion"
        )
        npcs.append(item_guy)
        
        return npcs
    
    def _create_pokecenter_npcs(self) -> List[NPC]:
        """Create NPCs for Pokemon Center."""
        npcs = []
        
        # Nurse Joy
        nurse_joy = NPC(
            name="Nurse Joy",
            x=7, y=5,
            sprite="nurse_joy",
            dialogue=[
                "Welcome to the Pokemon Center!",
                "Would you like me to heal your Pokemon?",
                "...healing complete! Your Pokemon are fully healed!",
                "We hope to see you again!"
            ],
            facing_direction="down",
            movement_type="static"
        )
        # Mark as special healing NPC
        nurse_joy.is_healer = True
        npcs.append(nurse_joy)
        
        # PC User
        pc_user = NPC(
            name="Trainer",
            x=3, y=8,
            sprite="trainer",
            dialogue=[
                "The PC is great for storing extra Pokemon!",
                "You can store up to 30 Pokemon in each box."
            ],
            facing_direction="up"
        )
        npcs.append(pc_user)
        
        return npcs
    
    def update(self, dt: float, player: Player):
        """Update world state."""
        # Update map transition effect
        if self.map_transition_active:
            self._update_map_transition(dt, player)
            return None  # Block other updates during transition

        # Update camera to follow player (smooth lerp)
        self._update_camera(dt, player)

        # Update NPCs
        self._update_npcs(dt)

        # Update ambient effects
        self._update_ambient(dt, player)

        # Update area banner
        if self.area_banner_active:
            self.area_banner_timer += dt
            if self.area_banner_timer >= self.area_banner_duration:
                self.area_banner_active = False

        # Update interaction cooldown
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= dt

        # Check for wild encounters if player moved
        if not player.is_moving and not self.current_dialogue:
            grid_x, grid_y = player.get_grid_position()

            # Check if in tall grass
            if self.current_map.check_wild_encounter(grid_x, grid_y):
                # Track consecutive steps in grass
                if self.last_encounter_position != (grid_x, grid_y):
                    self.steps_in_grass += 1
                    self.last_encounter_position = (grid_x, grid_y)

                    # Check if encounter should occur
                    if self.encounter_system.should_encounter(self.current_map_id, self.steps_in_grass):
                        # Check if repel is active
                        lead_pokemon = player.active_pokemon if hasattr(player, 'active_pokemon') and player.active_pokemon else None
                        lead_level = lead_pokemon.level if lead_pokemon else 1

                        if not self.encounter_system.check_repel(lead_level):
                            self.steps_in_grass = 0
                            return "wild_encounter"
            else:
                # Reset grass counter when not in grass
                self.steps_in_grass = 0
                self.last_encounter_position = None

        return None

    def _update_map_transition(self, dt: float, player: Player):
        """Update map transition fade effect."""
        if self.map_transition_phase == "fade_out":
            self.map_transition_alpha = min(255,
                                            self.map_transition_alpha + int(self.map_transition_speed * dt))
            if self.map_transition_alpha >= 255:
                # Fully faded out -- execute the warp
                if self.pending_warp:
                    warp = self.pending_warp
                    self._execute_map_change(warp.target_map, warp.target_x, warp.target_y, player)
                    self.pending_warp = None
                self.map_transition_phase = "fade_in"
        elif self.map_transition_phase == "fade_in":
            self.map_transition_alpha = max(0,
                                            self.map_transition_alpha - int(self.map_transition_speed * dt))
            if self.map_transition_alpha <= 0:
                self.map_transition_active = False
                self.map_transition_phase = "none"

    def _update_camera(self, dt: float, player: Player):
        """Update camera position with smooth lerp following."""
        # Calculate target position centered on player
        target_x = player.pixel_x - self.screen_width // 2
        target_y = player.pixel_y - self.screen_height // 2

        # Clamp target to map bounds (prevent showing void)
        max_x = max(0, self.current_map.width * self.current_map.tile_size - self.screen_width)
        max_y = max(0, self.current_map.height * self.current_map.tile_size - self.screen_height)

        clamped_x = max(0, min(target_x, max_x))
        clamped_y = max(0, min(target_y, max_y))

        # Smooth lerp interpolation
        lerp_factor = min(1.0, self.camera_lerp_speed * dt)
        self.camera_x += (clamped_x - self.camera_x) * lerp_factor
        self.camera_y += (clamped_y - self.camera_y) * lerp_factor

    def _update_ambient(self, dt: float, player: Player):
        """Update ambient particle effects."""
        self.ambient_timer += dt

        # Spawn grass particles near tall grass tiles in view
        if random.random() < 0.08:  # ~8% chance per frame
            # Pick a random spot in the viewport
            rand_screen_x = random.randint(0, self.screen_width)
            rand_screen_y = random.randint(0, self.screen_height)
            world_x = int((rand_screen_x + self.camera_x) // self.current_map.tile_size)
            world_y = int((rand_screen_y + self.camera_y) // self.current_map.tile_size)

            tile = self.current_map.get_tile(world_x, world_y)
            if tile:
                if tile.type == TileType.TALL_GRASS:
                    # Spawn a leaf particle
                    self.ambient_particles.append({
                        'type': 'leaf',
                        'x': float(rand_screen_x),
                        'y': float(rand_screen_y),
                        'vx': random.uniform(-0.5, 0.5),
                        'vy': random.uniform(-1.5, -0.5),
                        'life': 1.0,
                        'size': random.randint(2, 3),
                    })
                elif tile.type == TileType.WATER:
                    # Spawn a sparkle particle
                    self.ambient_particles.append({
                        'type': 'sparkle',
                        'x': float(rand_screen_x),
                        'y': float(rand_screen_y),
                        'vx': 0,
                        'vy': 0,
                        'life': 1.0,
                        'size': random.randint(1, 2),
                    })

        # Update existing particles
        for p in self.ambient_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if p['type'] == 'leaf':
                p['vy'] += 0.05  # gravity
                p['vx'] += math.sin(self.ambient_timer * 3 + p['x'] * 0.1) * 0.02
            p['life'] -= dt * 1.5
        self.ambient_particles = [p for p in self.ambient_particles if p['life'] > 0]

        # Cap particles
        if len(self.ambient_particles) > 40:
            self.ambient_particles = self.ambient_particles[-40:]
    
    def _update_npcs(self, dt: float):
        """Update NPC behaviors."""
        npcs = self.npcs.get(self.current_map_id, [])
        
        for npc in npcs:
            if npc.movement_type == "wander":
                # Random movement for wandering NPCs
                if random.randint(1, 300) == 1:  # Small chance each frame
                    directions = ["up", "down", "left", "right"]
                    direction = random.choice(directions)
                    dx, dy = 0, 0
                    
                    if direction == "up":
                        dy = -1
                    elif direction == "down":
                        dy = 1
                    elif direction == "left":
                        dx = -1
                    elif direction == "right":
                        dx = 1
                    
                    new_x = npc.x + dx
                    new_y = npc.y + dy
                    
                    # Check movement range from origin and collision
                    if (abs(new_x - npc.origin_x) <= npc.movement_range and
                        abs(new_y - npc.origin_y) <= npc.movement_range and
                        self.current_map.is_walkable(new_x, new_y) and
                        not self._is_npc_at(new_x, new_y)):
                        npc.x = new_x
                        npc.y = new_y
                        npc.facing_direction = direction
    
    def _is_npc_at(self, x: int, y: int) -> bool:
        """Check if an NPC is at the given position."""
        npcs = self.npcs.get(self.current_map_id, [])
        for npc in npcs:
            if npc.x == x and npc.y == y:
                return True
        return False
    
    def can_move_to(self, x: int, y: int) -> bool:
        """Check if a position can be moved to."""
        # Check map collision
        if not self.current_map.is_walkable(x, y):
            return False
        
        # Check NPC collision
        if self._is_npc_at(x, y):
            return False
        
        return True
    
    def interact(self, player: Player) -> Optional[Dict]:
        """Handle player interaction."""
        if self.interaction_cooldown > 0:
            return None
        
        # Get position player is facing
        facing_x, facing_y = player.get_facing_position()
        
        # Check for NPC interaction
        npcs = self.npcs.get(self.current_map_id, [])
        for npc in npcs:
            if npc.x == facing_x and npc.y == facing_y:
                self.interaction_cooldown = 0.5
                
                # Start dialogue
                self.current_dialogue = npc.dialogue.copy()
                self.dialogue_index = 0
                
                # Face the player
                if player.facing_direction == "up":
                    npc.facing_direction = "down"
                elif player.facing_direction == "down":
                    npc.facing_direction = "up"
                elif player.facing_direction == "left":
                    npc.facing_direction = "right"
                elif player.facing_direction == "right":
                    npc.facing_direction = "left"
                
                return {
                    "type": "npc",
                    "npc": npc,
                    "dialogue": self.current_dialogue[0]
                }
        
        # Check for map object interaction
        obj = self.current_map.get_object_at(facing_x, facing_y)
        if obj:
            self.interaction_cooldown = 0.5
            
            if obj.object_type == "sign":
                self.current_dialogue = [obj.data.get("text", "...")]
                self.dialogue_index = 0
                return {
                    "type": "sign",
                    "dialogue": self.current_dialogue[0]
                }
        
        return None
    
    def advance_dialogue(self) -> Optional[str]:
        """Advance to next dialogue line."""
        if not self.current_dialogue:
            return None
        
        self.dialogue_index += 1
        
        if self.dialogue_index >= len(self.current_dialogue):
            # Dialogue finished
            self.current_dialogue = None
            self.dialogue_index = 0
            return None
        
        return self.current_dialogue[self.dialogue_index]
    
    def change_map(self, new_map_id: str, x: int, y: int, player: Player, immediate: bool = False):
        """Start a fade-to-black map transition, or execute immediately."""
        if new_map_id not in self.maps:
            return
        if immediate:
            self._execute_map_change(new_map_id, x, y, player)
            return
        # Start fade-out transition
        self.map_transition_active = True
        self.map_transition_phase = "fade_out"
        self.map_transition_alpha = 0
        self.pending_warp = Warp(0, 0, new_map_id, x, y)

    def _execute_map_change(self, new_map_id: str, x: int, y: int, player: Player):
        """Actually swap the map data (called during transition)."""
        old_map_id = self.current_map_id

        self.current_map_id = new_map_id
        self.current_map = self.maps[new_map_id]

        # Update player position
        player.grid_x = x
        player.grid_y = y
        player.pixel_x = x * player.TILE_SIZE
        player.pixel_y = y * player.TILE_SIZE
        player.target_x = player.pixel_x
        player.target_y = player.pixel_y

        # Snap camera to new position immediately
        target_cx = player.pixel_x - self.screen_width // 2
        target_cy = player.pixel_y - self.screen_height // 2
        max_cx = max(0, self.current_map.width * self.current_map.tile_size - self.screen_width)
        max_cy = max(0, self.current_map.height * self.current_map.tile_size - self.screen_height)
        self.camera_x = float(max(0, min(target_cx, max_cx)))
        self.camera_y = float(max(0, min(target_cy, max_cy)))

        # Reset encounter counters
        self.steps_in_grass = 0
        self.last_encounter_position = None

        if new_map_id != old_map_id:
            self.encounter_system.break_chain()

        # Show area name banner if entering a new named area
        area_name = self.current_map.name
        if area_name and area_name != self.last_area_name:
            self.last_area_name = area_name
            self.area_banner_text = area_name
            self.area_banner_timer = 0.0
            self.area_banner_active = True

    def check_warps(self, player: Player):
        """Check if player stepped on a warp."""
        if self.map_transition_active:
            return  # Don't warp during an active transition
        grid_x, grid_y = player.get_grid_position()
        warp = self.current_map.get_warp_at(grid_x, grid_y)

        if warp:
            self.change_map(warp.target_map, warp.target_x, warp.target_y, player)
    
    def render(self, screen: pygame.Surface, player: Player):
        """Render the world with all visual enhancements."""
        cam_x = int(self.camera_x)
        cam_y = int(self.camera_y)

        # Draw map
        self.current_map.render(screen, cam_x, cam_y)

        # Draw NPCs
        npcs = self.npcs.get(self.current_map_id, [])
        for npc in npcs:
            self._render_npc(screen, npc, player)

        # Draw player
        player.render(screen, cam_x, cam_y)

        # Draw ambient particles
        self._render_ambient(screen)

        # Day/night tint overlay
        if self.day_night_enabled:
            self._render_day_night_tint(screen)

        # Draw dialogue box if active
        if self.current_dialogue:
            self._render_dialogue(screen)

        # Draw area name banner
        if self.area_banner_active:
            self._render_area_banner(screen)

        # Draw map transition overlay (fade to/from black)
        if self.map_transition_active:
            self._render_map_transition(screen)
    
    def _render_npc(self, screen: pygame.Surface, npc: NPC, player: Player):
        """Render an NPC with detailed visuals, per-type outfits, and indicators."""
        ts = self.current_map.tile_size
        cam_x = int(self.camera_x)
        cam_y = int(self.camera_y)
        sx = npc.x * ts - cam_x
        sy = npc.y * ts - cam_y

        t = time.time()

        # Position-based seed for consistent per-NPC variation
        pos_seed = npc.x * 7919 + npc.y * 6271

        # Idle breathing/bobbing animation
        bob = math.sin(t * 2.5 + pos_seed * 0.1) * 1.5
        sy_bob = int(sy + bob)

        # Choose outfit colors based on NPC type/sprite
        # (shirt/coat color, pants/skirt color, label, has_apron)
        outfit_map = {
            "prof_oak":    ((240, 240, 240), (140, 100, 60)),    # White lab coat, brown pants
            "rival":       ((120, 50, 180),  (60, 60, 80)),      # Purple jacket, dark pants
            "youngster":   ((255, 180, 50),  (100, 60, 30)),     # Orange shirt, shorts
            "bug_catcher": ((80, 180, 80),   (60, 80, 40)),      # Green outfit
            "gentleman":   ((50, 50, 60),    (40, 40, 50)),      # Dark suit
            "nurse_joy":   ((255, 150, 180), (255, 240, 245)),   # Pink top, white skirt
            "trainer":     ((200, 50, 50),   (50, 50, 70)),      # Red shirt, dark pants
            "lass":        ((255, 130, 160), (100, 100, 200)),   # Pink top, blue skirt
            "hiker":       ((140, 100, 60),  (80, 60, 40)),      # Brown outfit
            "swimmer":     ((60, 140, 220),  (60, 140, 220)),    # Blue swimwear
            "rocket":      ((40, 40, 40),    (40, 40, 40)),      # All black
        }
        sprite_key = npc.sprite if npc.sprite in outfit_map else "trainer"
        shirt_color, pants_color = outfit_map[sprite_key]

        # Override for defeated trainers (greyed out)
        if npc.is_trainer and npc.defeated:
            shirt_color = (120, 120, 120)
            pants_color = (90, 90, 90)

        # Derived darker/lighter shades for detail
        shirt_dark = (max(0, shirt_color[0] - 30),
                      max(0, shirt_color[1] - 30),
                      max(0, shirt_color[2] - 30))
        shirt_light = (min(255, shirt_color[0] + 25),
                       min(255, shirt_color[1] + 25),
                       min(255, shirt_color[2] + 25))

        # --- Shadow ---
        shadow_surf = pygame.Surface((ts + 2, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50),
                            pygame.Rect(5, 0, ts - 8, 8))
        screen.blit(shadow_surf, (sx - 1, sy + ts - 5))

        # --- Shoes ---
        body_y = sy_bob + 13
        leg_y = body_y + 12
        shoe_y = leg_y + 5
        shoe_color = (60, 40, 25) if sprite_key != "nurse_joy" else (255, 255, 255)
        pygame.draw.rect(screen, shoe_color,
                         pygame.Rect(sx + 8, shoe_y, 6, 2))
        pygame.draw.rect(screen, shoe_color,
                         pygame.Rect(sx + ts - 14, shoe_y, 6, 2))

        # --- Legs ---
        pygame.draw.rect(screen, pants_color,
                         pygame.Rect(sx + 9, leg_y, 5, 6), border_radius=1)
        pygame.draw.rect(screen, pants_color,
                         pygame.Rect(sx + ts - 14, leg_y, 5, 6), border_radius=1)

        # --- Body ---
        body_rect = pygame.Rect(sx + 7, body_y, ts - 14, 12)
        pygame.draw.rect(screen, shirt_color, body_rect, border_radius=2)
        # Shading on body (left lighter, right darker)
        pygame.draw.rect(screen, shirt_light,
                         pygame.Rect(sx + 7, body_y + 1, (ts - 14) // 2, 10),
                         border_radius=1)
        # Center detail line
        pygame.draw.line(screen, shirt_dark,
                         (sx + ts // 2, body_y + 2),
                         (sx + ts // 2, body_y + 10), 1)

        # Special details per NPC type
        if sprite_key == "prof_oak":
            # Lab coat collar
            pygame.draw.line(screen, (220, 220, 225),
                             (sx + 9, body_y), (sx + ts - 9, body_y), 2)
            # Coat pocket
            pygame.draw.rect(screen, (220, 220, 225),
                             pygame.Rect(sx + 9, body_y + 7, 5, 3), 1)
        elif sprite_key == "nurse_joy":
            # Nurse cross emblem
            cross_x = sx + ts // 2
            cross_y = body_y + 4
            pygame.draw.line(screen, (255, 50, 50),
                             (cross_x - 2, cross_y), (cross_x + 2, cross_y), 2)
            pygame.draw.line(screen, (255, 50, 50),
                             (cross_x, cross_y - 2), (cross_x, cross_y + 2), 2)
            # White apron
            pygame.draw.rect(screen, (255, 255, 255),
                             pygame.Rect(sx + 9, body_y + 8, ts - 18, 4))
        elif sprite_key == "rival":
            # Pendant / chain
            pygame.draw.circle(screen, (220, 200, 80),
                               (sx + ts // 2, body_y + 2), 1)

        # --- Arms ---
        arm_skin = (255, 210, 175)
        arm_y = body_y + 2
        if npc.facing_direction in ("down", "up"):
            pygame.draw.rect(screen, shirt_color,
                             pygame.Rect(sx + 4, arm_y, 3, 3))
            pygame.draw.rect(screen, arm_skin,
                             pygame.Rect(sx + 4, arm_y + 3, 3, 5))
            pygame.draw.rect(screen, shirt_color,
                             pygame.Rect(sx + ts - 7, arm_y, 3, 3))
            pygame.draw.rect(screen, arm_skin,
                             pygame.Rect(sx + ts - 7, arm_y + 3, 3, 5))
        elif npc.facing_direction == "left":
            pygame.draw.rect(screen, shirt_color,
                             pygame.Rect(sx + 4, arm_y, 3, 3))
            pygame.draw.rect(screen, arm_skin,
                             pygame.Rect(sx + 4, arm_y + 3, 3, 6))
        elif npc.facing_direction == "right":
            pygame.draw.rect(screen, shirt_color,
                             pygame.Rect(sx + ts - 7, arm_y, 3, 3))
            pygame.draw.rect(screen, arm_skin,
                             pygame.Rect(sx + ts - 7, arm_y + 3, 3, 6))

        # --- Head ---
        head_cx = sx + ts // 2
        head_cy = sy_bob + 10
        skin_color = (255, 215, 175)
        skin_shadow = (235, 190, 150)
        pygame.draw.circle(screen, skin_shadow, (head_cx + 1, head_cy + 1), 7)
        pygame.draw.circle(screen, skin_color, (head_cx, head_cy), 7)

        # Hair color varies by NPC
        hair_colors = {
            "prof_oak":    (180, 180, 180),   # Grey/white
            "rival":       (100, 60, 30),      # Brown
            "youngster":   (60, 40, 20),        # Dark brown
            "bug_catcher": (80, 60, 30),        # Brown
            "gentleman":   (50, 50, 50),        # Black
            "nurse_joy":   (255, 120, 150),     # Pink
            "trainer":     (80, 50, 30),         # Brown
            "lass":        (200, 160, 60),       # Blonde
            "hiker":       (120, 80, 40),        # Auburn
            "swimmer":     (40, 30, 20),         # Black
            "rocket":      (30, 30, 35),         # Very dark
        }
        hair_color = hair_colors.get(sprite_key, (60, 40, 20))

        # Hair rendering based on facing direction
        if npc.facing_direction == "up":
            # Full hair from behind
            pygame.draw.circle(screen, hair_color, (head_cx, head_cy - 1), 7)
            # Hair detail lines
            pygame.draw.arc(screen, (max(0, hair_color[0] - 20),
                                     max(0, hair_color[1] - 20),
                                     max(0, hair_color[2] - 20)),
                            pygame.Rect(head_cx - 6, head_cy - 6, 12, 10),
                            0.5, 2.5, 2)
        else:
            # Hair top / bangs
            pygame.draw.arc(screen, hair_color,
                            pygame.Rect(head_cx - 7, head_cy - 8, 14, 12),
                            math.pi + 0.2, 2 * math.pi - 0.2, 6)
            # Hair highlight
            pygame.draw.arc(screen, (min(255, hair_color[0] + 30),
                                     min(255, hair_color[1] + 30),
                                     min(255, hair_color[2] + 20)),
                            pygame.Rect(head_cx - 5, head_cy - 7, 10, 8),
                            math.pi + 0.5, 2 * math.pi - 0.5, 2)

        # --- Eyes (based on facing direction) ---
        if npc.facing_direction == "down":
            # Eye whites
            pygame.draw.circle(screen, (255, 255, 255), (head_cx - 3, head_cy + 1), 2)
            pygame.draw.circle(screen, (255, 255, 255), (head_cx + 3, head_cy + 1), 2)
            # Pupils
            pygame.draw.circle(screen, (30, 30, 40), (head_cx - 3, head_cy + 1), 1)
            pygame.draw.circle(screen, (30, 30, 40), (head_cx + 3, head_cy + 1), 1)
            # Shine
            pygame.draw.circle(screen, (255, 255, 255), (head_cx - 2, head_cy), 1)
        elif npc.facing_direction == "left":
            pygame.draw.circle(screen, (255, 255, 255), (head_cx - 4, head_cy + 1), 2)
            pygame.draw.circle(screen, (30, 30, 40), (head_cx - 4, head_cy + 1), 1)
        elif npc.facing_direction == "right":
            pygame.draw.circle(screen, (255, 255, 255), (head_cx + 4, head_cy + 1), 2)
            pygame.draw.circle(screen, (30, 30, 40), (head_cx + 4, head_cy + 1), 1)
        # "up" -> no eyes visible

        # --- Interaction indicator ---
        px, py = player.get_grid_position()
        dist = abs(px - npc.x) + abs(py - npc.y)  # Manhattan distance

        if dist <= 3:
            indicator_y = sy_bob - 10
            indicator_x = sx + ts // 2

            if npc.is_trainer and not npc.defeated:
                # Animated exclamation mark for undefeated trainers
                pulse = (math.sin(t * 5) + 1) * 0.5
                bounce = int(math.sin(t * 6) * 2)
                ind_color = (255, int(50 + pulse * 100), 50)

                # White bubble background
                bub_rect = pygame.Rect(indicator_x - 9, indicator_y - 5 + bounce, 18, 18)
                pygame.draw.ellipse(screen, (255, 255, 255), bub_rect)
                pygame.draw.ellipse(screen, (0, 0, 0), bub_rect, 1)
                # Bubble tail
                pygame.draw.polygon(screen, (255, 255, 255),
                                    [(indicator_x - 2, indicator_y + 12 + bounce),
                                     (indicator_x + 2, indicator_y + 12 + bounce),
                                     (indicator_x, indicator_y + 16 + bounce)])

                font = pygame.font.Font(None, 24)
                ind_text = font.render("!", True, ind_color)
                screen.blit(ind_text, (indicator_x - ind_text.get_width() // 2,
                                       indicator_y - 3 + bounce))
            elif dist <= 2:
                # Animated speech bubble dots for regular NPCs
                dot_phase = int(t * 3) % 3

                # Small bubble background
                bub_w = 22
                bub_h = 12
                bub_surf = pygame.Surface((bub_w, bub_h), pygame.SRCALPHA)
                pygame.draw.ellipse(bub_surf, (255, 255, 255, 200),
                                    pygame.Rect(0, 0, bub_w, bub_h))
                pygame.draw.ellipse(bub_surf, (0, 0, 0, 120),
                                    pygame.Rect(0, 0, bub_w, bub_h), 1)
                screen.blit(bub_surf, (indicator_x - bub_w // 2, indicator_y - 2))

                for i in range(3):
                    dot_brightness = 50 if i <= dot_phase else 180
                    dot_color = (dot_brightness, dot_brightness, dot_brightness)
                    pygame.draw.circle(screen, dot_color,
                                       (indicator_x - 6 + i * 6, indicator_y + 4), 2)
    
    def _render_dialogue(self, screen: pygame.Surface):
        """Render dialogue box."""
        # Create dialogue box
        box_height = 120
        box_margin = 20
        box_rect = pygame.Rect(box_margin, 
                              screen.get_height() - box_height - box_margin,
                              screen.get_width() - 2 * box_margin,
                              box_height)
        
        # Draw box background
        pygame.draw.rect(screen, (255, 255, 255), box_rect)
        pygame.draw.rect(screen, (0, 0, 0), box_rect, 3)
        
        # Draw text
        if self.current_dialogue and self.dialogue_index < len(self.current_dialogue):
            font = pygame.font.Font(None, 24)
            text = self.current_dialogue[self.dialogue_index]
            
            # Word wrap
            words = text.split(' ')
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                text_surface = font.render(test_line, True, (0, 0, 0))
                
                if text_surface.get_width() > box_rect.width - 40:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
                else:
                    current_line.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw lines
            y = box_rect.y + 20
            for line in lines[:4]:  # Max 4 lines
                text_surface = font.render(line, True, (0, 0, 0))
                screen.blit(text_surface, (box_rect.x + 20, y))
                y += 25
            
            # Draw continue indicator
            if self.dialogue_index < len(self.current_dialogue) - 1:
                indicator = font.render("▼", True, (0, 0, 0))
                screen.blit(indicator, 
                          (box_rect.right - 30, box_rect.bottom - 25))
    
    def _render_ambient(self, screen: pygame.Surface):
        """Render ambient particle effects (leaf, sparkle)."""
        for p in self.ambient_particles:
            alpha = max(0, min(255, int(255 * p['life'])))
            size = max(1, int(p['size'] * p['life']))

            if p['type'] == 'leaf':
                color = (30, 140 + int(40 * p['life']), 30)
                if size > 0:
                    pygame.draw.circle(screen, color,
                                       (int(p['x']), int(p['y'])), size)
            elif p['type'] == 'sparkle':
                brightness = int(200 + 55 * p['life'])
                color = (brightness, brightness, min(255, brightness + 20))
                if size > 0:
                    pygame.draw.circle(screen, color,
                                       (int(p['x']), int(p['y'])), size)

    def _render_day_night_tint(self, screen: pygame.Surface):
        """Apply a subtle day/night tint overlay based on system time."""
        from datetime import datetime
        hour = datetime.now().hour

        # Define tint colors and alpha for different times
        # Morning (5-9): warm golden tint
        # Day (10-16): no tint / very subtle bright
        # Evening (17-20): orange/amber
        # Night (21-4): blue/dark
        if 5 <= hour < 9:
            tint_color = (255, 200, 100)
            tint_alpha = 15
        elif 9 <= hour < 17:
            tint_color = (255, 255, 230)
            tint_alpha = 5
        elif 17 <= hour < 21:
            tint_color = (255, 150, 50)
            tint_alpha = 25
        else:
            tint_color = (30, 30, 80)
            tint_alpha = 40

        tint_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        tint_surf.fill((*tint_color, tint_alpha))
        screen.blit(tint_surf, (0, 0))

    def _render_area_banner(self, screen: pygame.Surface):
        """Render a stylish area name banner that fades in and out."""
        progress = self.area_banner_timer / self.area_banner_duration

        # Fade in for first 20%, stay for middle 60%, fade out for last 20%
        if progress < 0.2:
            alpha = int(255 * (progress / 0.2))
        elif progress > 0.8:
            alpha = int(255 * ((1.0 - progress) / 0.2))
        else:
            alpha = 255

        alpha = max(0, min(255, alpha))

        # Banner dimensions
        font = pygame.font.Font(None, 42)
        text_surf = font.render(self.area_banner_text, True, (255, 255, 255))
        text_w = text_surf.get_width()
        text_h = text_surf.get_height()

        banner_w = text_w + 60
        banner_h = text_h + 20
        banner_x = (self.screen_width - banner_w) // 2
        banner_y = 80

        # Background with slide-in effect
        slide_offset = 0
        if progress < 0.15:
            slide_offset = int((1 - progress / 0.15) * 30)

        # Draw banner background
        banner_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        pygame.draw.rect(banner_surf, (20, 20, 40, int(alpha * 0.8)),
                         pygame.Rect(0, 0, banner_w, banner_h), border_radius=8)
        pygame.draw.rect(banner_surf, (200, 180, 100, alpha),
                         pygame.Rect(0, 0, banner_w, banner_h), 2)
        # Decorative lines
        pygame.draw.line(banner_surf, (200, 180, 100, alpha),
                         (10, banner_h // 2), (20, banner_h // 2), 2)
        pygame.draw.line(banner_surf, (200, 180, 100, alpha),
                         (banner_w - 20, banner_h // 2), (banner_w - 10, banner_h // 2), 2)

        screen.blit(banner_surf, (banner_x, banner_y - slide_offset))

        # Draw text
        text_alpha_surf = pygame.Surface((text_w, text_h), pygame.SRCALPHA)
        text_color = (255, 255, 255, alpha)
        text_rendered = font.render(self.area_banner_text, True, (255, 255, 255))
        text_alpha_surf.blit(text_rendered, (0, 0))
        text_alpha_surf.set_alpha(alpha)
        screen.blit(text_alpha_surf,
                     (banner_x + 30, banner_y + 10 - slide_offset))

    def _render_map_transition(self, screen: pygame.Surface):
        """Render the fade-to-black map transition overlay."""
        if self.map_transition_alpha > 0:
            fade_surf = pygame.Surface((self.screen_width, self.screen_height))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(min(255, self.map_transition_alpha))
            screen.blit(fade_surf, (0, 0))

    def get_wild_encounter(self, player_data: Optional[Dict] = None) -> Optional[Pokemon]:
        """Get a wild Pokemon encounter for the current area."""
        return self.encounter_system.get_encounter(self.current_map_id, player_data)
    
    def use_repel(self, steps: int):
        """Use a repel item."""
        self.encounter_system.use_repel(steps)
    
    def get_encounter_info(self) -> Dict:
        """Get information about the current encounter chain."""
        species, count = self.encounter_system.get_chain_info()
        return {
            "chain_species": species,
            "chain_count": count,
            "area": self.current_map_id,
            "repel_steps": self.encounter_system.repel_steps
        }