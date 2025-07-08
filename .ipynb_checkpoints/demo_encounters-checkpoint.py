#!/usr/bin/env python3
"""
Demo script showing the wild Pokemon encounter system in action
"""

import pygame
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.game import Game, GameState
from src.world import World
from src.player import Player
from src.pokemon import create_pokemon_from_species
from src.encounters import EncounterSystem
from src.ui import UIState


def main():
    """Run the encounter system demo."""
    pygame.init()
    
    print("=== Wild Pokemon Encounter System Demo ===")
    print("Controls:")
    print("- Arrow keys or WASD: Move around")
    print("- Hold Shift: Run (move faster)")
    print("- Space: Interact/Continue dialogue")
    print("- I: Open inventory (use Repel)")
    print("- Escape: Exit demo")
    print("\nFeatures demonstrated:")
    print("- Walk in tall grass to encounter wild Pokemon")
    print("- Different Pokemon appear based on area")
    print("- Time-based encounters (morning/day/night)")
    print("- Encounter chains increase shiny chance")
    print("- Repel items prevent encounters")
    print("\nPress any key to start...")
    
    # Create game instance
    game = Game()
    
    # Wait for key press
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                return
    
    # Start new game
    game.create_new_game()
    
    # Add some items to player inventory
    game.player.inventory["repel"] = 5
    game.player.inventory["super_repel"] = 3
    game.player.inventory["max_repel"] = 1
    
    # Move player to Route 1 where there's tall grass
    game.world.change_map("route_1", 10, 10, game.player)
    
    # Custom game loop with encounter info display
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    while game.running:
        dt = clock.tick(60) / 1000.0
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game.running = False
                else:
                    game.handle_events()
            else:
                game.handle_events()
        
        # Update game
        game.update(dt)
        
        # Render game
        game.render()
        
        # Draw encounter info overlay
        if game.game_state == GameState.WORLD:
            draw_encounter_info(game.screen, font, game.world)
        
        pygame.display.flip()
    
    pygame.quit()
    print("\nThanks for trying the Pokemon Encounter System!")


def draw_encounter_info(screen, font, world):
    """Draw encounter system information overlay."""
    info = world.get_encounter_info()
    
    # Background for info
    info_rect = pygame.Rect(10, 10, 300, 120)
    pygame.draw.rect(screen, (0, 0, 0), info_rect)
    pygame.draw.rect(screen, (255, 255, 255), info_rect, 2)
    
    # Draw info text
    y = 20
    texts = [
        f"Area: {world.encounter_system.encounter_tables.get(info['area'], {}).get('area_name', 'Unknown')}",
        f"Repel Steps: {info['repel_steps']}",
        f"Chain Species: {info['chain_species'] or 'None'}",
        f"Chain Count: {info['chain_count']}",
        f"Steps in Grass: {world.steps_in_grass}"
    ]
    
    for text in texts:
        text_surface = font.render(text, True, (255, 255, 255))
        screen.blit(text_surface, (20, y))
        y += 20
    
    # Show available Pokemon in area
    area_info = world.encounter_system.get_area_info(info['area'])
    if area_info:
        # Count total Pokemon
        total = 0
        for rarity in area_info['pokemon_by_rarity'].values():
            total += len(rarity)
        
        hint_text = f"Pokemon in area: {total} species"
        hint_surface = font.render(hint_text, True, (255, 255, 100))
        screen.blit(hint_surface, (20, y))


if __name__ == "__main__":
    main()