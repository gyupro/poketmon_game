#!/usr/bin/env python3
"""
Demo script showing how to use the sprite downloader utility.
"""

import os
from utils.downloader import SpriteDownloader


def main():
    """Demonstrate sprite downloader usage."""
    print("=== Sprite Downloader Demo ===\n")
    
    # Initialize downloader
    sprite_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sprites")
    downloader = SpriteDownloader(sprite_directory=sprite_dir)
    
    # Example 1: Get a sprite (download if needed)
    print("1. Getting Pikachu sprite (will use existing if already downloaded):")
    pikachu_sprite = downloader.get_sprite_path(25)
    if pikachu_sprite:
        print(f"   Pikachu sprite: {pikachu_sprite}")
    
    # Example 2: Get a back sprite
    print("\n2. Getting Charmander back sprite:")
    charmander_back = downloader.get_sprite_path(4, back=True)
    if charmander_back:
        print(f"   Charmander back sprite: {charmander_back}")
    
    # Example 3: Download a new Pokemon sprite
    print("\n3. Downloading a new Pokemon (Charizard - ID: 6):")
    charizard = downloader.download_sprite(6, back=False)
    if charizard:
        print(f"   Downloaded: {charizard}")
    
    # Example 4: Download shiny variant
    print("\n4. Downloading shiny Eevee:")
    shiny_eevee = downloader.download_sprite(133, shiny=True)
    if shiny_eevee:
        print(f"   Shiny Eevee: {shiny_eevee}")
    
    # Example 5: Batch download with all variants
    print("\n5. Batch downloading multiple Pokemon with back sprites:")
    legendary_birds = [144, 145, 146]  # Articuno, Zapdos, Moltres
    downloader.download_batch(legendary_birds, include_back=True)
    
    # Example 6: Resize a sprite
    print("\n6. Resizing Pikachu sprite to 64x64:")
    if pikachu_sprite:
        resized_sprite = downloader.resize_sprite(pikachu_sprite, (64, 64))
        print(f"   Resized sprite: {resized_sprite}")
    
    # Example 7: Clean up specific files (optional)
    print("\n7. Current sprite directory contents:")
    sprites = [f for f in os.listdir(sprite_dir) if f.endswith('.png')]
    print(f"   Total sprites: {len(sprites)}")
    print(f"   First 5 sprites: {sprites[:5]}")
    
    print("\nDemo complete! Check the assets/sprites/ directory for all downloaded sprites.")


if __name__ == "__main__":
    main()