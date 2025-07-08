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
    
    def download_sprite(self, pokemon_id: int, shiny: bool = False, back: bool = False) -> Optional[str]:
        """
        Download a Pokemon sprite by ID.
        
        Args:
            pokemon_id: The Pokemon's ID number
            shiny: Whether to download the shiny variant
            back: Whether to download the back sprite
        
        Returns:
            Path to the downloaded sprite or None if failed
        """
        # Construct URL
        variant_parts = []
        if back:
            variant_parts.append("back")
        if shiny:
            variant_parts.append("shiny")
        variant_parts.append("normal" if not variant_parts else "")
        variant = "_".join(filter(None, variant_parts))
        
        filename = f"{pokemon_id}_{variant}.png"
        
        # Build URL path components
        url_parts = []
        if back:
            url_parts.append("back")
        if shiny:
            url_parts.append("shiny")
        url_path = "/".join(url_parts) + "/" if url_parts else ""
        url = f"{self.base_url}/{url_path}{pokemon_id}.png"
        
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
    
    def download_batch(self, pokemon_ids: list, include_shiny: bool = False, include_back: bool = False):
        """
        Download sprites for multiple Pokemon.
        
        Args:
            pokemon_ids: List of Pokemon IDs to download
            include_shiny: Whether to also download shiny variants
            include_back: Whether to also download back sprites
        """
        success_count = 0
        total_attempts = 0
        
        for pokemon_id in pokemon_ids:
            # Download front normal sprite
            total_attempts += 1
            if self.download_sprite(pokemon_id, shiny=False, back=False):
                success_count += 1
            
            # Download back normal sprite if requested
            if include_back:
                total_attempts += 1
                if self.download_sprite(pokemon_id, shiny=False, back=True):
                    success_count += 1
            
            # Download shiny sprites if requested
            if include_shiny:
                total_attempts += 1
                if self.download_sprite(pokemon_id, shiny=True, back=False):
                    success_count += 1
                
                # Download back shiny sprite if both are requested
                if include_back:
                    total_attempts += 1
                    if self.download_sprite(pokemon_id, shiny=True, back=True):
                        success_count += 1
        
        print(f"Downloaded {success_count}/{total_attempts} sprites successfully")
    
    def get_sprite_path(self, pokemon_id: int, shiny: bool = False, back: bool = False) -> Optional[str]:
        """
        Get the path to a Pokemon sprite, downloading if necessary.
        
        Args:
            pokemon_id: The Pokemon's ID number
            shiny: Whether to get the shiny variant
            back: Whether to get the back sprite
        
        Returns:
            Path to the sprite or None if not available
        """
        # Construct variant string
        variant_parts = []
        if back:
            variant_parts.append("back")
        if shiny:
            variant_parts.append("shiny")
        variant_parts.append("normal" if not variant_parts else "")
        variant = "_".join(filter(None, variant_parts))
        
        filename = f"{pokemon_id}_{variant}.png"
        filepath = os.path.join(self.sprite_directory, filename)
        
        # If sprite exists, return path
        if os.path.exists(filepath):
            return filepath
        
        # Try to download it
        return self.download_sprite(pokemon_id, shiny, back)
    
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
        self.download_batch(starter_ids, include_shiny=False, include_back=True)
    
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
    
    # Get back sprite
    back_sprite_path = downloader.get_sprite_path(25, back=True)  # Pikachu back
    if back_sprite_path:
        print(f"Pikachu back sprite available at: {back_sprite_path}")