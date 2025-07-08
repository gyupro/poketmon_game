"""
Sprite Downloader - Downloads Pokemon sprites from online sources
"""

import os
import requests
from PIL import Image
from typing import Optional


class SpriteDownloader:
    """Downloads and manages Pokemon sprites."""
    
    def __init__(self, sprite_directory: str = "assets/sprites"):
        self.sprite_directory = sprite_directory
        self.base_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"
        
        # Ensure sprite directory exists
        os.makedirs(self.sprite_directory, exist_ok=True)
    
    def download_sprite(self, pokemon_id: int, shiny: bool = False) -> Optional[str]:
        """
        Download a Pokemon sprite by ID.
        
        Args:
            pokemon_id: The Pokemon's ID number
            shiny: Whether to download the shiny variant
        
        Returns:
            Path to the downloaded sprite or None if failed
        """
        # Construct URL
        variant = "shiny" if shiny else "normal"
        filename = f"{pokemon_id}_{variant}.png"
        url = f"{self.base_url}/{'' if not shiny else 'shiny/'}{pokemon_id}.png"
        
        # Check if already downloaded
        filepath = os.path.join(self.sprite_directory, filename)
        if os.path.exists(filepath):
            return filepath
        
        try:
            # Download sprite
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Save to file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Verify it's a valid image
            img = Image.open(filepath)
            img.verify()
            
            print(f"Downloaded sprite for Pokemon ID {pokemon_id}")
            return filepath
            
        except Exception as e:
            print(f"Failed to download sprite for Pokemon ID {pokemon_id}: {e}")
            # Clean up partial download
            if os.path.exists(filepath):
                os.remove(filepath)
            return None
    
    def download_batch(self, pokemon_ids: list, include_shiny: bool = False):
        """
        Download sprites for multiple Pokemon.
        
        Args:
            pokemon_ids: List of Pokemon IDs to download
            include_shiny: Whether to also download shiny variants
        """
        success_count = 0
        
        for pokemon_id in pokemon_ids:
            # Download normal sprite
            if self.download_sprite(pokemon_id, shiny=False):
                success_count += 1
            
            # Download shiny sprite if requested
            if include_shiny:
                if self.download_sprite(pokemon_id, shiny=True):
                    success_count += 1
        
        print(f"Downloaded {success_count} sprites successfully")
    
    def get_sprite_path(self, pokemon_id: int, shiny: bool = False) -> Optional[str]:
        """
        Get the path to a Pokemon sprite, downloading if necessary.
        
        Args:
            pokemon_id: The Pokemon's ID number
            shiny: Whether to get the shiny variant
        
        Returns:
            Path to the sprite or None if not available
        """
        variant = "shiny" if shiny else "normal"
        filename = f"{pokemon_id}_{variant}.png"
        filepath = os.path.join(self.sprite_directory, filename)
        
        # If sprite exists, return path
        if os.path.exists(filepath):
            return filepath
        
        # Try to download it
        return self.download_sprite(pokemon_id, shiny)
    
    def resize_sprite(self, filepath: str, size: tuple) -> str:
        """
        Resize a sprite to specified dimensions.
        
        Args:
            filepath: Path to the sprite
            size: Target size (width, height)
        
        Returns:
            Path to resized sprite
        """
        # Create output filename
        basename = os.path.basename(filepath)
        name, ext = os.path.splitext(basename)
        resized_name = f"{name}_resized_{size[0]}x{size[1]}{ext}"
        resized_path = os.path.join(self.sprite_directory, resized_name)
        
        # Check if already resized
        if os.path.exists(resized_path):
            return resized_path
        
        try:
            # Open and resize image
            img = Image.open(filepath)
            img_resized = img.resize(size, Image.Resampling.LANCZOS)
            
            # Save resized image
            img_resized.save(resized_path)
            
            return resized_path
            
        except Exception as e:
            print(f"Failed to resize sprite {filepath}: {e}")
            return filepath  # Return original if resize fails
    
    def download_starter_sprites(self):
        """Download sprites for the starter Pokemon."""
        # Gen 1 starters
        starter_ids = [
            1,   # Bulbasaur
            4,   # Charmander
            7,   # Squirtle
            25,  # Pikachu (bonus)
        ]
        
        print("Downloading starter Pokemon sprites...")
        self.download_batch(starter_ids, include_shiny=False)
    
    def clean_cache(self):
        """Remove all downloaded sprites."""
        count = 0
        for filename in os.listdir(self.sprite_directory):
            if filename.endswith('.png'):
                filepath = os.path.join(self.sprite_directory, filename)
                os.remove(filepath)
                count += 1
        
        print(f"Removed {count} sprite files")


# Example usage
if __name__ == "__main__":
    downloader = SpriteDownloader()
    
    # Download starter sprites
    downloader.download_starter_sprites()
    
    # Get a specific sprite
    sprite_path = downloader.get_sprite_path(25)  # Pikachu
    if sprite_path:
        print(f"Pikachu sprite available at: {sprite_path}")