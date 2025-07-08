"""
Battle System - Comprehensive Pokemon battle mechanics
"""

import random
import math
from typing import Optional, List, Tuple, Dict, Union
from enum import Enum
from .pokemon import Pokemon, StatusCondition, Move, PokemonType
from .items import Item, PokeballItem, get_item
from .player import Player


class BattleType(Enum):
    """Types of battles."""
    WILD = "wild"
    TRAINER = "trainer"
    GYM_LEADER = "gym_leader"
    ELITE_FOUR = "elite_four"
    CHAMPION = "champion"


class BattleAction(Enum):
    """Actions that can be taken in battle."""
    FIGHT = "fight"
    BAG = "bag"
    POKEMON = "pokemon"
    RUN = "run"


class BattleState(Enum):
    """Current state of the battle."""
    SELECTING_ACTION = "selecting_action"
    SELECTING_MOVE = "selecting_move"
    SELECTING_TARGET = "selecting_target"
    SELECTING_ITEM = "selecting_item"
    SELECTING_POKEMON = "selecting_pokemon"
    TURN_EXECUTION = "turn_execution"
    BATTLE_END = "battle_end"


class TurnAction:
    """Represents an action to be taken during a turn."""
    
    def __init__(self, action_type: str, user: Pokemon, priority: int = 0, **kwargs):
        self.action_type = action_type
        self.user = user
        self.priority = priority
        self.kwargs = kwargs
    
    def get_effective_priority(self) -> Tuple[int, int]:
        """Get effective priority for turn order (priority, speed)."""
        speed = self.user.get_modified_stat("speed") if self.user else 0
        return (self.priority, speed)


class Trainer:
    """Represents an AI trainer in battle."""
    
    def __init__(self, name: str, pokemon_team: List[Pokemon], 
                 trainer_class: str = "Trainer", prize_money: int = 100,
                 ai_level: int = 1):
        self.name = name
        self.trainer_class = trainer_class
        self.pokemon_team = pokemon_team
        self.active_pokemon = pokemon_team[0] if pokemon_team else None
        self.prize_money = prize_money
        self.ai_level = ai_level  # 1-5, higher is smarter
        self.items = {}  # Trainer inventory
    
    def get_first_healthy_pokemon(self) -> Optional[Pokemon]:
        """Get the first non-fainted Pokemon."""
        for pokemon in self.pokemon_team:
            if not pokemon.is_fainted:
                return pokemon
        return None
    
    def switch_pokemon(self, index: int) -> bool:
        """Switch to Pokemon at given index."""
        if 0 <= index < len(self.pokemon_team):
            pokemon = self.pokemon_team[index]
            if not pokemon.is_fainted and pokemon != self.active_pokemon:
                self.active_pokemon = pokemon
                return True
        return False
    
    def can_battle(self) -> bool:
        """Check if trainer has any Pokemon that can battle."""
        return any(not p.is_fainted for p in self.pokemon_team)


class Battle:
    """Comprehensive Pokemon battle system."""
    
    def __init__(self, player: Player, opponent: Union[Pokemon, Trainer], 
                 battle_type: BattleType = BattleType.WILD,
                 can_catch: bool = True, can_run: bool = True):
        self.player = player
        self.player_pokemon = player.active_pokemon
        
        # Handle different opponent types
        if isinstance(opponent, Pokemon):
            self.opponent = None
            self.opponent_pokemon = opponent
            self.battle_type = BattleType.WILD
        else:
            self.opponent = opponent
            self.opponent_pokemon = opponent.active_pokemon
            self.battle_type = battle_type
        
        self.can_catch = can_catch and self.battle_type == BattleType.WILD
        self.can_run = can_run
        
        # Battle state
        self.turn = 0
        self.battle_log: List[str] = []
        self.is_over = False
        self.winner = None
        self.state = BattleState.SELECTING_ACTION
        
        # Turn tracking
        self.player_action: Optional[TurnAction] = None
        self.opponent_action: Optional[TurnAction] = None
        
        # Battle effects
        self.weather = None  # Current weather condition
        self.weather_turns = 0
        self.terrain = None  # Current terrain
        self.terrain_turns = 0
        self.trick_room_turns = 0  # Reverses speed priority
        
        # Move tracking
        self.last_used_move: Optional[Move] = None
        self.consecutive_move_count = 0
        
        # Catch tracking
        self.catch_attempts = 0
        self.shake_count = 0
    
    def start(self):
        """Initialize the battle."""
        self.add_to_log(f"Battle started!")
        
        if self.battle_type == BattleType.WILD:
            self.add_to_log(f"A wild {self.opponent_pokemon.species_name} appeared!")
        else:
            self.add_to_log(f"{self.opponent.trainer_class} {self.opponent.name} wants to battle!")
            self.add_to_log(f"{self.opponent.name} sent out {self.opponent_pokemon.species_name}!")
        
        self.add_to_log(f"Go! {self.player_pokemon.nickname}!")
        self.add_to_log("")
    
    def add_to_log(self, message: str):
        """Add message to battle log."""
        self.battle_log.append(message)
    
    def get_valid_actions(self) -> List[BattleAction]:
        """Get list of valid actions for current state."""
        actions = [BattleAction.FIGHT]
        
        # Check if player has usable items
        if any(count > 0 for count in self.player.inventory.values()):
            actions.append(BattleAction.BAG)
        
        # Check if player can switch Pokemon
        if any(p != self.player_pokemon and not p.is_fainted 
               for p in self.player.pokemon_team):
            actions.append(BattleAction.POKEMON)
        
        # Can only run from wild battles
        if self.can_run and self.battle_type == BattleType.WILD:
            actions.append(BattleAction.RUN)
        
        return actions
    
    def get_valid_moves(self) -> List[Tuple[int, Move]]:
        """Get list of valid moves for the active Pokemon."""
        valid_moves = []
        for i, move in enumerate(self.player_pokemon.moves):
            if move.current_pp > 0:
                valid_moves.append((i, move))
        return valid_moves
    
    def get_switchable_pokemon(self) -> List[Tuple[int, Pokemon]]:
        """Get list of Pokemon that can be switched to."""
        switchable = []
        for i, pokemon in enumerate(self.player.pokemon_team):
            if pokemon != self.player_pokemon and not pokemon.is_fainted:
                switchable.append((i, pokemon))
        return switchable
    
    def set_player_action(self, action_type: BattleAction, **kwargs) -> bool:
        """Set the player's action for this turn."""
        if self.is_over:
            return False
        
        if action_type == BattleAction.FIGHT:
            move_index = kwargs.get("move_index")
            if move_index is None:
                return False
            move = self.player_pokemon.moves[move_index]
            self.player_action = TurnAction(
                "move", self.player_pokemon, 
                priority=move.priority, 
                move_index=move_index
            )
        
        elif action_type == BattleAction.BAG:
            item_id = kwargs.get("item_id")
            target_index = kwargs.get("target_index", 0)
            if not item_id or item_id not in self.player.inventory:
                return False
            self.player_action = TurnAction(
                "item", self.player_pokemon,
                priority=6,  # Items have high priority
                item_id=item_id,
                target_index=target_index
            )
        
        elif action_type == BattleAction.POKEMON:
            switch_index = kwargs.get("switch_index")
            if switch_index is None:
                return False
            self.player_action = TurnAction(
                "switch", self.player_pokemon,
                priority=6,  # Switching has high priority
                switch_index=switch_index
            )
        
        elif action_type == BattleAction.RUN:
            self.player_action = TurnAction(
                "run", self.player_pokemon,
                priority=6  # Running has high priority
            )
        
        else:
            return False
        
        # Get opponent action
        self._get_opponent_action()
        
        # Execute turn
        self._execute_turn()
        return True
    
    def _get_opponent_action(self):
        """Determine opponent's action using AI."""
        if self.battle_type == BattleType.WILD:
            # Wild Pokemon just attack
            self.opponent_action = self._get_wild_pokemon_move()
        else:
            # Trainer AI
            self.opponent_action = self._get_trainer_action()
    
    def _get_wild_pokemon_move(self) -> TurnAction:
        """Get move for wild Pokemon (simple AI)."""
        valid_moves = [(i, m) for i, m in enumerate(self.opponent_pokemon.moves) 
                       if m.current_pp > 0]
        
        if not valid_moves:
            # Struggle if no PP
            return TurnAction("struggle", self.opponent_pokemon)
        
        # Random move selection for wild Pokemon
        move_index, move = random.choice(valid_moves)
        return TurnAction(
            "move", self.opponent_pokemon,
            priority=move.priority,
            move_index=move_index
        )
    
    def _get_trainer_action(self) -> TurnAction:
        """Get action for trainer using AI based on level."""
        ai_level = self.opponent.ai_level
        
        # Check if should switch Pokemon
        if self._should_trainer_switch():
            best_switch = self._get_best_switch()
            if best_switch is not None:
                return TurnAction(
                    "switch", self.opponent_pokemon,
                    priority=6,
                    switch_index=best_switch
                )
        
        # Check if should use item
        if ai_level >= 3 and self._should_trainer_use_item():
            item_action = self._get_best_item_use()
            if item_action:
                return item_action
        
        # Otherwise, select a move
        return self._get_trainer_move()
    
    def _should_trainer_switch(self) -> bool:
        """Determine if trainer should switch Pokemon."""
        if not self.opponent or self.opponent.ai_level < 2:
            return False
        
        # Don't switch if this is the last Pokemon
        healthy_count = sum(1 for p in self.opponent.pokemon_team if not p.is_fainted)
        if healthy_count <= 1:
            return False
        
        current = self.opponent_pokemon
        player = self.player_pokemon
        
        # Switch if current Pokemon has bad type matchup
        effectiveness = self._calculate_type_matchup(player.types, current.types)
        if effectiveness >= 2.0 and current.current_hp > current.stats["hp"] * 0.5:
            return random.random() < 0.7  # 70% chance to switch
        
        # Switch if current Pokemon is at low HP and not faster
        if (current.current_hp < current.stats["hp"] * 0.25 and 
            current.get_modified_stat("speed") < player.get_modified_stat("speed")):
            return random.random() < 0.8  # 80% chance to switch
        
        return False
    
    def _get_best_switch(self) -> Optional[int]:
        """Get the best Pokemon to switch to."""
        if not self.opponent:
            return None
        
        player = self.player_pokemon
        best_score = -999
        best_index = None
        
        for i, pokemon in enumerate(self.opponent.pokemon_team):
            if pokemon.is_fainted or pokemon == self.opponent_pokemon:
                continue
            
            # Calculate switch score
            score = 0
            
            # Type effectiveness
            effectiveness = self._calculate_type_matchup(pokemon.types, player.types)
            score += (2 - effectiveness) * 50  # Favor good defensive matchups
            
            # HP percentage
            hp_percent = pokemon.current_hp / pokemon.stats["hp"]
            score += hp_percent * 30
            
            # Speed advantage
            if pokemon.get_modified_stat("speed") > player.get_modified_stat("speed"):
                score += 20
            
            # Status condition penalty
            if pokemon.status != StatusCondition.NONE:
                score -= 15
            
            if score > best_score:
                best_score = score
                best_index = i
        
        return best_index
    
    def _should_trainer_use_item(self) -> bool:
        """Determine if trainer should use an item."""
        # Simplified - trainers don't use items in this implementation
        # Could be expanded to include item usage
        return False
    
    def _get_trainer_move(self) -> TurnAction:
        """Select best move for trainer's Pokemon."""
        ai_level = self.opponent.ai_level if self.opponent else 1
        opp_pokemon = self.opponent_pokemon
        player_pokemon = self.player_pokemon
        
        valid_moves = [(i, m) for i, m in enumerate(opp_pokemon.moves) 
                       if m.current_pp > 0]
        
        if not valid_moves:
            return TurnAction("struggle", opp_pokemon)
        
        if ai_level == 1:
            # Level 1: Random moves
            move_index, move = random.choice(valid_moves)
            return TurnAction("move", opp_pokemon, priority=move.priority, move_index=move_index)
        
        # Level 2+: Smarter move selection
        best_score = -999
        best_move_index = 0
        best_move = valid_moves[0][1]
        
        for move_index, move in valid_moves:
            score = 0
            
            # Base power
            if move.category != "status":
                score += move.power
                
                # Type effectiveness
                effectiveness = opp_pokemon.get_type_effectiveness(move.type, player_pokemon.types)
                score *= effectiveness
                
                # STAB bonus
                if move.type in opp_pokemon.types:
                    score *= 1.5
                
                # Category matchup
                if move.category == "physical":
                    attack_ratio = opp_pokemon.get_modified_stat("attack") / player_pokemon.get_modified_stat("defense")
                else:
                    attack_ratio = opp_pokemon.get_modified_stat("sp_attack") / player_pokemon.get_modified_stat("sp_defense")
                score *= attack_ratio
            
            # Status moves
            else:
                # Prioritize status moves when appropriate
                if move.effect == "paralysis" and player_pokemon.status == StatusCondition.NONE:
                    score += 60
                elif move.effect == "sleep" and player_pokemon.status == StatusCondition.NONE:
                    score += 80
                elif move.effect == "burn" and player_pokemon.status == StatusCondition.NONE:
                    score += 50
                elif move.effect and "raise" in move.effect:
                    # Extract stat name from effect
                    stat_parts = move.effect.split("_")
                    if len(stat_parts) >= 2:
                        stat_name = "_".join(stat_parts[1:])
                        if stat_name in opp_pokemon.stat_stages and opp_pokemon.stat_stages[stat_name] < 2:
                            score += 40
                effectiveness = 1.0  # Status moves have neutral effectiveness
            
            # AI level adjustments
            if ai_level >= 3:
                # Consider accuracy
                score *= (move.accuracy / 100)
                
                # Avoid ineffective moves
                if move.category != "status" and effectiveness == 0:
                    score = -1000
            
            if ai_level >= 4:
                # Consider HP thresholds
                opp_hp_percent = opp_pokemon.current_hp / opp_pokemon.stats["hp"]
                player_hp_percent = player_pokemon.current_hp / player_pokemon.stats["hp"]
                
                # Prioritize finishing moves
                if move.category != "status":
                    estimated_damage = self._estimate_damage(move, opp_pokemon, player_pokemon)
                    if estimated_damage >= player_pokemon.current_hp:
                        score += 100
                
                # Use setup moves when safe
                if opp_hp_percent > 0.7 and player_hp_percent < 0.3:
                    if move.effect and "raise" in move.effect:
                        score += 50
            
            if score > best_score:
                best_score = score
                best_move_index = move_index
                best_move = move
        
        return TurnAction("move", opp_pokemon, priority=best_move.priority, move_index=best_move_index)
    
    def _estimate_damage(self, move: Move, attacker: Pokemon, defender: Pokemon) -> int:
        """Estimate damage for AI calculations."""
        if move.category == "status":
            return 0
        
        # Simplified damage calculation for AI
        if move.category == "physical":
            attack = attacker.get_modified_stat("attack")
            defense = defender.get_modified_stat("defense")
        else:
            attack = attacker.get_modified_stat("sp_attack")
            defense = defender.get_modified_stat("sp_defense")
        
        damage = ((2 * attacker.level + 10) / 250) * (attack / defense) * move.power + 2
        
        # Type effectiveness
        effectiveness = attacker.get_type_effectiveness(move.type, defender.types)
        damage *= effectiveness
        
        # STAB
        if move.type in attacker.types:
            damage *= 1.5
        
        return int(damage * 0.9)  # Average roll
    
    def _calculate_type_matchup(self, attacker_types: List[PokemonType], 
                                defender_types: List[PokemonType]) -> float:
        """Calculate overall type matchup advantage."""
        total_effectiveness = 0
        count = 0
        
        for att_type in attacker_types:
            for def_type in defender_types:
                effectiveness = 1.0
                # This is simplified - would need full type chart
                total_effectiveness += effectiveness
                count += 1
        
        return total_effectiveness / count if count > 0 else 1.0
    
    def _execute_turn(self):
        """Execute the turn with both actions."""
        self.turn += 1
        turn_actions = []
        
        # Collect actions
        if self.player_action:
            turn_actions.append(("player", self.player_action))
        if self.opponent_action:
            turn_actions.append(("opponent", self.opponent_action))
        
        # Sort by priority and speed
        turn_actions.sort(key=lambda x: x[1].get_effective_priority(), reverse=True)
        
        # Apply trick room effect
        if self.trick_room_turns > 0:
            # Reverse speed order within same priority
            # This is simplified - would need more complex sorting
            pass
        
        # Execute actions in order
        for actor, action in turn_actions:
            if self.is_over:
                break
            
            if action.action_type == "move":
                self._execute_move(actor, action)
            elif action.action_type == "item":
                self._execute_item(actor, action)
            elif action.action_type == "switch":
                self._execute_switch(actor, action)
            elif action.action_type == "run":
                self._execute_run(actor, action)
            elif action.action_type == "struggle":
                self._execute_struggle(actor, action)
        
        # End of turn effects
        if not self.is_over:
            self._process_end_of_turn()
        
        # Reset actions
        self.player_action = None
        self.opponent_action = None
    
    def _execute_move(self, actor: str, action: TurnAction):
        """Execute a move action."""
        attacker = self.player_pokemon if actor == "player" else self.opponent_pokemon
        defender = self.opponent_pokemon if actor == "player" else self.player_pokemon
        
        # Check if attacker can move
        can_move, status_events = attacker.process_status()
        for event in status_events:
            self.add_to_log(event)
        
        if not can_move:
            return
        
        # Check flinch
        if attacker.status == StatusCondition.FLINCHED:
            self.add_to_log(f"{attacker.nickname} flinched and couldn't move!")
            attacker.status = StatusCondition.NONE  # Flinch only lasts one turn
            return
        
        # Get and use move
        move_index = action.kwargs["move_index"]
        move = attacker.moves[move_index]
        
        if not move.use():
            self.add_to_log(f"{attacker.nickname} has no PP left for {move.name}!")
            return
        
        self.add_to_log(f"{attacker.nickname} used {move.name}!")
        
        # Calculate hit/miss
        accuracy = move.accuracy
        if accuracy < 999:  # 999 means always hits
            accuracy *= attacker.get_accuracy_multiplier()
            accuracy *= defender.get_evasion_multiplier()
            
            if random.randint(1, 100) > accuracy:
                self.add_to_log("But it missed!")
                return
        
        # Execute move effect
        if move.category == "status":
            self._execute_status_move(attacker, defender, move)
        else:
            self._execute_damage_move(attacker, defender, move)
        
        # Track last move
        self.last_used_move = move
        if move == self.last_used_move:
            self.consecutive_move_count += 1
        else:
            self.consecutive_move_count = 1
    
    def _execute_damage_move(self, attacker: Pokemon, defender: Pokemon, move: Move):
        """Execute a damaging move."""
        # Calculate damage
        damage, effectiveness, events = attacker.calculate_damage(move, defender)
        
        # Apply damage
        if damage > 0:
            for event in events:
                self.add_to_log(event)
            
            damage_events = defender.take_damage(damage)
            self.add_to_log(f"{defender.nickname} took {damage} damage!")
            
            for event in damage_events:
                self.add_to_log(event)
            
            # Check for additional effects
            if move.effect and move.effect_chance > 0:
                if random.randint(1, 100) <= move.effect_chance:
                    self._apply_move_effect(move.effect, attacker, defender)
            
            # Check if defender fainted
            if defender.is_fainted:
                self._handle_faint(defender, attacker)
    
    def _execute_status_move(self, attacker: Pokemon, defender: Pokemon, move: Move):
        """Execute a status move."""
        if move.effect:
            self._apply_move_effect(move.effect, attacker, defender)
        else:
            self.add_to_log("But nothing happened!")
    
    def _apply_move_effect(self, effect: str, attacker: Pokemon, target: Pokemon):
        """Apply a move's additional effect."""
        if effect == "paralysis":
            if target.apply_status(StatusCondition.PARALYZED):
                self.add_to_log(f"{target.nickname} was paralyzed!")
            else:
                self.add_to_log(f"{target.nickname} is already affected by a status condition!")
        
        elif effect == "burn":
            if target.apply_status(StatusCondition.BURNED):
                self.add_to_log(f"{target.nickname} was burned!")
        
        elif effect == "freeze":
            if target.apply_status(StatusCondition.FROZEN):
                self.add_to_log(f"{target.nickname} was frozen solid!")
        
        elif effect == "poison":
            if target.apply_status(StatusCondition.POISONED):
                self.add_to_log(f"{target.nickname} was poisoned!")
        
        elif effect == "sleep":
            if target.apply_status(StatusCondition.ASLEEP):
                self.add_to_log(f"{target.nickname} fell asleep!")
        
        elif effect == "confusion":
            if target.confusion_turns == 0:
                target.confusion_turns = random.randint(1, 4)
                self.add_to_log(f"{target.nickname} became confused!")
        
        elif effect == "flinch":
            target.status = StatusCondition.FLINCHED
        
        elif effect == "lower_attack":
            success, message = target.modify_stat_stage("attack", -1)
            if success:
                self.add_to_log(message)
        
        elif effect == "lower_defense":
            success, message = target.modify_stat_stage("defense", -1)
            if success:
                self.add_to_log(message)
        
        elif effect == "lower_speed":
            success, message = target.modify_stat_stage("speed", -1)
            if success:
                self.add_to_log(message)
        
        elif effect == "lower_sp_attack":
            success, message = target.modify_stat_stage("sp_attack", -1)
            if success:
                self.add_to_log(message)
        
        elif effect == "lower_sp_defense":
            success, message = target.modify_stat_stage("sp_defense", -1)
            if success:
                self.add_to_log(message)
        
        elif effect == "lower_accuracy":
            success, message = target.modify_stat_stage("accuracy", -1)
            if success:
                self.add_to_log(message)
        
        elif effect == "lower_evasion":
            success, message = target.modify_stat_stage("evasion", -1)
            if success:
                self.add_to_log(message)
        
        elif effect == "raise_attack":
            success, message = attacker.modify_stat_stage("attack", 1)
            if success:
                self.add_to_log(message)
        
        elif effect == "raise_defense":
            success, message = attacker.modify_stat_stage("defense", 1)
            if success:
                self.add_to_log(message)
        
        elif effect == "raise_speed":
            success, message = attacker.modify_stat_stage("speed", 1)
            if success:
                self.add_to_log(message)
        
        elif effect == "raise_sp_attack":
            success, message = attacker.modify_stat_stage("sp_attack", 1)
            if success:
                self.add_to_log(message)
        
        elif effect == "raise_sp_defense":
            success, message = attacker.modify_stat_stage("sp_defense", 1)
            if success:
                self.add_to_log(message)
        
        elif effect == "raise_defense_sharply":
            success, message = attacker.modify_stat_stage("defense", 2)
            if success:
                self.add_to_log(message)
        
        elif effect == "raise_sp_attack_sharply":
            success, message = attacker.modify_stat_stage("sp_attack", 2)
            if success:
                self.add_to_log(message)
        
        elif effect == "raise_sp_defense_sharply":
            success, message = attacker.modify_stat_stage("sp_defense", 2)
            if success:
                self.add_to_log(message)
        
        elif effect == "raise_speed_sharply":
            success, message = attacker.modify_stat_stage("speed", 2)
            if success:
                self.add_to_log(message)
        
        elif effect == "dragon_dance":
            success1, message1 = attacker.modify_stat_stage("attack", 1)
            success2, message2 = attacker.modify_stat_stage("speed", 1)
            if success1:
                self.add_to_log(message1)
            if success2:
                self.add_to_log(message2)
        
        elif effect == "shell_smash":
            # Lower defenses
            attacker.modify_stat_stage("defense", -1)
            attacker.modify_stat_stage("sp_defense", -1)
            # Raise offenses and speed
            success1, message1 = attacker.modify_stat_stage("attack", 2)
            success2, message2 = attacker.modify_stat_stage("sp_attack", 2)
            success3, message3 = attacker.modify_stat_stage("speed", 2)
            if success1 or success2 or success3:
                self.add_to_log(f"{attacker.nickname} broke its shell!")
        
        elif effect == "heal":
            amount = attacker.stats["hp"] // 2
            if attacker.heal(amount):
                self.add_to_log(f"{attacker.nickname} restored its HP!")
        
        elif effect == "weather_rain":
            self.weather = "rain"
            self.weather_turns = 5
            self.add_to_log("It started to rain!")
        
        elif effect == "weather_sun":
            self.weather = "sun"
            self.weather_turns = 5
            self.add_to_log("The sunlight turned harsh!")
        
        elif effect == "weather_hail":
            self.weather = "hail"
            self.weather_turns = 5
            self.add_to_log("It started to hail!")
    
    def _execute_item(self, actor: str, action: TurnAction):
        """Execute an item use."""
        item_id = action.kwargs["item_id"]
        target_index = action.kwargs.get("target_index", 0)
        
        if actor == "player":
            item = get_item(item_id)
            if not item:
                return
            
            # Handle different item types
            if isinstance(item, PokeballItem) and self.can_catch:
                self._attempt_catch(item)
            else:
                # Use item on Pokemon
                target = self.player.pokemon_team[target_index]
                success, message = item.use(target)
                if success:
                    self.player.inventory[item_id] -= 1
                    self.add_to_log(message)
                else:
                    self.add_to_log(f"The {item.name} won't have any effect!")
    
    def _attempt_catch(self, pokeball: PokeballItem):
        """Attempt to catch a wild Pokemon."""
        if self.battle_type != BattleType.WILD:
            self.add_to_log("You can't catch a trainer's Pokemon!")
            return
        
        self.add_to_log(f"You used a {pokeball.name}!")
        self.player.inventory[pokeball.id] -= 1
        
        # Calculate catch rate
        target = self.opponent_pokemon
        max_hp = target.stats["hp"]
        current_hp = target.current_hp
        catch_rate = 45  # Base catch rate (would come from species data)
        
        # Status bonus
        status_bonus = 1.0
        if target.status in [StatusCondition.ASLEEP, StatusCondition.FROZEN]:
            status_bonus = 2.0
        elif target.status in [StatusCondition.PARALYZED, StatusCondition.BURNED, 
                               StatusCondition.POISONED, StatusCondition.BADLY_POISONED]:
            status_bonus = 1.5
        
        # Calculate modified catch rate
        modified_rate = (((3 * max_hp - 2 * current_hp) * catch_rate * pokeball.catch_rate_modifier * status_bonus) / (3 * max_hp))
        
        # Master Ball always catches
        if pokeball.catch_rate_modifier >= 255:
            self._catch_success()
            return
        
        # Shake checks (4 shakes = catch)
        shake_probability = 65536 / (255 / modified_rate) ** 0.1875
        
        self.shake_count = 0
        for i in range(4):
            if random.randint(0, 65535) < shake_probability:
                self.shake_count += 1
                if i < 3:
                    self.add_to_log("*shake*")
            else:
                break
        
        if self.shake_count >= 4:
            self._catch_success()
        else:
            self.add_to_log(f"Oh no! The Pokemon broke free!")
            if self.shake_count == 0:
                self.add_to_log("It didn't even shake!")
            elif self.shake_count == 1:
                self.add_to_log("It appeared to be caught!")
            elif self.shake_count == 2:
                self.add_to_log("Aargh! Almost had it!")
            elif self.shake_count == 3:
                self.add_to_log("Shoot! It was so close, too!")
    
    def _catch_success(self):
        """Handle successful Pokemon catch."""
        self.add_to_log(f"Gotcha! {self.opponent_pokemon.species_name} was caught!")
        
        # Add to player's team or PC
        if len(self.player.pokemon_team) < 6:
            self.player.add_pokemon(self.opponent_pokemon)
            self.add_to_log(f"{self.opponent_pokemon.species_name} was added to your party!")
        else:
            self.add_to_log(f"{self.opponent_pokemon.species_name} was sent to the PC!")
        
        self.end_battle("player")
    
    def _execute_switch(self, actor: str, action: TurnAction):
        """Execute a Pokemon switch."""
        switch_index = action.kwargs["switch_index"]
        
        if actor == "player":
            old_pokemon = self.player_pokemon
            if self.player.switch_active_pokemon(switch_index):
                self.player_pokemon = self.player.active_pokemon
                self.add_to_log(f"Come back, {old_pokemon.nickname}!")
                self.add_to_log(f"Go! {self.player_pokemon.nickname}!")
                # Reset stat stages
                old_pokemon.reset_stat_stages()
        else:
            if self.opponent and self.opponent.switch_pokemon(switch_index):
                old_pokemon = self.opponent_pokemon
                self.opponent_pokemon = self.opponent.active_pokemon
                self.add_to_log(f"{self.opponent.name} withdrew {old_pokemon.species_name}!")
                self.add_to_log(f"{self.opponent.name} sent out {self.opponent_pokemon.species_name}!")
                # Reset stat stages
                old_pokemon.reset_stat_stages()
    
    def _execute_run(self, actor: str, action: TurnAction):
        """Execute run attempt."""
        if actor == "player" and self.can_run:
            # Run calculation
            player_speed = self.player_pokemon.get_modified_stat("speed")
            opponent_speed = self.opponent_pokemon.get_modified_stat("speed")
            
            # Formula: (Player Speed * 32) / (Opponent Speed / 4) % 256 + 30 * attempts
            escape_chance = ((player_speed * 32) // (opponent_speed // 4)) % 256 + 30 * (self.turn - 1)
            
            if escape_chance >= 256 or random.randint(0, 255) < escape_chance:
                self.add_to_log("Got away safely!")
                self.end_battle("ran")
            else:
                self.add_to_log("Can't escape!")
    
    def _execute_struggle(self, actor: str, action: TurnAction):
        """Execute struggle when no moves have PP."""
        attacker = self.player_pokemon if actor == "player" else self.opponent_pokemon
        defender = self.opponent_pokemon if actor == "player" else self.player_pokemon
        
        self.add_to_log(f"{attacker.nickname} has no moves left!")
        self.add_to_log(f"{attacker.nickname} used Struggle!")
        
        # Struggle is a 50 power physical move
        struggle_move = Move("Struggle", PokemonType.NORMAL, "physical", 50, 100, 999)
        damage, _, _ = attacker.calculate_damage(struggle_move, defender)
        
        defender.take_damage(damage)
        self.add_to_log(f"{defender.nickname} took {damage} damage!")
        
        # Recoil damage (1/4 max HP)
        recoil = max(1, attacker.stats["hp"] // 4)
        attacker.take_damage(recoil)
        self.add_to_log(f"{attacker.nickname} was damaged by recoil!")
        
        # Check faints
        if defender.is_fainted:
            self._handle_faint(defender, attacker)
        if attacker.is_fainted:
            self._handle_faint(attacker, defender)
    
    def _handle_faint(self, fainted: Pokemon, victor: Pokemon):
        """Handle a Pokemon fainting."""
        # Award experience if player's Pokemon won
        if victor in self.player.pokemon_team and self.battle_type != BattleType.WILD:
            base_exp = fainted.get_exp_yield()
            
            # Calculate experience
            # Simplified formula
            exp_gain = int((base_exp * fainted.level) / 7)
            
            # Award to all participating Pokemon (simplified - just the victor)
            exp_events = victor.gain_exp(exp_gain)
            for event in exp_events:
                self.add_to_log(event)
        
        # Check for battle end
        if fainted == self.player_pokemon:
            # Try to switch to next Pokemon
            next_pokemon = self.player.get_first_healthy_pokemon()
            if next_pokemon:
                self.player.active_pokemon = next_pokemon
                self.player_pokemon = next_pokemon
                self.add_to_log(f"Go! {next_pokemon.nickname}!")
                # Reset stat stages
                fainted.reset_stat_stages()
            else:
                # Player lost
                self.end_battle("opponent")
        
        elif fainted == self.opponent_pokemon:
            if self.battle_type == BattleType.WILD:
                # Wild Pokemon fainted - battle ends
                self.end_battle("player")
            else:
                # Trainer battle - try to send next Pokemon
                next_pokemon = self.opponent.get_first_healthy_pokemon()
                if next_pokemon:
                    self.opponent.active_pokemon = next_pokemon
                    self.opponent_pokemon = next_pokemon
                    self.add_to_log(f"{self.opponent.name} sent out {next_pokemon.species_name}!")
                    # Reset stat stages
                    fainted.reset_stat_stages()
                else:
                    # Opponent lost
                    self.end_battle("player")
    
    def _process_end_of_turn(self):
        """Process end-of-turn effects."""
        # Weather effects
        if self.weather:
            self.weather_turns -= 1
            
            if self.weather == "hail":
                # Hail damages non-Ice types
                for pokemon in [self.player_pokemon, self.opponent_pokemon]:
                    if not pokemon.is_fainted and PokemonType.ICE not in pokemon.types:
                        damage = max(1, pokemon.stats["hp"] // 16)
                        pokemon.take_damage(damage)
                        self.add_to_log(f"{pokemon.nickname} is buffeted by the hail!")
            
            if self.weather_turns <= 0:
                if self.weather == "rain":
                    self.add_to_log("The rain stopped.")
                elif self.weather == "sun":
                    self.add_to_log("The sunlight faded.")
                elif self.weather == "hail":
                    self.add_to_log("The hail stopped.")
                self.weather = None
        
        # Status damage
        for pokemon in [self.player_pokemon, self.opponent_pokemon]:
            if not pokemon.is_fainted:
                damage_events = pokemon.apply_end_turn_damage()
                for event in damage_events:
                    self.add_to_log(event)
                
                if pokemon.is_fainted:
                    self._handle_faint(pokemon, 
                                      self.opponent_pokemon if pokemon == self.player_pokemon else self.player_pokemon)
    
    def end_battle(self, result: str):
        """End the battle with given result."""
        self.is_over = True
        self.winner = result
        
        if result == "player":
            self.add_to_log("You won!")
            
            # Award prize money for trainer battles
            if self.opponent:
                prize = self.opponent.prize_money
                self.player.add_money(prize)
                self.add_to_log(f"You got ${prize} for winning!")
        
        elif result == "opponent":
            self.add_to_log("You lost!")
            if self.opponent:
                self.add_to_log(f"You blacked out!")
                # Could teleport to Pokemon Center here
        
        elif result == "ran":
            # Successfully ran away
            pass
        
        self.state = BattleState.BATTLE_END
    
    def get_battle_status(self) -> Dict:
        """Get current battle status for UI."""
        return {
            "player_pokemon": {
                "name": self.player_pokemon.nickname,
                "level": self.player_pokemon.level,
                "hp": self.player_pokemon.current_hp,
                "max_hp": self.player_pokemon.stats["hp"],
                "status": self.player_pokemon.status.value,
                "types": [t.value for t in self.player_pokemon.types]
            },
            "opponent_pokemon": {
                "name": self.opponent_pokemon.species_name,
                "level": self.opponent_pokemon.level,
                "hp": self.opponent_pokemon.current_hp,
                "max_hp": self.opponent_pokemon.stats["hp"],
                "status": self.opponent_pokemon.status.value,
                "types": [t.value for t in self.opponent_pokemon.types]
            },
            "turn": self.turn,
            "is_over": self.is_over,
            "winner": self.winner,
            "can_catch": self.can_catch,
            "can_run": self.can_run,
            "weather": self.weather,
            "state": self.state.value
        }