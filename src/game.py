"""
Main Game Logic - Core game loop and state management
"""

import pygame
import random
from typing import Optional
from .player import Player
from .pokemon import Pokemon, PokemonType, StatusCondition
from .battle import Battle, BattleType
from .ui import UI, UIState
from .items import get_item
from .world import World
from .encounter_effects import EncounterEffects, EncounterInfo


class GameState:
    """Different game states."""
    MENU = "menu"
    WORLD = "world"
    BATTLE = "battle"
    PAUSED = "paused"
    POKEMON_MENU = "pokemon_menu"
    BAG_MENU = "bag_menu"


class Game:
    """Main game class that manages the game loop and states."""
    
    def __init__(self):
        # Display settings - Larger window
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 800
        self.FPS = 60
        
        # Initialize Pygame
        print("  - Creating game window...")
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Pokemon Game")
        self.clock = pygame.time.Clock()
        
        # Show loading screen
        self.show_loading_screen("Initializing game...")
        
        # Game states
        self.running = True
        self.game_state = GameState.MENU
        self.previous_state = None
        
        # Initialize game components
        print("  - Loading UI components...")
        self.player: Optional[Player] = None
        self.current_battle: Optional[Battle] = None
        self.ui = UI(self.screen)
        self.world: Optional[World] = None
        
        # Enhanced encounter system
        self.encounter_effects = EncounterEffects(self.screen)
        self.encounter_info = EncounterInfo()
        self.show_encounter_info = True  # Toggle with F1 key
        
        self.show_loading_screen("Loading complete!")
        
        # Input handling
        self.keys_pressed = {}
        self.key_repeat_timers = {}  # For handling held keys
        
        # Game started flag
        self.game_started = False
        
        # Starter selection
        self.starter_selection_active = False
        self.selected_starter = 0
        
        # Current NPC for interactions
        self.current_npc = None
    
    def load_map_data(self):
        """Load or generate map data."""
        # Map data is now handled by the World class
        pass
    
    def create_new_game(self):
        """Initialize a new game."""
        self.show_loading_screen("Creating new game...")
        
        # Create world
        print("  - Loading world data...")
        self.world = World()
        
        # Create player at spawn point
        player_name = "Ash"  # Would get from menu input in full implementation
        spawn_x, spawn_y = 10, 10  # Starting position in Pallet Town
        self.player = Player(player_name, spawn_x, spawn_y)
        
        # Show starter selection
        self.show_starter_selection()
        
    def show_starter_selection(self):
        """Show starter Pokemon selection screen."""
        self.game_state = GameState.MENU
        
        # Show helpful message
        print("\n=== GAME TIP ===")
        print("You're starting in Pallet Town at position (10, 10)")
        print("To find wild Pokemon:")
        print("1. Go STRAIGHT UP (NORTH) to the VERY TOP of the town")
        print("2. Exit is at the top edge (y=0, x=18-22)")
        print("3. Once in Route 1, walk in the TALL GRASS")
        print("================\n")
        self.starter_selection_active = True
        self.selected_starter = 0
        
    def select_starter(self, starter_index):
        """Select a starter Pokemon."""
        # Use the create_pokemon_from_species function since we have the data
        from .pokemon import create_pokemon_from_species
        
        # Starter Pokemon IDs (Bulbasaur, Charmander, Squirtle)
        starter_ids = [1, 4, 7]
        
        # Create the starter Pokemon
        starter_pokemon = create_pokemon_from_species(starter_ids[starter_index], level=5)
        
        self.player.add_pokemon(starter_pokemon)
        
        # Add some starter items
        self.player.inventory["pokeball"] = 10
        self.player.inventory["potion"] = 5
        self.player.inventory["super_potion"] = 2
        
        self.starter_selection_active = False
        self.game_state = GameState.WORLD
        self.ui.state = UIState.GAME_WORLD
        self.game_started = True
    
    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0  # Delta time in seconds
            
            # Handle events
            self.handle_events()
            
            # Update game state
            self.update(dt)
            
            # Render
            self.render()
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Let UI handle events first
            if self.ui.handle_event(event, self):
                continue
            
            # Handle keyboard events
            elif event.type == pygame.KEYDOWN:
                self.keys_pressed[event.key] = True
                self.handle_keypress(event.key)
            
            elif event.type == pygame.KEYUP:
                self.keys_pressed[event.key] = False
    
    def handle_keypress(self, key):
        """Handle specific key press events."""
        if self.game_state == GameState.MENU:
            if self.starter_selection_active:
                # Handle starter selection
                if key == pygame.K_LEFT:
                    self.selected_starter = max(0, self.selected_starter - 1)
                elif key == pygame.K_RIGHT:
                    self.selected_starter = min(2, self.selected_starter + 1)
                elif key == pygame.K_RETURN:
                    self.select_starter(self.selected_starter)
                elif key == pygame.K_ESCAPE:
                    self.starter_selection_active = False
                    self.ui.state = UIState.MAIN_MENU
            elif self.ui.state == UIState.MAIN_MENU:
                # Menu navigation handled by UI
                pass
        
        elif self.game_state == GameState.WORLD:
            if key == pygame.K_ESCAPE:
                # Toggle pause
                self.toggle_pause()
            
            elif key == pygame.K_i:
                # Open inventory
                self.game_state = GameState.BAG_MENU
                self.ui.state = UIState.BAG_MENU
            
            elif key == pygame.K_p:
                # Open Pokemon menu
                self.game_state = GameState.POKEMON_MENU
                self.ui.state = UIState.POKEMON_MENU
            
            elif key == pygame.K_SPACE:
                # Interact with objects
                if self.world:
                    if self.world.current_dialogue:
                        # Advance dialogue
                        next_dialogue = self.world.advance_dialogue()
                        if not next_dialogue:
                            # Dialogue finished - check for special actions
                            self.handle_dialogue_completion()
                    else:
                        # Start new interaction
                        interaction = self.world.interact(self.player)
                        if interaction:
                            # Handle different interaction types
                            if interaction["type"] == "npc":
                                npc = interaction["npc"]
                                # Store current NPC for later use
                                self.current_npc = npc
                                if npc.is_trainer and not npc.defeated:
                                    # Show exclamation mark for trainer battle
                                    self.encounter_effects.start_exclamation(
                                        (npc.x * 32 - self.world.camera_x + 16,
                                         npc.y * 32 - self.world.camera_y - 20)
                                    )
            
            elif key == pygame.K_F1:
                # Toggle encounter info display
                self.show_encounter_info = not self.show_encounter_info
        
        elif self.game_state == GameState.BATTLE:
            # Battle input handled by UI battle menu
            if self.current_battle and self.current_battle.is_over:
                if key == pygame.K_SPACE:
                    self.end_battle()
        
        elif self.game_state == GameState.POKEMON_MENU:
            if key == pygame.K_ESCAPE:
                self.game_state = GameState.WORLD
                self.ui.state = UIState.GAME_WORLD
        
        elif self.game_state == GameState.BAG_MENU:
            if key == pygame.K_ESCAPE:
                self.game_state = GameState.WORLD
                self.ui.state = UIState.GAME_WORLD
        
        elif self.game_state == GameState.PAUSED:
            if key == pygame.K_ESCAPE:
                self.toggle_pause()
    
    def toggle_pause(self):
        """Toggle pause state."""
        if self.game_state == GameState.PAUSED:
            self.game_state = self.previous_state
            self.ui.state = UIState.GAME_WORLD
        else:
            self.previous_state = self.game_state
            self.game_state = GameState.PAUSED
            self.ui.state = UIState.PAUSE_MENU
    
    def handle_dialogue_completion(self):
        """Handle special actions after dialogue completion."""
        if self.current_npc and hasattr(self.current_npc, 'is_healer') and self.current_npc.is_healer:
            # Heal all Pokemon
            self.heal_all_pokemon()
            # Reset current NPC
            self.current_npc = None
            # Show healing effect message
            print("Your Pokemon have been fully healed!")
    
    def heal_all_pokemon(self):
        """Heal all Pokemon in the player's team."""
        if not self.player:
            return
        
        for pokemon in self.player.pokemon_team:
            # Restore HP
            pokemon.current_hp = pokemon.stats['hp']
            # Restore PP for all moves
            for move in pokemon.moves:
                move.current_pp = move.pp
            # Remove status conditions
            pokemon.status = StatusCondition.NONE
            pokemon.status_turns = 0
            
        print(f"All {len(self.player.pokemon_team)} Pokemon have been healed!")
    
    def update(self, dt):
        """Update game logic."""
        # Update UI animations
        self.ui.update(dt)
        
        # Update based on game state
        if self.game_state == GameState.WORLD:
            self.update_world(dt)
        elif self.game_state == GameState.BATTLE:
            self.update_battle(dt)
        
        # Update encounter effects
        self.encounter_effects.update(dt)
    
    def update_world(self, dt):
        """Update world exploration state."""
        if not self.player or not self.world:
            return
        
        # Handle player movement (grid-based)
        if not self.player.is_moving and not self.world.current_dialogue:
            # Check for running
            is_running = (self.keys_pressed.get(pygame.K_LSHIFT, False) or 
                         self.keys_pressed.get(pygame.K_RSHIFT, False))
            
            # Check movement keys
            if self.keys_pressed.get(pygame.K_LEFT, False) or self.keys_pressed.get(pygame.K_a, False):
                self._try_move_player("left", is_running)
            elif self.keys_pressed.get(pygame.K_RIGHT, False) or self.keys_pressed.get(pygame.K_d, False):
                self._try_move_player("right", is_running)
            elif self.keys_pressed.get(pygame.K_UP, False) or self.keys_pressed.get(pygame.K_w, False):
                self._try_move_player("up", is_running)
            elif self.keys_pressed.get(pygame.K_DOWN, False) or self.keys_pressed.get(pygame.K_s, False):
                self._try_move_player("down", is_running)
        
        # Update player
        self.player.update(dt)
        
        # Add grass rustling effect when in tall grass
        if self.world and not self.player.is_moving:
            grid_x, grid_y = self.player.get_grid_position()
            if self.world.current_map.check_wild_encounter(grid_x, grid_y):
                # Add occasional grass particles
                if random.random() < 0.05:  # 5% chance per frame
                    self.encounter_effects.add_grass_rustle(
                        self.player.pixel_x - self.world.camera_x,
                        self.player.pixel_y - self.world.camera_y + 16
                    )
        
        # Update world
        world_event = self.world.update(dt, self.player)
        
        # Handle world events
        if world_event == "wild_encounter":
            self.trigger_wild_encounter()
        
        # Check for map transitions
        if not self.player.is_moving:
            self.world.check_warps(self.player)
    
    def _try_move_player(self, direction: str, is_running: bool):
        """Try to move the player in a direction."""
        if not self.player or not self.world:
            return
        
        # Calculate target position
        dx, dy = 0, 0
        if direction == "up":
            dy = -1
        elif direction == "down":
            dy = 1
        elif direction == "left":
            dx = -1
        elif direction == "right":
            dx = 1
        
        target_x = self.player.grid_x + dx
        target_y = self.player.grid_y + dy
        
        # Check if movement is valid
        if self.world.can_move_to(target_x, target_y):
            self.player.start_move(direction, is_running)
    
    def update_battle(self, dt):
        """Update battle state."""
        # Battle updates are handled through events and UI
        pass
    
    def trigger_wild_encounter(self):
        """Start a wild Pokemon encounter."""
        if not self.player or not self.player.can_battle() or not self.world:
            return
        
        # Get player data for special encounter conditions
        player_data = {
            "badge_count": getattr(self.player, 'badge_count', 0),
            "elite_four_defeated": getattr(self.player, 'elite_four_defeated', False),
            # Add more player data as needed
        }
        
        # Get wild Pokemon from encounter system
        wild_pokemon = self.world.get_wild_encounter(player_data)
        
        if not wild_pokemon:
            # Fallback if no encounter data for current area
            print(f"No encounter data for area: {self.world.current_map_id}")
            return
        
        # Start encounter effects
        if wild_pokemon.is_shiny:
            # Special effect for shiny Pokemon
            self.encounter_effects.start_flash((255, 215, 0))  # Gold flash
            self.encounter_effects.add_shiny_sparkle(
                self.player.pixel_x - self.world.camera_x,
                self.player.pixel_y - self.world.camera_y
            )
            self.encounter_effects.start_encounter_transition("flash")
        else:
            # Normal encounter transition
            self.encounter_effects.start_encounter_transition("spiral")
        
        # Small delay before battle (handled by transition effect)
        # In a real implementation, you'd wait for the transition to complete
        
        # Start battle
        self.current_battle = Battle(self.player, wild_pokemon, BattleType.WILD)
        self.current_battle.start()
        self.game_state = GameState.BATTLE
        self.ui.state = UIState.BATTLE
    
    def end_battle(self):
        """End current battle and return to world."""
        self.current_battle = None
        self.game_state = GameState.WORLD
        self.ui.state = UIState.GAME_WORLD
    
    def render(self):
        """Render the game."""
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Render based on game state
        if self.game_state == GameState.MENU:
            if self.starter_selection_active:
                self.render_starter_selection()
            else:
                # UI handles menu rendering
                pass
        
        elif self.game_state == GameState.WORLD:
            self.render_world()
        
        elif self.game_state == GameState.BATTLE:
            # UI handles battle rendering
            pass
        
        elif self.game_state in [GameState.POKEMON_MENU, GameState.BAG_MENU]:
            # UI handles these menus
            pass
        
        # Let UI draw on top if not in starter selection
        if not self.starter_selection_active:
            self.ui.draw(self)
        
        # Update display
        pygame.display.flip()
    
    def render_world(self):
        """Render the world exploration view."""
        if self.world and self.player:
            self.world.render(self.screen, self.player)
            
            # Render encounter effects
            self.encounter_effects.render()
            
            # Render encounter info HUD
            if self.show_encounter_info:
                encounter_data = self.world.get_encounter_info()
                self.encounter_info.render(self.screen, encounter_data)
            
            # Show current position (helpful for navigation)
            pos_font = pygame.font.Font(None, 20)
            grid_x, grid_y = self.player.get_grid_position()
            pos_text = f"Position: ({grid_x}, {grid_y}) - {self.world.current_map.name}"
            pos_surface = pos_font.render(pos_text, True, (255, 255, 255))
            pos_bg = pygame.Surface((pos_surface.get_width() + 10, pos_surface.get_height() + 4))
            pos_bg.fill((0, 0, 0))
            pos_bg.set_alpha(128)
            self.screen.blit(pos_bg, (5, 5))
            self.screen.blit(pos_surface, (10, 7))
                
            # Instructions hint
            font = pygame.font.Font(None, 20)
            hint_text = font.render("Press F1 to toggle encounter info", True, (255, 255, 255))
            hint_bg = pygame.Surface((hint_text.get_width() + 10, hint_text.get_height() + 4))
            hint_bg.fill((0, 0, 0))
            hint_bg.set_alpha(128)
            self.screen.blit(hint_bg, (self.SCREEN_WIDTH - hint_text.get_width() - 15, 5))
            self.screen.blit(hint_text, (self.SCREEN_WIDTH - hint_text.get_width() - 10, 7))
            
            # Show tip if in area without encounters
            if self.world.current_map_id not in self.world.encounter_system.encounter_tables:
                tip_font = pygame.font.Font(None, 28)
                tip_text = "No wild Pokemon here! Go STRAIGHT UP to the TOP of town for Route 1!"
                text_surface = tip_font.render(tip_text, True, (255, 255, 0))
                text_rect = text_surface.get_rect(center=(self.SCREEN_WIDTH // 2, 60))
                
                # Draw background
                bg_rect = text_rect.inflate(20, 10)
                pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
                pygame.draw.rect(self.screen, (255, 255, 0), bg_rect, 2)
                
                # Draw text
                self.screen.blit(text_surface, text_rect)
        else:
            # Fallback rendering
            self.screen.fill((34, 139, 34))
    
    def render_starter_selection(self):
        """Render the starter Pokemon selection screen."""
        # Background
        self.screen.fill((248, 248, 248))
        
        # Title
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("Choose Your Starter Pokemon!", True, (0, 0, 0))
        title_rect = title_text.get_rect(center=(self.SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Starter options
        starters = [
            ("Bulbasaur", 1, (120, 200, 80), "Grass/Poison"),
            ("Charmander", 4, (240, 128, 48), "Fire"),
            ("Squirtle", 7, (104, 144, 240), "Water")
        ]
        
        card_width = 200
        card_height = 250
        spacing = 50
        total_width = (card_width * 3) + (spacing * 2)
        start_x = (self.SCREEN_WIDTH - total_width) // 2
        start_y = 150
        
        for i, (name, species_id, color, type_text) in enumerate(starters):
            x = start_x + (i * (card_width + spacing))
            
            # Card background
            card_rect = pygame.Rect(x, start_y, card_width, card_height)
            card_color = (255, 255, 255)
            if i == self.selected_starter:
                card_color = (255, 255, 200)
                pygame.draw.rect(self.screen, (255, 215, 0), card_rect, 5)
            else:
                pygame.draw.rect(self.screen, (200, 200, 200), card_rect, 3)
            
            pygame.draw.rect(self.screen, card_color, card_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), card_rect, 2)
            
            # Pokemon sprite
            sprite_rect = pygame.Rect(x + 50, start_y + 20, 100, 100)
            sprite_filename = f"{species_id}_normal.png"
            sprite_path = f"assets/sprites/{sprite_filename}"
            
            # Try to load and display the sprite
            try:
                sprite = pygame.image.load(sprite_path)
                sprite = pygame.transform.scale(sprite, (100, 100))
                self.screen.blit(sprite, sprite_rect)
            except:
                # Fallback to colored rectangle if sprite not found
                pygame.draw.rect(self.screen, color, sprite_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), sprite_rect, 2)
                
                # Draw Pokemon name in the sprite area as fallback
                fallback_font = pygame.font.Font(None, 16)
                fallback_text = fallback_font.render(name, True, (255, 255, 255))
                fallback_rect = fallback_text.get_rect(center=sprite_rect.center)
                self.screen.blit(fallback_text, fallback_rect)
            
            # Pokemon name
            font = pygame.font.Font(None, 28)
            name_text = font.render(name, True, (0, 0, 0))
            name_rect = name_text.get_rect(center=(x + card_width // 2, start_y + 140))
            self.screen.blit(name_text, name_rect)
            
            # Type
            type_font = pygame.font.Font(None, 22)
            type_text_surface = type_font.render(type_text, True, (64, 64, 64))
            type_rect = type_text_surface.get_rect(center=(x + card_width // 2, start_y + 170))
            self.screen.blit(type_text_surface, type_rect)
            
            # Level
            level_text = type_font.render("Level 5", True, (64, 64, 64))
            level_rect = level_text.get_rect(center=(x + card_width // 2, start_y + 195))
            self.screen.blit(level_text, level_rect)
        
        # Instructions
        inst_font = pygame.font.Font(None, 24)
        instructions = [
            "Use LEFT/RIGHT arrows to select",
            "Press ENTER to confirm your choice",
            "Press ESC to return to main menu"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_text = inst_font.render(instruction, True, (64, 64, 64))
            inst_rect = inst_text.get_rect(center=(self.SCREEN_WIDTH // 2, 450 + (i * 30)))
            self.screen.blit(inst_text, inst_rect)
    
    def show_loading_screen(self, message="Loading..."):
        """Show a loading screen with a message."""
        self.screen.fill((0, 0, 0))
        
        # Loading text
        font = pygame.font.Font(None, 48)
        text = font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)
        
        # Progress bar background
        bar_width = 400
        bar_height = 20
        bar_x = (self.SCREEN_WIDTH - bar_width) // 2
        bar_y = self.SCREEN_HEIGHT // 2 + 50
        
        pygame.draw.rect(self.screen, (64, 64, 64), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        pygame.display.flip()