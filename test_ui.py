#!/usr/bin/env python3
"""
Test script to verify the UI system works correctly
"""

import pygame
import sys
from src.ui import UI, UIState, Colors
from src.game import Game
from src.pokemon import Pokemon, PokemonType, Move
from src.player import Player


def test_ui_components():
    """Test individual UI components."""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("UI Component Test")
    clock = pygame.time.Clock()
    
    # Create UI
    ui = UI(screen)
    
    # Create test data
    player = Player("Test Player", 100, 100)
    
    # Create a test Pokemon
    test_pokemon = Pokemon(
        species_id=25,
        species_name="Pikachu",
        types=[PokemonType.ELECTRIC],
        base_stats={"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        level=10
    )
    test_pokemon.moves = [
        Move("Thunder Shock", PokemonType.ELECTRIC, "special", 40, 100, 30),
        Move("Quick Attack", PokemonType.NORMAL, "physical", 40, 100, 30),
        Move("Thunder Wave", PokemonType.ELECTRIC, "status", 0, 90, 20, effect="paralysis"),
        Move("Double Team", PokemonType.NORMAL, "status", 0, 100, 15, effect="raise_evasion")
    ]
    
    player.add_pokemon(test_pokemon)
    player.add_item("pokeball", 10)
    player.add_item("potion", 5)
    player.add_item("super_potion", 3)
    
    # Test different UI states
    test_states = [UIState.MAIN_MENU, UIState.POKEMON_MENU, UIState.BAG_MENU]
    current_state_index = 0
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Cycle through states
                    current_state_index = (current_state_index + 1) % len(test_states)
                    ui.state = test_states[current_state_index]
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # Clear screen
        screen.fill(Colors.BLACK)
        
        # Update UI
        ui.update(dt)
        
        # Draw based on current state
        if ui.state == UIState.MAIN_MENU:
            ui.draw_main_menu()
        elif ui.state == UIState.POKEMON_MENU:
            ui.draw_pokemon_menu(player)
        elif ui.state == UIState.BAG_MENU:
            ui.draw_bag_menu(player)
        
        # Draw instructions
        font = pygame.font.Font(None, 24)
        inst_text = f"Current: {ui.state.value} - Press SPACE to change, ESC to quit"
        inst_surface = font.render(inst_text, True, Colors.WHITE)
        screen.blit(inst_surface, (10, 10))
        
        pygame.display.flip()
    
    pygame.quit()


def main():
    """Run the full game."""
    try:
        import main as game_main
        game_main.main()
    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Uncomment the line you want to test
    test_ui_components()  # Test individual UI components
    # main()  # Run the full game