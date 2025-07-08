"""
Battle System - Handles Pokemon battles
"""

import random
from typing import Optional, Tuple
from .pokemon import Pokemon


class Battle:
    """Manages turn-based Pokemon battles."""
    
    def __init__(self, player_pokemon: Pokemon, opponent_pokemon: Pokemon):
        self.player_pokemon = player_pokemon
        self.opponent_pokemon = opponent_pokemon
        self.turn = 0
        self.battle_log = []
        self.is_over = False
        self.winner = None
    
    def start(self):
        """Initialize the battle."""
        self.add_to_log(f"Battle started!")
        self.add_to_log(f"{self.player_pokemon.name} vs {self.opponent_pokemon.name}")
        self.add_to_log("")
    
    def add_to_log(self, message: str):
        """Add message to battle log."""
        self.battle_log.append(message)
    
    def player_turn(self, move_index: int) -> bool:
        """Execute player's turn."""
        if self.is_over:
            return False
        
        move = self.player_pokemon.use_move(move_index)
        if not move:
            self.add_to_log("Invalid move!")
            return False
        
        self.execute_move(self.player_pokemon, self.opponent_pokemon, move)
        
        # Check if opponent fainted
        if self.opponent_pokemon.is_fainted:
            self.end_battle(self.player_pokemon)
            return True
        
        # Opponent's turn
        self.opponent_turn()
        
        # Check if player fainted
        if self.player_pokemon.is_fainted:
            self.end_battle(self.opponent_pokemon)
        
        self.turn += 1
        return True
    
    def opponent_turn(self):
        """Execute opponent's turn (AI)."""
        # Simple AI: Choose random move
        move_index = random.randint(0, len(self.opponent_pokemon.moves) - 1)
        move = self.opponent_pokemon.use_move(move_index)
        
        if move:
            self.execute_move(self.opponent_pokemon, self.player_pokemon, move)
    
    def execute_move(self, attacker: Pokemon, defender: Pokemon, move: dict):
        """Execute a move and apply effects."""
        self.add_to_log(f"{attacker.name} used {move['name']}!")
        
        if move.get("missed", False):
            self.add_to_log("But it missed!")
        else:
            damage = attacker.calculate_damage(move, defender)
            defender.take_damage(damage)
            
            # Check type effectiveness
            effectiveness = attacker.get_type_effectiveness(move["type"], defender.type.lower())
            if effectiveness > 1:
                self.add_to_log("It's super effective!")
            elif effectiveness < 1:
                self.add_to_log("It's not very effective...")
            
            self.add_to_log(f"{defender.name} took {damage} damage!")
            self.add_to_log(f"{defender.name} HP: {defender.current_hp}/{defender.max_hp}")
        
        self.add_to_log("")
    
    def end_battle(self, winner: Pokemon):
        """End the battle and declare winner."""
        self.is_over = True
        self.winner = winner
        loser = self.opponent_pokemon if winner == self.player_pokemon else self.player_pokemon
        
        self.add_to_log(f"{loser.name} fainted!")
        self.add_to_log(f"{winner.name} wins!")
        
        # Award experience (simplified)
        if winner == self.player_pokemon:
            exp_gained = self.opponent_pokemon.level * 50
            self.add_to_log(f"{self.player_pokemon.name} gained {exp_gained} EXP!")
    
    def get_battle_status(self) -> dict:
        """Get current battle status."""
        return {
            "player_hp": self.player_pokemon.current_hp,
            "player_max_hp": self.player_pokemon.max_hp,
            "opponent_hp": self.opponent_pokemon.current_hp,
            "opponent_max_hp": self.opponent_pokemon.max_hp,
            "turn": self.turn,
            "is_over": self.is_over,
            "winner": self.winner.name if self.winner else None
        }
    
    def run_away(self) -> bool:
        """Attempt to run from battle."""
        # Simple run calculation based on speed
        escape_chance = (self.player_pokemon.speed * 32) / self.opponent_pokemon.speed + 30
        
        if random.randint(1, 100) <= escape_chance:
            self.add_to_log("Got away safely!")
            self.is_over = True
            return True
        else:
            self.add_to_log("Can't escape!")
            self.opponent_turn()
            return False