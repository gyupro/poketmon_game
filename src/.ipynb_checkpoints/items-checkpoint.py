"""
Items System - Defines all usable items in the game
"""

from enum import Enum
from typing import Dict, Optional, Callable
from .pokemon import Pokemon, StatusCondition


class ItemCategory(Enum):
    """Categories of items."""
    HEALING = "healing"
    STATUS = "status"
    POKEBALL = "pokeball"
    BATTLE = "battle"
    KEY = "key"


class Item:
    """Base class for all items."""
    
    def __init__(self, item_id: str, name: str, description: str, 
                 category: ItemCategory, price: int, 
                 can_use_in_battle: bool = True,
                 can_use_outside_battle: bool = True):
        self.id = item_id
        self.name = name
        self.description = description
        self.category = category
        self.price = price
        self.can_use_in_battle = can_use_in_battle
        self.can_use_outside_battle = can_use_outside_battle
    
    def use(self, target: Optional[Pokemon] = None, **kwargs) -> tuple[bool, str]:
        """Use the item. Returns (success, message)."""
        return False, "This item cannot be used."


class HealingItem(Item):
    """Item that restores HP."""
    
    def __init__(self, item_id: str, name: str, description: str, 
                 price: int, heal_amount: int):
        super().__init__(item_id, name, description, ItemCategory.HEALING, price)
        self.heal_amount = heal_amount
    
    def use(self, target: Optional[Pokemon] = None, **kwargs) -> tuple[bool, str]:
        if not target:
            return False, "No target selected!"
        
        if target.is_fainted:
            return False, f"{target.nickname} has fainted and cannot use this item!"
        
        if target.current_hp >= target.stats["hp"]:
            return False, f"{target.nickname} already has full HP!"
        
        old_hp = target.current_hp
        target.heal(self.heal_amount)
        healed = target.current_hp - old_hp
        
        return True, f"{target.nickname} recovered {healed} HP!"


class StatusHealingItem(Item):
    """Item that cures status conditions."""
    
    def __init__(self, item_id: str, name: str, description: str, 
                 price: int, cures_statuses: list[StatusCondition]):
        super().__init__(item_id, name, description, ItemCategory.STATUS, price)
        self.cures_statuses = cures_statuses
    
    def use(self, target: Optional[Pokemon] = None, **kwargs) -> tuple[bool, str]:
        if not target:
            return False, "No target selected!"
        
        if target.is_fainted:
            return False, f"{target.nickname} has fainted and cannot use this item!"
        
        if StatusCondition.NONE in self.cures_statuses:  # Full heal
            if target.status == StatusCondition.NONE:
                return False, f"{target.nickname} doesn't have any status condition!"
            target.cure_status()
            return True, f"{target.nickname} was cured of all status conditions!"
        
        if target.status in self.cures_statuses:
            status_name = target.status.value
            target.cure_status()
            return True, f"{target.nickname} was cured of {status_name}!"
        
        return False, f"This item won't have any effect on {target.nickname}!"


class ReviveItem(Item):
    """Item that revives fainted Pokemon."""
    
    def __init__(self, item_id: str, name: str, description: str, 
                 price: int, restore_percentage: float):
        super().__init__(item_id, name, description, ItemCategory.HEALING, price,
                        can_use_in_battle=False)
        self.restore_percentage = restore_percentage
    
    def use(self, target: Optional[Pokemon] = None, **kwargs) -> tuple[bool, str]:
        if not target:
            return False, "No target selected!"
        
        if not target.is_fainted:
            return False, f"{target.nickname} hasn't fainted!"
        
        # Revive and restore HP
        target.is_fainted = False
        restore_amount = int(target.stats["hp"] * self.restore_percentage)
        target.current_hp = restore_amount
        
        return True, f"{target.nickname} was revived!"


class PokeballItem(Item):
    """Item for catching Pokemon."""
    
    def __init__(self, item_id: str, name: str, description: str, 
                 price: int, catch_rate_modifier: float):
        super().__init__(item_id, name, description, ItemCategory.POKEBALL, price,
                        can_use_outside_battle=False)
        self.catch_rate_modifier = catch_rate_modifier
    
    def use(self, target: Optional[Pokemon] = None, **kwargs) -> tuple[bool, str]:
        # Catch rate calculation would be handled in the battle system
        return True, f"You used a {self.name}!"


class PPRestoreItem(Item):
    """Item that restores PP to moves."""
    
    def __init__(self, item_id: str, name: str, description: str, 
                 price: int, pp_amount: int, restore_all_moves: bool = False):
        super().__init__(item_id, name, description, ItemCategory.BATTLE, price,
                        can_use_in_battle=False)
        self.pp_amount = pp_amount
        self.restore_all_moves = restore_all_moves
    
    def use(self, target: Optional[Pokemon] = None, **kwargs) -> tuple[bool, str]:
        if not target:
            return False, "No target selected!"
        
        move_index = kwargs.get("move_index", 0)
        
        if self.restore_all_moves:
            for move in target.moves:
                move.restore_pp(self.pp_amount)
            return True, f"All of {target.nickname}'s moves had their PP restored!"
        else:
            if 0 <= move_index < len(target.moves):
                move = target.moves[move_index]
                if move.current_pp >= move.pp:
                    return False, f"{move.name} already has full PP!"
                old_pp = move.current_pp
                move.restore_pp(self.pp_amount)
                restored = move.current_pp - old_pp
                return True, f"{move.name} had {restored} PP restored!"
            return False, "Invalid move selected!"


class BattleStatItem(Item):
    """Item that temporarily boosts stats in battle."""
    
    def __init__(self, item_id: str, name: str, description: str, 
                 price: int, stat: str, stages: int):
        super().__init__(item_id, name, description, ItemCategory.BATTLE, price,
                        can_use_outside_battle=False)
        self.stat = stat
        self.stages = stages
    
    def use(self, target: Optional[Pokemon] = None, **kwargs) -> tuple[bool, str]:
        if not target:
            return False, "No target selected!"
        
        success, message = target.modify_stat_stage(self.stat, self.stages)
        return success, message


# Define all items in the game
ITEM_REGISTRY: Dict[str, Item] = {
    # Healing items
    "potion": HealingItem("potion", "Potion", "Restores 20 HP", 300, 20),
    "super_potion": HealingItem("super_potion", "Super Potion", "Restores 50 HP", 700, 50),
    "hyper_potion": HealingItem("hyper_potion", "Hyper Potion", "Restores 200 HP", 1200, 200),
    "max_potion": HealingItem("max_potion", "Max Potion", "Fully restores HP", 2500, 9999),
    "fresh_water": HealingItem("fresh_water", "Fresh Water", "Restores 50 HP", 200, 50),
    "soda_pop": HealingItem("soda_pop", "Soda Pop", "Restores 60 HP", 300, 60),
    "lemonade": HealingItem("lemonade", "Lemonade", "Restores 80 HP", 350, 80),
    "moomoo_milk": HealingItem("moomoo_milk", "Moomoo Milk", "Restores 100 HP", 500, 100),
    
    # Status healing items
    "antidote": StatusHealingItem("antidote", "Antidote", "Cures poison", 100, 
                                  [StatusCondition.POISONED, StatusCondition.BADLY_POISONED]),
    "burn_heal": StatusHealingItem("burn_heal", "Burn Heal", "Cures burn", 250, 
                                   [StatusCondition.BURNED]),
    "ice_heal": StatusHealingItem("ice_heal", "Ice Heal", "Cures freeze", 250, 
                                  [StatusCondition.FROZEN]),
    "awakening": StatusHealingItem("awakening", "Awakening", "Cures sleep", 250, 
                                   [StatusCondition.ASLEEP]),
    "paralyze_heal": StatusHealingItem("paralyze_heal", "Paralyze Heal", "Cures paralysis", 200, 
                                       [StatusCondition.PARALYZED]),
    "full_heal": StatusHealingItem("full_heal", "Full Heal", "Cures all status problems", 600, 
                                   [StatusCondition.NONE]),  # Special case for all statuses
    "full_restore": HealingItem("full_restore", "Full Restore", "Fully restores HP and status", 3000, 9999),
    
    # Revival items
    "revive": ReviveItem("revive", "Revive", "Revives with half HP", 1500, 0.5),
    "max_revive": ReviveItem("max_revive", "Max Revive", "Revives with full HP", 4000, 1.0),
    
    # Pokeballs
    "pokeball": PokeballItem("pokeball", "Poke Ball", "A basic ball for catching Pokemon", 200, 1.0),
    "great_ball": PokeballItem("great_ball", "Great Ball", "A good ball with higher catch rate", 600, 1.5),
    "ultra_ball": PokeballItem("ultra_ball", "Ultra Ball", "A great ball with high catch rate", 1200, 2.0),
    "master_ball": PokeballItem("master_ball", "Master Ball", "Catches any Pokemon without fail", 0, 255.0),
    
    # PP restoration
    "ether": PPRestoreItem("ether", "Ether", "Restores 10 PP to one move", 1200, 10),
    "max_ether": PPRestoreItem("max_ether", "Max Ether", "Fully restores PP to one move", 2000, 999),
    "elixir": PPRestoreItem("elixir", "Elixir", "Restores 10 PP to all moves", 3000, 10, True),
    "max_elixir": PPRestoreItem("max_elixir", "Max Elixir", "Fully restores PP to all moves", 4500, 999, True),
    
    # Battle stat items
    "x_attack": BattleStatItem("x_attack", "X Attack", "Raises Attack in battle", 500, "attack", 1),
    "x_defense": BattleStatItem("x_defense", "X Defense", "Raises Defense in battle", 550, "defense", 1),
    "x_speed": BattleStatItem("x_speed", "X Speed", "Raises Speed in battle", 350, "speed", 1),
    "x_special": BattleStatItem("x_special", "X Special", "Raises Sp. Attack in battle", 350, "sp_attack", 1),
    "x_sp_def": BattleStatItem("x_sp_def", "X Sp. Def", "Raises Sp. Defense in battle", 350, "sp_defense", 1),
    "x_accuracy": BattleStatItem("x_accuracy", "X Accuracy", "Raises accuracy in battle", 950, "accuracy", 1),
    "dire_hit": BattleStatItem("dire_hit", "Dire Hit", "Raises critical hit ratio", 650, "critical", 1),
}


def get_item(item_id: str) -> Optional[Item]:
    """Get an item by its ID."""
    return ITEM_REGISTRY.get(item_id)