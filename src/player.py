"""
Player Class - Represents the game player
"""

from typing import List, Optional, Tuple
from .pokemon import Pokemon
import pygame
import os
import math


class Player:
    """Represents the player character in the Pokemon game."""
    
    TILE_SIZE = 32
    MOVE_SPEED = 8   # Tiles per second (increased from 4)
    RUN_SPEED = 12  # Tiles per second when running (increased from 8)
    
    def __init__(self, name: str, x: int = 0, y: int = 0):
        self.name = name
        # Grid position (in tiles)
        self.grid_x = x
        self.grid_y = y
        # Pixel position (for smooth movement)
        self.pixel_x = x * self.TILE_SIZE
        self.pixel_y = y * self.TILE_SIZE
        # Target position for movement
        self.target_x = self.pixel_x
        self.target_y = self.pixel_y
        
        self.pokemon_team: List[Pokemon] = []
        self.active_pokemon: Optional[Pokemon] = None
        self.money = 1000
        self.badges = []
        self.inventory = {
            "pokeball": 5,
            "potion": 3,
            "super_potion": 1
        }
        
        # Movement state
        self.facing_direction = "down"
        self.is_moving = False
        self.is_running = False
        self.move_progress = 0.0
        self.move_cooldown = 0.0
        
        # Sprite data
        self.sprite_frame = 0
        self.animation_timer = 0.0
        self.sprites = self._load_sprites()
    
    def add_pokemon(self, pokemon: Pokemon) -> bool:
        """Add a Pokemon to the team (max 6)."""
        if len(self.pokemon_team) < 6:
            self.pokemon_team.append(pokemon)
            if not self.active_pokemon:
                self.active_pokemon = pokemon
            return True
        return False
    
    def remove_pokemon(self, pokemon: Pokemon) -> bool:
        """Remove a Pokemon from the team."""
        if pokemon in self.pokemon_team and len(self.pokemon_team) > 1:
            self.pokemon_team.remove(pokemon)
            if self.active_pokemon == pokemon:
                self.active_pokemon = self.get_first_healthy_pokemon()
            return True
        return False
    
    def switch_active_pokemon(self, index: int) -> bool:
        """Switch active Pokemon by index."""
        if 0 <= index < len(self.pokemon_team):
            pokemon = self.pokemon_team[index]
            if not pokemon.is_fainted:
                self.active_pokemon = pokemon
                return True
        return False
    
    def get_first_healthy_pokemon(self) -> Optional[Pokemon]:
        """Get the first non-fainted Pokemon in team."""
        for pokemon in self.pokemon_team:
            if not pokemon.is_fainted:
                return pokemon
        return None
    
    def heal_all_pokemon(self):
        """Fully heal all Pokemon in team."""
        for pokemon in self.pokemon_team:
            pokemon.current_hp = pokemon.stats["hp"]
            pokemon.is_fainted = False
            pokemon.cure_status()
    
    def add_item(self, item_name: str, quantity: int = 1):
        """Add items to inventory."""
        if item_name in self.inventory:
            self.inventory[item_name] += quantity
        else:
            self.inventory[item_name] = quantity
    
    def use_item(self, item_name: str, target_pokemon: Optional[Pokemon] = None) -> bool:
        """Use an item from inventory."""
        if item_name not in self.inventory or self.inventory[item_name] <= 0:
            return False
        
        success = False
        
        if item_name == "potion" and target_pokemon:
            if not target_pokemon.is_fainted:
                target_pokemon.heal(20)
                success = True
        
        elif item_name == "super_potion" and target_pokemon:
            if not target_pokemon.is_fainted:
                target_pokemon.heal(50)
                success = True
        
        elif item_name == "pokeball":
            # Pokeball logic would be handled elsewhere
            success = True
        
        if success:
            self.inventory[item_name] -= 1
        
        return success
    
    def _load_sprites(self) -> dict:
        """Load player sprites (placeholder for now)."""
        # This would load actual sprite sheets in a full implementation
        return {
            "down": [(255, 0, 0)],  # Red placeholder
            "up": [(200, 0, 0)],
            "left": [(150, 0, 0)],
            "right": [(100, 0, 0)]
        }
    
    def start_move(self, direction: str, is_running: bool = False):
        """Start moving in a direction if not already moving."""
        if self.is_moving or self.move_cooldown > 0:
            return False
        
        # Calculate target position based on direction
        dx, dy = 0, 0
        if direction == "up":
            dy = -1
        elif direction == "down":
            dy = 1
        elif direction == "left":
            dx = -1
        elif direction == "right":
            dx = 1
        
        # Check if target position is valid (collision detection done by game/world)
        new_grid_x = self.grid_x + dx
        new_grid_y = self.grid_y + dy
        
        # Start movement
        self.target_x = new_grid_x * self.TILE_SIZE
        self.target_y = new_grid_y * self.TILE_SIZE
        self.is_moving = True
        self.is_running = is_running
        self.move_progress = 0.0
        
        return True
    
    def update(self, dt: float):
        """Update player movement and animation."""
        # Update movement cooldown
        if self.move_cooldown > 0:
            self.move_cooldown -= dt
        
        # Update movement
        if self.is_moving:
            # Calculate move speed
            speed = self.RUN_SPEED if self.is_running else self.MOVE_SPEED
            self.move_progress += speed * dt
            
            if self.move_progress >= 1.0:
                # Movement complete
                self.pixel_x = self.target_x
                self.pixel_y = self.target_y
                self.grid_x = self.pixel_x // self.TILE_SIZE
                self.grid_y = self.pixel_y // self.TILE_SIZE
                self.is_moving = False
                self.move_progress = 0.0
                # Small cooldown to prevent movement feeling too fast
                self.move_cooldown = 0.02
            else:
                # Interpolate position
                start_x = self.grid_x * self.TILE_SIZE
                start_y = self.grid_y * self.TILE_SIZE
                self.pixel_x = start_x + (self.target_x - start_x) * self.move_progress
                self.pixel_y = start_y + (self.target_y - start_y) * self.move_progress
        
        # Update animation
        self.animation_timer += dt
        if self.animation_timer >= 0.2:  # Change frame every 0.2 seconds
            self.animation_timer = 0.0
            if self.is_moving:
                self.sprite_frame = (self.sprite_frame + 1) % 4
            else:
                self.sprite_frame = 0
    
    def get_grid_position(self) -> Tuple[int, int]:
        """Get current grid position."""
        return (self.grid_x, self.grid_y)
    
    def get_facing_position(self) -> Tuple[int, int]:
        """Get the grid position the player is facing."""
        dx, dy = 0, 0
        if self.facing_direction == "up":
            dy = -1
        elif self.facing_direction == "down":
            dy = 1
        elif self.facing_direction == "left":
            dx = -1
        elif self.facing_direction == "right":
            dx = 1
        
        return (self.grid_x + dx, self.grid_y + dy)
    
    def render(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """Render the player character with detailed sprite."""
        screen_x = int(self.pixel_x - camera_x)
        screen_y = int(self.pixel_y - camera_y)
        ts = self.TILE_SIZE
        t = self.animation_timer

        # Walking bobbing animation
        bob_offset = 0
        if self.is_moving:
            bob_offset = int(math.sin(t * 16) * 2)

        # --- Shadow under the player ---
        shadow_surf = pygame.Surface((ts + 4, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 55),
                            pygame.Rect(4, 0, ts - 4, 10))
        screen.blit(shadow_surf, (screen_x - 2, screen_y + ts - 6))

        # --- Shoes (drawn first so legs overlap) ---
        shoe_color = (180, 40, 40)
        shoe_highlight = (210, 70, 60)
        body_y = screen_y + 12 + bob_offset
        leg_y = body_y + 14
        shoe_y = leg_y + 5
        leg_phase = math.sin(t * 16) * 3 if self.is_moving else 0

        # Left shoe
        ls_y = int(shoe_y + leg_phase) if self.is_moving else shoe_y
        pygame.draw.rect(screen, shoe_color,
                         pygame.Rect(screen_x + 7, ls_y, 7, 3), border_radius=1)
        pygame.draw.rect(screen, shoe_highlight,
                         pygame.Rect(screen_x + 7, ls_y, 5, 1))
        # Right shoe
        rs_y = int(shoe_y - leg_phase) if self.is_moving else shoe_y
        pygame.draw.rect(screen, shoe_color,
                         pygame.Rect(screen_x + ts - 14, rs_y, 7, 3), border_radius=1)
        pygame.draw.rect(screen, shoe_highlight,
                         pygame.Rect(screen_x + ts - 14, rs_y, 5, 1))

        # --- Legs (walking animation) ---
        leg_color = (50, 50, 65)  # Dark pants
        leg_highlight = (65, 65, 80)
        if self.is_moving:
            # Left leg
            ll_y = int(leg_y + leg_phase)
            pygame.draw.rect(screen, leg_color,
                             pygame.Rect(screen_x + 8, ll_y, 6, 6), border_radius=1)
            pygame.draw.rect(screen, leg_highlight,
                             pygame.Rect(screen_x + 8, ll_y, 3, 5))
            # Right leg
            rl_y = int(leg_y - leg_phase)
            pygame.draw.rect(screen, leg_color,
                             pygame.Rect(screen_x + ts - 14, rl_y, 6, 6), border_radius=1)
            pygame.draw.rect(screen, leg_highlight,
                             pygame.Rect(screen_x + ts - 14, rl_y, 3, 5))
        else:
            pygame.draw.rect(screen, leg_color,
                             pygame.Rect(screen_x + 8, leg_y, 6, 5), border_radius=1)
            pygame.draw.rect(screen, leg_highlight,
                             pygame.Rect(screen_x + 8, leg_y, 3, 4))
            pygame.draw.rect(screen, leg_color,
                             pygame.Rect(screen_x + ts - 14, leg_y, 6, 5), border_radius=1)
            pygame.draw.rect(screen, leg_highlight,
                             pygame.Rect(screen_x + ts - 14, leg_y, 3, 4))

        # --- Body (torso / jacket) ---
        jacket_color = (30, 100, 200)  # Blue jacket
        jacket_dark = (20, 75, 165)
        jacket_light = (50, 120, 220)
        body_rect = pygame.Rect(screen_x + 6, body_y, ts - 12, 14)
        pygame.draw.rect(screen, jacket_color, body_rect, border_radius=3)
        # Jacket shading (left lighter, right darker)
        pygame.draw.rect(screen, jacket_light,
                         pygame.Rect(screen_x + 6, body_y + 1, (ts - 12) // 2, 12),
                         border_radius=2)
        # Jacket zipper line
        pygame.draw.line(screen, jacket_dark,
                         (screen_x + ts // 2, body_y + 2),
                         (screen_x + ts // 2, body_y + 13), 1)
        # Collar
        pygame.draw.line(screen, (240, 240, 245),
                         (screen_x + 8, body_y),
                         (screen_x + ts - 8, body_y), 1)

        # --- Backpack (visible from behind and sides) ---
        if self.facing_direction == "up":
            bp_rect = pygame.Rect(screen_x + 8, body_y + 2, ts - 16, 10)
            pygame.draw.rect(screen, (160, 50, 40), bp_rect, border_radius=2)
            pygame.draw.rect(screen, (140, 40, 30), bp_rect, 1)
            # Backpack strap
            pygame.draw.line(screen, (130, 35, 28),
                             (screen_x + 10, body_y), (screen_x + 10, body_y + 5), 1)
            pygame.draw.line(screen, (130, 35, 28),
                             (screen_x + ts - 10, body_y), (screen_x + ts - 10, body_y + 5), 1)
        elif self.facing_direction in ("left", "right"):
            bp_x = screen_x + ts - 8 if self.facing_direction == "left" else screen_x + 3
            bp_rect = pygame.Rect(bp_x, body_y + 3, 5, 8)
            pygame.draw.rect(screen, (160, 50, 40), bp_rect, border_radius=1)

        # --- Arms ---
        arm_skin = (255, 210, 175)
        arm_sleeve = (35, 105, 205)
        arm_y = body_y + 2
        arm_swing = math.sin(t * 16) * 2.5 if self.is_moving else 0

        if self.facing_direction in ("down", "up"):
            # Left arm
            la_y = int(arm_y + arm_swing)
            pygame.draw.rect(screen, arm_sleeve,
                             pygame.Rect(screen_x + 3, la_y, 4, 4), border_radius=1)
            pygame.draw.rect(screen, arm_skin,
                             pygame.Rect(screen_x + 3, la_y + 4, 3, 5))
            # Right arm
            ra_y = int(arm_y - arm_swing)
            pygame.draw.rect(screen, arm_sleeve,
                             pygame.Rect(screen_x + ts - 7, ra_y, 4, 4), border_radius=1)
            pygame.draw.rect(screen, arm_skin,
                             pygame.Rect(screen_x + ts - 6, ra_y + 4, 3, 5))
        elif self.facing_direction == "left":
            # Front arm visible
            pygame.draw.rect(screen, arm_sleeve,
                             pygame.Rect(screen_x + 2, arm_y, 4, 4), border_radius=1)
            pygame.draw.rect(screen, arm_skin,
                             pygame.Rect(screen_x + 2, arm_y + 4, 3, 5))
        elif self.facing_direction == "right":
            pygame.draw.rect(screen, arm_sleeve,
                             pygame.Rect(screen_x + ts - 6, arm_y, 4, 4), border_radius=1)
            pygame.draw.rect(screen, arm_skin,
                             pygame.Rect(screen_x + ts - 5, arm_y + 4, 3, 5))

        # --- Head ---
        head_cx = screen_x + ts // 2
        head_cy = screen_y + 9 + bob_offset
        head_r = 7

        # Skin color
        skin_color = (255, 220, 185)
        skin_shadow = (235, 195, 160)
        pygame.draw.circle(screen, skin_shadow, (head_cx + 1, head_cy + 1), head_r)
        pygame.draw.circle(screen, skin_color, (head_cx, head_cy), head_r)

        # --- Cap / Hat ---
        hat_color = (220, 50, 50)
        hat_dark = (180, 35, 35)
        hat_band = (240, 240, 240)
        if self.facing_direction == "up":
            # Cap visible from behind (full coverage)
            pygame.draw.circle(screen, hat_color, (head_cx, head_cy - 1), head_r)
            # Brim (back edge)
            pygame.draw.arc(screen, hat_dark,
                            pygame.Rect(head_cx - head_r, head_cy - head_r,
                                        head_r * 2, head_r * 2),
                            0.3, math.pi - 0.3, head_r)
            # Band
            pygame.draw.line(screen, hat_band,
                             (head_cx - 5, head_cy + 3), (head_cx + 5, head_cy + 3), 1)
            # Hair peeking below cap
            pygame.draw.rect(screen, (50, 35, 18),
                             pygame.Rect(head_cx - 5, head_cy + 4, 10, 3))
        else:
            # Cap top dome
            pygame.draw.circle(screen, hat_color, (head_cx, head_cy - 3), 6)
            # Cap front brim
            brim_dir = 0
            if self.facing_direction == "left":
                brim_dir = -1
            elif self.facing_direction == "right":
                brim_dir = 1

            brim_x = head_cx + brim_dir * 3
            pygame.draw.ellipse(screen, hat_dark,
                                pygame.Rect(brim_x - 7, head_cy - 2, 14, 5))
            pygame.draw.ellipse(screen, hat_color,
                                pygame.Rect(brim_x - 6, head_cy - 2, 12, 4))
            # Cap band / logo accent
            pygame.draw.line(screen, hat_band,
                             (head_cx - 4, head_cy - 1), (head_cx + 4, head_cy - 1), 1)
            # Cap button on top
            pygame.draw.circle(screen, hat_band, (head_cx, head_cy - 6), 1)

        # --- Eyes (direction indicator with whites and pupils) ---
        if self.facing_direction == "down":
            # White of eye
            pygame.draw.circle(screen, (255, 255, 255), (head_cx - 3, head_cy + 1), 3)
            pygame.draw.circle(screen, (255, 255, 255), (head_cx + 3, head_cy + 1), 3)
            # Pupils
            pygame.draw.circle(screen, (30, 30, 40), (head_cx - 3, head_cy + 2), 2)
            pygame.draw.circle(screen, (30, 30, 40), (head_cx + 3, head_cy + 2), 2)
            # Eye shine
            pygame.draw.circle(screen, (255, 255, 255), (head_cx - 2, head_cy + 1), 1)
            pygame.draw.circle(screen, (255, 255, 255), (head_cx + 4, head_cy + 1), 1)
            # Mouth
            pygame.draw.line(screen, (200, 140, 130),
                             (head_cx - 1, head_cy + 5), (head_cx + 1, head_cy + 5), 1)
        elif self.facing_direction == "up":
            pass  # Back of head -- no eyes visible
        elif self.facing_direction == "left":
            # Single visible eye (left profile)
            pygame.draw.circle(screen, (255, 255, 255), (head_cx - 4, head_cy + 1), 3)
            pygame.draw.circle(screen, (30, 30, 40), (head_cx - 5, head_cy + 2), 2)
            pygame.draw.circle(screen, (255, 255, 255), (head_cx - 4, head_cy + 1), 1)
        elif self.facing_direction == "right":
            # Single visible eye (right profile)
            pygame.draw.circle(screen, (255, 255, 255), (head_cx + 4, head_cy + 1), 3)
            pygame.draw.circle(screen, (30, 30, 40), (head_cx + 5, head_cy + 2), 2)
            pygame.draw.circle(screen, (255, 255, 255), (head_cx + 4, head_cy + 1), 1)
    
    def can_battle(self) -> bool:
        """Check if player has any Pokemon that can battle."""
        return any(not pokemon.is_fainted for pokemon in self.pokemon_team)
    
    def add_money(self, amount: int):
        """Add money to player's wallet."""
        self.money += amount
    
    def spend_money(self, amount: int) -> bool:
        """Spend money if player has enough."""
        if self.money >= amount:
            self.money -= amount
            return True
        return False
    
    def add_badge(self, badge_name: str):
        """Add a gym badge to collection."""
        if badge_name not in self.badges:
            self.badges.append(badge_name)
    
    def get_position(self) -> tuple:
        """Get player's current pixel position."""
        return (self.pixel_x, self.pixel_y)
    
    def get_lead_pokemon(self) -> Optional[Pokemon]:
        """Get the first non-fainted Pokemon in the team."""
        for pokemon in self.pokemon_team:
            if not pokemon.is_fainted:
                return pokemon
        return None
    
    def __str__(self):
        return f"Player {self.name} - Pokemon: {len(self.pokemon_team)}, Money: ${self.money}"