"""
Player Class - Represents the game player
"""

from typing import List, Optional, Tuple
from .pokemon import Pokemon
import pygame
import os


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
        """Render the player sprite."""
        # Calculate screen position
        screen_x = int(self.pixel_x - camera_x)
        screen_y = int(self.pixel_y - camera_y)
        
        # Draw player (placeholder rectangle for now)
        player_rect = pygame.Rect(screen_x, screen_y, self.TILE_SIZE, self.TILE_SIZE)
        color = self.sprites[self.facing_direction][0]
        pygame.draw.rect(screen, color, player_rect)
        pygame.draw.rect(screen, (0, 0, 0), player_rect, 2)
        
        # Draw direction indicator
        center_x = screen_x + self.TILE_SIZE // 2
        center_y = screen_y + self.TILE_SIZE // 2
        if self.facing_direction == "up":
            pygame.draw.polygon(screen, (255, 255, 0), 
                              [(center_x, screen_y - 5), 
                               (center_x - 5, screen_y), 
                               (center_x + 5, screen_y)])
        elif self.facing_direction == "down":
            pygame.draw.polygon(screen, (255, 255, 0), 
                              [(center_x, screen_y + self.TILE_SIZE + 5), 
                               (center_x - 5, screen_y + self.TILE_SIZE), 
                               (center_x + 5, screen_y + self.TILE_SIZE)])
        elif self.facing_direction == "left":
            pygame.draw.polygon(screen, (255, 255, 0), 
                              [(screen_x - 5, center_y), 
                               (screen_x, center_y - 5), 
                               (screen_x, center_y + 5)])
        elif self.facing_direction == "right":
            pygame.draw.polygon(screen, (255, 255, 0), 
                              [(screen_x + self.TILE_SIZE + 5, center_y), 
                               (screen_x + self.TILE_SIZE, center_y - 5), 
                               (screen_x + self.TILE_SIZE, center_y + 5)])
    
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