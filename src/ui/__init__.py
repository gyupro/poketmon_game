"""
UI Package - Modern, polished UI system for Pokemon game

This module acts as a facade, preserving the original public API.
``from src.ui import UI, UIState`` works unchanged.
"""

import pygame
import os
from typing import Optional, Tuple, Dict
from enum import Enum

from ..player import Player
from ..battle import Battle, BattleState, BattleAction
from ..pokemon import Pokemon, Move

from .components import Colors, Button, HealthBar, ExperienceBar
from .battle_ui import BattleUI, PokemonInfoPanel, BattleMenu
from .menu_ui import MenuUI
from .world_hud import WorldHUD
from .dialog import DialogBox
from .shop_ui import ShopUI


class UIState(Enum):
    """Different UI states for the game."""
    MAIN_MENU = "main_menu"
    GAME_WORLD = "game_world"
    BATTLE = "battle"
    PAUSE_MENU = "pause_menu"
    POKEMON_MENU = "pokemon_menu"
    BAG_MENU = "bag_menu"
    SAVE_MENU = "save_menu"
    OPTIONS_MENU = "options_menu"


class UI:
    """Main UI manager for the game -- facade that delegates to sub-modules."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        # Fonts
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 48)
        self.font_huge = pygame.font.Font(None, 72)
        self.font_title = pygame.font.Font(None, 96)

        self.state = UIState.MAIN_MENU

        # Timing
        self._time = 0.0

        # Sprite cache (shared across sub-modules)
        self.sprite_cache: Dict[str, pygame.Surface] = {}

        # Transition
        self.transition_alpha = 0
        self.transition_speed = 500
        self.transitioning = False

        # Delegate modules
        self._battle_ui = BattleUI(
            screen, self.sprite_cache,
            self.font_small, self.font_medium, self.font_large,
        )
        self._menu_ui = MenuUI(
            screen, self.sprite_cache,
            self.font_small, self.font_medium, self.font_large,
            self.font_huge, self.font_title,
        )
        self._world_hud = WorldHUD(screen, self.font_small, self.font_medium)
        self._shop_ui = ShopUI(screen)

        # Expose battle sub-objects for backwards compatibility
        self.battle_dialog = self._battle_ui.battle_dialog
        self.battle_menu = self._battle_ui.battle_menu
        self.player_info_panel = self._battle_ui.player_info_panel
        self.opponent_info_panel = self._battle_ui.opponent_info_panel
        self.player_sprite_pos = self._battle_ui.player_sprite_pos
        self.opponent_sprite_pos = self._battle_ui.opponent_sprite_pos
        self.battle_animation_manager = self._battle_ui.battle_animation_manager

        # Expose menu buttons for backwards compatibility
        self.main_menu_buttons = self._menu_ui.main_menu_buttons

    # ---- sprite loading ----

    def load_sprite(self, sprite_path: str, size: Optional[Tuple[int, int]] = None) -> Optional[pygame.Surface]:
        cache_key = f"{sprite_path}_{size}" if size else sprite_path
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]
        try:
            if os.path.exists(sprite_path):
                sprite = pygame.image.load(sprite_path)
                if size:
                    sprite = pygame.transform.scale(sprite, size)
                self.sprite_cache[cache_key] = sprite
                return sprite
        except Exception:
            pass
        return None

    # ---- state management ----

    def change_state(self, new_state: UIState):
        self.state = new_state
        self.transitioning = True
        self.transition_alpha = 255

    def show_location(self, name: str):
        """Show a location banner that fades in and out."""
        self._world_hud.show_location(name)

    # ---- update ----

    def update(self, dt: float, game=None):
        self._time += dt

        # Transition fade
        if self.transitioning and self.transition_alpha > 0:
            self.transition_alpha = max(0, self.transition_alpha - self.transition_speed * dt)
            if self.transition_alpha == 0:
                self.transitioning = False

        # Location banner
        self._world_hud.update(dt)

        # Battle state
        if self.state == UIState.BATTLE:
            self._battle_ui.update(dt, game, self._time)
        else:
            # Reset VS flag and clear battle bg cache when not in battle
            if self._battle_ui._vs_shown_for_battle:
                self._battle_ui.reset()

    # ---- event handling ----

    def handle_event(self, event: pygame.event.Event, game) -> bool:
        if self.state == UIState.MAIN_MENU:
            # Don't handle menu events during starter selection (game handles it)
            if getattr(game, 'starter_selection_active', False):
                return False
            return self._menu_ui.handle_main_menu_event(event, game)

        elif self.state == UIState.PAUSE_MENU:
            def _set_ui_state(name: str):
                self.state = UIState[name]
            return self._menu_ui.handle_pause_menu_event(event, game, _set_ui_state)

        elif self.state == UIState.POKEMON_MENU:
            return self._menu_ui.handle_pokemon_menu_event(event, game)

        elif self.state == UIState.BAG_MENU:
            return self._menu_ui.handle_bag_menu_event(event, game)

        elif self.state == UIState.BATTLE:
            # Block input during VS screen
            if self._battle_ui.battle_animation_manager.has_vs_screen():
                return True
            action = self._battle_ui.battle_menu.handle_event(event)
            if action and game.current_battle:
                action_type, params = action
                game.current_battle.set_player_action(action_type, **params)
                return True
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if not self._battle_ui.battle_dialog.is_complete:
                        self._battle_ui.battle_dialog.skip_animation()
                        return True

        return False

    # ================================================================
    # DRAW METHODS  (delegate to sub-modules)
    # ================================================================

    def draw_main_menu(self):
        self._menu_ui.draw_main_menu(self._time)

    def draw_pause_menu(self, player: Player):
        self._menu_ui.draw_pause_menu(player)

    def draw_pokemon_menu(self, player: Player):
        self._menu_ui.draw_pokemon_menu(player)

    def draw_bag_menu(self, player: Player):
        self._menu_ui.draw_bag_menu(player)

    def draw_world_hud(self, player: Player):
        self._world_hud.draw(player)

    def draw_battle(self, battle: Battle):
        self._battle_ui.draw_battle(self.screen, battle, self._time)

    def draw_transition(self):
        if self.transition_alpha > 0:
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(self.transition_alpha)))
            self.screen.blit(overlay, (0, 0))

    # ---- Main draw dispatcher ----

    def draw(self, game):
        if self.state == UIState.MAIN_MENU:
            self.draw_main_menu()

        elif self.state == UIState.GAME_WORLD:
            self.draw_world_hud(game.player)

        elif self.state == UIState.BATTLE:
            if game.current_battle:
                self.draw_battle(game.current_battle)

        elif self.state == UIState.PAUSE_MENU:
            self.draw_pause_menu(game.player)

        elif self.state == UIState.POKEMON_MENU:
            self.draw_pokemon_menu(game.player)

        elif self.state == UIState.BAG_MENU:
            self.draw_bag_menu(game.player)

        self.draw_transition()


__all__ = [
    'UI', 'UIState',
    'Colors', 'Button', 'HealthBar', 'ExperienceBar',
    'BattleUI', 'PokemonInfoPanel', 'BattleMenu',
    'MenuUI', 'WorldHUD', 'DialogBox', 'ShopUI',
]
