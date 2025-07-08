#!/usr/bin/env python3
"""
Battle System Demo - Showcases all features of the comprehensive battle system
"""

import sys
sys.path.append('.')

from src.pokemon import create_pokemon_from_species, StatusCondition, Nature
from src.battle import Battle, BattleType, BattleAction, Trainer
from src.player import Player
from src.items import get_item


def print_separator():
    print("\n" + "="*60 + "\n")


def print_pokemon_status(pokemon):
    """Print detailed Pokemon status."""
    print(f"{pokemon.nickname} (Lv.{pokemon.level} {'/'.join([t.value for t in pokemon.types])})")
    print(f"  HP: {pokemon.current_hp}/{pokemon.stats['hp']}")
    print(f"  Status: {pokemon.status.value}")
    print(f"  Nature: {pokemon.nature.nature_name}")
    print(f"  Ability: {pokemon.ability.name}")
    print(f"  Stats: ATK:{pokemon.stats['attack']} DEF:{pokemon.stats['defense']} "
          f"SPA:{pokemon.stats['sp_attack']} SPD:{pokemon.stats['sp_defense']} SPE:{pokemon.stats['speed']}")
    print(f"  Moves: {', '.join([f'{m.name} ({m.current_pp}/{m.pp} PP)' for m in pokemon.moves])}")


def demo_comprehensive_battle():
    """Demonstrate all features of the battle system."""
    
    print("=== COMPREHENSIVE POKEMON BATTLE SYSTEM DEMO ===")
    print_separator()
    
    # Create player with a full team
    player = Player("Champion Red")
    
    # Add diverse team with different types and moves
    team_data = [
        (25, "Pikachu", 50),     # Electric
        (4, "Charizard", 48),    # Fire
        (7, "Blastoise", 46),    # Water
        (1, "Venusaur", 44),     # Grass/Poison
        (143, "Snorlax", 42),    # Normal
        (94, "Gengar", 40),      # Ghost/Poison
    ]
    
    for species_id, nickname, level in team_data:
        pokemon = create_pokemon_from_species(species_id, level=level)
        pokemon.nickname = nickname
        player.add_pokemon(pokemon)
    
    # Give player items
    player.inventory = {
        "potion": 10,
        "super_potion": 5,
        "hyper_potion": 3,
        "max_potion": 1,
        "full_restore": 2,
        "revive": 3,
        "antidote": 5,
        "burn_heal": 5,
        "ice_heal": 5,
        "awakening": 5,
        "paralyze_heal": 5,
        "full_heal": 3,
        "pokeball": 20,
        "great_ball": 10,
        "ultra_ball": 5,
        "x_attack": 3,
        "x_defense": 3,
        "x_speed": 3,
    }
    
    # Create strong opponent trainer
    opponent_team = [
        create_pokemon_from_species(149, level=52),  # Dragonite
        create_pokemon_from_species(150, level=50),  # Mewtwo
        create_pokemon_from_species(144, level=48),  # Articuno
    ]
    
    elite_four = Trainer("Lance", opponent_team, "Elite Four", prize_money=5000, ai_level=4)
    
    print("PLAYER TEAM:")
    for i, pokemon in enumerate(player.pokemon_team):
        print(f"\n{i+1}. ", end="")
        print_pokemon_status(pokemon)
    
    print_separator()
    
    print("OPPONENT TEAM:")
    for i, pokemon in enumerate(elite_four.pokemon_team):
        print(f"\n{i+1}. ", end="")
        print_pokemon_status(pokemon)
    
    print_separator()
    
    # Start epic battle
    battle = Battle(player, elite_four, battle_type=BattleType.ELITE_FOUR, can_run=False)
    battle.start()
    
    print("BATTLE STARTED!")
    print("\nInitial battle log:")
    for log in battle.battle_log:
        print(f"  {log}")
    
    # Demonstrate various battle mechanics
    demonstrations = [
        ("1. PRIORITY MOVES", lambda: battle.set_player_action(BattleAction.FIGHT, move_index=2)),  # Quick Attack
        ("2. TYPE EFFECTIVENESS", lambda: battle.set_player_action(BattleAction.FIGHT, move_index=0)),  # Thunder Shock vs Dragon/Flying
        ("3. SWITCHING POKEMON", lambda: battle.set_player_action(BattleAction.POKEMON, switch_index=1)),  # Switch to Charizard
        ("4. STATUS MOVES", lambda: None),  # Will be done by finding appropriate move
        ("5. STAT MODIFICATIONS", lambda: None),  # Will be done by finding appropriate move
        ("6. ITEM USAGE", lambda: battle.set_player_action(BattleAction.BAG, item_id="x_attack", target_index=1)),
        ("7. HEALING ITEMS", lambda: None),  # Will be done when Pokemon is damaged
        ("8. CRITICAL HITS", lambda: battle.set_player_action(BattleAction.FIGHT, move_index=1)),  # High power move
        ("9. WEATHER EFFECTS", lambda: None),  # Will be done by finding weather move
        ("10. PP MANAGEMENT", lambda: None),  # Will show PP depletion
    ]
    
    turn = 0
    for demo_name, action in demonstrations[:3]:  # Run first 3 demos
        if battle.is_over:
            break
            
        turn += 1
        print_separator()
        print(f"TURN {turn} - DEMONSTRATING: {demo_name}")
        
        # Show current status
        status = battle.get_battle_status()
        print(f"\nPlayer's {status['player_pokemon']['name']} - "
              f"HP: {status['player_pokemon']['hp']}/{status['player_pokemon']['max_hp']} "
              f"Status: {status['player_pokemon']['status']}")
        print(f"Opponent's {status['opponent_pokemon']['name']} - "
              f"HP: {status['opponent_pokemon']['hp']}/{status['opponent_pokemon']['max_hp']} "
              f"Status: {status['opponent_pokemon']['status']}")
        
        # Execute action
        if action:
            action()
        
        # Show battle log for this turn
        print(f"\nBattle log for turn {turn}:")
        recent_logs = battle.battle_log[-15:]
        for log in recent_logs:
            print(f"  {log}")
    
    print_separator()
    print("BATTLE SUMMARY:")
    print(f"Total turns: {battle.turn}")
    print(f"Battle over: {battle.is_over}")
    print(f"Winner: {battle.winner}")
    
    if battle.weather:
        print(f"Current weather: {battle.weather}")
    
    print("\nFinal Pokemon status:")
    print(f"Player's active: {player.active_pokemon}")
    print(f"Opponent's active: {elite_four.active_pokemon}")


def demo_wild_encounter_with_catch():
    """Demonstrate wild Pokemon encounter and catching mechanics."""
    
    print_separator()
    print("=== WILD POKEMON ENCOUNTER DEMO ===")
    print_separator()
    
    # Create player
    player = Player("Pokemon Trainer")
    starter = create_pokemon_from_species(4, level=15)  # Charmander
    player.add_pokemon(starter)
    
    # Encounter rare Pokemon
    wild_mew = create_pokemon_from_species(151, level=50)
    
    print("A wild Mew appeared!")
    print_pokemon_status(wild_mew)
    
    # Start battle
    battle = Battle(player, wild_mew)
    battle.start()
    
    # Weaken the Pokemon first
    print("\n--- Weakening wild Pokemon ---")
    battle.set_player_action(BattleAction.FIGHT, move_index=0)
    
    # Try different Pokeballs
    pokeball_sequence = [
        ("pokeball", "Poke Ball"),
        ("great_ball", "Great Ball"),
        ("ultra_ball", "Ultra Ball"),
    ]
    
    for ball_id, ball_name in pokeball_sequence:
        if battle.is_over:
            break
            
        print(f"\n--- Attempting catch with {ball_name} ---")
        player.inventory[ball_id] = 5
        battle.set_player_action(BattleAction.BAG, item_id=ball_id)
        
        # Check last few logs
        for log in battle.battle_log[-5:]:
            if "shake" in log or "caught" in log or "broke free" in log:
                print(f"  {log}")


if __name__ == "__main__":
    # Run demonstrations
    demo_comprehensive_battle()
    demo_wild_encounter_with_catch()
    
    print_separator()
    print("=== DEMO COMPLETED ===")
    print("\nThe battle system includes:")
    print("- Turn-based combat with priority system")
    print("- Damage calculation using official formula")
    print("- Status condition effects each turn")
    print("- PP (Power Points) management")
    print("- Type effectiveness announcements")
    print("- Critical hit detection")
    print("- Accuracy and evasion checks")
    print("- Experience gain and leveling up")
    print("- Pokemon switching during battle")
    print("- Item usage (Potions, Status healers, Pokeballs)")
    print("- Wild encounters and Trainer battles")
    print("- AI opponent with difficulty levels")
    print("- Weather effects")
    print("- Stat stage modifications")
    print("- Move effects and secondary effects")
    print("- Catch rate calculations")
    print("- Prize money for winning battles")