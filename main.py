#!/usr/bin/env python3
"""
Pokemon Game - Main Entry Point
"""

import sys
import pygame
from src.game import Game


def main():
    """Main entry point for the Pokemon game."""
    print("=" * 60)
    print("  POKEMON GAME - Loading...")
    print("=" * 60)
    
    try:
        # Initialize Pygame modules
        print("Initializing Pygame...")
        pygame.init()
        
        print("Initializing font system...")
        if not pygame.font.init():
            print("Warning: Font system initialization failed")
        
        print("Initializing sound system...")
        try:
            # Initialize with no audio in WSL environment
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
        except pygame.error as e:
            print(f"Warning: Sound system initialization failed: {e}")
            print("Game will continue without sound.")
            # Disable mixer completely if initialization fails
            pygame.mixer.quit()
        
        # Set up display
        print("Setting up display...")
        pygame.display.set_caption("Pokemon Game")
        icon = pygame.Surface((32, 32))
        icon.fill((255, 0, 0))  # Red icon placeholder
        pygame.display.set_icon(icon)
        
        print("Loading game...")
        # Initialize and run the game
        game = Game()
        
        print("Game loaded successfully!")
        print("=" * 60)
        print("  Starting game loop...")
        print("=" * 60)
        
        game.run()
        
    except pygame.error as e:
        print(f"\nPygame Error: {e}")
        print("Please ensure Pygame is properly installed:")
        print("  pip install pygame")
    except ImportError as e:
        print(f"\nImport Error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
    except FileNotFoundError as e:
        print(f"\nFile Not Found Error: {e}")
        print("Please ensure you're running from the correct directory")
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease report this error if it persists.")
    finally:
        # Cleanup
        print("\nShutting down...")
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()