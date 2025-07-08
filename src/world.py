"""
World Management - Handles maps, NPCs, and world interactions
"""

import pygame
import random
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


class World:
    """Manages the game world, maps, and interactions."""
    
    def __init__(self):
        # Load all maps
        self.maps: Dict[str, Map] = create_sample_maps()
        self.current_map_id = "pallet_town"
        self.current_map = self.maps[self.current_map_id]
        
        # Camera settings
        self.camera_x = 0
        self.camera_y = 0
        self.screen_width = 800
        self.screen_height = 600
        
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
                    {"species": "Caterpie", "level": 4},
                    {"species": "Weedle", "level": 4}
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
        # Update camera to follow player
        self._update_camera(player)
        
        # Update NPCs
        self._update_npcs(dt)
        
        # Update interaction cooldown
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= dt
        
        # Check for wild encounters if player moved
        if player.is_moving and not self.current_dialogue:
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
                    lead_pokemon = player.get_lead_pokemon() if hasattr(player, 'get_lead_pokemon') else None
                    lead_level = lead_pokemon.level if lead_pokemon else 1
                    
                    if not self.encounter_system.check_repel(lead_level):
                        self.steps_in_grass = 0
                        return "wild_encounter"
            else:
                # Reset grass counter when not in grass
                self.steps_in_grass = 0
                self.last_encounter_position = None
        
        return None
    
    def _update_camera(self, player: Player):
        """Update camera position to follow player."""
        # Center camera on player
        target_x = player.pixel_x - self.screen_width // 2
        target_y = player.pixel_y - self.screen_height // 2
        
        # Clamp camera to map bounds
        max_x = max(0, self.current_map.width * self.current_map.tile_size - self.screen_width)
        max_y = max(0, self.current_map.height * self.current_map.tile_size - self.screen_height)
        
        self.camera_x = max(0, min(target_x, max_x))
        self.camera_y = max(0, min(target_y, max_y))
    
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
                    
                    # Check movement range and collision
                    if (abs(new_x - npc.x) <= npc.movement_range and
                        abs(new_y - npc.y) <= npc.movement_range and
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
    
    def change_map(self, new_map_id: str, x: int, y: int, player: Player):
        """Change to a different map."""
        if new_map_id not in self.maps:
            print(f"Warning: Map {new_map_id} not found!")
            return
        
        self.current_map_id = new_map_id
        self.current_map = self.maps[new_map_id]
        
        # Update player position
        player.grid_x = x
        player.grid_y = y
        player.pixel_x = x * player.TILE_SIZE
        player.pixel_y = y * player.TILE_SIZE
        player.target_x = player.pixel_x
        player.target_y = player.pixel_y
        
        # Reset encounter counters
        self.steps_in_grass = 0
        self.last_encounter_position = None
        
        # Break encounter chain if moving to different area
        if new_map_id != self.current_map_id:
            self.encounter_system.break_chain()
    
    def check_warps(self, player: Player):
        """Check if player stepped on a warp."""
        grid_x, grid_y = player.get_grid_position()
        warp = self.current_map.get_warp_at(grid_x, grid_y)
        
        if warp:
            self.change_map(warp.target_map, warp.target_x, warp.target_y, player)
    
    def render(self, screen: pygame.Surface, player: Player):
        """Render the world."""
        # Draw map
        self.current_map.render(screen, self.camera_x, self.camera_y)
        
        # Draw NPCs
        npcs = self.npcs.get(self.current_map_id, [])
        for npc in npcs:
            self._render_npc(screen, npc)
        
        # Draw player
        player.render(screen, self.camera_x, self.camera_y)
        
        # Draw dialogue box if active
        if self.current_dialogue:
            self._render_dialogue(screen)
    
    def _render_npc(self, screen: pygame.Surface, npc: NPC):
        """Render an NPC."""
        screen_x = npc.x * self.current_map.tile_size - self.camera_x
        screen_y = npc.y * self.current_map.tile_size - self.camera_y
        
        # Simple colored rectangle for now
        npc_rect = pygame.Rect(screen_x, screen_y, 
                              self.current_map.tile_size, 
                              self.current_map.tile_size)
        
        # Different colors for different NPC types
        if npc.is_trainer and not npc.defeated:
            color = (255, 100, 100)  # Red for undefeated trainers
        elif npc.is_trainer and npc.defeated:
            color = (100, 100, 100)  # Gray for defeated trainers
        else:
            color = (100, 200, 255)  # Blue for regular NPCs
        
        pygame.draw.rect(screen, color, npc_rect)
        pygame.draw.rect(screen, (0, 0, 0), npc_rect, 2)
        
        # Draw facing direction indicator
        center_x = screen_x + self.current_map.tile_size // 2
        center_y = screen_y + self.current_map.tile_size // 2
        
        if npc.facing_direction == "down":
            pygame.draw.circle(screen, (255, 255, 0), 
                             (center_x, screen_y + self.current_map.tile_size - 8), 3)
        elif npc.facing_direction == "up":
            pygame.draw.circle(screen, (255, 255, 0), 
                             (center_x, screen_y + 8), 3)
        elif npc.facing_direction == "left":
            pygame.draw.circle(screen, (255, 255, 0), 
                             (screen_x + 8, center_y), 3)
        elif npc.facing_direction == "right":
            pygame.draw.circle(screen, (255, 255, 0), 
                             (screen_x + self.current_map.tile_size - 8, center_y), 3)
    
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