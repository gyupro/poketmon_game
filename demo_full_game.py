#!/usr/bin/env python3
"""
Pokemon Game - Comprehensive Demo Script
Showcases all major features of the Pokemon game
"""

import pygame
import sys
import time
from src.game import Game, GameState
from src.player import Player
from src.pokemon import Pokemon, PokemonType, Move, create_pokemon_from_species
from src.ui import UIState
from src.battle import Battle, BattleType
from src.world import NPC


class PokemonGameDemo:
    """Demo class that showcases all game features."""
    
    def __init__(self):
        self.game = None
        self.demo_steps = []
        self.current_step = 0
        
    def print_header(self, text):
        """Print a formatted header."""
        print("\n" + "="*60)
        print(f"  {text}")
        print("="*60 + "\n")
        
    def print_info(self, text):
        """Print formatted info text."""
        print(f"[INFO] {text}")
        
    def wait_for_input(self, prompt="Press ENTER to continue..."):
        """Wait for user input."""
        input(f"\n{prompt}")
        
    def initialize_game(self):
        """Initialize the game with demo settings."""
        self.print_header("POKEMON GAME - COMPREHENSIVE DEMO")
        print("Welcome to the Pokemon Game Demo!")
        print("This demo will showcase all major features of the game.")
        print("\nFeatures to be demonstrated:")
        print("  1. Starter Pokemon Selection")
        print("  2. World Exploration")
        print("  3. NPC Interactions")
        print("  4. Wild Pokemon Encounters")
        print("  5. Battle System")
        print("  6. Pokemon Center Healing")
        print("  7. Item Usage")
        print("  8. Menu Navigation")
        
        self.wait_for_input()
        
        # Initialize Pygame
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()
        
        # Create game instance
        self.game = Game()
        
    def demo_starter_selection(self):
        """Demonstrate starter Pokemon selection."""
        self.print_header("STARTER POKEMON SELECTION")
        
        print("In a full game, you would select from three starter Pokemon:")
        print("  1. Bulbasaur (Grass/Poison)")
        print("  2. Charmander (Fire)")
        print("  3. Squirtle (Water)")
        
        # For demo, we'll create a custom starter selection
        starter_choice = input("\nChoose your starter (1-3): ").strip()
        
        if starter_choice not in ['1', '2', '3']:
            starter_choice = '1'
            print("Invalid choice. Defaulting to Bulbasaur.")
        
        # Create the game with chosen starter
        self.game.create_new_game()
        
        # Replace the random starter with chosen one
        starters = [
            (1, "Bulbasaur", PokemonType.GRASS, {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45}),
            (4, "Charmander", PokemonType.FIRE, {"hp": 39, "attack": 52, "defense": 43, "sp_attack": 60, "sp_defense": 50, "speed": 65}),
            (7, "Squirtle", PokemonType.WATER, {"hp": 44, "attack": 48, "defense": 65, "sp_attack": 50, "sp_defense": 64, "speed": 43})
        ]
        
        chosen_idx = int(starter_choice) - 1
        species_id, name, ptype, stats = starters[chosen_idx]
        
        # Clear current team and add chosen starter
        self.game.player.pokemon_team.clear()
        
        starter = Pokemon(
            species_id=species_id,
            species_name=name,
            types=[ptype],
            base_stats=stats,
            level=5
        )
        
        # Add starter moves
        starter.moves = [
            Move("Tackle", PokemonType.NORMAL, "physical", 40, 100, 35),
            Move("Growl", PokemonType.NORMAL, "status", 0, 100, 40, effect="lower_attack")
        ]
        
        # Add type-specific move
        if ptype == PokemonType.GRASS:
            starter.moves.append(Move("Vine Whip", PokemonType.GRASS, "physical", 45, 100, 25))
        elif ptype == PokemonType.FIRE:
            starter.moves.append(Move("Ember", PokemonType.FIRE, "special", 40, 100, 25))
        elif ptype == PokemonType.WATER:
            starter.moves.append(Move("Water Gun", PokemonType.WATER, "special", 40, 100, 25))
        
        self.game.player.add_pokemon(starter)
        
        print(f"\nYou received {name}!")
        print(f"Level: {starter.level}")
        print(f"Type: {ptype.value}")
        print(f"Moves: {', '.join([m.name for m in starter.moves])}")
        
        self.wait_for_input()
        
    def demo_controls(self):
        """Show game controls."""
        self.print_header("GAME CONTROLS")
        
        print("World Exploration:")
        print("  Arrow Keys / WASD - Move character")
        print("  Hold Shift - Run")
        print("  Space - Interact with NPCs/Objects")
        print("  I - Open Inventory")
        print("  P - Open Pokemon Menu")
        print("  ESC - Pause Menu")
        
        print("\nBattle Controls:")
        print("  1-4 - Select move")
        print("  Arrow Keys - Navigate menus")
        print("  Enter - Confirm selection")
        print("  B - Back/Cancel")
        print("  R - Run from battle (wild Pokemon only)")
        
        self.wait_for_input()
        
    def demo_world_exploration(self):
        """Demonstrate world exploration."""
        self.print_header("WORLD EXPLORATION")
        
        print("The game features:")
        print("  - Grid-based movement (like classic Pokemon games)")
        print("  - Multiple connected maps")
        print("  - Different terrain types:")
        print("    * Normal ground")
        print("    * Tall grass (wild Pokemon encounters)")
        print("    * Water (requires Surf)")
        print("    * Buildings with interiors")
        
        print("\nCurrent location: Pallet Town")
        print("Try exploring north to Route 1!")
        
        self.wait_for_input()
        
    def demo_npc_interaction(self):
        """Demonstrate NPC interactions."""
        self.print_header("NPC INTERACTIONS")
        
        print("NPCs in the game can:")
        print("  - Provide helpful dialogue")
        print("  - Give you items")
        print("  - Challenge you to battles (Trainers)")
        print("  - Offer services (Pokemon Center, Poke Mart)")
        
        print("\nIn Pallet Town, you can find:")
        print("  - Professor Oak (gives advice)")
        print("  - Your rival Gary (can battle)")
        print("  - Various townspeople")
        
        print("\nPress SPACE when facing an NPC to interact!")
        
        self.wait_for_input()
        
    def demo_wild_encounters(self):
        """Demonstrate wild Pokemon encounters."""
        self.print_header("WILD POKEMON ENCOUNTERS")
        
        print("Wild Pokemon appear in tall grass!")
        print("\nEncounter mechanics:")
        print("  - Random encounters based on area")
        print("  - Different Pokemon in different routes")
        print("  - Rarity system (common, uncommon, rare)")
        print("  - Level ranges based on area")
        
        print("\nRoute 1 Pokemon:")
        print("  - Pidgey (Common)")
        print("  - Rattata (Common)")
        print("  - Spearow (Uncommon)")
        print("  - Pikachu (Rare)")
        
        print("\nWalk through tall grass on Route 1 to encounter wild Pokemon!")
        
        self.wait_for_input()
        
    def demo_battle_system(self):
        """Demonstrate the battle system."""
        self.print_header("BATTLE SYSTEM")
        
        print("Battle features:")
        print("  - Turn-based combat")
        print("  - Type effectiveness system")
        print("  - Status conditions (Paralysis, Burn, Poison, etc.)")
        print("  - Move PP system")
        print("  - Experience and leveling")
        print("  - Stat modifications")
        print("  - Critical hits")
        print("  - Accuracy and evasion")
        
        print("\nBattle options:")
        print("  - Fight: Use moves")
        print("  - Bag: Use items")
        print("  - Pokemon: Switch Pokemon")
        print("  - Run: Escape (wild battles only)")
        
        self.wait_for_input()
        
    def demo_items(self):
        """Demonstrate item usage."""
        self.print_header("ITEM SYSTEM")
        
        print("Your starting inventory:")
        print("  - 5x Poke Ball (catch wild Pokemon)")
        print("  - 3x Potion (restore 20 HP)")
        print("  - 1x Super Potion (restore 50 HP)")
        
        print("\nItem categories:")
        print("  - Healing items (Potions, Status healers)")
        print("  - Poke Balls (Catch Pokemon)")
        print("  - Battle items (X Attack, X Defense)")
        print("  - Key items (Special items)")
        
        print("\nPress I to open inventory during exploration!")
        
        self.wait_for_input()
        
    def demo_pokemon_center(self):
        """Demonstrate Pokemon Center healing."""
        self.print_header("POKEMON CENTER")
        
        print("Pokemon Centers provide free healing services!")
        print("\nFeatures:")
        print("  - Fully heal all Pokemon")
        print("  - Restore PP for all moves")
        print("  - Cure all status conditions")
        print("  - PC storage system (future feature)")
        
        print("\nLook for the red-roofed building!")
        print("Talk to Nurse Joy inside to heal your Pokemon.")
        
        self.wait_for_input()
        
    def run_game_demo(self):
        """Run the actual game with demo features."""
        self.print_header("STARTING GAME")
        
        print("The game window will now open.")
        print("Remember the controls and try all the features!")
        print("\nDemo objectives:")
        print("  1. Walk around Pallet Town")
        print("  2. Talk to NPCs")
        print("  3. Go north to Route 1")
        print("  4. Walk in tall grass for wild encounters")
        print("  5. Battle a wild Pokemon")
        print("  6. Use items from your bag")
        print("  7. Visit the Pokemon Center")
        
        self.wait_for_input("Press ENTER to start the game...")
        
        # Run the game
        try:
            self.game.run()
        except Exception as e:
            print(f"\nError during game: {e}")
            import traceback
            traceback.print_exc()
        
    def cleanup(self):
        """Clean up resources."""
        if self.game:
            pygame.quit()
        
    def run(self):
        """Run the complete demo."""
        try:
            # Initialize
            self.initialize_game()
            
            # Run demo sections
            self.demo_starter_selection()
            self.demo_controls()
            self.demo_world_exploration()
            self.demo_npc_interaction()
            self.demo_wild_encounters()
            self.demo_battle_system()
            self.demo_items()
            self.demo_pokemon_center()
            
            # Run the actual game
            self.run_game_demo()
            
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user.")
        except Exception as e:
            print(f"\n\nError during demo: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
            print("\n\nThank you for trying the Pokemon Game Demo!")


def main():
    """Main entry point."""
    demo = PokemonGameDemo()
    demo.run()


if __name__ == "__main__":
    main()