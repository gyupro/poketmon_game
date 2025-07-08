#!/usr/bin/env python3
"""
Script to download sprites for 10 popular Pokemon.
Downloads both front and back sprites from PokeAPI.
"""

import os
import sys
from utils.downloader import SpriteDownloader


# Pokemon name to ID mapping
POPULAR_POKEMON = {
    "Pikachu": 25,
    "Charmander": 4,
    "Squirtle": 7,
    "Bulbasaur": 1,
    "Eevee": 133,
    "Gengar": 94,
    "Snorlax": 143,
    "Dragonite": 149,
    "Mewtwo": 150,
    "Mew": 151
}


def main():
    """Download sprites for popular Pokemon."""
    print("=== Pokemon Sprite Downloader ===")
    print(f"Downloading sprites for {len(POPULAR_POKEMON)} popular Pokemon...")
    print()
    
    # Initialize downloader with absolute path
    sprite_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sprites")
    downloader = SpriteDownloader(sprite_directory=sprite_dir)
    
    # Ensure the sprite directory exists
    os.makedirs(sprite_dir, exist_ok=True)
    print(f"Sprites will be saved to: {sprite_dir}")
    print()
    
    # Track download statistics
    total_downloads = 0
    successful_downloads = 0
    failed_pokemon = []
    
    # Download sprites for each Pokemon
    for name, pokemon_id in POPULAR_POKEMON.items():
        print(f"Downloading sprites for {name} (ID: {pokemon_id})...")
        
        # Download front sprite
        front_sprite = downloader.download_sprite(pokemon_id, shiny=False, back=False)
        total_downloads += 1
        if front_sprite:
            successful_downloads += 1
            print(f"  ✓ Front sprite downloaded: {os.path.basename(front_sprite)}")
        else:
            print(f"  ✗ Failed to download front sprite")
            failed_pokemon.append(f"{name} (front)")
        
        # Download back sprite
        back_sprite = downloader.download_sprite(pokemon_id, shiny=False, back=True)
        total_downloads += 1
        if back_sprite:
            successful_downloads += 1
            print(f"  ✓ Back sprite downloaded: {os.path.basename(back_sprite)}")
        else:
            print(f"  ✗ Failed to download back sprite")
            failed_pokemon.append(f"{name} (back)")
        
        print()
    
    # Print summary
    print("=== Download Summary ===")
    print(f"Total sprites attempted: {total_downloads}")
    print(f"Successfully downloaded: {successful_downloads}")
    print(f"Failed downloads: {total_downloads - successful_downloads}")
    
    if failed_pokemon:
        print("\nFailed to download:")
        for failed in failed_pokemon:
            print(f"  - {failed}")
    
    # List all downloaded files
    print("\n=== Downloaded Files ===")
    try:
        files = sorted([f for f in os.listdir(sprite_dir) if f.endswith('.png')])
        if files:
            for file in files:
                file_path = os.path.join(sprite_dir, file)
                file_size = os.path.getsize(file_path) / 1024  # Convert to KB
                print(f"  {file} ({file_size:.1f} KB)")
        else:
            print("  No sprite files found.")
    except Exception as e:
        print(f"  Error listing files: {e}")
    
    print(f"\nAll sprites saved to: {sprite_dir}")
    
    return 0 if successful_downloads == total_downloads else 1


if __name__ == "__main__":
    sys.exit(main())