"""
Wild Pokemon Encounter System - Comprehensive encounter tables and mechanics
"""

import random
import math
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

if TYPE_CHECKING:
    from .pokemon import Pokemon

from .pokemon import PokemonType, Nature, create_pokemon_from_species


class EncounterRarity(Enum):
    """Rarity tiers for Pokemon encounters."""
    COMMON = "common"       # 50% chance
    UNCOMMON = "uncommon"   # 30% chance
    RARE = "rare"          # 15% chance
    VERY_RARE = "very_rare" # 4% chance
    LEGENDARY = "legendary" # 1% chance


class TimeOfDay(Enum):
    """Time periods for time-based encounters."""
    MORNING = "morning"    # 4:00 - 9:59
    DAY = "day"           # 10:00 - 19:59
    NIGHT = "night"       # 20:00 - 3:59


@dataclass
class EncounterData:
    """Data for a potential Pokemon encounter."""
    species_id: int
    min_level: int
    max_level: int
    rarity: EncounterRarity
    conditions: Optional[Dict[str, any]] = None  # Special conditions like time, weather, etc.
    shiny_boost: float = 1.0  # Multiplier for shiny chance


@dataclass
class EncounterTable:
    """Encounter table for a specific area."""
    area_name: str
    base_encounter_rate: int  # Base percentage chance per step
    encounters: List[EncounterData]
    repel_effective: bool = True
    min_chain_encounters: int = 0  # Minimum encounters for chaining


class EncounterSystem:
    """Manages wild Pokemon encounters throughout the game."""
    
    # Base shiny chance (1 in 4096 in modern games)
    BASE_SHINY_CHANCE = 1 / 4096
    
    # Rarity weights
    RARITY_WEIGHTS = {
        EncounterRarity.COMMON: 50,
        EncounterRarity.UNCOMMON: 30,
        EncounterRarity.RARE: 15,
        EncounterRarity.VERY_RARE: 4,
        EncounterRarity.LEGENDARY: 1
    }
    
    def __init__(self):
        self.encounter_tables: Dict[str, EncounterTable] = self._create_encounter_tables()
        self.repel_steps = 0  # Steps remaining for repel effect
        self.chain_species = None  # Current chain species
        self.chain_count = 0  # Current chain count
        self.last_encounter_area = None
        
    def _create_encounter_tables(self) -> Dict[str, EncounterTable]:
        """Create all encounter tables for different areas."""
        tables = {}
        
        # Route 1 - Lore-accurate Gen 1 encounters
        tables["route_1"] = EncounterTable(
            area_name="Route 1",
            base_encounter_rate=12,
            encounters=[
                # Pidgey (~60%)
                EncounterData(16, 2, 5, EncounterRarity.COMMON),    # Pidgey
                # Rattata (~40%)
                EncounterData(19, 2, 4, EncounterRarity.UNCOMMON),  # Rattata
            ]
        )

        # Route 2 - Lore-accurate Gen 1 encounters
        tables["route_2"] = EncounterTable(
            area_name="Route 2",
            base_encounter_rate=12,
            encounters=[
                # Pidgey (~40%)
                EncounterData(16, 3, 6, EncounterRarity.COMMON),    # Pidgey
                # Rattata (~35%)
                EncounterData(19, 3, 5, EncounterRarity.UNCOMMON),  # Rattata
                # Caterpie (~25%)
                EncounterData(10, 3, 5, EncounterRarity.UNCOMMON),  # Caterpie
            ]
        )

        # Viridian Forest - Placeholder for future phases
        tables["viridian_forest"] = EncounterTable(
            area_name="Viridian Forest",
            base_encounter_rate=15,
            encounters=[]
        )

        # Route 3 - Placeholder for future phases
        tables["route_3"] = EncounterTable(
            area_name="Route 3",
            base_encounter_rate=12,
            encounters=[]
        )

        # Mt. Moon - Placeholder for future phases
        tables["mt_moon"] = EncounterTable(
            area_name="Mt. Moon",
            base_encounter_rate=12,
            encounters=[]
        )
        
        return tables
    
    def get_time_of_day(self) -> TimeOfDay:
        """Get current time of day based on system time."""
        hour = datetime.now().hour
        if 4 <= hour < 10:
            return TimeOfDay.MORNING
        elif 10 <= hour < 20:
            return TimeOfDay.DAY
        else:
            return TimeOfDay.NIGHT
    
    def use_repel(self, steps: int):
        """Activate repel effect for specified steps."""
        self.repel_steps = steps
    
    def check_repel(self, player_level: int) -> bool:
        """Check if repel prevents encounter."""
        if self.repel_steps > 0:
            self.repel_steps -= 1
            # Repel only works on Pokemon lower level than lead Pokemon
            # For now, since we don't have wild Pokemon level yet, repel blocks all encounters
            return True
        return False
    
    def should_encounter(self, area: str, steps_in_grass: int = 1) -> bool:
        """Determine if an encounter should occur."""
        if area not in self.encounter_tables:
            return False
        
        table = self.encounter_tables[area]
        
        # Dynamic encounter rate calculation
        base_rate = table.base_encounter_rate
        
        # Increase rate based on consecutive steps (more realistic curve)
        step_bonus = min(steps_in_grass * 1.5, 15)  # Max +15% from steps
        
        # Time of day modifier
        time_modifier = 1.0
        current_time = self.get_time_of_day()
        if current_time == TimeOfDay.MORNING:
            time_modifier = 1.1  # 10% more encounters in morning
        elif current_time == TimeOfDay.NIGHT:
            time_modifier = 1.2  # 20% more encounters at night
        
        # Chain bonus - slightly higher encounter rate when chaining
        chain_bonus = 0
        if self.chain_count > 5:
            chain_bonus = min(self.chain_count * 0.5, 10)  # Max +10% from chain
        
        # Calculate final rate
        modified_rate = (base_rate + step_bonus + chain_bonus) * time_modifier
        modified_rate = min(modified_rate, 45)  # Cap at 45%
        
        return random.randint(1, 100) <= modified_rate
    
    def get_encounter(self, area: str, player_data: Optional[Dict] = None) -> Optional['Pokemon']:
        """Generate a wild Pokemon encounter for the given area."""
        if area not in self.encounter_tables:
            return None
        
        table = self.encounter_tables[area]
        current_time = self.get_time_of_day()
        
        # Filter available encounters based on conditions
        available_encounters = []
        for enc in table.encounters:
            # Check time conditions
            if enc.conditions:
                if "time" in enc.conditions and enc.conditions["time"] != current_time:
                    continue
                if "requirement" in enc.conditions:
                    # Check special requirements (would need player data)
                    if player_data:
                        requirement = enc.conditions["requirement"]
                        if requirement == "elite_four_defeated" and not player_data.get("elite_four_defeated", False):
                            continue
                        elif requirement == "has_all_badges" and player_data.get("badge_count", 0) < 8:
                            continue
                        # Add more requirement checks as needed
                    else:
                        continue
            
            available_encounters.append(enc)
        
        if not available_encounters:
            return None
        
        # Select encounter based on rarity
        encounter = self._select_by_rarity(available_encounters)
        if not encounter:
            return None
        
        # Generate level
        level = random.randint(encounter.min_level, encounter.max_level)
        
        # Create Pokemon
        try:
            wild_pokemon = create_pokemon_from_species(encounter.species_id, level)
            
            # Check for shiny
            if self._check_shiny(encounter):
                wild_pokemon.is_shiny = True
            
            # Update chain if same species
            if self.chain_species == encounter.species_id:
                self.chain_count += 1
            else:
                self.chain_species = encounter.species_id
                self.chain_count = 1
            
            self.last_encounter_area = area
            
            return wild_pokemon
            
        except ValueError:
            # Species not in POKEMON_DATA, return None
            return None
    
    def _select_by_rarity(self, encounters: List[EncounterData]) -> Optional[EncounterData]:
        """Select an encounter based on rarity weights."""
        # Build weighted list
        weighted_encounters = []
        for enc in encounters:
            weight = self.RARITY_WEIGHTS.get(enc.rarity, 1)
            weighted_encounters.extend([enc] * weight)
        
        if not weighted_encounters:
            return None
        
        return random.choice(weighted_encounters)
    
    def _check_shiny(self, encounter: EncounterData) -> bool:
        """Check if the encountered Pokemon should be shiny."""
        shiny_chance = self.BASE_SHINY_CHANCE * encounter.shiny_boost
        
        # Chain bonus (increases shiny chance)
        if self.chain_count > 0:
            # Shiny charm effect at 40+ chain
            if self.chain_count >= 40:
                shiny_chance *= 3
            elif self.chain_count >= 30:
                shiny_chance *= 2.5
            elif self.chain_count >= 20:
                shiny_chance *= 2
            elif self.chain_count >= 10:
                shiny_chance *= 1.5
        
        return random.random() < shiny_chance
    
    def break_chain(self):
        """Break the current encounter chain."""
        self.chain_species = None
        self.chain_count = 0
    
    def get_chain_info(self) -> Tuple[Optional[int], int]:
        """Get current chain species and count."""
        return self.chain_species, self.chain_count
    
    def get_area_info(self, area: str) -> Optional[Dict]:
        """Get information about Pokemon available in an area."""
        if area not in self.encounter_tables:
            return None
        
        table = self.encounter_tables[area]
        
        # Organize by rarity
        info = {
            "area_name": table.area_name,
            "encounter_rate": table.base_encounter_rate,
            "pokemon_by_rarity": {
                EncounterRarity.COMMON.value: [],
                EncounterRarity.UNCOMMON.value: [],
                EncounterRarity.RARE.value: [],
                EncounterRarity.VERY_RARE.value: [],
                EncounterRarity.LEGENDARY.value: []
            }
        }
        
        for enc in table.encounters:
            pokemon_info = {
                "species_id": enc.species_id,
                "level_range": f"{enc.min_level}-{enc.max_level}",
                "conditions": enc.conditions
            }
            info["pokemon_by_rarity"][enc.rarity.value].append(pokemon_info)
        
        return info


# Special encounter functions for unique situations
def generate_starter_encounter(starter_id: int) -> 'Pokemon':
    """Generate a starter Pokemon with perfect IVs in some stats."""
    # Starters have at least 3 perfect IVs
    perfect_ivs = random.sample(["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"], 3)
    ivs = {}
    for stat in ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
        if stat in perfect_ivs:
            ivs[stat] = 31
        else:
            ivs[stat] = random.randint(0, 31)
    
    return create_pokemon_from_species(starter_id, level=5, ivs=ivs)


def generate_gift_pokemon(species_id: int, level: int, guaranteed_ivs: int = 0) -> 'Pokemon':
    """Generate a gift Pokemon with potentially guaranteed perfect IVs."""
    ivs = {}
    if guaranteed_ivs > 0:
        perfect_stats = random.sample(["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"], 
                                    min(guaranteed_ivs, 6))
        for stat in ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
            if stat in perfect_stats:
                ivs[stat] = 31
            else:
                ivs[stat] = random.randint(0, 31)
    
    return create_pokemon_from_species(species_id, level=level, ivs=ivs)


def generate_legendary_encounter(species_id: int, level: int) -> 'Pokemon':
    """Generate a legendary Pokemon with guaranteed 3 perfect IVs."""
    # Legendaries have at least 3 perfect IVs
    perfect_ivs = random.sample(["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"], 3)
    ivs = {}
    for stat in ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
        if stat in perfect_ivs:
            ivs[stat] = 31
        else:
            ivs[stat] = random.randint(0, 31)
    
    # Legendaries often have specific natures that suit them
    # This could be expanded to prefer certain natures for certain legendaries
    return create_pokemon_from_species(species_id, level=level, ivs=ivs)