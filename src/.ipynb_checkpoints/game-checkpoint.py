"""
Main Game Logic - Core game loop and state management
"""

import pygame
import random
from typing import Optional
from .player import Player
from .pokemon import Pokemon
from .battle import Battle
from .ui import UI


class Game:
    """Main game class that manages the game loop and states."""
    
    def __init__(self):
        # Display settings
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 600
        self.FPS = 60
        
        # Initialize Pygame
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Pokemon Game")
        self.clock = pygame.time.Clock()
        
        # Game states
        self.running = True
        self.game_state = "MENU"  # MENU, WORLD, BATTLE, INVENTORY
        
        # Initialize game components
        self.player = None
        self.current_battle: Optional[Battle] = None
        self.ui = UI(self.screen)
        
        # Map and world data
        self.map_data = self.load_map_data()
        self.wild_pokemon_areas = []
        
        # Input handling
        self.keys_pressed = {}
    
    def load_map_data(self):
        """Load or generate map data."""
        # Simple map for now - can be expanded with actual map files
        return {
            "width": 20,
            "height": 20,
            "spawn_point": (10, 10),
            "tiles": []  # Would contain actual tile data
        }
    
    def initialize_game(self):
        """Initialize a new game."""
        # Create player
        player_name = "Ash"  # Would get from menu input
        spawn_x, spawn_y = self.map_data["spawn_point"]
        self.player = Player(player_name, spawn_x * 32, spawn_y * 32)
        
        # Give player a starter Pokemon
        starters = [
            ("Bulbasaur", "grass"),
            ("Charmander", "fire"),
            ("Squirtle", "water")
        ]
        
        # For now, give random starter
        starter_name, starter_type = random.choice(starters)
        starter_pokemon = Pokemon(starter_name, starter_type, level=5)
        self.player.add_pokemon(starter_pokemon)
        
        self.game_state = "WORLD"
    
    def run(self):
        """Main game loop."""
        self.initialize_game()
        
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
            
            elif event.type == pygame.KEYDOWN:
                self.keys_pressed[event.key] = True
                self.handle_keypress(event.key)
            
            elif event.type == pygame.KEYUP:
                self.keys_pressed[event.key] = False
    
    def handle_keypress(self, key):
        """Handle specific key press events."""
        if self.game_state == "WORLD":
            # Movement keys are handled in update
            
            if key == pygame.K_SPACE:
                # Interact with objects
                pass
            
            elif key == pygame.K_i:
                # Open inventory
                self.game_state = "INVENTORY"
            
            elif key == pygame.K_p:
                # Open Pokemon menu
                pass
        
        elif self.game_state == "BATTLE":
            if self.current_battle and not self.current_battle.is_over:
                # Battle move selection
                if key == pygame.K_1:
                    self.current_battle.player_turn(0)
                elif key == pygame.K_2:
                    self.current_battle.player_turn(1)
                elif key == pygame.K_3:
                    self.current_battle.player_turn(2)
                elif key == pygame.K_4:
                    self.current_battle.player_turn(3)
                elif key == pygame.K_r:
                    # Try to run
                    if self.current_battle.run_away():
                        self.end_battle()
            else:
                # Return to world after battle
                if key == pygame.K_SPACE:
                    self.end_battle()
        
        elif self.game_state == "INVENTORY":
            if key == pygame.K_ESCAPE or key == pygame.K_i:
                self.game_state = "WORLD"
    
    def update(self, dt):
        """Update game logic."""
        if self.game_state == "WORLD":
            self.update_world(dt)
        elif self.game_state == "BATTLE":
            self.update_battle(dt)
    
    def update_world(self, dt):
        """Update world exploration state."""
        # Handle player movement
        dx, dy = 0, 0
        move_speed = self.player.move_speed
        
        if self.keys_pressed.get(pygame.K_LEFT, False):
            dx = -move_speed
        elif self.keys_pressed.get(pygame.K_RIGHT, False):
            dx = move_speed
        elif self.keys_pressed.get(pygame.K_UP, False):
            dy = -move_speed
        elif self.keys_pressed.get(pygame.K_DOWN, False):
            dy = move_speed
        
        if dx != 0 or dy != 0:
            self.player.move(dx, dy)
            
            # Check for random encounters (simplified)
            if random.randint(1, 100) <= 5:  # 5% chance per movement
                self.trigger_wild_encounter()
    
    def update_battle(self, dt):
        """Update battle state."""
        # Battle updates are handled through events
        pass
    
    def trigger_wild_encounter(self):
        """Start a wild Pokemon encounter."""
        if not self.player.can_battle():
            return
        
        # Generate random wild Pokemon
        wild_types = ["normal", "fire", "water", "grass"]
        wild_names = {
            "normal": ["Rattata", "Pidgey", "Meowth"],
            "fire": ["Vulpix", "Growlithe", "Ponyta"],
            "water": ["Psyduck", "Poliwag", "Goldeen"],
            "grass": ["Oddish", "Bellsprout", "Paras"]
        }
        
        wild_type = random.choice(wild_types)
        wild_name = random.choice(wild_names[wild_type])
        wild_level = random.randint(3, 7)
        
        wild_pokemon = Pokemon(wild_name, wild_type, wild_level)
        
        # Start battle
        self.current_battle = Battle(self.player.active_pokemon, wild_pokemon)
        self.current_battle.start()
        self.game_state = "BATTLE"
    
    def end_battle(self):
        """End current battle and return to world."""
        self.current_battle = None
        self.game_state = "WORLD"
    
    def render(self):
        """Render the game."""
        self.screen.fill((0, 0, 0))  # Clear screen
        
        if self.game_state == "WORLD":
            self.render_world()
        elif self.game_state == "BATTLE":
            self.render_battle()
        elif self.game_state == "INVENTORY":
            self.render_inventory()
        elif self.game_state == "MENU":
            self.render_menu()
        
        pygame.display.flip()
    
    def render_world(self):
        """Render the world exploration view."""
        # Draw map (simplified - just a green background for now)
        self.screen.fill((34, 139, 34))  # Forest green
        
        # Draw player
        player_rect = pygame.Rect(self.player.x, self.player.y, 32, 32)
        pygame.draw.rect(self.screen, (255, 0, 0), player_rect)
        
        # Draw UI elements
        self.ui.draw_player_status(self.player)
    
    def render_battle(self):
        """Render the battle view."""
        if self.current_battle:
            self.ui.draw_battle_screen(self.current_battle)
    
    def render_inventory(self):
        """Render the inventory view."""
        self.ui.draw_inventory(self.player)
    
    def render_menu(self):
        """Render the main menu."""
        self.ui.draw_main_menu()