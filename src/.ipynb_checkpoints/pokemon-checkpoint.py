"""
Pokemon Class - Represents a Pokemon entity
"""

import random
from typing import Dict, List, Optional


class Pokemon:
    """Represents a Pokemon with stats, moves, and battle capabilities."""
    
    def __init__(self, name: str, pokemon_type: str, level: int = 5):
        self.name = name
        self.type = pokemon_type
        self.level = level
        
        # Base stats
        self.base_hp = 45
        self.base_attack = 49
        self.base_defense = 49
        self.base_speed = 45
        
        # Current stats
        self.max_hp = self.calculate_stat(self.base_hp)
        self.current_hp = self.max_hp
        self.attack = self.calculate_stat(self.base_attack)
        self.defense = self.calculate_stat(self.base_defense)
        self.speed = self.calculate_stat(self.base_speed)
        
        # Moves
        self.moves: List[Dict] = self.initialize_moves()
        
        # Status
        self.status: Optional[str] = None
        self.is_fainted = False
    
    def calculate_stat(self, base_stat: int) -> int:
        """Calculate actual stat based on level and base stat."""
        return int(((2 * base_stat * self.level) / 100) + self.level + 10)
    
    def initialize_moves(self) -> List[Dict]:
        """Initialize Pokemon moves based on type."""
        move_pool = {
            "normal": [
                {"name": "Tackle", "power": 40, "accuracy": 100, "pp": 35, "type": "normal"},
                {"name": "Quick Attack", "power": 40, "accuracy": 100, "pp": 30, "type": "normal"}
            ],
            "fire": [
                {"name": "Ember", "power": 40, "accuracy": 100, "pp": 25, "type": "fire"},
                {"name": "Fire Spin", "power": 35, "accuracy": 85, "pp": 15, "type": "fire"}
            ],
            "water": [
                {"name": "Water Gun", "power": 40, "accuracy": 100, "pp": 25, "type": "water"},
                {"name": "Bubble", "power": 40, "accuracy": 100, "pp": 30, "type": "water"}
            ],
            "grass": [
                {"name": "Vine Whip", "power": 45, "accuracy": 100, "pp": 25, "type": "grass"},
                {"name": "Razor Leaf", "power": 55, "accuracy": 95, "pp": 25, "type": "grass"}
            ]
        }
        
        # Get type-specific moves or default to normal
        moves = move_pool.get(self.type.lower(), move_pool["normal"])
        
        # Add a normal type move for variety
        moves.append({"name": "Tackle", "power": 40, "accuracy": 100, "pp": 35, "type": "normal"})
        
        return moves[:4]  # Pokemon can know up to 4 moves
    
    def take_damage(self, damage: int):
        """Apply damage to the Pokemon."""
        self.current_hp = max(0, self.current_hp - damage)
        if self.current_hp == 0:
            self.is_fainted = True
    
    def heal(self, amount: int):
        """Heal the Pokemon by specified amount."""
        if not self.is_fainted:
            self.current_hp = min(self.max_hp, self.current_hp + amount)
    
    def use_move(self, move_index: int) -> Dict:
        """Use a move and return move data."""
        if 0 <= move_index < len(self.moves):
            move = self.moves[move_index].copy()
            # Check if move hits based on accuracy
            if random.randint(1, 100) <= move["accuracy"]:
                return move
            else:
                return {"name": move["name"], "power": 0, "missed": True}
        return None
    
    def get_type_effectiveness(self, attacking_type: str, defending_type: str) -> float:
        """Calculate type effectiveness multiplier."""
        type_chart = {
            "fire": {"grass": 2.0, "water": 0.5, "fire": 0.5},
            "water": {"fire": 2.0, "grass": 0.5, "water": 0.5},
            "grass": {"water": 2.0, "fire": 0.5, "grass": 0.5},
            "normal": {}
        }
        
        effectiveness = type_chart.get(attacking_type, {}).get(defending_type, 1.0)
        return effectiveness
    
    def calculate_damage(self, move: Dict, defender: 'Pokemon') -> int:
        """Calculate damage dealt by a move."""
        if move.get("missed", False):
            return 0
        
        # Basic damage formula
        level_factor = (2 * self.level + 10) / 250
        attack_defense_ratio = self.attack / defender.defense
        base_damage = level_factor * move["power"] * attack_defense_ratio + 2
        
        # Type effectiveness
        effectiveness = self.get_type_effectiveness(move["type"], defender.type.lower())
        
        # Random factor (85-100%)
        random_factor = random.randint(85, 100) / 100
        
        # Calculate final damage
        damage = int(base_damage * effectiveness * random_factor)
        
        return max(1, damage)  # Minimum 1 damage
    
    def __str__(self):
        return f"{self.name} (Lv.{self.level} {self.type}) HP: {self.current_hp}/{self.max_hp}"