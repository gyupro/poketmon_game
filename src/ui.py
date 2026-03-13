"""
UI Components - Modern, polished UI system for Pokemon game
"""

import pygame
import os
import math
import time
from typing import Optional, List, Tuple, Dict, Callable
from enum import Enum
from .player import Player
from .battle import Battle, BattleState, BattleAction
from .pokemon import Pokemon, StatusCondition, PokemonType, Move
from .battle_animations import BattleAnimationManager, AnimationType
from .items import ITEM_REGISTRY, ItemCategory


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


# ---------------------------------------------------------------------------
# Design System -- consistent palette, drawing helpers
# ---------------------------------------------------------------------------

class Colors:
    """Modern color palette used across all UI elements."""
    # Core
    WHITE = (248, 248, 248)
    BLACK = (16, 16, 16)
    RED = (234, 68, 68)
    GREEN = (72, 199, 142)
    BLUE = (66, 133, 244)
    YELLOW = (251, 188, 4)
    GRAY = (158, 158, 158)
    DARK_GRAY = (80, 80, 80)
    LIGHT_GRAY = (210, 210, 210)

    # Accent / brand
    ACCENT = (56, 128, 255)
    ACCENT_LIGHT = (100, 160, 255)
    ACCENT_DARK = (36, 90, 200)

    # Surfaces
    PANEL_BG = (30, 30, 46)           # dark card background
    PANEL_BG_LIGHT = (45, 45, 65)
    OVERLAY = (10, 10, 20)            # full-screen overlay tint
    CARD_BG = (38, 38, 56)
    CARD_BORDER = (70, 70, 100)

    # Text
    TEXT_PRIMARY = (240, 240, 250)
    TEXT_SECONDARY = (170, 170, 190)
    TEXT_DARK = (64, 64, 64)
    TEXT_LIGHT = (248, 248, 248)

    # HP
    HP_GREEN = (72, 199, 142)
    HP_YELLOW = (251, 188, 4)
    HP_RED = (234, 68, 68)
    EXP_BLUE = (66, 165, 245)

    # Pokemon type colors
    TYPE_COLORS = {
        PokemonType.NORMAL: (168, 168, 120),
        PokemonType.FIRE: (240, 128, 48),
        PokemonType.WATER: (104, 144, 240),
        PokemonType.ELECTRIC: (248, 208, 48),
        PokemonType.GRASS: (120, 200, 80),
        PokemonType.ICE: (152, 216, 216),
        PokemonType.FIGHTING: (192, 48, 40),
        PokemonType.POISON: (160, 64, 160),
        PokemonType.GROUND: (224, 192, 104),
        PokemonType.FLYING: (168, 144, 240),
        PokemonType.PSYCHIC: (248, 88, 136),
        PokemonType.BUG: (168, 184, 32),
        PokemonType.ROCK: (184, 160, 56),
        PokemonType.GHOST: (112, 88, 152),
        PokemonType.DRAGON: (112, 56, 248),
        PokemonType.DARK: (112, 88, 72),
        PokemonType.STEEL: (184, 184, 208),
        PokemonType.FAIRY: (238, 153, 172),
    }

    # Status condition colors
    STATUS_COLORS = {
        StatusCondition.PARALYZED: (248, 208, 48),
        StatusCondition.BURNED: (240, 128, 48),
        StatusCondition.POISONED: (160, 64, 160),
        StatusCondition.BADLY_POISONED: (130, 44, 130),
        StatusCondition.FROZEN: (152, 216, 216),
        StatusCondition.ASLEEP: (168, 168, 168),
        StatusCondition.CONFUSED: (248, 88, 136),
        StatusCondition.FLINCHED: (200, 200, 200),
    }

    # Legacy aliases so old references don't break
    MENU_BG = PANEL_BG
    MENU_BORDER = CARD_BORDER
    BUTTON_NORMAL = (55, 55, 80)
    BUTTON_HOVER = (70, 70, 105)
    BUTTON_PRESSED = (45, 45, 70)


def _draw_rounded_rect(surface: pygame.Surface, color, rect, radius: int = 10,
                        border: int = 0, border_color=None):
    """Draw a rectangle with rounded corners."""
    r = pygame.Rect(rect)
    if radius > min(r.width, r.height) // 2:
        radius = min(r.width, r.height) // 2

    temp = pygame.Surface((r.width, r.height), pygame.SRCALPHA)

    # Fill
    pygame.draw.rect(temp, color, (0, 0, r.width, r.height), border_radius=radius)

    if border > 0 and border_color:
        pygame.draw.rect(temp, border_color, (0, 0, r.width, r.height),
                         width=border, border_radius=radius)

    surface.blit(temp, r.topleft)


def _draw_shadow(surface: pygame.Surface, rect, radius: int = 10, offset: int = 4,
                  alpha: int = 60):
    """Draw a soft shadow behind a rect."""
    shadow = pygame.Surface((rect[2] + offset * 2, rect[3] + offset * 2), pygame.SRCALPHA)
    shadow_color = (0, 0, 0, alpha)
    pygame.draw.rect(shadow, shadow_color,
                     (offset, offset, rect[2], rect[3]),
                     border_radius=radius)
    surface.blit(shadow, (rect[0] - offset + offset, rect[1] - offset + offset))


def _draw_gradient_rect(surface: pygame.Surface, rect, color_top, color_bottom,
                         radius: int = 0):
    """Draw a vertical gradient rectangle."""
    r = pygame.Rect(rect)
    temp = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
    for y in range(r.height):
        t = y / max(r.height - 1, 1)
        c = tuple(int(color_top[i] + (color_bottom[i] - color_top[i]) * t)
                  for i in range(min(len(color_top), len(color_bottom))))
        pygame.draw.line(temp, c, (0, y), (r.width, y))
    if radius > 0:
        mask = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, r.width, r.height),
                         border_radius=radius)
        temp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surface.blit(temp, r.topleft)


def _draw_type_badge(surface: pygame.Surface, ptype: PokemonType, x: int, y: int,
                      font: pygame.font.Font):
    """Draw a small coloured type badge."""
    color = Colors.TYPE_COLORS.get(ptype, Colors.GRAY)
    label = ptype.value.upper()
    text_surf = font.render(label, True, Colors.WHITE)
    tw, th = text_surf.get_size()
    pad_x, pad_y = 8, 3
    badge_w = tw + pad_x * 2
    badge_h = th + pad_y * 2
    _draw_rounded_rect(surface, color, (x, y, badge_w, badge_h), radius=6)
    surface.blit(text_surf, (x + pad_x, y + pad_y))
    return badge_w


# ---------------------------------------------------------------------------
# Button
# ---------------------------------------------------------------------------

class Button:
    """Modern button with rounded corners and hover glow."""

    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 font: pygame.font.Font, callback: Optional[Callable] = None,
                 color_normal=None, color_hover=None, color_pressed=None,
                 text_color=None, icon: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.callback = callback
        self.icon = icon

        self.color_normal = color_normal or Colors.BUTTON_NORMAL
        self.color_hover = color_hover or Colors.BUTTON_HOVER
        self.color_pressed = color_pressed or Colors.BUTTON_PRESSED
        self.text_color = text_color or Colors.TEXT_PRIMARY

        self.current_color = self.color_normal
        self.is_hovered = False
        self.is_pressed = False
        self.enabled = True
        self.selected = False  # keyboard-driven highlight

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            if not self.is_pressed:
                self.current_color = self.color_hover if self.is_hovered else self.color_normal
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                self.current_color = self.color_pressed
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed and self.rect.collidepoint(event.pos):
                self.is_pressed = False
                self.current_color = self.color_hover
                if self.callback:
                    self.callback()
                return True
            self.is_pressed = False
            self.current_color = self.color_normal if not self.is_hovered else self.color_hover
        return False

    def draw(self, screen: pygame.Surface):
        color = self.color_hover if self.selected else self.current_color
        # Shadow
        _draw_shadow(screen, self.rect, radius=10, offset=3, alpha=40)
        # Background
        _draw_rounded_rect(screen, color, self.rect, radius=10)
        # Accent left stripe when selected
        if self.selected:
            stripe = pygame.Rect(self.rect.x, self.rect.y, 4, self.rect.height)
            _draw_rounded_rect(screen, Colors.ACCENT, stripe, radius=2)
        # Border
        _draw_rounded_rect(screen, (0, 0, 0, 0), self.rect, radius=10,
                           border=2, border_color=Colors.CARD_BORDER)
        # Icon + text
        label = f"{self.icon}  {self.text}" if self.icon else self.text
        text_surface = self.font.render(label, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


# ---------------------------------------------------------------------------
# DialogBox -- rounded, semi-transparent, gradient border, speaker tag, arrow
# ---------------------------------------------------------------------------

class DialogBox:
    """Modern dialog box with typewriter effect, speaker tag, bounce arrow."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 font: pygame.font.Font):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.padding = 20

        self.text = ""
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0.0
        self.char_delay = 22  # ms per character (faster = smoother)
        self.is_complete = False
        self.speaker = ""

        self.lines: List[str] = []
        self.max_lines = 3

        # Bouncing arrow
        self._arrow_timer = 0.0

    def set_text(self, text: str, speaker: str = ""):
        self.text = text
        self.speaker = speaker
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0.0
        self.is_complete = False
        self._wrap_text()

    def _wrap_text(self):
        words = self.text.split(" ")
        self.lines = []
        current_line = ""
        for word in words:
            test = (current_line + " " + word).strip()
            if self.font.size(test)[0] > self.rect.width - 2 * self.padding:
                if current_line:
                    self.lines.append(current_line)
                current_line = word
            else:
                current_line = test
        if current_line:
            self.lines.append(current_line)

    def update(self, dt: float):
        if not self.is_complete:
            self.char_timer += dt * 1000
            while self.char_timer >= self.char_delay and self.char_index < len(self.text):
                self.char_index += 1
                self.char_timer -= self.char_delay
                self.displayed_text = self.text[: self.char_index]
            if self.char_index >= len(self.text):
                self.is_complete = True
        self._arrow_timer += dt

    def skip_animation(self):
        self.displayed_text = self.text
        self.char_index = len(self.text)
        self.is_complete = True

    def draw(self, screen: pygame.Surface):
        # --- speaker tag ---
        if self.speaker:
            tag_font = pygame.font.Font(None, 22)
            tag_surf = tag_font.render(self.speaker, True, Colors.TEXT_PRIMARY)
            tw, th = tag_surf.get_size()
            tag_h = th + 10
            tag_rect = (self.rect.x + 16, self.rect.y - tag_h - 2, tw + 20, tag_h)
            _draw_rounded_rect(screen, Colors.ACCENT_DARK, tag_rect, radius=8)
            screen.blit(tag_surf, (tag_rect[0] + 10, tag_rect[1] + 5))

        # --- main box ---
        # shadow
        _draw_shadow(screen, self.rect, radius=12, offset=5, alpha=70)
        # dark semi-transparent bg
        bg_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (20, 20, 36, 220), (0, 0, self.rect.width, self.rect.height),
                         border_radius=12)
        screen.blit(bg_surf, self.rect.topleft)
        # gradient border
        _draw_rounded_rect(screen, (0, 0, 0, 0), self.rect, radius=12,
                           border=2, border_color=Colors.ACCENT_DARK)
        # inner light border
        inner = self.rect.inflate(-4, -4)
        _draw_rounded_rect(screen, (0, 0, 0, 0), inner, radius=10,
                           border=1, border_color=(80, 80, 120, 80))

        # --- text ---
        displayed_lines = self._get_displayed_lines()
        y_off = self.padding
        for line in displayed_lines[-self.max_lines:]:
            ts = self.font.render(line, True, Colors.TEXT_PRIMARY)
            screen.blit(ts, (self.rect.x + self.padding, self.rect.y + y_off))
            y_off += self.font.get_height() + 4

        # --- bouncing arrow when complete ---
        if self.is_complete and self.text:
            bounce = int(math.sin(self._arrow_timer * 4) * 4)
            ax = self.rect.right - 28
            ay = self.rect.bottom - 18 + bounce
            pts = [(ax, ay), (ax + 10, ay), (ax + 5, ay + 8)]
            pygame.draw.polygon(screen, Colors.ACCENT_LIGHT, pts)

    def _get_displayed_lines(self) -> List[str]:
        if not self.displayed_text:
            return []
        words = self.displayed_text.split(" ")
        lines: List[str] = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if self.font.size(test)[0] > self.rect.width - 2 * self.padding:
                if current:
                    lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        return lines


# ---------------------------------------------------------------------------
# HealthBar / ExperienceBar
# ---------------------------------------------------------------------------

class HealthBar:
    """Animated health bar with rounded ends."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.current_hp = 100
        self.max_hp = 100
        self.display_hp = 100.0
        self.animation_speed = 120

    def set_hp(self, current: int, maximum: int):
        self.current_hp = max(0, current)
        self.max_hp = max(1, maximum)

    def update(self, dt: float):
        if self.display_hp != self.current_hp:
            change = self.animation_speed * dt
            if self.display_hp > self.current_hp:
                self.display_hp = max(self.current_hp, self.display_hp - change)
            else:
                self.display_hp = min(self.current_hp, self.display_hp + change)

    def draw(self, screen: pygame.Surface, show_text: bool = True):
        dpct = self.display_hp / self.max_hp if self.max_hp else 0

        # Use display_hp for color so the color smoothly transitions with the bar
        if dpct > 0.5:
            # Green-to-yellow gradient based on exact position
            bar_top = (96, 255, 130)
            bar_bot = (56, 200, 96)
        elif dpct > 0.25:
            bar_top = (255, 230, 60)
            bar_bot = (220, 180, 30)
        else:
            bar_top = (255, 90, 60)
            bar_bot = (200, 50, 40)

        # Track bg with shadow
        shadow_rect = pygame.Rect(self.rect.x + 1, self.rect.y + 1,
                                  self.rect.width, self.rect.height)
        _draw_rounded_rect(screen, (20, 20, 30), shadow_rect, radius=self.rect.height // 2)
        _draw_rounded_rect(screen, (40, 42, 55), self.rect, radius=self.rect.height // 2)

        # Inner bg
        inner = pygame.Rect(self.rect.x + 2, self.rect.y + 2,
                            self.rect.width - 4, self.rect.height - 4)
        _draw_rounded_rect(screen, (25, 28, 38), inner, radius=max(1, self.rect.height // 2 - 2))

        # Gradient fill
        if dpct > 0:
            fill_w = max(self.rect.height - 4, int(inner.width * dpct))
            fill_rect = pygame.Rect(inner.x, inner.y, fill_w, inner.height)
            _draw_gradient_rect(screen, fill_rect, bar_top, bar_bot,
                                radius=max(1, self.rect.height // 2 - 2))

            # Top highlight
            if fill_w > 6:
                hl = pygame.Surface((fill_w - 4, max(1, inner.height // 3)), pygame.SRCALPHA)
                hl.fill((255, 255, 255, 60))
                screen.blit(hl, (inner.x + 2, inner.y + 1))

        # Thin border
        _draw_rounded_rect(screen, (0, 0, 0, 0), self.rect, radius=self.rect.height // 2,
                           border=1, border_color=(60, 65, 85))

        if show_text:
            font = pygame.font.Font(None, 16)
            hp_text = f"{int(self.display_hp)}/{self.max_hp}"
            # Shadow for readability
            shadow_s = font.render(hp_text, True, (0, 0, 0))
            screen.blit(shadow_s, (self.rect.right + 7, self.rect.centery - shadow_s.get_height() // 2 + 1))
            ts = font.render(hp_text, True, Colors.TEXT_PRIMARY)
            screen.blit(ts, (self.rect.right + 6, self.rect.centery - ts.get_height() // 2))


class ExperienceBar:
    """Experience bar."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.current_exp = 0
        self.needed_exp = 100
        self.display_exp = 0.0
        self.animation_speed = 200

    def set_exp(self, current: int, needed: int):
        self.current_exp = max(0, current)
        self.needed_exp = max(1, needed)

    def update(self, dt: float):
        if self.display_exp != self.current_exp:
            change = self.animation_speed * dt
            if self.display_exp < self.current_exp:
                self.display_exp = min(self.current_exp, self.display_exp + change)
            else:
                self.display_exp = max(self.current_exp, self.display_exp - change)

    def draw(self, screen: pygame.Surface):
        dpct = self.display_exp / self.needed_exp if self.needed_exp else 0
        _draw_rounded_rect(screen, (40, 40, 55), self.rect, radius=self.rect.height // 2)
        if dpct > 0:
            fill_w = max(self.rect.height, int(self.rect.width * dpct))
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            _draw_rounded_rect(screen, Colors.EXP_BLUE, fill_rect, radius=self.rect.height // 2)


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

        # HP label
        hp_label = font_tiny.render("HP", True, Colors.TEXT_SECONDARY)
        screen.blit(hp_label, (self.rect.x + 14, self.rect.y + self.rect.height - 38))

        self.health_bar.draw(screen, show_text=True)
        if self.is_player and self.exp_bar:
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


# ---------------------------------------------------------------------------
# UI -- Main manager
# ---------------------------------------------------------------------------

class UI:
    """Main UI manager for the game."""

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

        # Pause menu
        self._pause_selected = 0

        # Pokemon menu
        self._pokemon_selected = 0

        # Bag menu
        self._bag_tab = 0
        self._bag_selected = 0
        self._bag_tabs = ["Medicine", "Pokeballs", "Battle", "Key Items"]
        self._bag_tab_categories = [
            [ItemCategory.HEALING, ItemCategory.STATUS],
            [ItemCategory.POKEBALL],
            [ItemCategory.BATTLE, ItemCategory.FIELD],
            [ItemCategory.KEY],
        ]

        # Main menu
        self._menu_selected = 0

        # Main menu particles (real drift motion)
        import random as _r
        _rng = _r.Random(42)
        self._menu_particles = []
        for _ in range(40):
            self._menu_particles.append({
                'x': _rng.uniform(0, self.screen_width),
                'y': _rng.uniform(0, self.screen_height),
                'vx': _rng.uniform(-12, 12),
                'vy': _rng.uniform(-8, 8),
                'phase': _rng.uniform(0, 6.28),
                'size': _rng.randint(2, 5),
                'pulse_speed': _rng.uniform(1.5, 4.0),
            })

        # Location banner
        self._location_name = ""
        self._location_alpha = 0.0
        self._location_timer = 0.0

        # Sprite cache
        self.sprite_cache: Dict[str, pygame.Surface] = {}

        # Cached surfaces
        self._battle_bg_cache: Optional[pygame.Surface] = None

        # Transition
        self.transition_alpha = 0
        self.transition_speed = 500
        self.transitioning = False

        # VS screen and battle fade-in
        self._vs_shown_for_battle = False
        self._battle_fade_alpha = 0.0
        self._battle_fading_in = False

        self._init_battle_ui()
        self._init_menu_ui()

    # ---- init helpers ----

    def _init_battle_ui(self):
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

    def _init_menu_ui(self):
        btn_w = 260
        btn_h = 52
        cx = self.screen_width // 2 - btn_w // 2
        icons = ["\u25B6", "\u25CF", "\u2699", "\u2716"]
        labels = ["New Game", "Continue", "Options", "Quit"]
        self.main_menu_buttons: List[Button] = []
        for i, (label, icon) in enumerate(zip(labels, icons)):
            self.main_menu_buttons.append(
                Button(cx, 300 + i * 70, btn_w, btn_h, label, self.font_medium, icon=icon)
            )
        # Continue grayed out by default
        self.main_menu_buttons[1].enabled = False
        self.main_menu_buttons[1].text_color = Colors.DARK_GRAY

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
        if name != self._location_name:
            self._location_name = name
            self._location_alpha = 0.0
            self._location_timer = 3.0  # seconds to display

    # ---- update ----

    def update(self, dt: float, game=None):
        self._time += dt

        # Transition fade
        if self.transitioning and self.transition_alpha > 0:
            self.transition_alpha = max(0, self.transition_alpha - self.transition_speed * dt)
            if self.transition_alpha == 0:
                self.transitioning = False

        # Location banner
        if self._location_timer > 0:
            self._location_timer -= dt
            if self._location_timer > 2.5:
                self._location_alpha = min(1.0, self._location_alpha + dt * 4)
            elif self._location_timer < 0.5:
                self._location_alpha = max(0.0, self._location_alpha - dt * 4)
            else:
                self._location_alpha = 1.0

        # Battle fade-in
        if self._battle_fading_in and self._battle_fade_alpha > 0:
            self._battle_fade_alpha = max(0, self._battle_fade_alpha - 400 * dt)
            if self._battle_fade_alpha <= 0:
                self._battle_fading_in = False

        # Battle state
        if self.state == UIState.BATTLE:
            self.battle_dialog.update(dt)
            self.player_info_panel.update(dt)
            self.opponent_info_panel.update(dt)
            self.battle_animation_manager.update(dt)

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
        else:
            # Reset VS flag and clear battle bg cache when not in battle
            if self._vs_shown_for_battle:
                self._vs_shown_for_battle = False
                self._battle_bg_cache = None
                self.battle_animation_manager.clear()

    # ---- event handling ----

    def handle_event(self, event: pygame.event.Event, game) -> bool:
        if self.state == UIState.MAIN_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self._menu_selected = (self._menu_selected - 1) % len(self.main_menu_buttons)
                    # Skip disabled
                    if not self.main_menu_buttons[self._menu_selected].enabled:
                        self._menu_selected = (self._menu_selected - 1) % len(self.main_menu_buttons)
                elif event.key == pygame.K_DOWN:
                    self._menu_selected = (self._menu_selected + 1) % len(self.main_menu_buttons)
                    if not self.main_menu_buttons[self._menu_selected].enabled:
                        self._menu_selected = (self._menu_selected + 1) % len(self.main_menu_buttons)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    idx = self._menu_selected
                    if idx == 0:
                        game.create_new_game()
                        return True
                    elif idx == 3:
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        return True
                for i, btn in enumerate(self.main_menu_buttons):
                    btn.selected = (i == self._menu_selected)

            for i, btn in enumerate(self.main_menu_buttons):
                if btn.handle_event(event):
                    if i == 0:
                        game.create_new_game()
                        return True
                    elif btn.callback:
                        btn.callback()
                    return True

        elif self.state == UIState.PAUSE_MENU:
            if event.type == pygame.KEYDOWN:
                items_count = 5  # Resume, Pokemon, Bag, Save, Quit
                if event.key == pygame.K_UP:
                    self._pause_selected = (self._pause_selected - 1) % items_count
                elif event.key == pygame.K_DOWN:
                    self._pause_selected = (self._pause_selected + 1) % items_count
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self._pause_selected == 0:  # Resume
                        game.toggle_pause()
                    elif self._pause_selected == 1:  # Pokemon
                        from . import game as gm
                        game.game_state = gm.GameState.POKEMON_MENU
                        self.state = UIState.POKEMON_MENU
                    elif self._pause_selected == 2:  # Bag
                        from . import game as gm
                        game.game_state = gm.GameState.BAG_MENU
                        self.state = UIState.BAG_MENU
                    elif self._pause_selected == 4:  # Quit to menu
                        self.state = UIState.MAIN_MENU
                        from . import game as gm
                        game.game_state = gm.GameState.MENU
                        game.game_started = False
                    return True
                elif event.key == pygame.K_ESCAPE:
                    game.toggle_pause()
                    return True

        elif self.state == UIState.POKEMON_MENU:
            if event.type == pygame.KEYDOWN:
                team_len = len(game.player.pokemon_team) if game.player else 0
                if event.key == pygame.K_UP:
                    self._pokemon_selected = max(0, self._pokemon_selected - 1)
                elif event.key == pygame.K_DOWN:
                    self._pokemon_selected = min(team_len - 1, self._pokemon_selected + 1)
                elif event.key == pygame.K_ESCAPE:
                    return False  # let game.py handle ESC
                return True

        elif self.state == UIState.BAG_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self._bag_tab = max(0, self._bag_tab - 1)
                    self._bag_selected = 0
                elif event.key == pygame.K_RIGHT:
                    self._bag_tab = min(len(self._bag_tabs) - 1, self._bag_tab + 1)
                    self._bag_selected = 0
                elif event.key == pygame.K_UP:
                    self._bag_selected = max(0, self._bag_selected - 1)
                elif event.key == pygame.K_DOWN:
                    self._bag_selected += 1
                elif event.key == pygame.K_ESCAPE:
                    return False
                return True

        elif self.state == UIState.BATTLE:
            # Block input during VS screen
            if self.battle_animation_manager.has_vs_screen():
                return True
            action = self.battle_menu.handle_event(event)
            if action and game.current_battle:
                action_type, params = action
                game.current_battle.set_player_action(action_type, **params)
                return True
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if not self.battle_dialog.is_complete:
                        self.battle_dialog.skip_animation()
                        return True

        return False

    # ================================================================
    # DRAW METHODS
    # ================================================================

    # ---- Main Menu / Title Screen ----

    def draw_main_menu(self):
        # Animated gradient background with richer color shifting
        t = self._time * 0.3
        # Draw every 2nd line for performance, doubling line width
        for y in range(0, self.screen_height, 2):
            ratio = y / self.screen_height
            r = int(15 + 12 * math.sin(t + ratio * 2))
            g = int(12 + 10 * math.sin(t * 0.7 + ratio * 3))
            b = int(35 + 25 * math.sin(t * 0.5 + ratio * 1.5))
            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            pygame.draw.line(self.screen, color, (0, y), (self.screen_width, y))
            if y + 1 < self.screen_height:
                pygame.draw.line(self.screen, color, (0, y + 1), (self.screen_width, y + 1))

        # Floating particles with real drift motion
        for p in self._menu_particles:
            p['x'] += p['vx'] * 0.016  # approx dt at 60fps
            p['y'] += p['vy'] * 0.016
            # Wrap around screen edges
            if p['x'] < -10:
                p['x'] = self.screen_width + 10
            elif p['x'] > self.screen_width + 10:
                p['x'] = -10
            if p['y'] < -10:
                p['y'] = self.screen_height + 10
            elif p['y'] > self.screen_height + 10:
                p['y'] = -10

            pulse = math.sin(self._time * p['pulse_speed'] + p['phase'])
            alpha = int(50 + 50 * pulse)
            size = p['size']
            glow_size = size + 2
            dot = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            # Outer glow
            pygame.draw.circle(dot, (80, 120, 255, max(0, alpha // 3)),
                               (glow_size, glow_size), glow_size)
            # Inner bright core
            pygame.draw.circle(dot, (120, 160, 255, max(0, alpha)),
                               (glow_size, glow_size), size)
            self.screen.blit(dot, (int(p['x']) - glow_size, int(p['y']) - glow_size))

        # Title with animated glow intensity
        title = "POKEMON"
        glow_pulse = 0.5 + 0.5 * math.sin(self._time * 1.5)

        # Glow layer (pulsing)
        glow_font = pygame.font.Font(None, 104)
        glow_surf = glow_font.render(title, True, (56, 128, 255))
        glow_surf.set_alpha(int(30 + 25 * glow_pulse))
        gr = glow_surf.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(glow_surf, gr)
        # Shadow
        shadow = self.font_title.render(title, True, (0, 0, 0))
        sr = shadow.get_rect(center=(self.screen_width // 2 + 3, 148 + 3))
        self.screen.blit(shadow, sr)
        # Main yellow text
        main_title = self.font_title.render(title, True, Colors.YELLOW)
        mr = main_title.get_rect(center=(self.screen_width // 2, 148))
        self.screen.blit(main_title, mr)

        # Subtitle
        sub = self.font_medium.render("Adventure Awaits!", True, Colors.TEXT_SECONDARY)
        self.screen.blit(sub, sub.get_rect(center=(self.screen_width // 2, 210)))

        # Decorative gradient divider
        line_y = 240
        line_w = 240
        lx = self.screen_width // 2 - line_w // 2
        divider = pygame.Surface((line_w, 2), pygame.SRCALPHA)
        for px in range(line_w):
            dist = abs(px - line_w // 2) / (line_w // 2)
            a = int(180 * (1 - dist))
            divider.set_at((px, 0), (56, 128, 255, a))
            divider.set_at((px, 1), (56, 128, 255, a // 2))
        self.screen.blit(divider, (lx, line_y))

        # Buttons
        for i, btn in enumerate(self.main_menu_buttons):
            btn.selected = (i == self._menu_selected)
            btn.draw(self.screen)

        # Check for save file and enable Continue button
        save_exists = os.path.exists("save_game.json") or os.path.exists("save_data.json")
        self.main_menu_buttons[1].enabled = save_exists
        self.main_menu_buttons[1].text_color = Colors.TEXT_PRIMARY if save_exists else Colors.DARK_GRAY

        # Version
        ver = self.font_small.render("v1.0.0", True, Colors.TEXT_SECONDARY)
        self.screen.blit(ver, (12, self.screen_height - 28))

    # ---- Pause Menu ----

    def draw_pause_menu(self, player: Player):
        # Full-screen dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 180))
        self.screen.blit(overlay, (0, 0))

        # Centered card
        card_w, card_h = 360, 380
        cx = (self.screen_width - card_w) // 2
        cy = (self.screen_height - card_h) // 2

        _draw_shadow(self.screen, (cx, cy, card_w, card_h), radius=16, offset=8, alpha=80)
        _draw_rounded_rect(self.screen, Colors.PANEL_BG, (cx, cy, card_w, card_h), radius=16)
        _draw_rounded_rect(self.screen, (0, 0, 0, 0), (cx, cy, card_w, card_h),
                           radius=16, border=2, border_color=Colors.CARD_BORDER)

        # Title bar
        _draw_gradient_rect(self.screen, (cx, cy, card_w, 50),
                            Colors.ACCENT_DARK, Colors.PANEL_BG, radius=16)
        title = self.font_large.render("PAUSED", True, Colors.TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(self.screen_width // 2, cy + 25)))

        # Menu items with distinctive icons
        items = [
            ("\u25B6", "Resume"),
            ("\u2605", "Pokemon"),
            ("\u25C6", "Bag"),
            ("\u25CF", "Save"),
            ("\u2715", "Quit to Menu"),
        ]
        item_h = 48
        start_y = cy + 70
        for i, (icon, label) in enumerate(items):
            iy = start_y + i * (item_h + 6)
            item_rect = (cx + 20, iy, card_w - 40, item_h)

            if i == self._pause_selected:
                _draw_rounded_rect(self.screen, Colors.BUTTON_HOVER, item_rect, radius=10)
                # Accent stripe
                _draw_rounded_rect(self.screen, Colors.ACCENT,
                                   (cx + 20, iy, 4, item_h), radius=2)
            else:
                _draw_rounded_rect(self.screen, (0, 0, 0, 0), item_rect, radius=10,
                                   border=1, border_color=Colors.CARD_BORDER)

            # Icon
            icon_surf = self.font_medium.render(icon, True, Colors.ACCENT_LIGHT)
            self.screen.blit(icon_surf, (cx + 40, iy + 12))
            # Label
            lbl_surf = self.font_medium.render(label, True, Colors.TEXT_PRIMARY)
            self.screen.blit(lbl_surf, (cx + 75, iy + 12))

    # ---- Pokemon Team Menu ----

    def draw_pokemon_menu(self, player: Player):
        if not player:
            return
        # Semi-transparent dark overlay (world renders underneath in game.py)
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 210))
        self.screen.blit(overlay, (0, 0))

        # Header
        _draw_gradient_rect(self.screen, (0, 0, self.screen_width, 60),
                            Colors.ACCENT_DARK, Colors.OVERLAY)
        title = self.font_large.render("POKEMON TEAM", True, Colors.TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(self.screen_width // 2, 30)))

        if not player or not player.pokemon_team:
            empty = self.font_medium.render("No Pokemon in team!", True, Colors.TEXT_SECONDARY)
            self.screen.blit(empty, empty.get_rect(center=(self.screen_width // 2,
                                                           self.screen_height // 2)))
            return

        # Card list layout
        card_w = 560
        card_h_normal = 90
        card_h_expanded = 170
        gap = 10
        base_x = (self.screen_width - card_w) // 2
        cur_y = 80

        for i, pokemon in enumerate(player.pokemon_team):
            is_selected = (i == self._pokemon_selected)
            ch = card_h_expanded if is_selected else card_h_normal
            card_rect = (base_x, cur_y, card_w, ch)

            # Shadow + bg
            _draw_shadow(self.screen, card_rect, radius=12, offset=4, alpha=50)
            bg_color = Colors.PANEL_BG_LIGHT if is_selected else Colors.PANEL_BG
            if pokemon.is_fainted:
                bg_color = (50, 30, 30)
            _draw_rounded_rect(self.screen, bg_color, card_rect, radius=12)
            border_c = Colors.ACCENT if is_selected else Colors.CARD_BORDER
            _draw_rounded_rect(self.screen, (0, 0, 0, 0), card_rect, radius=12,
                               border=2, border_color=border_c)

            # Sprite circle with shadow
            sprite_cx = base_x + 50
            sprite_cy = cur_y + 45
            pcolor = Colors.TYPE_COLORS.get(
                pokemon.types[0] if pokemon.types else PokemonType.NORMAL, Colors.GRAY
            )
            sprite_fn = f"{pokemon.species_id}_normal.png"
            sprite_path = os.path.join("assets", "sprites", sprite_fn)
            sprite = self.load_sprite(sprite_path, (64, 64))

            # Drop shadow behind sprite area
            shadow_s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(shadow_s, (0, 0, 0, 40), (30, 32), 28)
            self.screen.blit(shadow_s, (sprite_cx - 30, sprite_cy - 28))

            if sprite:
                spr_rect = sprite.get_rect(center=(sprite_cx, sprite_cy))
                self.screen.blit(sprite, spr_rect)
            else:
                pygame.draw.circle(self.screen, pcolor, (sprite_cx, sprite_cy), 28)
                inner_c = tuple(min(255, c + 40) for c in pcolor)
                pygame.draw.circle(self.screen, inner_c, (sprite_cx - 3, sprite_cy - 4), 20)
                hl_c = tuple(min(255, c + 80) for c in pcolor)
                pygame.draw.circle(self.screen, hl_c, (sprite_cx - 8, sprite_cy - 10), 8)
                pygame.draw.circle(self.screen, (0, 0, 0), (sprite_cx, sprite_cy), 28, 2)
                init = self.font_small.render(pokemon.species_name[:3], True, Colors.WHITE)
                self.screen.blit(init, init.get_rect(center=(sprite_cx, sprite_cy + 2)))

            # Shiny indicator
            if getattr(pokemon, 'is_shiny', False):
                star_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                # Small golden star
                pts = []
                for si in range(10):
                    angle = (si / 10) * 2 * math.pi - math.pi / 2
                    r = 7 if si % 2 == 0 else 3
                    pts.append((8 + math.cos(angle) * r, 8 + math.sin(angle) * r))
                pygame.draw.polygon(star_surf, (255, 215, 0, 220), pts)
                self.screen.blit(star_surf, (sprite_cx + 18, sprite_cy - 28))

            # Name + Level
            info_x = base_x + 95
            name_surf = self.font_medium.render(
                f"{pokemon.nickname}", True, Colors.TEXT_PRIMARY
            )
            self.screen.blit(name_surf, (info_x, cur_y + 12))
            lvl_surf = self.font_small.render(
                f"Lv. {pokemon.level}", True, Colors.TEXT_SECONDARY
            )
            self.screen.blit(lvl_surf, (info_x + name_surf.get_width() + 10, cur_y + 16))

            # Type badges
            badge_x = info_x
            for pt in pokemon.types:
                bw = _draw_type_badge(self.screen, pt, badge_x, cur_y + 38,
                                      pygame.font.Font(None, 16))
                badge_x += bw + 6

            # HP bar
            hp_pct = pokemon.current_hp / pokemon.stats["hp"] if pokemon.stats["hp"] else 0
            hp_bar_x = info_x
            hp_bar_y = cur_y + 60
            hp_bar_w = card_w - 140
            hp_bar_h = 8
            hp_color = Colors.HP_GREEN if hp_pct > 0.5 else Colors.HP_YELLOW if hp_pct > 0.25 else Colors.HP_RED
            _draw_rounded_rect(self.screen, (40, 40, 55), (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h),
                               radius=4)
            if hp_pct > 0:
                fill_w = max(hp_bar_h, int(hp_bar_w * hp_pct))
                _draw_rounded_rect(self.screen, hp_color,
                                   (hp_bar_x, hp_bar_y, fill_w, hp_bar_h), radius=4)
            hp_txt = self.font_small.render(
                f"{pokemon.current_hp}/{pokemon.stats['hp']}", True, Colors.TEXT_SECONDARY
            )
            self.screen.blit(hp_txt, (hp_bar_x + hp_bar_w + 8, hp_bar_y - 2))

            # Status dot
            if pokemon.status != StatusCondition.NONE:
                sc = Colors.STATUS_COLORS.get(pokemon.status, Colors.RED)
                dot_x = base_x + card_w - 30
                dot_y = cur_y + 15
                pygame.draw.circle(self.screen, sc, (dot_x, dot_y), 6)
                st_label = self.font_small.render(pokemon.status.value[:3].upper(),
                                                  True, sc)
                self.screen.blit(st_label, (dot_x - st_label.get_width() - 4, dot_y - 6))

            # Expanded details
            if is_selected:
                detail_y = cur_y + 85
                # Moves
                moves_title = self.font_small.render("MOVES:", True, Colors.TEXT_SECONDARY)
                self.screen.blit(moves_title, (info_x, detail_y))
                for mi, move in enumerate(pokemon.moves[:4]):
                    mx = info_x + (mi % 2) * 200
                    my = detail_y + 20 + (mi // 2) * 22
                    mc = Colors.TYPE_COLORS.get(move.type, Colors.TEXT_SECONDARY)
                    ms = self.font_small.render(f"{move.name} ({move.current_pp}/{move.pp})",
                                               True, mc)
                    self.screen.blit(ms, (mx, my))

                # Stats summary
                stat_x = info_x
                stat_y = detail_y + 65
                stats_text = (f"ATK:{pokemon.stats.get('attack', 0)} "
                              f"DEF:{pokemon.stats.get('defense', 0)} "
                              f"SPD:{pokemon.stats.get('speed', 0)}")
                sts = self.font_small.render(stats_text, True, Colors.TEXT_SECONDARY)
                self.screen.blit(sts, (stat_x, stat_y))

            cur_y += ch + gap

        # Footer
        footer = self.font_small.render(
            "UP/DOWN: Select  |  ESC: Back", True, Colors.TEXT_SECONDARY
        )
        self.screen.blit(footer, footer.get_rect(center=(self.screen_width // 2,
                                                         self.screen_height - 25)))

    # ---- Bag / Inventory Menu ----

    def draw_bag_menu(self, player: Player):
        if not player:
            return
        # Semi-transparent dark overlay (world renders underneath in game.py)
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 210))
        self.screen.blit(overlay, (0, 0))

        # Header
        _draw_gradient_rect(self.screen, (0, 0, self.screen_width, 60),
                            Colors.ACCENT_DARK, Colors.OVERLAY)
        title = self.font_large.render("BAG", True, Colors.TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(self.screen_width // 2, 30)))

        # Tabs
        tab_w = self.screen_width // len(self._bag_tabs)
        for i, tab_name in enumerate(self._bag_tabs):
            tx = i * tab_w
            is_active = (i == self._bag_tab)
            tab_rect = (tx + 4, 70, tab_w - 8, 36)
            bg = Colors.ACCENT_DARK if is_active else Colors.PANEL_BG
            _draw_rounded_rect(self.screen, bg, tab_rect, radius=8)
            if is_active:
                _draw_rounded_rect(self.screen, (0, 0, 0, 0), tab_rect, radius=8,
                                   border=2, border_color=Colors.ACCENT)
            tc = Colors.TEXT_PRIMARY if is_active else Colors.TEXT_SECONDARY
            ts = self.font_small.render(tab_name, True, tc)
            self.screen.blit(ts, ts.get_rect(center=(tx + tab_w // 2, 88)))

        # Get items for current tab
        allowed_cats = self._bag_tab_categories[self._bag_tab]
        items_list: List[Tuple[str, int, str]] = []
        for item_id, qty in player.inventory.items():
            if qty <= 0:
                continue
            item_def = ITEM_REGISTRY.get(item_id)
            if item_def and item_def.category in allowed_cats:
                items_list.append((item_id, qty, item_def.name))
            elif not item_def and self._bag_tab == 3:  # unknown -> key items
                items_list.append((item_id, qty, item_id.replace("_", " ").title()))

        # Clamp selection
        if self._bag_selected >= len(items_list):
            self._bag_selected = max(0, len(items_list) - 1)

        # Layout: item list on left, description on right
        list_x = 40
        list_y = 120
        list_w = self.screen_width // 2 - 60
        list_h = self.screen_height - 180

        # List panel
        _draw_rounded_rect(self.screen, Colors.PANEL_BG, (list_x, list_y, list_w, list_h),
                           radius=12)
        _draw_rounded_rect(self.screen, (0, 0, 0, 0), (list_x, list_y, list_w, list_h),
                           radius=12, border=1, border_color=Colors.CARD_BORDER)

        # Description panel
        desc_x = self.screen_width // 2 + 20
        desc_w = self.screen_width // 2 - 60
        _draw_rounded_rect(self.screen, Colors.PANEL_BG,
                           (desc_x, list_y, desc_w, list_h), radius=12)
        _draw_rounded_rect(self.screen, (0, 0, 0, 0),
                           (desc_x, list_y, desc_w, list_h),
                           radius=12, border=1, border_color=Colors.CARD_BORDER)

        if not items_list:
            empty = self.font_medium.render("No items", True, Colors.TEXT_SECONDARY)
            self.screen.blit(empty, (list_x + 20, list_y + 20))
        else:
            item_h = 44
            for idx, (item_id, qty, display_name) in enumerate(items_list):
                iy = list_y + 10 + idx * (item_h + 4)
                if iy + item_h > list_y + list_h - 10:
                    break

                ir = (list_x + 8, iy, list_w - 16, item_h)
                if idx == self._bag_selected:
                    _draw_rounded_rect(self.screen, Colors.BUTTON_HOVER, ir, radius=8)
                    _draw_rounded_rect(self.screen, (0, 0, 0, 0), ir, radius=8,
                                       border=2, border_color=Colors.ACCENT)
                else:
                    _draw_rounded_rect(self.screen, (0, 0, 0, 0), ir, radius=8,
                                       border=1, border_color=(50, 50, 70))

                # Item name
                ns = self.font_medium.render(display_name, True, Colors.TEXT_PRIMARY)
                self.screen.blit(ns, (list_x + 22, iy + 10))

                # Quantity badge
                qty_text = f"x{qty}"
                qs = self.font_small.render(qty_text, True, Colors.TEXT_SECONDARY)
                qw = qs.get_width() + 12
                qr = (list_x + list_w - qw - 20, iy + 10, qw, 24)
                _draw_rounded_rect(self.screen, (60, 60, 85), qr, radius=6)
                self.screen.blit(qs, (qr[0] + 6, qr[1] + 4))

            # Description for selected
            if 0 <= self._bag_selected < len(items_list):
                sel_id = items_list[self._bag_selected][0]
                sel_item = ITEM_REGISTRY.get(sel_id)
                desc_title = self.font_medium.render(
                    sel_item.name if sel_item else sel_id, True, Colors.TEXT_PRIMARY
                )
                self.screen.blit(desc_title, (desc_x + 20, list_y + 20))

                # Divider
                pygame.draw.line(self.screen, Colors.CARD_BORDER,
                                 (desc_x + 20, list_y + 50),
                                 (desc_x + desc_w - 20, list_y + 50))

                if sel_item:
                    desc_text = sel_item.description
                    ds = self.font_small.render(desc_text, True, Colors.TEXT_SECONDARY)
                    self.screen.blit(ds, (desc_x + 20, list_y + 65))

                    # Category
                    cat_text = f"Category: {sel_item.category.value.title()}"
                    cs = self.font_small.render(cat_text, True, Colors.TEXT_SECONDARY)
                    self.screen.blit(cs, (desc_x + 20, list_y + 95))

                    # Price
                    if sel_item.price > 0:
                        price_text = f"Price: ${sel_item.price}"
                        ps = self.font_small.render(price_text, True, Colors.YELLOW)
                        self.screen.blit(ps, (desc_x + 20, list_y + 120))

                    # Use button hint
                    use_hint = self.font_small.render(
                        "Press ENTER to use", True, Colors.ACCENT_LIGHT
                    )
                    self.screen.blit(use_hint, (desc_x + 20, list_y + list_h - 40))

        # Footer
        footer = self.font_small.render(
            "LEFT/RIGHT: Tab  |  UP/DOWN: Select  |  ESC: Back", True, Colors.TEXT_SECONDARY
        )
        self.screen.blit(footer, footer.get_rect(center=(self.screen_width // 2,
                                                         self.screen_height - 20)))

    # ---- World HUD ----

    def draw_world_hud(self, player: Player):
        if not player:
            return

        # -- Location banner (top center, fade in/out) --
        if self._location_alpha > 0 and self._location_name:
            banner_w = max(200, self.font_medium.size(self._location_name)[0] + 60)
            banner_h = 36
            bx = (self.screen_width - banner_w) // 2
            by = 12
            banner_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            alpha_val = int(self._location_alpha * 200)
            pygame.draw.rect(banner_surf, (20, 20, 40, alpha_val),
                             (0, 0, banner_w, banner_h), border_radius=10)
            pygame.draw.rect(banner_surf, (*Colors.ACCENT, alpha_val),
                             (0, 0, banner_w, banner_h), width=2, border_radius=10)
            loc_text = self.font_medium.render(self._location_name, True,
                                              (*Colors.TEXT_PRIMARY[:3],))
            loc_text.set_alpha(int(self._location_alpha * 255))
            banner_surf.blit(loc_text, loc_text.get_rect(center=(banner_w // 2, banner_h // 2)))
            self.screen.blit(banner_surf, (bx, by))

        # -- Top-right: lead Pokemon mini info --
        if player.active_pokemon:
            p = player.active_pokemon
            mini_w = 180
            mini_h = 50
            mx = self.screen_width - mini_w - 12
            my = 12

            mini_surf = pygame.Surface((mini_w, mini_h), pygame.SRCALPHA)
            pygame.draw.rect(mini_surf, (20, 20, 40, 170),
                             (0, 0, mini_w, mini_h), border_radius=10)
            pygame.draw.rect(mini_surf, (*Colors.CARD_BORDER, 170),
                             (0, 0, mini_w, mini_h), width=1, border_radius=10)

            # Pokemon name
            nf = pygame.font.Font(None, 18)
            ns = nf.render(f"{p.nickname} Lv.{p.level}", True, Colors.TEXT_PRIMARY)
            mini_surf.blit(ns, (10, 6))

            # HP bar
            hp_pct = p.current_hp / p.stats["hp"] if p.stats["hp"] else 0
            hc = Colors.HP_GREEN if hp_pct > 0.5 else Colors.HP_YELLOW if hp_pct > 0.25 else Colors.HP_RED
            bar_x, bar_y, bar_w, bar_h = 10, 28, mini_w - 20, 7
            pygame.draw.rect(mini_surf, (40, 40, 55),
                             (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            if hp_pct > 0:
                fw = max(bar_h, int(bar_w * hp_pct))
                pygame.draw.rect(mini_surf, hc, (bar_x, bar_y, fw, bar_h), border_radius=3)

            hp_txt = nf.render(f"{p.current_hp}/{p.stats['hp']}", True, Colors.TEXT_SECONDARY)
            mini_surf.blit(hp_txt, (10, 38))

            self.screen.blit(mini_surf, (mx, my))

        # -- Bottom: context action hint --
        hint_text = "SPACE: Interact  |  P: Pokemon  |  I: Items  |  ESC: Menu"
        hint_surf = pygame.Surface((self.screen_width, 30), pygame.SRCALPHA)
        hint_surf.fill((10, 10, 20, 130))
        ht = self.font_small.render(hint_text, True, Colors.TEXT_SECONDARY)
        hint_surf.blit(ht, ht.get_rect(center=(self.screen_width // 2, 15)))
        self.screen.blit(hint_surf, (0, self.screen_height - 30))

    # ---- Battle ----

    def draw_battle(self, battle: Battle):
        shake_offset = self.battle_animation_manager.get_screen_offset()
        if shake_offset != (0, 0):
            temp = pygame.Surface((self.screen_width, self.screen_height))
            self._draw_battle_content(temp, battle)
            self.screen.blit(temp, shake_offset)
        else:
            self._draw_battle_content(self.screen, battle)
        self.battle_animation_manager.render(self.screen)

        # VS screen overlay
        player_name = battle.player_pokemon.nickname if battle.player_pokemon else ""
        opponent_name = battle.opponent_pokemon.species_name if battle.opponent_pokemon else ""
        self.battle_animation_manager.render_vs_screen(
            self.screen, player_name, opponent_name)

        # Battle fade-in overlay
        if self._battle_fade_alpha > 0:
            fade_surf = pygame.Surface((self.screen_width, self.screen_height))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(int(self._battle_fade_alpha))
            self.screen.blit(fade_surf, (0, 0))

    def _draw_battle_content(self, surface: pygame.Surface, battle: Battle):
        self._draw_battle_background_on_surface(surface)

        self.battle_menu.set_battle(battle)
        self.player_info_panel.set_pokemon(battle.player_pokemon)
        self.opponent_info_panel.set_pokemon(battle.opponent_pokemon)

        if battle.battle_log:
            latest = battle.battle_log[-1]
            if self.battle_dialog.text != latest:
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
            self._draw_battle_end_message(surface)

        if battle.state == BattleState.TURN_EXECUTION and battle.last_used_move:
            self._draw_type_effectiveness(battle)

        if hasattr(battle, "_move_just_used") and battle._move_just_used:
            self._trigger_move_animation(battle._move_just_used, battle._move_target_pos)
            battle._move_just_used = None

    def _draw_battle_background_on_surface(self, surface: pygame.Surface):
        """Draw a polished battle background with gradient sky and ground.

        The background is cached after first render for performance.
        """
        if self._battle_bg_cache is not None:
            surface.blit(self._battle_bg_cache, (0, 0))
            return

        bg = pygame.Surface((self.screen_width, self.screen_height))
        horizon_y = self.screen_height * 45 // 100

        # Sky gradient (deep blue top -> light cyan at horizon)
        for y_pos in range(horizon_y):
            ratio = y_pos / horizon_y
            r = int(70 + 130 * ratio)
            g = int(130 + 110 * ratio)
            b = int(200 + 50 * ratio)
            pygame.draw.line(bg, (r, g, b), (0, y_pos), (self.screen_width, y_pos))

        # Subtle clouds
        cloud_surf = pygame.Surface((self.screen_width, horizon_y), pygame.SRCALPHA)
        cloud_color = (240, 245, 255, 55)
        for cx, cy, cw, ch in [(200, 50, 180, 40), (500, 30, 220, 50),
                                (850, 60, 160, 35), (1100, 40, 200, 45)]:
            for j in range(3):
                ofs = j * 30
                pygame.draw.ellipse(cloud_surf, cloud_color,
                                    (cx + ofs - 20, cy - 5, cw // 2, ch))
        bg.blit(cloud_surf, (0, 0))

        # Ground gradient (light green top -> darker green bottom)
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

        # Subtle grass patches
        for gx in range(0, self.screen_width, 50):
            for gy in range(ground_start + 10, self.screen_height, 50):
                shade = 10 if (gx + gy) % 100 == 0 else -5
                patch_c = (max(0, 130 + shade), max(0, 190 + shade), max(0, 110 + shade))
                pygame.draw.circle(bg, patch_c, (gx + 25, gy + 25), 12)

        # Horizon line with subtle glow
        horizon_glow = pygame.Surface((self.screen_width, 6), pygame.SRCALPHA)
        horizon_glow.fill((180, 220, 180, 40))
        bg.blit(horizon_glow, (0, horizon_y - 3))
        pygame.draw.line(bg, (160, 210, 160),
                         (0, horizon_y), (self.screen_width, horizon_y), 2)

        # Player platform (with shadow, highlight, border)
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
            # Shadow behind sprite
            shadow_s = pygame.Surface((104, 104), pygame.SRCALPHA)
            pygame.draw.circle(shadow_s, (0, 0, 0, 60), (52, 54), 50)
            surface.blit(shadow_s, (position[0] - 52, position[1] - 52))
            # Main body
            pygame.draw.circle(surface, pcolor, position, 48)
            # Inner lighter circle for depth
            inner_c = tuple(min(255, c + 40) for c in pcolor)
            pygame.draw.circle(surface, inner_c, (position[0] - 5, position[1] - 8), 34)
            # Small highlight
            hl_c = tuple(min(255, c + 80) for c in pcolor)
            pygame.draw.circle(surface, hl_c, (position[0] - 12, position[1] - 16), 14)
            # Border
            pygame.draw.circle(surface, Colors.BLACK, position, 48, 3)
            # Name with shadow for readability
            shadow_text = self.font_small.render(pokemon.species_name, True, (0, 0, 0))
            surface.blit(shadow_text, shadow_text.get_rect(center=(position[0] + 1, position[1] + 1)))
            ns = self.font_small.render(pokemon.species_name, True, Colors.WHITE)
            surface.blit(ns, ns.get_rect(center=position))

    def _draw_type_effectiveness(self, battle: Battle):
        pass

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

        # Add floating damage number for damaging moves
        if move.category != "status" and move.power > 0:
            self.battle_animation_manager.add_damage_popup(
                (target_pos[0], target_pos[1] - 30),
                move.power, is_critical=False, effectiveness=1.0
            )

        # Screen shake for powerful moves
        if move.power >= 100:
            self.battle_animation_manager.add_animation(AnimationType.SHAKE, target_pos)

    def _draw_battle_end_message(self, surface: pygame.Surface):
        # Centered card-style result banner
        banner_w = 500
        banner_h = 120
        bx = (self.screen_width - banner_w) // 2
        by = (self.screen_height - banner_h) // 2

        _draw_shadow(surface, (bx, by, banner_w, banner_h), radius=16, offset=6, alpha=80)
        _draw_rounded_rect(surface, (20, 20, 36, 230), (bx, by, banner_w, banner_h), radius=16)
        _draw_rounded_rect(surface, (0, 0, 0, 0), (bx, by, banner_w, banner_h),
                           radius=16, border=2, border_color=Colors.ACCENT_DARK)

        # Top accent line
        accent_rect = (bx + 2, by + 2, banner_w - 4, 4)
        _draw_rounded_rect(surface, Colors.ACCENT, accent_rect, radius=2)

        msg = self.font_large.render("Battle Complete!", True, Colors.TEXT_PRIMARY)
        surface.blit(msg, msg.get_rect(center=(self.screen_width // 2, by + 45)))

        # Pulsing continue text
        pulse = 0.7 + 0.3 * math.sin(self._time * 3)
        sub_color = tuple(int(c * pulse) for c in Colors.TEXT_SECONDARY)
        sub = self.font_medium.render("Press SPACE / ENTER to continue",
                                      True, sub_color)
        surface.blit(sub, sub.get_rect(center=(self.screen_width // 2, by + 85)))

    # ---- Transition ----

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
