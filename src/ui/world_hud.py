"""
World HUD - World overlay drawing, location banner, context action hints
"""

import pygame

from ..player import Player

from .components import Colors


class WorldHUD:
    """Draws world HUD elements: location banner, lead Pokemon info, action hints."""

    def __init__(self, screen: pygame.Surface, font_small, font_medium):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.font_small = font_small
        self.font_medium = font_medium

        # Location banner
        self._location_name = ""
        self._location_alpha = 0.0
        self._location_timer = 0.0

    def show_location(self, name: str):
        """Show a location banner that fades in and out."""
        display_name = name.replace('_', ' ').title()
        if display_name != self._location_name:
            self._location_name = display_name
            self._location_alpha = 0.0
            self._location_timer = 3.0

    def update(self, dt: float):
        if self._location_timer > 0:
            self._location_timer -= dt
            if self._location_timer > 2.5:
                self._location_alpha = min(1.0, self._location_alpha + dt * 4)
            elif self._location_timer < 0.5:
                self._location_alpha = max(0.0, self._location_alpha - dt * 4)
            else:
                self._location_alpha = 1.0

    def draw(self, player: Player):
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
            mini_w = 220
            mini_h = 62
            mx = self.screen_width - mini_w - 12
            my = 12

            mini_surf = pygame.Surface((mini_w, mini_h), pygame.SRCALPHA)
            pygame.draw.rect(mini_surf, (20, 20, 40, 185),
                             (0, 0, mini_w, mini_h), border_radius=10)
            pygame.draw.rect(mini_surf, (*Colors.CARD_BORDER, 185),
                             (0, 0, mini_w, mini_h), width=1, border_radius=10)

            name_font = pygame.font.Font(None, 22)
            ns = name_font.render(p.nickname, True, Colors.TEXT_PRIMARY)
            mini_surf.blit(ns, (10, 7))
            lv_font = pygame.font.Font(None, 19)
            lv_surf = lv_font.render(f"Lv.{p.level}", True, Colors.TEXT_SECONDARY)
            mini_surf.blit(lv_surf, (mini_w - 10 - lv_surf.get_width(), 9))

            hp_pct = p.current_hp / p.stats["hp"] if p.stats["hp"] else 0
            hc = Colors.HP_GREEN if hp_pct > 0.5 else Colors.HP_YELLOW if hp_pct > 0.25 else Colors.HP_RED
            bar_x, bar_y, bar_w, bar_h = 10, 30, mini_w - 20, 10
            pygame.draw.rect(mini_surf, (40, 40, 55),
                             (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            if hp_pct > 0:
                fw = max(bar_h, int(bar_w * hp_pct))
                pygame.draw.rect(mini_surf, hc, (bar_x, bar_y, fw, bar_h), border_radius=4)

            hp_font = pygame.font.Font(None, 19)
            hp_txt = hp_font.render(f"HP {p.current_hp}/{p.stats['hp']}", True, Colors.TEXT_SECONDARY)
            mini_surf.blit(hp_txt, (10, 44))

            self.screen.blit(mini_surf, (mx, my))

        # -- Bottom: context action hint --
        hint_text = "SPACE: Interact  |  P: Pokemon  |  I: Items  |  ESC: Menu"
        hint_surf = pygame.Surface((self.screen_width, 30), pygame.SRCALPHA)
        hint_surf.fill((10, 10, 20, 130))
        ht = self.font_small.render(hint_text, True, Colors.TEXT_SECONDARY)
        hint_surf.blit(ht, ht.get_rect(center=(self.screen_width // 2, 15)))
        self.screen.blit(hint_surf, (0, self.screen_height - 30))
