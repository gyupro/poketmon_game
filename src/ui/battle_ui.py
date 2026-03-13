"""
Battle UI - Battle scene rendering, sprites, info panels, move selection, damage popups
"""

import pygame
import os
import math
from typing import Optional, List, Tuple, Dict

from ..pokemon import Pokemon, StatusCondition, PokemonType, Move
from ..battle import Battle, BattleState, BattleAction
from ..battle_animations import BattleAnimationManager, AnimationType

from .components import (
    Colors, Button, HealthBar, ExperienceBar,
    _draw_rounded_rect, _draw_shadow, _draw_gradient_rect, _draw_type_badge,
)
from .dialog import DialogBox


# ---------------------------------------------------------------------------
# PokemonInfoPanel (battle)
# ---------------------------------------------------------------------------

class PokemonInfoPanel:
    """Panel showing Pokemon name, level, HP, EXP during battle."""

    def __init__(self, x: int, y: int, width: int, height: int, is_player: bool = False):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_player = is_player
        self.pokemon: Optional[Pokemon] = None

        hp_y = y + 38
        self.health_bar = HealthBar(x + 14, hp_y, width - 80, 10)
        self.exp_bar = ExperienceBar(x + 14, hp_y + 18, width - 28, 5) if is_player else None

    def set_pokemon(self, pokemon: Pokemon):
        self.pokemon = pokemon
        if pokemon:
            self.health_bar.set_hp(pokemon.current_hp, pokemon.stats["hp"])
            if self.is_player and self.exp_bar:
                clvl = pokemon.get_exp_for_level(pokemon.level)
                nlvl = pokemon.get_exp_for_level(pokemon.level + 1)
                self.exp_bar.set_exp(pokemon.exp - clvl, nlvl - clvl)

    def update(self, dt: float):
        if self.pokemon:
            self.health_bar.set_hp(self.pokemon.current_hp, self.pokemon.stats["hp"])
            self.health_bar.update(dt)
            if self.exp_bar:
                self.exp_bar.update(dt)

    def draw(self, screen: pygame.Surface):
        if not self.pokemon:
            return
        # Card bg with shadow
        _draw_shadow(screen, self.rect, radius=12, offset=4, alpha=50)
        _draw_rounded_rect(screen, (30, 30, 46, 210), self.rect, radius=12)
        # Inner subtle highlight at top
        top_hl = pygame.Surface((self.rect.width - 4, 20), pygame.SRCALPHA)
        top_hl.fill((255, 255, 255, 8))
        screen.blit(top_hl, (self.rect.x + 2, self.rect.y + 2))
        _draw_rounded_rect(screen, (0, 0, 0, 0), self.rect, radius=12,
                           border=2, border_color=Colors.CARD_BORDER)

        font_name = pygame.font.Font(None, 24)
        font_level = pygame.font.Font(None, 18)
        font_tiny = pygame.font.Font(None, 16)

        # Name (with subtle text shadow)
        name_shadow = font_name.render(self.pokemon.nickname, True, (0, 0, 0))
        screen.blit(name_shadow, (self.rect.x + 15, self.rect.y + 9))
        name_surf = font_name.render(self.pokemon.nickname, True, Colors.TEXT_PRIMARY)
        screen.blit(name_surf, (self.rect.x + 14, self.rect.y + 8))

        # Level in a subtle badge
        lvl_text = f"Lv.{self.pokemon.level}"
        level_surf = font_level.render(lvl_text, True, Colors.TEXT_SECONDARY)
        lvl_x = self.rect.x + 14 + name_surf.get_width() + 8
        lvl_bg_w = level_surf.get_width() + 8
        _draw_rounded_rect(screen, (50, 50, 70, 120),
                           (lvl_x - 4, self.rect.y + 10, lvl_bg_w, 16), radius=4)
        screen.blit(level_surf, (lvl_x, self.rect.y + 10))

        # Type badges (right-aligned)
        badge_x = self.rect.right - 14
        for ptype in reversed(self.pokemon.types):
            bw = _draw_type_badge(screen, ptype, badge_x - 55, self.rect.y + 8, font_tiny)
            badge_x -= bw + 4

        # Status condition badge
        if self.pokemon.status != StatusCondition.NONE:
            sc = Colors.STATUS_COLORS.get(self.pokemon.status, Colors.RED)
            label = self.pokemon.status.value.upper()[:3]
            ss = font_tiny.render(label, True, Colors.WHITE)
            sw = ss.get_width() + 10
            sr = (self.rect.x + 14, self.rect.y + 28, sw, 16)
            _draw_rounded_rect(screen, sc, sr, radius=4)
            screen.blit(ss, (sr[0] + 5, sr[1] + 1))

        # HP label (positioned to the left of the HP bar)
        hp_label = font_tiny.render("HP", True, Colors.TEXT_SECONDARY)
        screen.blit(hp_label, (self.rect.x + 14, self.health_bar.rect.y - 12))

        self.health_bar.draw(screen, show_text=True)
        if self.is_player and self.exp_bar:
            exp_label = font_tiny.render("EXP", True, Colors.TEXT_SECONDARY)
            screen.blit(exp_label, (self.rect.x + 14, self.exp_bar.rect.y - 1))
            self.exp_bar.draw(screen)


# ---------------------------------------------------------------------------
# BattleMenu
# ---------------------------------------------------------------------------

class BattleMenu:
    """Battle action menu with modern styling."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 24)

        self.current_menu = "main"
        self.selected_index = 0
        self.battle: Optional[Battle] = None

        btn_w = (width - 60) // 2
        btn_h = 40
        icons = ["\u25B6", "\u2605", "\u25CF", "\u2192"]  # play, star, circle, arrow
        labels = ["FIGHT", "BAG", "POKEMON", "RUN"]
        self.main_buttons: List[Button] = []
        for i, (label, icon) in enumerate(zip(labels, icons)):
            bx = x + 20 + (i % 2) * (btn_w + 20)
            by = y + 20 + (i // 2) * 50
            self.main_buttons.append(
                Button(bx, by, btn_w, btn_h, label, self.font, icon=icon)
            )

    def set_battle(self, battle: Battle):
        self.battle = battle

    def handle_event(self, event: pygame.event.Event) -> Optional[Tuple[BattleAction, Dict]]:
        if not self.battle or self.battle.is_over:
            return None

        if self.current_menu == "main":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 2) % 4
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 2) % 4
                elif event.key == pygame.K_LEFT:
                    if self.selected_index % 2 == 1:
                        self.selected_index -= 1
                elif event.key == pygame.K_RIGHT:
                    if self.selected_index % 2 == 0:
                        self.selected_index += 1
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.selected_index == 0:
                        self.current_menu = "fight"
                        self.selected_index = 0
                    elif self.selected_index == 1:
                        return (BattleAction.BAG, {})
                    elif self.selected_index == 2:
                        return (BattleAction.POKEMON, {})
                    elif self.selected_index == 3:
                        return (BattleAction.RUN, {})

                for i, btn in enumerate(self.main_buttons):
                    btn.selected = (i == self.selected_index)

            for i, btn in enumerate(self.main_buttons):
                if btn.handle_event(event):
                    self.selected_index = i
                    if i == 0:
                        self.current_menu = "fight"
                        self.selected_index = 0
                    elif i == 1:
                        return (BattleAction.BAG, {})
                    elif i == 2:
                        return (BattleAction.POKEMON, {})
                    elif i == 3:
                        return (BattleAction.RUN, {})

        elif self.current_menu == "fight":
            if event.type == pygame.KEYDOWN:
                moves = self.battle.get_valid_moves()
                if event.key == pygame.K_ESCAPE:
                    self.current_menu = "main"
                elif event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 2)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = min(len(moves) - 1, self.selected_index + 2)
                elif event.key == pygame.K_LEFT:
                    self.selected_index = max(0, self.selected_index - 1)
                elif event.key == pygame.K_RIGHT:
                    self.selected_index = min(len(moves) - 1, self.selected_index + 1)
                elif event.key == pygame.K_RETURN:
                    if 0 <= self.selected_index < len(moves):
                        mi = moves[self.selected_index][0]
                        self.current_menu = "main"
                        return (BattleAction.FIGHT, {"move_index": mi})

        return None

    def draw(self, screen: pygame.Surface):
        # Card background
        _draw_shadow(screen, self.rect, radius=12, offset=4, alpha=50)
        _draw_rounded_rect(screen, (25, 25, 40, 220), self.rect, radius=12)
        _draw_rounded_rect(screen, (0, 0, 0, 0), self.rect, radius=12,
                           border=2, border_color=Colors.CARD_BORDER)

        if self.current_menu == "main":
            for i, btn in enumerate(self.main_buttons):
                btn.selected = (i == self.selected_index)
                btn.draw(screen)

        elif self.current_menu == "fight":
            if not self.battle or not self.battle.player_pokemon:
                return
            moves = self.battle.get_valid_moves()
            font_tiny = pygame.font.Font(None, 16)

            # Header
            title_surf = font_tiny.render("Choose a move:", True, Colors.TEXT_SECONDARY)
            screen.blit(title_surf, (self.rect.x + 16, self.rect.y + 8))
            back_surf = font_tiny.render("[ESC] Back", True, (120, 130, 160))
            screen.blit(back_surf, (self.rect.right - 80, self.rect.y + 8))

            # 2x2 grid of type-colored move buttons
            grid_x = self.rect.x + 12
            grid_y = self.rect.y + 28
            btn_w = (self.rect.width - 36) // 2
            btn_h = 50

            for i, (move_index, move) in enumerate(moves):
                col = i % 2
                row = i // 2
                bx = grid_x + col * (btn_w + 12)
                by = grid_y + row * (btn_h + 8)
                btn_rect = pygame.Rect(bx, by, btn_w, btn_h)

                type_color = Colors.TYPE_COLORS.get(move.type, Colors.GRAY)

                if i == self.selected_index:
                    # Brighter when selected
                    bc = tuple(min(255, int(c * 1.2)) for c in type_color)
                    _draw_rounded_rect(screen, bc, btn_rect, radius=8)
                    _draw_rounded_rect(screen, (0, 0, 0, 0), btn_rect, radius=8,
                                       border=2, border_color=(255, 255, 255))
                else:
                    # Dimmer when not selected
                    dc = tuple(max(0, c - 30) for c in type_color)
                    _draw_rounded_rect(screen, dc, btn_rect, radius=8)
                    _draw_rounded_rect(screen, (0, 0, 0, 0), btn_rect, radius=8,
                                       border=1, border_color=(0, 0, 0))

                # Top highlight
                hl_rect = pygame.Rect(bx + 2, by + 2, btn_w - 4, btn_h // 3)
                hl_s = pygame.Surface((hl_rect.width, hl_rect.height), pygame.SRCALPHA)
                hl_s.fill((255, 255, 255, 25))
                screen.blit(hl_s, (hl_rect.x, hl_rect.y))

                # Move name (white text)
                name_surf = self.font.render(move.name, True, (255, 255, 255))
                screen.blit(name_surf, (bx + 10, by + 6))

                # PP (top-right)
                pp_color = (255, 255, 255) if move.current_pp > move.pp * 0.25 else (255, 100, 100)
                pp_text = f"PP {move.current_pp}/{move.pp}"
                pp_surf = font_tiny.render(pp_text, True, pp_color)
                screen.blit(pp_surf, (bx + btn_w - pp_surf.get_width() - 8, by + 8))

                # Category icon (bottom-left)
                if move.category == "physical":
                    cat_label = "ATK"
                    cat_color = (240, 160, 80)
                elif move.category == "special":
                    cat_label = "SPA"
                    cat_color = (120, 160, 240)
                else:
                    cat_label = "STS"
                    cat_color = (168, 168, 168)
                cat_surf = font_tiny.render(cat_label, True, cat_color)
                screen.blit(cat_surf, (bx + 10, by + btn_h - 18))

                # Power (bottom-center)
                if move.category != "status" and move.power > 0:
                    pow_surf = font_tiny.render(f"Pwr:{move.power}", True, (220, 220, 230))
                    screen.blit(pow_surf, (bx + 45, by + btn_h - 18))

                # Accuracy (bottom-right)
                if move.accuracy < 999:
                    acc_text = f"Acc:{move.accuracy}"
                else:
                    acc_text = "Acc:--"
                acc_surf = font_tiny.render(acc_text, True, (180, 180, 200))
                screen.blit(acc_surf, (bx + btn_w - acc_surf.get_width() - 8, by + btn_h - 18))


class BattleUI:
    """Manages battle scene rendering: background, sprites, info panels, animations."""

    def __init__(self, screen: pygame.Surface, sprite_cache: Dict,
                 font_small, font_medium, font_large):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.sprite_cache = sprite_cache
        self.font_small = font_small
        self.font_medium = font_medium
        self.font_large = font_large

        self._battle_bg_cache: Optional[pygame.Surface] = None
        self._vs_shown_for_battle = False
        self._battle_fade_alpha = 0.0
        self._battle_fading_in = False
        self._last_battle_log_length = 0

        self.battle_dialog = DialogBox(
            40, self.screen_height - 160, self.screen_width - 80, 120, self.font_medium
        )
        self.battle_menu = BattleMenu(
            40, self.screen_height - 320, self.screen_width - 80, 140
        )
        self.player_info_panel = PokemonInfoPanel(
            self.screen_width - 350, self.screen_height - 440, 300, 100, True
        )
        self.opponent_info_panel = PokemonInfoPanel(50, 50, 300, 80, False)
        self.player_sprite_pos = (200, self.screen_height - 480)
        self.opponent_sprite_pos = (self.screen_width - 200, 180)
        self.battle_animation_manager = BattleAnimationManager()

    def load_sprite(self, sprite_path: str, size=None):
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

    def update(self, dt: float, game=None, time_val: float = 0.0):
        self.battle_dialog.update(dt)
        self.player_info_panel.update(dt)
        self.opponent_info_panel.update(dt)
        self.battle_animation_manager.update(dt)

        # Battle fade-in
        if self._battle_fading_in and self._battle_fade_alpha > 0:
            self._battle_fade_alpha = max(0, self._battle_fade_alpha - 400 * dt)
            if self._battle_fade_alpha <= 0:
                self._battle_fading_in = False

        # Trigger VS screen on battle start
        if game and game.current_battle and not self._vs_shown_for_battle:
            self._vs_shown_for_battle = True
            self.battle_animation_manager.start_vs_screen(
                self.screen_width, self.screen_height)
            self._battle_fading_in = True
            self._battle_fade_alpha = 255.0

        if hasattr(self, "_last_battle_log_length"):
            cur = len(game.current_battle.battle_log) if game and game.current_battle else 0
            if cur > self._last_battle_log_length:
                if game.current_battle and game.current_battle.last_used_move:
                    tp = self.opponent_sprite_pos if game.current_battle.player_pokemon else self.player_sprite_pos
                    self._trigger_move_animation(game.current_battle.last_used_move, tp)
            self._last_battle_log_length = cur
        else:
            self._last_battle_log_length = 0

    def reset(self):
        self._vs_shown_for_battle = False
        self._battle_bg_cache = None
        self.battle_animation_manager.clear()

    def draw_battle(self, surface: pygame.Surface, battle: Battle, time_val: float = 0.0):
        shake_offset = self.battle_animation_manager.get_screen_offset()
        if shake_offset != (0, 0):
            temp = pygame.Surface((self.screen_width, self.screen_height))
            self._draw_battle_content(temp, battle, time_val)
            surface.blit(temp, shake_offset)
        else:
            self._draw_battle_content(surface, battle, time_val)
        self.battle_animation_manager.render(surface)

        # VS screen overlay
        player_name = battle.player_pokemon.nickname if battle.player_pokemon else ""
        opponent_name = battle.opponent_pokemon.species_name if battle.opponent_pokemon else ""
        self.battle_animation_manager.render_vs_screen(
            surface, player_name, opponent_name)

        # Battle fade-in overlay
        if self._battle_fade_alpha > 0:
            fade_surf = pygame.Surface((self.screen_width, self.screen_height))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(int(self._battle_fade_alpha))
            surface.blit(fade_surf, (0, 0))

    def _draw_battle_content(self, surface: pygame.Surface, battle: Battle,
                              time_val: float = 0.0):
        self._draw_battle_background_on_surface(surface)

        self.battle_menu.set_battle(battle)
        self.player_info_panel.set_pokemon(battle.player_pokemon)
        self.opponent_info_panel.set_pokemon(battle.opponent_pokemon)

        if battle.battle_log:
            latest = ""
            for entry in reversed(battle.battle_log):
                if entry.strip():
                    latest = entry
                    break
            if latest and self.battle_dialog.text != latest:
                self.battle_dialog.set_text(latest)

        self._draw_pokemon_sprite_on_surface(surface, battle.player_pokemon,
                                             self.player_sprite_pos, True)
        self._draw_pokemon_sprite_on_surface(surface, battle.opponent_pokemon,
                                             self.opponent_sprite_pos, False)

        self.player_info_panel.draw(surface)
        self.opponent_info_panel.draw(surface)

        if battle.state in (BattleState.SELECTING_ACTION, BattleState.SELECTING_MOVE):
            self.battle_menu.draw(surface)

        self.battle_dialog.draw(surface)

        if battle.is_over:
            self._draw_battle_end_message(surface, time_val)

        if battle.state == BattleState.TURN_EXECUTION and battle.last_used_move:
            pass  # type effectiveness placeholder

        if hasattr(battle, "_move_just_used") and battle._move_just_used:
            self._trigger_move_animation(battle._move_just_used, battle._move_target_pos)
            battle._move_just_used = None

    def _draw_battle_background_on_surface(self, surface: pygame.Surface):
        if self._battle_bg_cache is not None:
            surface.blit(self._battle_bg_cache, (0, 0))
            return

        bg = pygame.Surface((self.screen_width, self.screen_height))
        horizon_y = self.screen_height * 45 // 100

        for y_pos in range(horizon_y):
            ratio = y_pos / horizon_y
            r = int(70 + 130 * ratio)
            g = int(130 + 110 * ratio)
            b = int(200 + 50 * ratio)
            pygame.draw.line(bg, (r, g, b), (0, y_pos), (self.screen_width, y_pos))

        cloud_surf = pygame.Surface((self.screen_width, horizon_y), pygame.SRCALPHA)
        cloud_color = (240, 245, 255, 55)
        for cx, cy, cw, ch in [(200, 50, 180, 40), (500, 30, 220, 50),
                                (850, 60, 160, 35), (1100, 40, 200, 45)]:
            for j in range(3):
                ofs = j * 30
                pygame.draw.ellipse(cloud_surf, cloud_color,
                                    (cx + ofs - 20, cy - 5, cw // 2, ch))
        bg.blit(cloud_surf, (0, 0))

        ground_start = horizon_y
        ground_height = self.screen_height - ground_start
        for y_pos in range(ground_height):
            ratio = y_pos / ground_height
            r = int(140 - 40 * ratio)
            g = int(200 - 50 * ratio)
            b = int(120 - 50 * ratio)
            pygame.draw.line(bg, (r, g, b),
                             (0, ground_start + y_pos),
                             (self.screen_width, ground_start + y_pos))

        for gx in range(0, self.screen_width, 50):
            for gy in range(ground_start + 10, self.screen_height, 50):
                shade = 10 if (gx + gy) % 100 == 0 else -5
                patch_c = (max(0, 130 + shade), max(0, 190 + shade), max(0, 110 + shade))
                pygame.draw.circle(bg, patch_c, (gx + 25, gy + 25), 12)

        horizon_glow = pygame.Surface((self.screen_width, 6), pygame.SRCALPHA)
        horizon_glow.fill((180, 220, 180, 40))
        bg.blit(horizon_glow, (0, horizon_y - 3))
        pygame.draw.line(bg, (160, 210, 160),
                         (0, horizon_y), (self.screen_width, horizon_y), 2)

        # Player platform
        plat_cx, plat_cy = 200, self.screen_height - 395
        plat_w, plat_h = 210, 70
        shadow_s = pygame.Surface((plat_w + 20, plat_h + 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 50), (0, 0, plat_w + 20, plat_h + 10))
        bg.blit(shadow_s, (plat_cx - plat_w // 2 - 5, plat_cy - plat_h // 2 + 5))
        plat_rect = pygame.Rect(plat_cx - plat_w // 2, plat_cy - plat_h // 2, plat_w, plat_h)
        pygame.draw.ellipse(bg, (110, 170, 110), plat_rect)
        edge_rect = pygame.Rect(plat_cx - plat_w // 2 + 8, plat_cy - plat_h // 2 + 5,
                                plat_w - 16, plat_h - 20)
        pygame.draw.ellipse(bg, (130, 195, 130), edge_rect)
        pygame.draw.ellipse(bg, (80, 130, 80), plat_rect, 3)

        # Opponent platform
        opp_cx, opp_cy = self.screen_width - 200, 260
        opp_w, opp_h = 200, 65
        shadow_s2 = pygame.Surface((opp_w + 20, opp_h + 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s2, (0, 0, 0, 50), (0, 0, opp_w + 20, opp_h + 10))
        bg.blit(shadow_s2, (opp_cx - opp_w // 2 - 5, opp_cy - opp_h // 2 + 5))
        opp_rect = pygame.Rect(opp_cx - opp_w // 2, opp_cy - opp_h // 2, opp_w, opp_h)
        pygame.draw.ellipse(bg, (110, 170, 110), opp_rect)
        edge_rect2 = pygame.Rect(opp_cx - opp_w // 2 + 8, opp_cy - opp_h // 2 + 5,
                                 opp_w - 16, opp_h - 20)
        pygame.draw.ellipse(bg, (130, 195, 130), edge_rect2)
        pygame.draw.ellipse(bg, (80, 130, 80), opp_rect, 3)

        self._battle_bg_cache = bg
        surface.blit(bg, (0, 0))

    def _draw_pokemon_sprite_on_surface(self, surface, pokemon, position, is_back):
        if not pokemon:
            return
        sprite_fn = f"{pokemon.species_id}_{'back' if is_back else 'normal'}.png"
        sprite_path = os.path.join("assets", "sprites", sprite_fn)
        sprite = self.load_sprite(sprite_path, (128, 128))
        if sprite:
            sr = sprite.get_rect(center=position)
            surface.blit(sprite, sr)
        else:
            pcolor = Colors.TYPE_COLORS.get(
                pokemon.types[0] if pokemon.types else PokemonType.NORMAL, Colors.GRAY
            )
            shadow_s = pygame.Surface((104, 104), pygame.SRCALPHA)
            pygame.draw.circle(shadow_s, (0, 0, 0, 60), (52, 54), 50)
            surface.blit(shadow_s, (position[0] - 52, position[1] - 52))
            pygame.draw.circle(surface, pcolor, position, 48)
            inner_c = tuple(min(255, c + 40) for c in pcolor)
            pygame.draw.circle(surface, inner_c, (position[0] - 5, position[1] - 8), 34)
            hl_c = tuple(min(255, c + 80) for c in pcolor)
            pygame.draw.circle(surface, hl_c, (position[0] - 12, position[1] - 16), 14)
            pygame.draw.circle(surface, Colors.BLACK, position, 48, 3)
            shadow_text = self.font_small.render(pokemon.species_name, True, (0, 0, 0))
            surface.blit(shadow_text, shadow_text.get_rect(center=(position[0] + 1, position[1] + 1)))
            ns = self.font_small.render(pokemon.species_name, True, Colors.WHITE)
            surface.blit(ns, ns.get_rect(center=position))

    def _trigger_move_animation(self, move: Move, target_pos: Tuple[int, int]):
        if not move or not target_pos:
            return
        type_anims = {
            PokemonType.NORMAL: AnimationType.NORMAL,
            PokemonType.FIRE: AnimationType.FIRE,
            PokemonType.WATER: AnimationType.WATER,
            PokemonType.ELECTRIC: AnimationType.ELECTRIC,
            PokemonType.GRASS: AnimationType.GRASS,
            PokemonType.ICE: AnimationType.ICE,
            PokemonType.FIGHTING: AnimationType.FIGHTING,
            PokemonType.POISON: AnimationType.POISON,
            PokemonType.GROUND: AnimationType.GROUND,
            PokemonType.FLYING: AnimationType.FLYING,
            PokemonType.PSYCHIC: AnimationType.PSYCHIC,
            PokemonType.BUG: AnimationType.BUG,
            PokemonType.ROCK: AnimationType.ROCK,
            PokemonType.GHOST: AnimationType.GHOST,
            PokemonType.DRAGON: AnimationType.DRAGON,
            PokemonType.DARK: AnimationType.DARK,
            PokemonType.STEEL: AnimationType.STEEL,
            PokemonType.FAIRY: AnimationType.FAIRY,
        }
        anim = type_anims.get(move.type, AnimationType.HIT)
        self.battle_animation_manager.add_animation(anim, target_pos)

        if move.category != "status" and move.power > 0:
            self.battle_animation_manager.add_damage_popup(
                (target_pos[0], target_pos[1] - 30),
                move.power, is_critical=False, effectiveness=1.0
            )

        if move.power >= 100:
            self.battle_animation_manager.add_animation(AnimationType.SHAKE, target_pos)

    def _draw_battle_end_message(self, surface: pygame.Surface, time_val: float = 0.0):
        banner_w = 500
        banner_h = 120
        bx = (self.screen_width - banner_w) // 2
        by = (self.screen_height - banner_h) // 2

        _draw_shadow(surface, (bx, by, banner_w, banner_h), radius=16, offset=6, alpha=80)
        _draw_rounded_rect(surface, (20, 20, 36, 230), (bx, by, banner_w, banner_h), radius=16)
        _draw_rounded_rect(surface, (0, 0, 0, 0), (bx, by, banner_w, banner_h),
                           radius=16, border=2, border_color=Colors.ACCENT_DARK)

        accent_rect = (bx + 2, by + 2, banner_w - 4, 4)
        _draw_rounded_rect(surface, Colors.ACCENT, accent_rect, radius=2)

        msg = self.font_large.render("Battle Complete!", True, Colors.TEXT_PRIMARY)
        surface.blit(msg, msg.get_rect(center=(self.screen_width // 2, by + 45)))

        pulse = 0.7 + 0.3 * math.sin(time_val * 3)
        sub_color = tuple(int(c * pulse) for c in Colors.TEXT_SECONDARY)
        sub = self.font_medium.render("Press SPACE / ENTER to continue",
                                      True, sub_color)
        surface.blit(sub, sub.get_rect(center=(self.screen_width // 2, by + 85)))
