#!/usr/bin/env python3
"""
Test script for the wild Pokemon encounter system
"""

import pygame
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.encounters import EncounterSystem, TimeOfDay
from src.pokemon import create_pokemon_from_species, POKEMON_DATA
from src.world import World
from src.player import Player


def test_encounter_system():
    """Test various aspects of the encounter system."""
    print("=== Pokemon Encounter System Test ===\n")
    
    # Initialize encounter system
    encounter_system = EncounterSystem()
    
    # Test 1: Time of day
    print("1. Time of Day Test")
    current_time = encounter_system.get_time_of_day()
    print(f"Current time period: {current_time.value}")
    print()
    
    # Test 2: Encounter tables
    print("2. Available Areas")
    for area_id in encounter_system.encounter_tables:
        table = encounter_system.encounter_tables[area_id]
        print(f"- {table.area_name} (base rate: {table.base_encounter_rate}%)")
    print()
    
    # Test 3: Route 1 encounters
    print("3. Route 1 Encounter Test")
    print("Simulating 10 encounters on Route 1:")
    for i in range(10):
        # Simulate encounter check
        if encounter_system.should_encounter("route_1", steps_in_grass=i+1):
            pokemon = encounter_system.get_encounter("route_1")
            if pokemon:
                shiny_str = " (SHINY!)" if pokemon.is_shiny else ""
                print(f"  Encounter {i+1}: {pokemon.species_name} Lv.{pokemon.level}{shiny_str}")
            else:
                print(f"  Encounter {i+1}: No Pokemon found (missing data)")
        else:
            print(f"  Step {i+1}: No encounter")
    print()
    
    # Test 4: Repel functionality
    print("4. Repel Test")
    encounter_system.use_repel(5)
    print(f"Repel active for {encounter_system.repel_steps} steps")
    for i in range(6):
        repelled = encounter_system.check_repel(player_level=10)
        print(f"  Step {i+1}: Repelled = {repelled}, Steps remaining = {encounter_system.repel_steps}")
    print()
    
    # Test 5: Chain encounters
    print("5. Chain Encounter Test")
    print("Simulating chain building (catching same species):")
    # Force encounters of same species
    encounter_system.chain_species = 25  # Pikachu
    encounter_system.chain_count = 0
    
    for i in range(5):
        encounter_system.chain_count += 1
        species, count = encounter_system.get_chain_info()
        print(f"  Chain #{count}: {POKEMON_DATA.get(species, {}).get('name', 'Unknown')} " +
              f"(Shiny chance boost: {encounter_system._get_chain_shiny_multiplier(count):.1f}x)")
    print()
    
    # Test 6: Special areas
    print("6. Special Area Encounters")
    special_areas = ["cerulean_cave", "victory_road", "power_plant"]
    for area in special_areas:
        print(f"\n{area}:")
        info = encounter_system.get_area_info(area)
        if info:
            print(f"  Base encounter rate: {info['encounter_rate']}%")
            print("  Legendary Pokemon:")
            for legendary in info["pokemon_by_rarity"]["legendary"]:
                conditions = legendary.get("conditions", {})
                req = conditions.get("requirement", "None")
                print(f"    - Species #{legendary['species_id']} (Requirement: {req})")
    print()


def test_world_integration():
    """Test world integration with encounter system."""
    print("\n=== World Integration Test ===\n")
    
    # Initialize pygame (required for World)
    pygame.init()
    
    # Create world and player
    world = World()
    player = Player("Test Trainer", 10, 10)
    
    # Give player a Pokemon
    starter = create_pokemon_from_species(25, level=10)  # Pikachu
    player.add_pokemon(starter)
    
    print(f"Player has {len(player.pokemon_team)} Pokemon")
    print(f"Lead Pokemon: {player.pokemon_team[0].species_name} Lv.{player.pokemon_team[0].level}")
    
    # Test wild encounter generation
    print("\nGenerating wild encounter:")
    wild_pokemon = world.get_wild_encounter()
    if wild_pokemon:
        print(f"Wild {wild_pokemon.species_name} appeared! (Lv.{wild_pokemon.level})")
        print(f"HP: {wild_pokemon.current_hp}/{wild_pokemon.stats['hp']}")
        print(f"Types: {[t.value for t in wild_pokemon.types]}")
        print(f"Moves: {[m.name for m in wild_pokemon.moves]}")
    else:
        print("No wild Pokemon in this area")
    
    # Test repel usage
    print("\nUsing Max Repel:")
    world.use_repel(250)
    info = world.get_encounter_info()
    print(f"Repel steps remaining: {info['repel_steps']}")
    print(f"Current area: {info['area']}")
    print(f"Chain species: {info['chain_species']}")
    print(f"Chain count: {info['chain_count']}")
    
    pygame.quit()


def _get_chain_shiny_multiplier(self, chain_count):
    """Helper to calculate shiny multiplier from chain."""
    if chain_count >= 40:
        return 3.0
    elif chain_count >= 30:
        return 2.5
    elif chain_count >= 20:
        return 2.0
    elif chain_count >= 10:
        return 1.5
    else:
        return 1.0


# Add helper method to EncounterSystem for testing
EncounterSystem._get_chain_shiny_multiplier = _get_chain_shiny_multiplier


if __name__ == "__main__":
    test_encounter_system()
    test_world_integration()
    print("\n=== All tests completed ===")