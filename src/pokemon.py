"""
Pokemon Class - Comprehensive Pokemon entity with stats, IVs, EVs, natures, abilities, etc.
"""

import random
import math
from typing import Dict, List, Optional, Tuple
from enum import Enum


class StatusCondition(Enum):
    """Status conditions that can affect Pokemon."""
    NONE = "none"
    PARALYZED = "paralyzed"
    BURNED = "burned"
    POISONED = "poisoned"
    BADLY_POISONED = "badly_poisoned"
    FROZEN = "frozen"
    ASLEEP = "asleep"
    CONFUSED = "confused"
    FLINCHED = "flinched"


class PokemonType(Enum):
    """All Pokemon types."""
    NORMAL = "normal"
    FIRE = "fire"
    WATER = "water"
    ELECTRIC = "electric"
    GRASS = "grass"
    ICE = "ice"
    FIGHTING = "fighting"
    POISON = "poison"
    GROUND = "ground"
    FLYING = "flying"
    PSYCHIC = "psychic"
    BUG = "bug"
    ROCK = "rock"
    GHOST = "ghost"
    DRAGON = "dragon"
    DARK = "dark"
    STEEL = "steel"
    FAIRY = "fairy"


class Nature(Enum):
    """Pokemon natures that affect stats."""
    HARDY = ("hardy", None, None)  # Neutral
    LONELY = ("lonely", "attack", "defense")
    BRAVE = ("brave", "attack", "speed")
    ADAMANT = ("adamant", "attack", "sp_attack")
    NAUGHTY = ("naughty", "attack", "sp_defense")
    BOLD = ("bold", "defense", "attack")
    DOCILE = ("docile", None, None)  # Neutral
    RELAXED = ("relaxed", "defense", "speed")
    IMPISH = ("impish", "defense", "sp_attack")
    LAX = ("lax", "defense", "sp_defense")
    TIMID = ("timid", "speed", "attack")
    HASTY = ("hasty", "speed", "defense")
    SERIOUS = ("serious", None, None)  # Neutral
    JOLLY = ("jolly", "speed", "sp_attack")
    NAIVE = ("naive", "speed", "sp_defense")
    MODEST = ("modest", "sp_attack", "attack")
    MILD = ("mild", "sp_attack", "defense")
    QUIET = ("quiet", "sp_attack", "speed")
    BASHFUL = ("bashful", None, None)  # Neutral
    RASH = ("rash", "sp_attack", "sp_defense")
    CALM = ("calm", "sp_defense", "attack")
    GENTLE = ("gentle", "sp_defense", "defense")
    SASSY = ("sassy", "sp_defense", "speed")
    CAREFUL = ("careful", "sp_defense", "sp_attack")
    QUIRKY = ("quirky", None, None)  # Neutral
    
    def __init__(self, name: str, increased_stat: Optional[str], decreased_stat: Optional[str]):
        self.nature_name = name
        self.increased_stat = increased_stat
        self.decreased_stat = decreased_stat


# Type effectiveness chart
TYPE_EFFECTIVENESS = {
    PokemonType.NORMAL: {
        PokemonType.ROCK: 0.5,
        PokemonType.GHOST: 0.0,
        PokemonType.STEEL: 0.5
    },
    PokemonType.FIRE: {
        PokemonType.FIRE: 0.5,
        PokemonType.WATER: 0.5,
        PokemonType.GRASS: 2.0,
        PokemonType.ICE: 2.0,
        PokemonType.BUG: 2.0,
        PokemonType.ROCK: 0.5,
        PokemonType.DRAGON: 0.5,
        PokemonType.STEEL: 2.0
    },
    PokemonType.WATER: {
        PokemonType.FIRE: 2.0,
        PokemonType.WATER: 0.5,
        PokemonType.GRASS: 0.5,
        PokemonType.GROUND: 2.0,
        PokemonType.ROCK: 2.0,
        PokemonType.DRAGON: 0.5
    },
    PokemonType.ELECTRIC: {
        PokemonType.WATER: 2.0,
        PokemonType.ELECTRIC: 0.5,
        PokemonType.GRASS: 0.5,
        PokemonType.GROUND: 0.0,
        PokemonType.FLYING: 2.0,
        PokemonType.DRAGON: 0.5
    },
    PokemonType.GRASS: {
        PokemonType.FIRE: 0.5,
        PokemonType.WATER: 2.0,
        PokemonType.GRASS: 0.5,
        PokemonType.POISON: 0.5,
        PokemonType.GROUND: 2.0,
        PokemonType.FLYING: 0.5,
        PokemonType.BUG: 0.5,
        PokemonType.ROCK: 2.0,
        PokemonType.DRAGON: 0.5,
        PokemonType.STEEL: 0.5
    },
    PokemonType.ICE: {
        PokemonType.FIRE: 0.5,
        PokemonType.WATER: 0.5,
        PokemonType.GRASS: 2.0,
        PokemonType.ICE: 0.5,
        PokemonType.GROUND: 2.0,
        PokemonType.FLYING: 2.0,
        PokemonType.DRAGON: 2.0,
        PokemonType.STEEL: 0.5
    },
    PokemonType.FIGHTING: {
        PokemonType.NORMAL: 2.0,
        PokemonType.ICE: 2.0,
        PokemonType.POISON: 0.5,
        PokemonType.FLYING: 0.5,
        PokemonType.PSYCHIC: 0.5,
        PokemonType.BUG: 0.5,
        PokemonType.ROCK: 2.0,
        PokemonType.GHOST: 0.0,
        PokemonType.DARK: 2.0,
        PokemonType.STEEL: 2.0,
        PokemonType.FAIRY: 0.5
    },
    PokemonType.POISON: {
        PokemonType.GRASS: 2.0,
        PokemonType.POISON: 0.5,
        PokemonType.GROUND: 0.5,
        PokemonType.ROCK: 0.5,
        PokemonType.GHOST: 0.5,
        PokemonType.STEEL: 0.0,
        PokemonType.FAIRY: 2.0
    },
    PokemonType.GROUND: {
        PokemonType.FIRE: 2.0,
        PokemonType.ELECTRIC: 2.0,
        PokemonType.GRASS: 0.5,
        PokemonType.POISON: 2.0,
        PokemonType.FLYING: 0.0,
        PokemonType.BUG: 0.5,
        PokemonType.ROCK: 2.0,
        PokemonType.STEEL: 2.0
    },
    PokemonType.FLYING: {
        PokemonType.ELECTRIC: 0.5,
        PokemonType.GRASS: 2.0,
        PokemonType.FIGHTING: 2.0,
        PokemonType.BUG: 2.0,
        PokemonType.ROCK: 0.5,
        PokemonType.STEEL: 0.5
    },
    PokemonType.PSYCHIC: {
        PokemonType.FIGHTING: 2.0,
        PokemonType.POISON: 2.0,
        PokemonType.PSYCHIC: 0.5,
        PokemonType.DARK: 0.0,
        PokemonType.STEEL: 0.5
    },
    PokemonType.BUG: {
        PokemonType.FIRE: 0.5,
        PokemonType.GRASS: 2.0,
        PokemonType.FIGHTING: 0.5,
        PokemonType.POISON: 0.5,
        PokemonType.FLYING: 0.5,
        PokemonType.PSYCHIC: 2.0,
        PokemonType.GHOST: 0.5,
        PokemonType.DARK: 2.0,
        PokemonType.STEEL: 0.5,
        PokemonType.FAIRY: 0.5
    },
    PokemonType.ROCK: {
        PokemonType.FIRE: 2.0,
        PokemonType.ICE: 2.0,
        PokemonType.FIGHTING: 0.5,
        PokemonType.GROUND: 0.5,
        PokemonType.FLYING: 2.0,
        PokemonType.BUG: 2.0,
        PokemonType.STEEL: 0.5
    },
    PokemonType.GHOST: {
        PokemonType.NORMAL: 0.0,
        PokemonType.PSYCHIC: 2.0,
        PokemonType.GHOST: 2.0,
        PokemonType.DARK: 0.5
    },
    PokemonType.DRAGON: {
        PokemonType.DRAGON: 2.0,
        PokemonType.STEEL: 0.5,
        PokemonType.FAIRY: 0.0
    },
    PokemonType.DARK: {
        PokemonType.FIGHTING: 0.5,
        PokemonType.PSYCHIC: 2.0,
        PokemonType.GHOST: 2.0,
        PokemonType.DARK: 0.5,
        PokemonType.FAIRY: 0.5
    },
    PokemonType.STEEL: {
        PokemonType.FIRE: 0.5,
        PokemonType.WATER: 0.5,
        PokemonType.ELECTRIC: 0.5,
        PokemonType.ICE: 2.0,
        PokemonType.ROCK: 2.0,
        PokemonType.STEEL: 0.5,
        PokemonType.FAIRY: 2.0
    },
    PokemonType.FAIRY: {
        PokemonType.FIRE: 0.5,
        PokemonType.FIGHTING: 2.0,
        PokemonType.POISON: 0.5,
        PokemonType.DRAGON: 2.0,
        PokemonType.DARK: 2.0,
        PokemonType.STEEL: 0.5
    }
}


class Move:
    """Represents a Pokemon move."""
    def __init__(self, name: str, move_type: PokemonType, category: str, power: int, 
                 accuracy: int, pp: int, priority: int = 0, effect: Optional[str] = None,
                 effect_chance: int = 0):
        self.name = name
        self.type = move_type
        self.category = category  # "physical", "special", or "status"
        self.power = power
        self.accuracy = accuracy
        self.pp = pp
        self.current_pp = pp
        self.priority = priority
        self.effect = effect
        self.effect_chance = effect_chance
    
    def use(self) -> bool:
        """Use the move, decreasing PP."""
        if self.current_pp > 0:
            self.current_pp -= 1
            return True
        return False
    
    def restore_pp(self, amount: int = None):
        """Restore PP to the move."""
        if amount is None:
            self.current_pp = self.pp
        else:
            self.current_pp = min(self.pp, self.current_pp + amount)


class Ability:
    """Represents a Pokemon ability."""
    def __init__(self, name: str, description: str, effect_type: str = None):
        self.name = name
        self.description = description
        self.effect_type = effect_type  # e.g., "stat_boost", "weather", "damage_reduction"


class Pokemon:
    """Comprehensive Pokemon class with full stat system, IVs, EVs, natures, etc."""
    
    def __init__(self, species_data: Dict, level: int = 5, 
                 ivs: Optional[Dict[str, int]] = None,
                 evs: Optional[Dict[str, int]] = None,
                 nature: Optional[Nature] = None,
                 ability: Optional[Ability] = None):
        # Basic info
        self.species_name = species_data["name"]
        self.nickname = species_data["name"]
        self.species_id = species_data["id"]
        self.types = [PokemonType(t) for t in species_data["types"]]
        self.level = level
        
        # Base stats
        self.base_stats = species_data["base_stats"]
        
        # Individual Values (0-31)
        self.ivs = ivs or {
            "hp": random.randint(0, 31),
            "attack": random.randint(0, 31),
            "defense": random.randint(0, 31),
            "sp_attack": random.randint(0, 31),
            "sp_defense": random.randint(0, 31),
            "speed": random.randint(0, 31)
        }
        
        # Effort Values (0-252 per stat, max 510 total)
        self.evs = evs or {
            "hp": 0,
            "attack": 0,
            "defense": 0,
            "sp_attack": 0,
            "sp_defense": 0,
            "speed": 0
        }
        
        # Nature
        self.nature = nature or random.choice(list(Nature))
        
        # Ability
        available_abilities = [Ability(**a) for a in species_data["abilities"]]
        self.ability = ability or random.choice(available_abilities)
        
        # Calculate actual stats
        self.stats = self._calculate_stats()
        self.current_hp = self.stats["hp"]
        
        # Moves
        self.moves: List[Move] = []
        self.learnset = species_data["learnset"]
        self._learn_moves_up_to_level()
        
        # Status
        self.status = StatusCondition.NONE
        self.status_counter = 0  # For sleep turns, badly poisoned damage, etc.
        self.is_fainted = False
        self.confusion_turns = 0
        
        # Special properties
        self.is_shiny = False  # Shiny Pokemon have different coloration
        
        # Experience
        self.experience_group = species_data.get("experience_group", "medium_fast")
        self.current_exp = self._calculate_exp_for_level(level)
        self.exp_to_next_level = self._calculate_exp_for_level(level + 1) - self.current_exp
        
        # Battle stats modifiers (for stat stages in battle)
        self.stat_stages = {
            "attack": 0,
            "defense": 0,
            "sp_attack": 0,
            "sp_defense": 0,
            "speed": 0,
            "accuracy": 0,
            "evasion": 0
        }
    
    def _calculate_stats(self) -> Dict[str, int]:
        """Calculate actual stats based on base stats, level, IVs, EVs, and nature."""
        stats = {}
        
        # HP calculation is different
        stats["hp"] = self._calculate_hp()
        
        # Other stats
        for stat in ["attack", "defense", "sp_attack", "sp_defense", "speed"]:
            base = self.base_stats[stat]
            iv = self.ivs[stat]
            ev = self.evs[stat]
            
            # Standard stat formula
            stat_value = math.floor(((2 * base + iv + math.floor(ev / 4)) * self.level / 100 + 5))
            
            # Apply nature modifier
            if self.nature.increased_stat == stat:
                stat_value = math.floor(stat_value * 1.1)
            elif self.nature.decreased_stat == stat:
                stat_value = math.floor(stat_value * 0.9)
            
            stats[stat] = stat_value
        
        return stats
    
    def _calculate_hp(self) -> int:
        """Calculate HP stat (different formula than other stats)."""
        base = self.base_stats["hp"]
        iv = self.ivs["hp"]
        ev = self.evs["hp"]
        
        return math.floor(((2 * base + iv + math.floor(ev / 4)) * self.level / 100) + self.level + 10)
    
    def _calculate_exp_for_level(self, level: int) -> int:
        """Calculate total experience needed for a given level."""
        if level <= 1:
            return 0
        
        # Different experience groups have different formulas
        if self.experience_group == "fast":
            return int(0.8 * (level ** 3))
        elif self.experience_group == "medium_fast":
            return level ** 3
        elif self.experience_group == "medium_slow":
            return int(1.2 * (level ** 3) - 15 * (level ** 2) + 100 * level - 140)
        elif self.experience_group == "slow":
            return int(1.25 * (level ** 3))
        else:  # Default to medium fast
            return level ** 3
    
    def _learn_moves_up_to_level(self):
        """Learn moves based on current level."""
        # Sort learnset by level
        sorted_moves = sorted(self.learnset, key=lambda x: x["level"])
        
        # Learn up to 4 most recent moves
        learned_moves = []
        for move_data in sorted_moves:
            if move_data["level"] <= self.level:
                move = Move(
                    name=move_data["name"],
                    move_type=PokemonType(move_data["type"]),
                    category=move_data["category"],
                    power=move_data["power"],
                    accuracy=move_data["accuracy"],
                    pp=move_data["pp"],
                    priority=move_data.get("priority", 0),
                    effect=move_data.get("effect"),
                    effect_chance=move_data.get("effect_chance", 0)
                )
                learned_moves.append(move)
        
        # Keep only the last 4 moves
        self.moves = learned_moves[-4:] if len(learned_moves) > 4 else learned_moves
    
    def gain_exp(self, amount: int) -> List[str]:
        """Gain experience and potentially level up. Returns list of events."""
        events = []
        self.current_exp += amount
        events.append(f"{self.nickname} gained {amount} Exp. Points!")
        
        # Check for level up
        while self.current_exp >= self._calculate_exp_for_level(self.level + 1) and self.level < 100:
            self.level += 1
            events.append(f"{self.nickname} grew to level {self.level}!")
            
            # Recalculate stats
            old_stats = self.stats.copy()
            self.stats = self._calculate_stats()
            
            # Heal HP difference from level up
            hp_gain = self.stats["hp"] - old_stats["hp"]
            self.current_hp += hp_gain
            
            # Check for new moves
            for move_data in self.learnset:
                if move_data["level"] == self.level:
                    events.append(f"{self.nickname} is trying to learn {move_data['name']}!")
                    # In a real game, this would prompt the player
                    # For now, auto-learn if less than 4 moves
                    if len(self.moves) < 4:
                        new_move = Move(
                            name=move_data["name"],
                            move_type=PokemonType(move_data["type"]),
                            category=move_data["category"],
                            power=move_data["power"],
                            accuracy=move_data["accuracy"],
                            pp=move_data["pp"],
                            priority=move_data.get("priority", 0),
                            effect=move_data.get("effect"),
                            effect_chance=move_data.get("effect_chance", 0)
                        )
                        self.moves.append(new_move)
                        events.append(f"{self.nickname} learned {move_data['name']}!")
        
        # Update exp to next level
        if self.level < 100:
            current_level_exp = self._calculate_exp_for_level(self.level)
            next_level_exp = self._calculate_exp_for_level(self.level + 1)
            self.exp_to_next_level = next_level_exp - self.current_exp
        else:
            self.exp_to_next_level = 0
        
        return events
    
    def take_damage(self, damage: int) -> List[str]:
        """Apply damage and check for fainting."""
        events = []
        self.current_hp = max(0, self.current_hp - damage)
        
        if self.current_hp == 0 and not self.is_fainted:
            self.is_fainted = True
            self.status = StatusCondition.NONE  # Clear status on faint
            events.append(f"{self.nickname} fainted!")
        
        return events
    
    def heal(self, amount: int) -> bool:
        """Heal HP. Returns True if healing was effective."""
        if self.is_fainted or self.current_hp >= self.stats["hp"]:
            return False
        
        self.current_hp = min(self.stats["hp"], self.current_hp + amount)
        return True
    
    def cure_status(self) -> bool:
        """Cure status condition. Returns True if status was cured."""
        if self.status != StatusCondition.NONE:
            self.status = StatusCondition.NONE
            self.status_counter = 0
            return True
        return False
    
    def apply_status(self, status: StatusCondition) -> bool:
        """Apply a status condition. Returns True if successful."""
        # Can't apply status to fainted Pokemon
        if self.is_fainted:
            return False
        
        # Can't apply status if already has one (except confusion which stacks)
        if self.status != StatusCondition.NONE and status != StatusCondition.CONFUSED:
            return False
        
        # Some types are immune to certain statuses
        if status == StatusCondition.BURNED and PokemonType.FIRE in self.types:
            return False
        if status == StatusCondition.FROZEN and PokemonType.ICE in self.types:
            return False
        if status in [StatusCondition.POISONED, StatusCondition.BADLY_POISONED] and \
           (PokemonType.POISON in self.types or PokemonType.STEEL in self.types):
            return False
        if status == StatusCondition.PARALYZED and PokemonType.ELECTRIC in self.types:
            return False
        
        self.status = status
        
        # Set initial counters
        if status == StatusCondition.ASLEEP:
            self.status_counter = random.randint(1, 3)  # 1-3 turns
        elif status == StatusCondition.BADLY_POISONED:
            self.status_counter = 1  # Damage multiplier
        elif status == StatusCondition.CONFUSED:
            self.confusion_turns = random.randint(1, 4)  # 1-4 turns
        
        return True
    
    def process_status(self) -> Tuple[bool, List[str]]:
        """Process status effects at end of turn. Returns (can_move, events)."""
        events = []
        can_move = True
        
        if self.status == StatusCondition.ASLEEP:
            self.status_counter -= 1
            if self.status_counter <= 0:
                self.status = StatusCondition.NONE
                events.append(f"{self.nickname} woke up!")
            else:
                events.append(f"{self.nickname} is fast asleep!")
                can_move = False
        
        elif self.status == StatusCondition.PARALYZED:
            if random.random() < 0.25:  # 25% chance to not move
                events.append(f"{self.nickname} is paralyzed! It can't move!")
                can_move = False
        
        elif self.status == StatusCondition.FROZEN:
            if random.random() < 0.2:  # 20% chance to thaw
                self.status = StatusCondition.NONE
                events.append(f"{self.nickname} thawed out!")
            else:
                events.append(f"{self.nickname} is frozen solid!")
                can_move = False
        
        # Confusion is separate from main status
        if self.confusion_turns > 0:
            self.confusion_turns -= 1
            if self.confusion_turns == 0:
                events.append(f"{self.nickname} snapped out of confusion!")
            else:
                events.append(f"{self.nickname} is confused!")
                if random.random() < 0.33:  # 33% chance to hurt itself
                    # Confusion damage calculation
                    damage = self.calculate_confusion_damage()
                    self.take_damage(damage)
                    events.append(f"{self.nickname} hurt itself in confusion!")
                    can_move = False
        
        return can_move, events
    
    def apply_end_turn_damage(self) -> List[str]:
        """Apply damage from burn/poison at end of turn."""
        events = []
        
        if self.status == StatusCondition.BURNED:
            damage = max(1, self.stats["hp"] // 16)
            self.take_damage(damage)
            events.append(f"{self.nickname} is hurt by its burn!")
        
        elif self.status == StatusCondition.POISONED:
            damage = max(1, self.stats["hp"] // 8)
            self.take_damage(damage)
            events.append(f"{self.nickname} is hurt by poison!")
        
        elif self.status == StatusCondition.BADLY_POISONED:
            damage = max(1, (self.stats["hp"] // 16) * self.status_counter)
            self.take_damage(damage)
            events.append(f"{self.nickname} is hurt by poison!")
            self.status_counter = min(15, self.status_counter + 1)  # Cap at 15
        
        return events
    
    def calculate_confusion_damage(self) -> int:
        """Calculate self-inflicted confusion damage."""
        # Use a base 40 power physical "move" against self
        level_factor = (2 * self.level + 10) / 250
        attack = self.get_modified_stat("attack")
        defense = self.get_modified_stat("defense")
        base_damage = level_factor * 40 * (attack / defense) + 2
        return max(1, int(base_damage))
    
    def get_modified_stat(self, stat: str) -> int:
        """Get stat with battle modifiers applied."""
        if stat == "hp":
            return self.stats["hp"]  # HP doesn't have stages
        
        base_value = self.stats[stat]
        stage = self.stat_stages.get(stat, 0)
        
        # Stat stage multipliers
        if stage >= 0:
            multiplier = (2 + stage) / 2
        else:
            multiplier = 2 / (2 - stage)
        
        modified = int(base_value * multiplier)
        
        # Apply status effects
        if stat == "attack" and self.status == StatusCondition.BURNED:
            modified = int(modified * 0.5)
        elif stat == "speed" and self.status == StatusCondition.PARALYZED:
            modified = int(modified * 0.25)
        
        return modified
    
    def modify_stat_stage(self, stat: str, stages: int) -> Tuple[bool, str]:
        """Modify a stat stage. Returns (success, message)."""
        current = self.stat_stages[stat]
        new_stage = max(-6, min(6, current + stages))
        
        if new_stage == current:
            if stages > 0:
                return False, f"{self.nickname}'s {stat} won't go any higher!"
            else:
                return False, f"{self.nickname}'s {stat} won't go any lower!"
        
        self.stat_stages[stat] = new_stage
        change = new_stage - current
        
        if change == 1:
            return True, f"{self.nickname}'s {stat} rose!"
        elif change == 2:
            return True, f"{self.nickname}'s {stat} rose sharply!"
        elif change >= 3:
            return True, f"{self.nickname}'s {stat} rose drastically!"
        elif change == -1:
            return True, f"{self.nickname}'s {stat} fell!"
        elif change == -2:
            return True, f"{self.nickname}'s {stat} fell harshly!"
        else:  # -3 or lower
            return True, f"{self.nickname}'s {stat} fell severely!"
    
    def reset_stat_stages(self):
        """Reset all stat stages to 0."""
        for stat in self.stat_stages:
            self.stat_stages[stat] = 0
    
    def calculate_damage(self, move: Move, defender: 'Pokemon', 
                        critical: bool = False) -> Tuple[int, float, List[str]]:
        """Calculate damage dealt by a move. Returns (damage, effectiveness, events)."""
        events = []
        
        # Check if move missed
        accuracy = move.accuracy
        if self.stat_stages["accuracy"] != 0:
            accuracy = accuracy * self.get_accuracy_multiplier()
        if defender.stat_stages["evasion"] != 0:
            accuracy = accuracy * defender.get_evasion_multiplier()
        
        if random.randint(1, 100) > accuracy:
            return 0, 1.0, [f"{self.nickname}'s attack missed!"]
        
        # Status moves don't deal damage
        if move.category == "status":
            return 0, 1.0, events
        
        # Get attacking and defending stats
        if move.category == "physical":
            attack_stat = self.get_modified_stat("attack")
            defense_stat = defender.get_modified_stat("defense")
        else:  # special
            attack_stat = self.get_modified_stat("sp_attack")
            defense_stat = defender.get_modified_stat("sp_defense")
        
        # Basic damage formula
        level_factor = (2 * self.level + 10) / 250
        attack_defense_ratio = attack_stat / defense_stat
        base_damage = level_factor * move.power * attack_defense_ratio + 2
        
        # Critical hit (ignores stat drops)
        if not critical:
            # Base critical rate is 1/16
            crit_chance = 1/16
            critical = random.random() < crit_chance
        
        if critical:
            base_damage *= 1.5
            events.append("A critical hit!")
        
        # Type effectiveness
        effectiveness = self.get_type_effectiveness(move.type, defender.types)
        if effectiveness > 1:
            events.append("It's super effective!")
        elif effectiveness < 1 and effectiveness > 0:
            events.append("It's not very effective...")
        elif effectiveness == 0:
            events.append("It had no effect!")
        
        # STAB (Same Type Attack Bonus)
        if move.type in self.types:
            base_damage *= 1.5
        
        # Random factor (85-100%)
        random_factor = random.randint(85, 100) / 100
        
        # Calculate final damage
        damage = int(base_damage * effectiveness * random_factor)
        
        return max(1, damage) if effectiveness > 0 else 0, effectiveness, events
    
    def get_accuracy_multiplier(self) -> float:
        """Get accuracy multiplier based on stat stage."""
        stage = self.stat_stages["accuracy"]
        if stage >= 0:
            return (3 + stage) / 3
        else:
            return 3 / (3 - stage)
    
    def get_evasion_multiplier(self) -> float:
        """Get evasion multiplier based on stat stage."""
        stage = self.stat_stages["evasion"]
        if stage >= 0:
            return 3 / (3 + stage)
        else:
            return (3 - stage) / 3
    
    def get_type_effectiveness(self, attacking_type: PokemonType, 
                               defending_types: List[PokemonType]) -> float:
        """Calculate type effectiveness multiplier."""
        effectiveness = 1.0
        
        for def_type in defending_types:
            if attacking_type in TYPE_EFFECTIVENESS:
                if def_type in TYPE_EFFECTIVENESS[attacking_type]:
                    effectiveness *= TYPE_EFFECTIVENESS[attacking_type][def_type]
        
        return effectiveness
    
    def can_battle(self) -> bool:
        """Check if Pokemon can battle."""
        return not self.is_fainted and self.current_hp > 0
    
    def get_exp_yield(self) -> int:
        """Calculate experience points this Pokemon gives when defeated."""
        # Base exp yield would normally come from species data
        # Using a simple formula based on level for now
        base_exp = 64  # This would come from species data
        return int(base_exp * self.level / 7)
    
    def __str__(self):
        type_str = "/".join([t.value for t in self.types])
        status_str = f" {self.status.value.upper()}" if self.status != StatusCondition.NONE else ""
        return (f"{self.nickname} (Lv.{self.level} {type_str}) "
                f"HP: {self.current_hp}/{self.stats['hp']}{status_str}")


# Pokemon species data for the 10 Pokemon we have sprites for
POKEMON_DATA = {
    1: {  # Bulbasaur
        "id": 1,
        "name": "Bulbasaur",
        "types": ["grass", "poison"],
        "base_stats": {
            "hp": 45,
            "attack": 49,
            "defense": 49,
            "sp_attack": 65,
            "sp_defense": 65,
            "speed": 45
        },
        "abilities": [
            {"name": "Overgrow", "description": "Powers up Grass-type moves when HP is low", "effect_type": "low_hp_boost"},
            {"name": "Chlorophyll", "description": "Boosts Speed in sunny weather", "effect_type": "weather_speed"}
        ],
        "experience_group": "medium_slow",
        "learnset": [
            {"level": 1, "name": "Tackle", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Growl", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 40, "effect": "lower_attack"},
            {"level": 3, "name": "Vine Whip", "type": "grass", "category": "physical", "power": 45, "accuracy": 100, "pp": 25},
            {"level": 7, "name": "Leech Seed", "type": "grass", "category": "status", "power": 0, "accuracy": 90, "pp": 10, "effect": "leech_seed"},
            {"level": 9, "name": "Razor Leaf", "type": "grass", "category": "physical", "power": 55, "accuracy": 95, "pp": 25},
            {"level": 13, "name": "Poison Powder", "type": "poison", "category": "status", "power": 0, "accuracy": 75, "pp": 35, "effect": "poison"},
            {"level": 15, "name": "Sleep Powder", "type": "grass", "category": "status", "power": 0, "accuracy": 75, "pp": 15, "effect": "sleep"},
            {"level": 19, "name": "Take Down", "type": "normal", "category": "physical", "power": 90, "accuracy": 85, "pp": 20, "effect": "recoil"},
            {"level": 21, "name": "Sweet Scent", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "lower_evasion"},
            {"level": 25, "name": "Growth", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "raise_sp_attack"},
            {"level": 27, "name": "Double-Edge", "type": "normal", "category": "physical", "power": 120, "accuracy": 100, "pp": 15, "effect": "recoil"},
            {"level": 31, "name": "Worry Seed", "type": "grass", "category": "status", "power": 0, "accuracy": 100, "pp": 10},
            {"level": 33, "name": "Synthesis", "type": "grass", "category": "status", "power": 0, "accuracy": 100, "pp": 5, "effect": "heal"},
            {"level": 37, "name": "Seed Bomb", "type": "grass", "category": "physical", "power": 80, "accuracy": 100, "pp": 15}
        ]
    },
    4: {  # Charmander
        "id": 4,
        "name": "Charmander",
        "types": ["fire"],
        "base_stats": {
            "hp": 39,
            "attack": 52,
            "defense": 43,
            "sp_attack": 60,
            "sp_defense": 50,
            "speed": 65
        },
        "abilities": [
            {"name": "Blaze", "description": "Powers up Fire-type moves when HP is low", "effect_type": "low_hp_boost"},
            {"name": "Solar Power", "description": "Boosts Sp. Attack in sunny weather but loses HP", "effect_type": "weather_boost"}
        ],
        "experience_group": "medium_slow",
        "learnset": [
            {"level": 1, "name": "Scratch", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Growl", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 40, "effect": "lower_attack"},
            {"level": 4, "name": "Ember", "type": "fire", "category": "special", "power": 40, "accuracy": 100, "pp": 25, "effect": "burn", "effect_chance": 10},
            {"level": 8, "name": "Smokescreen", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "lower_accuracy"},
            {"level": 12, "name": "Dragon Breath", "type": "dragon", "category": "special", "power": 60, "accuracy": 100, "pp": 20, "effect": "paralysis", "effect_chance": 30},
            {"level": 17, "name": "Fire Fang", "type": "fire", "category": "physical", "power": 65, "accuracy": 95, "pp": 15, "effect": "burn", "effect_chance": 10},
            {"level": 20, "name": "Slash", "type": "normal", "category": "physical", "power": 70, "accuracy": 100, "pp": 20},
            {"level": 24, "name": "Flamethrower", "type": "fire", "category": "special", "power": 90, "accuracy": 100, "pp": 15, "effect": "burn", "effect_chance": 10},
            {"level": 28, "name": "Scary Face", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "lower_speed"},
            {"level": 32, "name": "Fire Spin", "type": "fire", "category": "special", "power": 35, "accuracy": 85, "pp": 15, "effect": "trap"},
            {"level": 36, "name": "Inferno", "type": "fire", "category": "special", "power": 100, "accuracy": 50, "pp": 5, "effect": "burn", "effect_chance": 100},
            {"level": 40, "name": "Flare Blitz", "type": "fire", "category": "physical", "power": 120, "accuracy": 100, "pp": 15, "effect": "recoil_burn"}
        ]
    },
    7: {  # Squirtle
        "id": 7,
        "name": "Squirtle",
        "types": ["water"],
        "base_stats": {
            "hp": 44,
            "attack": 48,
            "defense": 65,
            "sp_attack": 50,
            "sp_defense": 64,
            "speed": 43
        },
        "abilities": [
            {"name": "Torrent", "description": "Powers up Water-type moves when HP is low", "effect_type": "low_hp_boost"},
            {"name": "Rain Dish", "description": "Restores HP in rain", "effect_type": "weather_heal"}
        ],
        "experience_group": "medium_slow",
        "learnset": [
            {"level": 1, "name": "Tackle", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Tail Whip", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "effect": "lower_defense"},
            {"level": 3, "name": "Water Gun", "type": "water", "category": "special", "power": 40, "accuracy": 100, "pp": 25},
            {"level": 6, "name": "Withdraw", "type": "water", "category": "status", "power": 0, "accuracy": 100, "pp": 40, "effect": "raise_defense"},
            {"level": 9, "name": "Rapid Spin", "type": "normal", "category": "physical", "power": 50, "accuracy": 100, "pp": 40},
            {"level": 12, "name": "Bite", "type": "dark", "category": "physical", "power": 60, "accuracy": 100, "pp": 25, "effect": "flinch", "effect_chance": 30},
            {"level": 15, "name": "Water Pulse", "type": "water", "category": "special", "power": 60, "accuracy": 100, "pp": 20, "effect": "confusion", "effect_chance": 20},
            {"level": 18, "name": "Protect", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "priority": 4},
            {"level": 21, "name": "Rain Dance", "type": "water", "category": "status", "power": 0, "accuracy": 100, "pp": 5, "effect": "weather_rain"},
            {"level": 24, "name": "Aqua Tail", "type": "water", "category": "physical", "power": 90, "accuracy": 90, "pp": 10},
            {"level": 27, "name": "Shell Smash", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 15, "effect": "shell_smash"},
            {"level": 30, "name": "Iron Defense", "type": "steel", "category": "status", "power": 0, "accuracy": 100, "pp": 15, "effect": "raise_defense_sharply"},
            {"level": 33, "name": "Hydro Pump", "type": "water", "category": "special", "power": 110, "accuracy": 80, "pp": 5},
            {"level": 36, "name": "Skull Bash", "type": "normal", "category": "physical", "power": 130, "accuracy": 100, "pp": 10}
        ]
    },
    25: {  # Pikachu
        "id": 25,
        "name": "Pikachu",
        "types": ["electric"],
        "base_stats": {
            "hp": 35,
            "attack": 55,
            "defense": 40,
            "sp_attack": 50,
            "sp_defense": 50,
            "speed": 90
        },
        "abilities": [
            {"name": "Static", "description": "May paralyze on contact", "effect_type": "contact_status"},
            {"name": "Lightning Rod", "description": "Draws in Electric-type moves", "effect_type": "type_immunity"}
        ],
        "experience_group": "medium_fast",
        "learnset": [
            {"level": 1, "name": "Thunder Shock", "type": "electric", "category": "special", "power": 40, "accuracy": 100, "pp": 30, "effect": "paralysis", "effect_chance": 10},
            {"level": 1, "name": "Growl", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 40, "effect": "lower_attack"},
            {"level": 4, "name": "Quick Attack", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 30, "priority": 1},
            {"level": 8, "name": "Thunder Wave", "type": "electric", "category": "status", "power": 0, "accuracy": 90, "pp": 20, "effect": "paralysis"},
            {"level": 12, "name": "Electro Ball", "type": "electric", "category": "special", "power": 60, "accuracy": 100, "pp": 10},
            {"level": 16, "name": "Double Team", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 15, "effect": "raise_evasion"},
            {"level": 20, "name": "Spark", "type": "electric", "category": "physical", "power": 65, "accuracy": 100, "pp": 20, "effect": "paralysis", "effect_chance": 30},
            {"level": 24, "name": "Nuzzle", "type": "electric", "category": "physical", "power": 20, "accuracy": 100, "pp": 20, "effect": "paralysis", "effect_chance": 100},
            {"level": 28, "name": "Discharge", "type": "electric", "category": "special", "power": 80, "accuracy": 100, "pp": 15, "effect": "paralysis", "effect_chance": 30},
            {"level": 32, "name": "Slam", "type": "normal", "category": "physical", "power": 80, "accuracy": 75, "pp": 20},
            {"level": 36, "name": "Thunderbolt", "type": "electric", "category": "special", "power": 90, "accuracy": 100, "pp": 15, "effect": "paralysis", "effect_chance": 10},
            {"level": 40, "name": "Agility", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "effect": "raise_speed_sharply"},
            {"level": 44, "name": "Wild Charge", "type": "electric", "category": "physical", "power": 90, "accuracy": 100, "pp": 15, "effect": "recoil"},
            {"level": 48, "name": "Light Screen", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 30},
            {"level": 52, "name": "Thunder", "type": "electric", "category": "special", "power": 110, "accuracy": 70, "pp": 10, "effect": "paralysis", "effect_chance": 30}
        ]
    },
    94: {  # Gengar
        "id": 94,
        "name": "Gengar",
        "types": ["ghost", "poison"],
        "base_stats": {
            "hp": 60,
            "attack": 65,
            "defense": 60,
            "sp_attack": 130,
            "sp_defense": 75,
            "speed": 110
        },
        "abilities": [
            {"name": "Cursed Body", "description": "May disable a move on contact", "effect_type": "contact_disable"},
            {"name": "Levitate", "description": "Immune to Ground-type moves", "effect_type": "type_immunity"}
        ],
        "experience_group": "medium_slow",
        "learnset": [
            {"level": 1, "name": "Shadow Punch", "type": "ghost", "category": "physical", "power": 60, "accuracy": 999, "pp": 20},
            {"level": 1, "name": "Hypnosis", "type": "psychic", "category": "status", "power": 0, "accuracy": 60, "pp": 20, "effect": "sleep"},
            {"level": 1, "name": "Lick", "type": "ghost", "category": "physical", "power": 30, "accuracy": 100, "pp": 30, "effect": "paralysis", "effect_chance": 30},
            {"level": 1, "name": "Mean Look", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 5, "effect": "trap"},
            {"level": 8, "name": "Curse", "type": "ghost", "category": "status", "power": 0, "accuracy": 100, "pp": 10},
            {"level": 12, "name": "Night Shade", "type": "ghost", "category": "special", "power": 1, "accuracy": 100, "pp": 15},
            {"level": 16, "name": "Confuse Ray", "type": "ghost", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "confusion"},
            {"level": 20, "name": "Sucker Punch", "type": "dark", "category": "physical", "power": 70, "accuracy": 100, "pp": 5, "priority": 1},
            {"level": 24, "name": "Payback", "type": "dark", "category": "physical", "power": 50, "accuracy": 100, "pp": 10},
            {"level": 28, "name": "Shadow Ball", "type": "ghost", "category": "special", "power": 80, "accuracy": 100, "pp": 15, "effect": "lower_sp_defense", "effect_chance": 20},
            {"level": 32, "name": "Dream Eater", "type": "psychic", "category": "special", "power": 100, "accuracy": 100, "pp": 15},
            {"level": 36, "name": "Dark Pulse", "type": "dark", "category": "special", "power": 80, "accuracy": 100, "pp": 15, "effect": "flinch", "effect_chance": 20},
            {"level": 40, "name": "Destiny Bond", "type": "ghost", "category": "status", "power": 0, "accuracy": 100, "pp": 5},
            {"level": 44, "name": "Hex", "type": "ghost", "category": "special", "power": 65, "accuracy": 100, "pp": 10},
            {"level": 48, "name": "Nightmare", "type": "ghost", "category": "status", "power": 0, "accuracy": 100, "pp": 15}
        ]
    },
    133: {  # Eevee
        "id": 133,
        "name": "Eevee",
        "types": ["normal"],
        "base_stats": {
            "hp": 55,
            "attack": 55,
            "defense": 50,
            "sp_attack": 45,
            "sp_defense": 65,
            "speed": 55
        },
        "abilities": [
            {"name": "Run Away", "description": "Ensures escape from wild Pokemon", "effect_type": "escape"},
            {"name": "Adaptability", "description": "Increases STAB from 1.5x to 2x", "effect_type": "stab_boost"},
            {"name": "Anticipation", "description": "Warns of dangerous moves", "effect_type": "danger_sense"}
        ],
        "experience_group": "medium_fast",
        "learnset": [
            {"level": 1, "name": "Tackle", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Tail Whip", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "effect": "lower_defense"},
            {"level": 1, "name": "Helping Hand", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "priority": 5},
            {"level": 5, "name": "Sand Attack", "type": "ground", "category": "status", "power": 0, "accuracy": 100, "pp": 15, "effect": "lower_accuracy"},
            {"level": 10, "name": "Quick Attack", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 30, "priority": 1},
            {"level": 15, "name": "Baby-Doll Eyes", "type": "fairy", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "priority": 1, "effect": "lower_attack"},
            {"level": 20, "name": "Swift", "type": "normal", "category": "special", "power": 60, "accuracy": 999, "pp": 20},
            {"level": 25, "name": "Bite", "type": "dark", "category": "physical", "power": 60, "accuracy": 100, "pp": 25, "effect": "flinch", "effect_chance": 30},
            {"level": 30, "name": "Copycat", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 20},
            {"level": 35, "name": "Baton Pass", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 40},
            {"level": 40, "name": "Take Down", "type": "normal", "category": "physical", "power": 90, "accuracy": 85, "pp": 20, "effect": "recoil"},
            {"level": 45, "name": "Charm", "type": "fairy", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "lower_attack_sharply"},
            {"level": 50, "name": "Double-Edge", "type": "normal", "category": "physical", "power": 120, "accuracy": 100, "pp": 15, "effect": "recoil"},
            {"level": 55, "name": "Last Resort", "type": "normal", "category": "physical", "power": 140, "accuracy": 100, "pp": 5}
        ]
    },
    143: {  # Snorlax
        "id": 143,
        "name": "Snorlax",
        "types": ["normal"],
        "base_stats": {
            "hp": 160,
            "attack": 110,
            "defense": 65,
            "sp_attack": 65,
            "sp_defense": 110,
            "speed": 30
        },
        "abilities": [
            {"name": "Immunity", "description": "Prevents poisoning", "effect_type": "status_immunity"},
            {"name": "Thick Fat", "description": "Reduces Fire and Ice damage", "effect_type": "type_resist"},
            {"name": "Gluttony", "description": "Uses berries earlier", "effect_type": "item_trigger"}
        ],
        "experience_group": "slow",
        "learnset": [
            {"level": 1, "name": "Tackle", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Recycle", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10},
            {"level": 4, "name": "Defense Curl", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 40, "effect": "raise_defense"},
            {"level": 8, "name": "Amnesia", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "raise_sp_defense_sharply"},
            {"level": 12, "name": "Lick", "type": "ghost", "category": "physical", "power": 30, "accuracy": 100, "pp": 30, "effect": "paralysis", "effect_chance": 30},
            {"level": 16, "name": "Yawn", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "drowsy"},
            {"level": 20, "name": "Rest", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "rest"},
            {"level": 20, "name": "Snore", "type": "normal", "category": "special", "power": 50, "accuracy": 100, "pp": 15},
            {"level": 20, "name": "Sleep Talk", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10},
            {"level": 24, "name": "Body Slam", "type": "normal", "category": "physical", "power": 85, "accuracy": 100, "pp": 15, "effect": "paralysis", "effect_chance": 30},
            {"level": 28, "name": "Block", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 5, "effect": "trap"},
            {"level": 32, "name": "Belly Drum", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "max_attack"},
            {"level": 36, "name": "Crunch", "type": "dark", "category": "physical", "power": 80, "accuracy": 100, "pp": 15, "effect": "lower_defense", "effect_chance": 20},
            {"level": 40, "name": "Heavy Slam", "type": "steel", "category": "physical", "power": 80, "accuracy": 100, "pp": 10},
            {"level": 44, "name": "High Horsepower", "type": "ground", "category": "physical", "power": 95, "accuracy": 95, "pp": 10},
            {"level": 48, "name": "Hammer Arm", "type": "fighting", "category": "physical", "power": 100, "accuracy": 90, "pp": 10, "effect": "lower_speed_self"},
            {"level": 52, "name": "Giga Impact", "type": "normal", "category": "physical", "power": 150, "accuracy": 90, "pp": 5, "effect": "recharge"}
        ]
    },
    144: {  # Articuno
        "id": 144,
        "name": "Articuno",
        "types": ["ice", "flying"],
        "base_stats": {
            "hp": 90,
            "attack": 85,
            "defense": 100,
            "sp_attack": 95,
            "sp_defense": 125,
            "speed": 85
        },
        "abilities": [
            {"name": "Pressure", "description": "Opponent uses 2 PP per move", "effect_type": "pp_drain"},
            {"name": "Snow Cloak", "description": "Raises evasion in hail", "effect_type": "weather_evasion"}
        ],
        "experience_group": "slow",
        "learnset": [
            {"level": 1, "name": "Gust", "type": "flying", "category": "special", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Powder Snow", "type": "ice", "category": "special", "power": 40, "accuracy": 100, "pp": 25, "effect": "freeze", "effect_chance": 10},
            {"level": 5, "name": "Mist", "type": "ice", "category": "status", "power": 0, "accuracy": 100, "pp": 30},
            {"level": 10, "name": "Ice Shard", "type": "ice", "category": "physical", "power": 40, "accuracy": 100, "pp": 30, "priority": 1},
            {"level": 15, "name": "Reflect", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 20},
            {"level": 20, "name": "Agility", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "effect": "raise_speed_sharply"},
            {"level": 25, "name": "Ancient Power", "type": "rock", "category": "special", "power": 60, "accuracy": 100, "pp": 5, "effect": "all_stats_up", "effect_chance": 10},
            {"level": 30, "name": "Tailwind", "type": "flying", "category": "status", "power": 0, "accuracy": 100, "pp": 15},
            {"level": 35, "name": "Freeze-Dry", "type": "ice", "category": "special", "power": 70, "accuracy": 100, "pp": 20, "effect": "freeze", "effect_chance": 10},
            {"level": 40, "name": "Roost", "type": "flying", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "heal"},
            {"level": 45, "name": "Ice Beam", "type": "ice", "category": "special", "power": 90, "accuracy": 100, "pp": 10, "effect": "freeze", "effect_chance": 10},
            {"level": 50, "name": "Hail", "type": "ice", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "weather_hail"},
            {"level": 55, "name": "Hurricane", "type": "flying", "category": "special", "power": 110, "accuracy": 70, "pp": 10, "effect": "confusion", "effect_chance": 30},
            {"level": 60, "name": "Mind Reader", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 5},
            {"level": 65, "name": "Sheer Cold", "type": "ice", "category": "special", "power": 999, "accuracy": 30, "pp": 5},
            {"level": 70, "name": "Blizzard", "type": "ice", "category": "special", "power": 110, "accuracy": 70, "pp": 5, "effect": "freeze", "effect_chance": 10}
        ]
    },
    145: {  # Zapdos
        "id": 145,
        "name": "Zapdos",
        "types": ["electric", "flying"],
        "base_stats": {
            "hp": 90,
            "attack": 90,
            "defense": 85,
            "sp_attack": 125,
            "sp_defense": 90,
            "speed": 100
        },
        "abilities": [
            {"name": "Pressure", "description": "Opponent uses 2 PP per move", "effect_type": "pp_drain"},
            {"name": "Static", "description": "May paralyze on contact", "effect_type": "contact_status"}
        ],
        "experience_group": "slow",
        "learnset": [
            {"level": 1, "name": "Peck", "type": "flying", "category": "physical", "power": 35, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Thunder Shock", "type": "electric", "category": "special", "power": 40, "accuracy": 100, "pp": 30, "effect": "paralysis", "effect_chance": 10},
            {"level": 5, "name": "Thunder Wave", "type": "electric", "category": "status", "power": 0, "accuracy": 90, "pp": 20, "effect": "paralysis"},
            {"level": 10, "name": "Detect", "type": "fighting", "category": "status", "power": 0, "accuracy": 100, "pp": 5, "priority": 4},
            {"level": 15, "name": "Pluck", "type": "flying", "category": "physical", "power": 60, "accuracy": 100, "pp": 20},
            {"level": 20, "name": "Ancient Power", "type": "rock", "category": "special", "power": 60, "accuracy": 100, "pp": 5, "effect": "all_stats_up", "effect_chance": 10},
            {"level": 25, "name": "Charge", "type": "electric", "category": "status", "power": 0, "accuracy": 100, "pp": 20},
            {"level": 30, "name": "Agility", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "effect": "raise_speed_sharply"},
            {"level": 35, "name": "Discharge", "type": "electric", "category": "special", "power": 80, "accuracy": 100, "pp": 15, "effect": "paralysis", "effect_chance": 30},
            {"level": 40, "name": "Rain Dance", "type": "water", "category": "status", "power": 0, "accuracy": 100, "pp": 5, "effect": "weather_rain"},
            {"level": 45, "name": "Light Screen", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 30},
            {"level": 50, "name": "Drill Peck", "type": "flying", "category": "physical", "power": 80, "accuracy": 100, "pp": 20},
            {"level": 55, "name": "Thunderbolt", "type": "electric", "category": "special", "power": 90, "accuracy": 100, "pp": 15, "effect": "paralysis", "effect_chance": 10},
            {"level": 60, "name": "Roost", "type": "flying", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "heal"},
            {"level": 65, "name": "Magnetic Rise", "type": "electric", "category": "status", "power": 0, "accuracy": 100, "pp": 10},
            {"level": 70, "name": "Zap Cannon", "type": "electric", "category": "special", "power": 120, "accuracy": 50, "pp": 5, "effect": "paralysis", "effect_chance": 100},
            {"level": 75, "name": "Thunder", "type": "electric", "category": "special", "power": 110, "accuracy": 70, "pp": 10, "effect": "paralysis", "effect_chance": 30}
        ]
    },
    146: {  # Moltres
        "id": 146,
        "name": "Moltres",
        "types": ["fire", "flying"],
        "base_stats": {
            "hp": 90,
            "attack": 100,
            "defense": 90,
            "sp_attack": 125,
            "sp_defense": 85,
            "speed": 90
        },
        "abilities": [
            {"name": "Pressure", "description": "Opponent uses 2 PP per move", "effect_type": "pp_drain"},
            {"name": "Flame Body", "description": "May burn on contact", "effect_type": "contact_status"}
        ],
        "experience_group": "slow",
        "learnset": [
            {"level": 1, "name": "Wing Attack", "type": "flying", "category": "physical", "power": 60, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Ember", "type": "fire", "category": "special", "power": 40, "accuracy": 100, "pp": 25, "effect": "burn", "effect_chance": 10},
            {"level": 5, "name": "Fire Spin", "type": "fire", "category": "special", "power": 35, "accuracy": 85, "pp": 15, "effect": "trap"},
            {"level": 10, "name": "Agility", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "effect": "raise_speed_sharply"},
            {"level": 15, "name": "Endure", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "priority": 4},
            {"level": 20, "name": "Ancient Power", "type": "rock", "category": "special", "power": 60, "accuracy": 100, "pp": 5, "effect": "all_stats_up", "effect_chance": 10},
            {"level": 25, "name": "Flame Wheel", "type": "fire", "category": "physical", "power": 60, "accuracy": 100, "pp": 25, "effect": "burn", "effect_chance": 10},
            {"level": 30, "name": "Safeguard", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 25},
            {"level": 35, "name": "Air Slash", "type": "flying", "category": "special", "power": 75, "accuracy": 95, "pp": 15, "effect": "flinch", "effect_chance": 30},
            {"level": 40, "name": "Sunny Day", "type": "fire", "category": "status", "power": 0, "accuracy": 100, "pp": 5, "effect": "weather_sun"},
            {"level": 45, "name": "Heat Wave", "type": "fire", "category": "special", "power": 95, "accuracy": 90, "pp": 10, "effect": "burn", "effect_chance": 10},
            {"level": 50, "name": "Solar Beam", "type": "grass", "category": "special", "power": 120, "accuracy": 100, "pp": 10},
            {"level": 55, "name": "Sky Attack", "type": "flying", "category": "physical", "power": 140, "accuracy": 90, "pp": 5},
            {"level": 60, "name": "Roost", "type": "flying", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "heal"},
            {"level": 65, "name": "Hurricane", "type": "flying", "category": "special", "power": 110, "accuracy": 70, "pp": 10, "effect": "confusion", "effect_chance": 30},
            {"level": 70, "name": "Burn Up", "type": "fire", "category": "special", "power": 130, "accuracy": 100, "pp": 5}
        ]
    },
    149: {  # Dragonite
        "id": 149,
        "name": "Dragonite",
        "types": ["dragon", "flying"],
        "base_stats": {
            "hp": 91,
            "attack": 134,
            "defense": 95,
            "sp_attack": 100,
            "sp_defense": 100,
            "speed": 80
        },
        "abilities": [
            {"name": "Inner Focus", "description": "Prevents flinching", "effect_type": "flinch_immunity"},
            {"name": "Multiscale", "description": "Reduces damage when HP is full", "effect_type": "full_hp_defense"}
        ],
        "experience_group": "slow",
        "learnset": [
            {"level": 1, "name": "Fire Punch", "type": "fire", "category": "physical", "power": 75, "accuracy": 100, "pp": 15, "effect": "burn", "effect_chance": 10},
            {"level": 1, "name": "Thunder Punch", "type": "electric", "category": "physical", "power": 75, "accuracy": 100, "pp": 15, "effect": "paralysis", "effect_chance": 10},
            {"level": 1, "name": "Roost", "type": "flying", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "heal"},
            {"level": 1, "name": "Extreme Speed", "type": "normal", "category": "physical", "power": 80, "accuracy": 100, "pp": 5, "priority": 2},
            {"level": 1, "name": "Wrap", "type": "normal", "category": "physical", "power": 15, "accuracy": 90, "pp": 20, "effect": "trap"},
            {"level": 1, "name": "Leer", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "effect": "lower_defense"},
            {"level": 1, "name": "Twister", "type": "dragon", "category": "special", "power": 40, "accuracy": 100, "pp": 20, "effect": "flinch", "effect_chance": 20},
            {"level": 1, "name": "Thunder Wave", "type": "electric", "category": "status", "power": 0, "accuracy": 90, "pp": 20, "effect": "paralysis"},
            {"level": 5, "name": "Dragon Tail", "type": "dragon", "category": "physical", "power": 60, "accuracy": 90, "pp": 10, "priority": -6},
            {"level": 11, "name": "Agility", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "effect": "raise_speed_sharply"},
            {"level": 15, "name": "Dragon Rage", "type": "dragon", "category": "special", "power": 40, "accuracy": 100, "pp": 10},
            {"level": 21, "name": "Slam", "type": "normal", "category": "physical", "power": 80, "accuracy": 75, "pp": 20},
            {"level": 25, "name": "Aqua Tail", "type": "water", "category": "physical", "power": 90, "accuracy": 90, "pp": 10},
            {"level": 33, "name": "Dragon Rush", "type": "dragon", "category": "physical", "power": 100, "accuracy": 75, "pp": 10, "effect": "flinch", "effect_chance": 20},
            {"level": 39, "name": "Safeguard", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 25},
            {"level": 41, "name": "Wing Attack", "type": "flying", "category": "physical", "power": 60, "accuracy": 100, "pp": 35},
            {"level": 47, "name": "Dragon Dance", "type": "dragon", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "dragon_dance"},
            {"level": 53, "name": "Outrage", "type": "dragon", "category": "physical", "power": 120, "accuracy": 100, "pp": 10},
            {"level": 61, "name": "Hyper Beam", "type": "normal", "category": "special", "power": 150, "accuracy": 90, "pp": 5, "effect": "recharge"},
            {"level": 67, "name": "Hurricane", "type": "flying", "category": "special", "power": 110, "accuracy": 70, "pp": 10, "effect": "confusion", "effect_chance": 30}
        ]
    },
    150: {  # Mewtwo
        "id": 150,
        "name": "Mewtwo",
        "types": ["psychic"],
        "base_stats": {
            "hp": 106,
            "attack": 110,
            "defense": 90,
            "sp_attack": 154,
            "sp_defense": 90,
            "speed": 130
        },
        "abilities": [
            {"name": "Pressure", "description": "Opponent uses 2 PP per move", "effect_type": "pp_drain"},
            {"name": "Unnerve", "description": "Prevents opponent from using berries", "effect_type": "item_block"}
        ],
        "experience_group": "slow",
        "learnset": [
            {"level": 1, "name": "Life Dew", "type": "water", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "heal_team"},
            {"level": 1, "name": "Laser Focus", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 30},
            {"level": 1, "name": "Disable", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 20},
            {"level": 1, "name": "Confusion", "type": "psychic", "category": "special", "power": 50, "accuracy": 100, "pp": 25, "effect": "confusion", "effect_chance": 10},
            {"level": 8, "name": "Swift", "type": "normal", "category": "special", "power": 60, "accuracy": 999, "pp": 20},
            {"level": 16, "name": "Ancient Power", "type": "rock", "category": "special", "power": 60, "accuracy": 100, "pp": 5, "effect": "all_stats_up", "effect_chance": 10},
            {"level": 24, "name": "Psycho Cut", "type": "psychic", "category": "physical", "power": 70, "accuracy": 100, "pp": 20},
            {"level": 32, "name": "Safeguard", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 25},
            {"level": 40, "name": "Amnesia", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "raise_sp_defense_sharply"},
            {"level": 48, "name": "Psychic", "type": "psychic", "category": "special", "power": 90, "accuracy": 100, "pp": 10, "effect": "lower_sp_defense", "effect_chance": 10},
            {"level": 56, "name": "Barrier", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "raise_defense_sharply"},
            {"level": 64, "name": "Aura Sphere", "type": "fighting", "category": "special", "power": 80, "accuracy": 999, "pp": 20},
            {"level": 72, "name": "Recover", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "heal"},
            {"level": 80, "name": "Future Sight", "type": "psychic", "category": "special", "power": 120, "accuracy": 100, "pp": 10},
            {"level": 88, "name": "Mist", "type": "ice", "category": "status", "power": 0, "accuracy": 100, "pp": 30},
            {"level": 96, "name": "Psystrike", "type": "psychic", "category": "special", "power": 100, "accuracy": 100, "pp": 10}
        ]
    },
    151: {  # Mew
        "id": 151,
        "name": "Mew",
        "types": ["psychic"],
        "base_stats": {
            "hp": 100,
            "attack": 100,
            "defense": 100,
            "sp_attack": 100,
            "sp_defense": 100,
            "speed": 100
        },
        "abilities": [
            {"name": "Synchronize", "description": "Passes status problems to the opponent", "effect_type": "status_mirror"}
        ],
        "experience_group": "medium_slow",
        "learnset": [
            {"level": 1, "name": "Pound", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Reflect Type", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 15},
            {"level": 10, "name": "Amnesia", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "raise_sp_defense_sharply"},
            {"level": 20, "name": "Baton Pass", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 40},
            {"level": 30, "name": "Ancient Power", "type": "rock", "category": "special", "power": 60, "accuracy": 100, "pp": 5, "effect": "all_stats_up", "effect_chance": 10},
            {"level": 40, "name": "Life Dew", "type": "water", "category": "status", "power": 0, "accuracy": 100, "pp": 10, "effect": "heal_team"},
            {"level": 50, "name": "Nasty Plot", "type": "dark", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "raise_sp_attack_sharply"},
            {"level": 60, "name": "Metronome", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10},
            {"level": 70, "name": "Imprison", "type": "psychic", "category": "status", "power": 0, "accuracy": 100, "pp": 10},
            {"level": 80, "name": "Transform", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 10},
            {"level": 90, "name": "Aura Sphere", "type": "fighting", "category": "special", "power": 80, "accuracy": 999, "pp": 20},
            {"level": 100, "name": "Psychic", "type": "psychic", "category": "special", "power": 90, "accuracy": 100, "pp": 10, "effect": "lower_sp_defense", "effect_chance": 10}
        ]
    },
    16: {  # Pidgey
        "id": 16,
        "name": "Pidgey",
        "types": ["normal", "flying"],
        "base_stats": {
            "hp": 40,
            "attack": 45,
            "defense": 40,
            "sp_attack": 35,
            "sp_defense": 35,
            "speed": 56
        },
        "abilities": [
            {"name": "Keen Eye", "description": "Prevents accuracy loss", "effect_type": "accuracy_protect"},
            {"name": "Tangled Feet", "description": "Raises evasion when confused", "effect_type": "confusion_evasion"}
        ],
        "experience_group": "medium_slow",
        "learnset": [
            {"level": 1, "name": "Tackle", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 5, "name": "Sand Attack", "type": "ground", "category": "status", "power": 0, "accuracy": 100, "pp": 15, "effect": "lower_accuracy"},
            {"level": 9, "name": "Gust", "type": "flying", "category": "special", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 13, "name": "Quick Attack", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 30, "priority": 1}
        ]
    },
    19: {  # Rattata
        "id": 19,
        "name": "Rattata",
        "types": ["normal"],
        "base_stats": {
            "hp": 30,
            "attack": 56,
            "defense": 35,
            "sp_attack": 25,
            "sp_defense": 35,
            "speed": 72
        },
        "abilities": [
            {"name": "Run Away", "description": "Ensures escape from wild Pokemon", "effect_type": "escape"},
            {"name": "Guts", "description": "Boosts Attack when statused", "effect_type": "status_attack_boost"}
        ],
        "experience_group": "medium_fast",
        "learnset": [
            {"level": 1, "name": "Tackle", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Tail Whip", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 30, "effect": "lower_defense"},
            {"level": 4, "name": "Quick Attack", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 30, "priority": 1},
            {"level": 7, "name": "Focus Energy", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 30}
        ]
    },
    10: {  # Caterpie
        "id": 10,
        "name": "Caterpie",
        "types": ["bug"],
        "base_stats": {
            "hp": 45,
            "attack": 30,
            "defense": 35,
            "sp_attack": 20,
            "sp_defense": 20,
            "speed": 45
        },
        "abilities": [
            {"name": "Shield Dust", "description": "Blocks additional effects", "effect_type": "effect_immunity"},
            {"name": "Run Away", "description": "Ensures escape from wild Pokemon", "effect_type": "escape"}
        ],
        "experience_group": "medium_fast",
        "learnset": [
            {"level": 1, "name": "Tackle", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "String Shot", "type": "bug", "category": "status", "power": 0, "accuracy": 95, "pp": 40, "effect": "lower_speed"},
            {"level": 9, "name": "Bug Bite", "type": "bug", "category": "physical", "power": 60, "accuracy": 100, "pp": 20}
        ]
    },
    13: {  # Weedle
        "id": 13,
        "name": "Weedle",
        "types": ["bug", "poison"],
        "base_stats": {
            "hp": 40,
            "attack": 35,
            "defense": 30,
            "sp_attack": 20,
            "sp_defense": 20,
            "speed": 50
        },
        "abilities": [
            {"name": "Shield Dust", "description": "Blocks additional effects", "effect_type": "effect_immunity"},
            {"name": "Run Away", "description": "Ensures escape from wild Pokemon", "effect_type": "escape"}
        ],
        "experience_group": "medium_fast",
        "learnset": [
            {"level": 1, "name": "Poison Sting", "type": "poison", "category": "physical", "power": 15, "accuracy": 100, "pp": 35, "effect": "poison", "effect_chance": 30},
            {"level": 1, "name": "String Shot", "type": "bug", "category": "status", "power": 0, "accuracy": 95, "pp": 40, "effect": "lower_speed"},
            {"level": 9, "name": "Bug Bite", "type": "bug", "category": "physical", "power": 60, "accuracy": 100, "pp": 20}
        ]
    },
    41: {  # Zubat
        "id": 41,
        "name": "Zubat",
        "types": ["poison", "flying"],
        "base_stats": {
            "hp": 40,
            "attack": 45,
            "defense": 35,
            "sp_attack": 30,
            "sp_defense": 40,
            "speed": 55
        },
        "abilities": [
            {"name": "Inner Focus", "description": "Prevents flinching", "effect_type": "flinch_immunity"},
            {"name": "Infiltrator", "description": "Bypasses barriers", "effect_type": "barrier_bypass"}
        ],
        "experience_group": "medium_fast",
        "learnset": [
            {"level": 1, "name": "Absorb", "type": "grass", "category": "special", "power": 20, "accuracy": 100, "pp": 25, "effect": "drain"},
            {"level": 4, "name": "Supersonic", "type": "normal", "category": "status", "power": 0, "accuracy": 55, "pp": 20, "effect": "confusion"},
            {"level": 8, "name": "Astonish", "type": "ghost", "category": "physical", "power": 30, "accuracy": 100, "pp": 15, "effect": "flinch", "effect_chance": 30},
            {"level": 12, "name": "Bite", "type": "dark", "category": "physical", "power": 60, "accuracy": 100, "pp": 25, "effect": "flinch", "effect_chance": 30}
        ]
    },
    74: {  # Geodude
        "id": 74,
        "name": "Geodude",
        "types": ["rock", "ground"],
        "base_stats": {
            "hp": 40,
            "attack": 80,
            "defense": 100,
            "sp_attack": 30,
            "sp_defense": 30,
            "speed": 20
        },
        "abilities": [
            {"name": "Rock Head", "description": "Prevents recoil damage", "effect_type": "recoil_immunity"},
            {"name": "Sturdy", "description": "Cannot be knocked out with one hit", "effect_type": "ohko_immunity"}
        ],
        "experience_group": "medium_slow",
        "learnset": [
            {"level": 1, "name": "Tackle", "type": "normal", "category": "physical", "power": 40, "accuracy": 100, "pp": 35},
            {"level": 1, "name": "Defense Curl", "type": "normal", "category": "status", "power": 0, "accuracy": 100, "pp": 40, "effect": "raise_defense"},
            {"level": 4, "name": "Mud Sport", "type": "ground", "category": "status", "power": 0, "accuracy": 100, "pp": 15},
            {"level": 6, "name": "Rock Polish", "type": "rock", "category": "status", "power": 0, "accuracy": 100, "pp": 20, "effect": "raise_speed_sharply"},
            {"level": 10, "name": "Rock Throw", "type": "rock", "category": "physical", "power": 50, "accuracy": 90, "pp": 15}
        ]
    }
}


def create_pokemon_from_species(species_id: int, level: int = 5, **kwargs) -> Pokemon:
    """Helper function to create a Pokemon from species data."""
    if species_id not in POKEMON_DATA:
        raise ValueError(f"Unknown Pokemon species ID: {species_id}")
    
    return Pokemon(POKEMON_DATA[species_id], level=level, **kwargs)