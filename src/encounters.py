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
        
        # Route 1 - Early game route with diverse encounters
        tables["route_1"] = EncounterTable(
            area_name="Route 1",
            base_encounter_rate=12,  # Slightly higher for more encounters
            encounters=[
                # Common Pokemon (50%)
                EncounterData(1, 2, 5, EncounterRarity.COMMON),   # Bulbasaur
                EncounterData(4, 2, 5, EncounterRarity.COMMON),   # Charmander
                EncounterData(7, 2, 5, EncounterRarity.COMMON),   # Squirtle
                
                # Uncommon Pokemon (30%)
                EncounterData(133, 3, 5, EncounterRarity.UNCOMMON),  # Eevee
                EncounterData(25, 3, 5, EncounterRarity.UNCOMMON),   # Pikachu
                
                # Rare Pokemon (15%)
                EncounterData(94, 4, 6, EncounterRarity.RARE),       # Gengar
                EncounterData(143, 4, 6, EncounterRarity.RARE),      # Snorlax
                EncounterData(149, 5, 7, EncounterRarity.RARE),      # Dragonite
                
                # Very Rare Pokemon (4%)
                EncounterData(151, 8, 10, EncounterRarity.VERY_RARE, shiny_boost=3.0),  # Mew (triple shiny chance)
                EncounterData(6, 10, 15, EncounterRarity.VERY_RARE),  # Charizard
            ]
        )
        
        # Viridian Forest
        tables["viridian_forest"] = EncounterTable(
            area_name="Viridian Forest",
            base_encounter_rate=15,
            encounters=[
                # Common Pokemon
                EncounterData(1, 3, 6, EncounterRarity.COMMON),   # Bulbasaur
                EncounterData(25, 3, 6, EncounterRarity.COMMON),  # Pikachu
                
                # Uncommon Pokemon
                EncounterData(4, 4, 7, EncounterRarity.UNCOMMON),   # Charmander
                EncounterData(7, 4, 7, EncounterRarity.UNCOMMON),   # Squirtle
                
                # Rare finds
                EncounterData(133, 5, 8, EncounterRarity.RARE),     # Eevee
                EncounterData(6, 10, 12, EncounterRarity.VERY_RARE) # Charizard
            ]
        )
        
        # Mt. Moon
        tables["mt_moon"] = EncounterTable(
            area_name="Mt. Moon",
            base_encounter_rate=12,
            encounters=[
                # Cave Pokemon
                EncounterData(94, 8, 12, EncounterRarity.COMMON),   # Gengar
                EncounterData(25, 7, 10, EncounterRarity.COMMON),   # Pikachu
                EncounterData(133, 8, 12, EncounterRarity.UNCOMMON), # Eevee
                EncounterData(143, 10, 15, EncounterRarity.RARE),   # Snorlax
                
                # Very rare
                EncounterData(151, 12, 15, EncounterRarity.VERY_RARE),  # Mew
            ]
        )
        
        # Route 25 (Bill's area)
        tables["route_25"] = EncounterTable(
            area_name="Route 25",
            base_encounter_rate=10,
            encounters=[
                EncounterData(16, 10, 14, EncounterRarity.COMMON),  # Pidgey
                EncounterData(43, 12, 16, EncounterRarity.COMMON),  # Oddish (night)
                EncounterData(69, 12, 16, EncounterRarity.COMMON),  # Bellsprout (day)
                EncounterData(63, 10, 15, EncounterRarity.UNCOMMON),  # Abra
                EncounterData(17, 15, 17, EncounterRarity.RARE),  # Pidgeotto
                EncounterData(132, 15, 15, EncounterRarity.VERY_RARE),  # Ditto
            ]
        )
        
        # Cerulean Cave - End game area
        tables["cerulean_cave"] = EncounterTable(
            area_name="Cerulean Cave",
            base_encounter_rate=15,
            encounters=[
                # High level Pokemon
                EncounterData(94, 46, 55, EncounterRarity.COMMON),   # Gengar
                EncounterData(6, 46, 52, EncounterRarity.COMMON),    # Charizard
                EncounterData(149, 49, 56, EncounterRarity.UNCOMMON), # Dragonite
                EncounterData(143, 50, 58, EncounterRarity.UNCOMMON), # Snorlax
                
                # Legendary Birds
                EncounterData(144, 60, 60, EncounterRarity.RARE),     # Articuno
                EncounterData(145, 60, 60, EncounterRarity.RARE),     # Zapdos
                EncounterData(146, 60, 60, EncounterRarity.RARE),     # Moltres
                
                # Legendary Pokemon (special conditions)
                EncounterData(150, 70, 70, EncounterRarity.LEGENDARY,
                            {"requirement": "elite_four_defeated"}),  # Mewtwo
                EncounterData(151, 70, 70, EncounterRarity.LEGENDARY,
                            {"requirement": "mewtwo_defeated"}),  # Mew
            ]
        )
        
        # Safari Zone
        tables["safari_zone"] = EncounterTable(
            area_name="Safari Zone",
            base_encounter_rate=20,
            encounters=[
                # Unique Safari Zone Pokemon
                EncounterData(111, 20, 27, EncounterRarity.COMMON),  # Rhyhorn
                EncounterData(84, 22, 26, EncounterRarity.COMMON),  # Doduo
                EncounterData(102, 22, 27, EncounterRarity.COMMON),  # Exeggcute
                EncounterData(113, 25, 25, EncounterRarity.UNCOMMON),  # Chansey
                EncounterData(115, 25, 30, EncounterRarity.UNCOMMON),  # Kangaskhan
                EncounterData(123, 25, 28, EncounterRarity.RARE),  # Scyther
                EncounterData(127, 25, 28, EncounterRarity.RARE),  # Pinsir
                EncounterData(128, 28, 30, EncounterRarity.VERY_RARE),  # Tauros
            ]
        )
        
        # Victory Road
        tables["victory_road"] = EncounterTable(
            area_name="Victory Road",
            base_encounter_rate=10,
            encounters=[
                EncounterData(74, 40, 44, EncounterRarity.COMMON),  # Geodude
                EncounterData(75, 42, 46, EncounterRarity.COMMON),  # Graveler
                EncounterData(95, 40, 46, EncounterRarity.UNCOMMON),  # Onix
                EncounterData(66, 40, 45, EncounterRarity.UNCOMMON),  # Machop
                EncounterData(67, 42, 47, EncounterRarity.RARE),  # Machoke
                EncounterData(68, 46, 50, EncounterRarity.VERY_RARE),  # Machamp
                
                # Legendary bird (special condition)
                EncounterData(146, 50, 50, EncounterRarity.LEGENDARY,
                            {"requirement": "has_all_badges"}),  # Moltres
            ]
        )
        
        # Power Plant - Electric type haven
        tables["power_plant"] = EncounterTable(
            area_name="Power Plant",
            base_encounter_rate=12,
            encounters=[
                EncounterData(25, 22, 26, EncounterRarity.COMMON),  # Pikachu
                EncounterData(81, 25, 29, EncounterRarity.COMMON),  # Magnemite
                EncounterData(100, 25, 30, EncounterRarity.UNCOMMON),  # Voltorb
                EncounterData(82, 30, 35, EncounterRarity.UNCOMMON),  # Magneton
                EncounterData(26, 32, 35, EncounterRarity.RARE),  # Raichu
                EncounterData(101, 33, 38, EncounterRarity.RARE),  # Electrode
                EncounterData(125, 35, 40, EncounterRarity.VERY_RARE),  # Electabuzz
                
                # Legendary bird
                EncounterData(145, 50, 50, EncounterRarity.LEGENDARY,
                            {"requirement": "power_restored"}),  # Zapdos
            ]
        )
        
        # Seafoam Islands
        tables["seafoam_islands"] = EncounterTable(
            area_name="Seafoam Islands",
            base_encounter_rate=10,
            encounters=[
                EncounterData(86, 28, 32, EncounterRarity.COMMON),  # Seel
                EncounterData(90, 28, 33, EncounterRarity.COMMON),  # Shellder
                EncounterData(54, 30, 35, EncounterRarity.UNCOMMON),  # Psyduck
                EncounterData(79, 30, 35, EncounterRarity.UNCOMMON),  # Slowpoke
                EncounterData(87, 34, 38, EncounterRarity.RARE),  # Dewgong
                EncounterData(91, 34, 38, EncounterRarity.RARE),  # Cloyster
                EncounterData(131, 35, 40, EncounterRarity.VERY_RARE),  # Lapras
                
                # Legendary bird
                EncounterData(144, 50, 50, EncounterRarity.LEGENDARY,
                            {"requirement": "boulders_moved"}),  # Articuno
            ]
        )
        
        # Special area for Mew
        tables["faraway_island"] = EncounterTable(
            area_name="Faraway Island",
            base_encounter_rate=5,
            encounters=[
                EncounterData(151, 30, 30, EncounterRarity.LEGENDARY,
                            {"requirement": "special_ticket"}),  # Mew
            ]
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