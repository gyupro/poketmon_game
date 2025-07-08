#!/usr/bin/env python3
"""
Pokemon Game - Main Entry Point
"""

import sys
import pygame
from src.game import Game


def main():
    """Main entry point for the Pokemon game."""
    pygame.init()
    
    # Initialize the game
    game = Game()
    
    # Run the game
    game.run()
    
    # Cleanup
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()