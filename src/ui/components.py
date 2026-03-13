"""
UI Components - Colors, drawing helpers, Button, HealthBar, ExperienceBar
"""

import pygame
import math
from typing import Optional, Callable, List

from ..pokemon import PokemonType, StatusCondition


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
# HealthBar / ExperienceBar
# ---------------------------------------------------------------------------

class HealthBar:
    """Animated health bar with rounded ends."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.current_hp = 0
        self.max_hp = 1
        self.display_hp = 0.0
        self.animation_speed = 120
        self._initialized = False

    def set_hp(self, current: int, maximum: int):
        self.current_hp = max(0, current)
        self.max_hp = max(1, maximum)
        if not self._initialized:
            self.display_hp = float(self.current_hp)
            self._initialized = True

    def update(self, dt: float):
        if self.display_hp != self.current_hp:
            change = self.animation_speed * dt
            if self.display_hp > self.current_hp:
                self.display_hp = max(self.current_hp, self.display_hp - change)
            else:
                self.display_hp = min(self.current_hp, self.display_hp + change)

    def draw(self, screen: pygame.Surface, show_text: bool = True):
        dpct = min(1.0, self.display_hp / self.max_hp) if self.max_hp else 0

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
            hp_text = f"{self.current_hp}/{self.max_hp}"
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
        dpct = min(1.0, self.display_exp / self.needed_exp) if self.needed_exp else 0
        _draw_rounded_rect(screen, (40, 40, 55), self.rect, radius=self.rect.height // 2)
        if dpct > 0:
            fill_w = max(self.rect.height, int(self.rect.width * dpct))
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            _draw_rounded_rect(screen, Colors.EXP_BLUE, fill_rect, radius=self.rect.height // 2)
