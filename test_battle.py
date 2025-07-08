#!/usr/bin/env python3
"""
Test script for the comprehensive battle system
"""

import sys
sys.path.append('.')

from src.pokemon import create_pokemon_from_species, StatusCondition
from src.battle import Battle, BattleType, BattleAction, Trainer
from src.player import Player
from src.items import get_item


def test_wild_battle():
    """Test a wild Pokemon battle."""
    print("=== WILD POKEMON BATTLE TEST ===\n")
    
    # Create player with a team
    player = Player("Ash")
    pikachu = create_pokemon_from_species(25, level=20)
    pikachu.nickname = "Sparky"
    player.add_pokemon(pikachu)
    
    # Create wild Pokemon
    wild_bulbasaur = create_pokemon_from_species(1, level=15)
    
    # Start battle
    battle = Battle(player, wild_bulbasaur)
    battle.start()
    
    # Print initial status
    print("Initial battle log:")
    for log in battle.battle_log:
        print(f"  {log}")
    
    # Simulate a few turns
    print("\n--- Turn 1: Use Thunder Shock ---")
    battle.set_player_action(BattleAction.FIGHT, move_index=0)
    
    print("\nBattle log after turn 1:")
    for log in battle.battle_log[-10:]:
        print(f"  {log}")
    
    # Try to catch
    print("\n--- Turn 2: Throw Pokeball ---")
    battle.set_player_action(BattleAction.BAG, item_id="pokeball")
    
    print("\nBattle log after catch attempt:")
    for log in battle.battle_log[-10:]:
        print(f"  {log}")
    
    print(f"\nBattle over: {battle.is_over}")
    print(f"Winner: {battle.winner}")


def test_trainer_battle():
    """Test a trainer battle."""
    print("\n\n=== TRAINER BATTLE TEST ===\n")
    
    # Create player team
    player = Player("Red")
    charmander = create_pokemon_from_species(4, level=25)
    squirtle = create_pokemon_from_species(7, level=23)
    player.add_pokemon(charmander)
    player.add_pokemon(squirtle)
    
    # Create opponent trainer
    opponent_team = [
        create_pokemon_from_species(25, level=22),  # Pikachu
        create_pokemon_from_species(133, level=20)  # Eevee
    ]
    trainer = Trainer("Gary", opponent_team, "Rival", prize_money=500, ai_level=3)
    
    # Start battle
    battle = Battle(player, trainer, battle_type=BattleType.TRAINER)
    battle.start()
    
    print("Initial battle log:")
    for log in battle.battle_log:
        print(f"  {log}")
    
    # Simulate turns
    print("\n--- Turn 1: Charmander uses Ember ---")
    battle.set_player_action(BattleAction.FIGHT, move_index=2)  # Ember
    
    print("\nBattle log after turn 1:")
    for log in battle.battle_log[-15:]:
        print(f"  {log}")
    
    # Switch Pokemon
    print("\n--- Turn 2: Switch to Squirtle ---")
    battle.set_player_action(BattleAction.POKEMON, switch_index=1)
    
    print("\nBattle log after switch:")
    for log in battle.battle_log[-10:]:
        print(f"  {log}")
    
    # Continue battle
    print("\n--- Turn 3: Squirtle uses Water Gun ---")
    battle.set_player_action(BattleAction.FIGHT, move_index=2)  # Water Gun
    
    print("\nBattle log after turn 3:")
    for log in battle.battle_log[-15:]:
        print(f"  {log}")


def test_status_effects():
    """Test status conditions and effects."""
    print("\n\n=== STATUS EFFECTS TEST ===\n")
    
    # Create Pokemon
    player = Player("Test")
    pokemon1 = create_pokemon_from_species(4, level=30)
    player.add_pokemon(pokemon1)
    
    pokemon2 = create_pokemon_from_species(7, level=30)
    
    # Start battle
    battle = Battle(player, pokemon2)
    battle.start()
    
    # Find a move that causes status
    status_moves = [(i, m) for i, m in enumerate(pokemon1.moves) if m.effect in ["burn", "paralysis"]]
    if status_moves:
        move_index, move = status_moves[0]
        print(f"Using {move.name} which can cause {move.effect}")
        battle.set_player_action(BattleAction.FIGHT, move_index=move_index)
        
        print("\nBattle log:")
        for log in battle.battle_log[-10:]:
            print(f"  {log}")


def test_items():
    """Test item usage in battle."""
    print("\n\n=== ITEM USAGE TEST ===\n")
    
    # Create player with items
    player = Player("Trainer")
    pokemon = create_pokemon_from_species(25, level=25)
    player.add_pokemon(pokemon)
    
    # Give player more items
    player.inventory["potion"] = 5
    player.inventory["super_potion"] = 3
    player.inventory["paralyze_heal"] = 2
    
    # Damage the Pokemon
    pokemon.take_damage(30)
    
    # Create opponent
    opponent = create_pokemon_from_species(1, level=20)
    
    # Start battle
    battle = Battle(player, opponent)
    battle.start()
    
    print(f"Pikachu HP: {pokemon.current_hp}/{pokemon.stats['hp']}")
    
    # Use potion
    print("\n--- Using Potion ---")
    battle.set_player_action(BattleAction.BAG, item_id="potion", target_index=0)
    
    print("\nBattle log after using potion:")
    for log in battle.battle_log[-10:]:
        print(f"  {log}")
    
    print(f"Pikachu HP after potion: {pokemon.current_hp}/{pokemon.stats['hp']}")


def test_experience_and_leveling():
    """Test experience gain and leveling."""
    print("\n\n=== EXPERIENCE AND LEVELING TEST ===\n")
    
    # Create low level Pokemon
    player = Player("Youngster")
    caterpie = create_pokemon_from_species(25, level=5)  # Low level Pikachu
    player.add_pokemon(caterpie)
    
    print(f"Starting: {caterpie} - Exp: {caterpie.current_exp}")
    print(f"Moves: {[m.name for m in caterpie.moves]}")
    
    # Battle a higher level Pokemon
    opponent = create_pokemon_from_species(143, level=20)  # Snorlax
    opponent.current_hp = 10  # Make it easy to defeat
    
    battle = Battle(player, opponent)
    battle.start()
    
    # Defeat opponent
    print("\n--- Defeating opponent for experience ---")
    battle.set_player_action(BattleAction.FIGHT, move_index=0)
    
    print("\nBattle log with experience gain:")
    for log in battle.battle_log[-15:]:
        print(f"  {log}")
    
    print(f"\nAfter battle: {caterpie} - Exp: {caterpie.current_exp}")
    print(f"Moves: {[m.name for m in caterpie.moves]}")


if __name__ == "__main__":
    # Run all tests
    test_wild_battle()
    test_trainer_battle()
    test_status_effects()
    test_items()
    test_experience_and_leveling()
    
    print("\n\n=== ALL TESTS COMPLETED ===")