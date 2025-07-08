#!/usr/bin/env python3
"""
Demo script to showcase the new map system
"""

import pygame
import sys
from src.game import Game
from src.world import World
from src.player import Player
from src.map import TileType


def main():
    """Run a demo of the map system."""
    pygame.init()
    pygame.font.init()
    
    # Create display
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pokemon Map System Demo")
    clock = pygame.time.Clock()
    
    # Create world and player
    world = World()
    player = Player("Demo Player", 10, 10)
    
    # Game loop
    running = True
    keys = {}
    font = pygame.font.Font(None, 24)
    
    print("\n=== POKEMON MAP SYSTEM DEMO ===")
    print("Controls:")
    print("  Arrow Keys / WASD - Move")
    print("  Hold Shift - Run")
    print("  Space - Interact")
    print("  ESC - Exit")
    print("\nFeatures:")
    print("  - Grid-based movement (like classic Pokemon)")
    print("  - Multiple connected maps with transitions")
    print("  - NPCs with dialogue")
    print("  - Collision detection")
    print("  - Wild Pokemon areas (tall grass)")
    print("\nTry walking to the north edge of town to reach Route 1!")
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                keys[event.key] = True
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Handle interaction
                    if world.current_dialogue:
                        world.advance_dialogue()
                    else:
                        interaction = world.interact(player)
            elif event.type == pygame.KEYUP:
                keys[event.key] = False
        
        # Handle movement
        if not player.is_moving and not world.current_dialogue:
            is_running = keys.get(pygame.K_LSHIFT, False) or keys.get(pygame.K_RSHIFT, False)
            
            if keys.get(pygame.K_LEFT, False) or keys.get(pygame.K_a, False):
                target_x = player.grid_x - 1
                target_y = player.grid_y
                if world.can_move_to(target_x, target_y):
                    player.start_move("left", is_running)
            elif keys.get(pygame.K_RIGHT, False) or keys.get(pygame.K_d, False):
                target_x = player.grid_x + 1
                target_y = player.grid_y
                if world.can_move_to(target_x, target_y):
                    player.start_move("right", is_running)
            elif keys.get(pygame.K_UP, False) or keys.get(pygame.K_w, False):
                target_x = player.grid_x
                target_y = player.grid_y - 1
                if world.can_move_to(target_x, target_y):
                    player.start_move("up", is_running)
            elif keys.get(pygame.K_DOWN, False) or keys.get(pygame.K_s, False):
                target_x = player.grid_x
                target_y = player.grid_y + 1
                if world.can_move_to(target_x, target_y):
                    player.start_move("down", is_running)
        
        # Update
        player.update(dt)
        world.update(dt, player)
        
        # Check warps
        if not player.is_moving:
            world.check_warps(player)
        
        # Render
        screen.fill((0, 0, 0))
        world.render(screen, player)
        
        # Draw UI info
        info_text = f"Map: {world.current_map.name} | Position: ({player.grid_x}, {player.grid_y})"
        if player.is_running:
            info_text += " | RUNNING"
        text_surface = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        
        # Draw controls hint
        if not world.current_dialogue:
            hint_text = "Arrow Keys: Move | Shift: Run | Space: Interact | ESC: Exit"
        else:
            hint_text = "Press SPACE to continue dialogue..."
        hint_surface = font.render(hint_text, True, (255, 255, 255))
        screen.blit(hint_surface, (10, screen.get_height() - 30))
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()