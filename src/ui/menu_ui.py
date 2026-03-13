"""
Menu UI - Main menu, pause menu, Pokemon team menu, bag menu
"""

import pygame
import os
import math
from typing import Optional, List, Tuple, Dict

from ..player import Player
from ..pokemon import PokemonType, StatusCondition
from ..items import ITEM_REGISTRY, ItemCategory

from .components import (
    Colors, Button,
    _draw_rounded_rect, _draw_shadow, _draw_gradient_rect, _draw_type_badge,
)


class MenuUI:
    """Handles rendering and event handling for all menu screens."""

    def __init__(self, screen: pygame.Surface, sprite_cache: Dict,
                 font_small, font_medium, font_large, font_huge, font_title):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.sprite_cache = sprite_cache
        self.font_small = font_small
        self.font_medium = font_medium
        self.font_large = font_large
        self.font_huge = font_huge
        self.font_title = font_title

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

        self._init_menu_buttons()

    def _init_menu_buttons(self):
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

    # ---- Event Handling ----

    def handle_main_menu_event(self, event, game) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._menu_selected = (self._menu_selected - 1) % len(self.main_menu_buttons)
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

        return False

    def handle_pause_menu_event(self, event, game, ui_state_setter) -> bool:
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
                    from .. import game as gm
                    game.game_state = gm.GameState.POKEMON_MENU
                    ui_state_setter("POKEMON_MENU")
                elif self._pause_selected == 2:  # Bag
                    from .. import game as gm
                    game.game_state = gm.GameState.BAG_MENU
                    ui_state_setter("BAG_MENU")
                elif self._pause_selected == 4:  # Quit to menu
                    ui_state_setter("MAIN_MENU")
                    from .. import game as gm
                    game.game_state = gm.GameState.MENU
                    game.game_started = False
                return True
            elif event.key == pygame.K_ESCAPE:
                game.toggle_pause()
                return True
        return False

    def handle_pokemon_menu_event(self, event, game) -> bool:
        if event.type == pygame.KEYDOWN:
            team_len = len(game.player.pokemon_team) if game.player else 0
            if event.key == pygame.K_UP:
                self._pokemon_selected = max(0, self._pokemon_selected - 1)
            elif event.key == pygame.K_DOWN:
                self._pokemon_selected = min(team_len - 1, self._pokemon_selected + 1)
            elif event.key == pygame.K_ESCAPE:
                return False  # let game.py handle ESC
            return True
        return False

    def handle_bag_menu_event(self, event, game) -> bool:
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
        return False

    # ---- Drawing ----

    def draw_main_menu(self, time_val: float):
        t = time_val * 0.3
        for y in range(0, self.screen_height, 2):
            ratio = y / self.screen_height
            r = int(15 + 12 * math.sin(t + ratio * 2))
            g = int(12 + 10 * math.sin(t * 0.7 + ratio * 3))
            b = int(35 + 25 * math.sin(t * 0.5 + ratio * 1.5))
            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            pygame.draw.line(self.screen, color, (0, y), (self.screen_width, y))
            if y + 1 < self.screen_height:
                pygame.draw.line(self.screen, color, (0, y + 1), (self.screen_width, y + 1))

        for p in self._menu_particles:
            p['x'] += p['vx'] * 0.016
            p['y'] += p['vy'] * 0.016
            if p['x'] < -10:
                p['x'] = self.screen_width + 10
            elif p['x'] > self.screen_width + 10:
                p['x'] = -10
            if p['y'] < -10:
                p['y'] = self.screen_height + 10
            elif p['y'] > self.screen_height + 10:
                p['y'] = -10

            pulse = math.sin(time_val * p['pulse_speed'] + p['phase'])
            alpha = int(50 + 50 * pulse)
            size = p['size']
            glow_size = size + 2
            dot = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (80, 120, 255, max(0, alpha // 3)),
                               (glow_size, glow_size), glow_size)
            pygame.draw.circle(dot, (120, 160, 255, max(0, alpha)),
                               (glow_size, glow_size), size)
            self.screen.blit(dot, (int(p['x']) - glow_size, int(p['y']) - glow_size))

        title = "POKEMON"
        glow_pulse = 0.5 + 0.5 * math.sin(time_val * 1.5)

        glow_font = pygame.font.Font(None, 104)
        glow_surf = glow_font.render(title, True, (56, 128, 255))
        glow_surf.set_alpha(int(30 + 25 * glow_pulse))
        gr = glow_surf.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(glow_surf, gr)
        shadow = self.font_title.render(title, True, (0, 0, 0))
        sr = shadow.get_rect(center=(self.screen_width // 2 + 3, 148 + 3))
        self.screen.blit(shadow, sr)
        main_title = self.font_title.render(title, True, Colors.YELLOW)
        mr = main_title.get_rect(center=(self.screen_width // 2, 148))
        self.screen.blit(main_title, mr)

        sub = self.font_medium.render("Adventure Awaits!", True, Colors.TEXT_SECONDARY)
        self.screen.blit(sub, sub.get_rect(center=(self.screen_width // 2, 210)))

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

        for i, btn in enumerate(self.main_menu_buttons):
            btn.selected = (i == self._menu_selected)
            btn.draw(self.screen)

        save_exists = os.path.exists("save_game.json") or os.path.exists("save_data.json")
        self.main_menu_buttons[1].enabled = save_exists
        self.main_menu_buttons[1].text_color = Colors.TEXT_PRIMARY if save_exists else Colors.DARK_GRAY

        ver = self.font_small.render("v1.0.0", True, Colors.TEXT_SECONDARY)
        self.screen.blit(ver, (12, self.screen_height - 28))

    def draw_pause_menu(self, player: Player):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 180))
        self.screen.blit(overlay, (0, 0))

        card_w, card_h = 360, 380
        cx = (self.screen_width - card_w) // 2
        cy = (self.screen_height - card_h) // 2

        _draw_shadow(self.screen, (cx, cy, card_w, card_h), radius=16, offset=8, alpha=80)
        _draw_rounded_rect(self.screen, Colors.PANEL_BG, (cx, cy, card_w, card_h), radius=16)
        _draw_rounded_rect(self.screen, (0, 0, 0, 0), (cx, cy, card_w, card_h),
                           radius=16, border=2, border_color=Colors.CARD_BORDER)

        _draw_gradient_rect(self.screen, (cx, cy, card_w, 50),
                            Colors.ACCENT_DARK, Colors.PANEL_BG, radius=16)
        title = self.font_large.render("PAUSED", True, Colors.TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(self.screen_width // 2, cy + 25)))

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
                _draw_rounded_rect(self.screen, Colors.ACCENT,
                                   (cx + 20, iy, 4, item_h), radius=2)
            else:
                _draw_rounded_rect(self.screen, (0, 0, 0, 0), item_rect, radius=10,
                                   border=1, border_color=Colors.CARD_BORDER)

            icon_surf = self.font_medium.render(icon, True, Colors.ACCENT_LIGHT)
            self.screen.blit(icon_surf, (cx + 40, iy + 12))
            lbl_surf = self.font_medium.render(label, True, Colors.TEXT_PRIMARY)
            self.screen.blit(lbl_surf, (cx + 75, iy + 12))

    def draw_pokemon_menu(self, player: Player):
        if not player:
            return
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 210))
        self.screen.blit(overlay, (0, 0))

        _draw_gradient_rect(self.screen, (0, 0, self.screen_width, 60),
                            Colors.ACCENT_DARK, Colors.OVERLAY)
        title = self.font_large.render("POKEMON TEAM", True, Colors.TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(self.screen_width // 2, 30)))

        if not player or not player.pokemon_team:
            empty = self.font_medium.render("No Pokemon in team!", True, Colors.TEXT_SECONDARY)
            self.screen.blit(empty, empty.get_rect(center=(self.screen_width // 2,
                                                           self.screen_height // 2)))
            return

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

            _draw_shadow(self.screen, card_rect, radius=12, offset=4, alpha=50)
            bg_color = Colors.PANEL_BG_LIGHT if is_selected else Colors.PANEL_BG
            if pokemon.is_fainted:
                bg_color = (50, 30, 30)
            _draw_rounded_rect(self.screen, bg_color, card_rect, radius=12)
            border_c = Colors.ACCENT if is_selected else Colors.CARD_BORDER
            _draw_rounded_rect(self.screen, (0, 0, 0, 0), card_rect, radius=12,
                               border=2, border_color=border_c)

            sprite_cx = base_x + 50
            sprite_cy = cur_y + 45
            pcolor = Colors.TYPE_COLORS.get(
                pokemon.types[0] if pokemon.types else PokemonType.NORMAL, Colors.GRAY
            )
            sprite_fn = f"{pokemon.species_id}_normal.png"
            sprite_path = os.path.join("assets", "sprites", sprite_fn)
            sprite = self.load_sprite(sprite_path, (64, 64))

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

            if getattr(pokemon, 'is_shiny', False):
                star_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                pts = []
                for si in range(10):
                    angle = (si / 10) * 2 * math.pi - math.pi / 2
                    r = 7 if si % 2 == 0 else 3
                    pts.append((8 + math.cos(angle) * r, 8 + math.sin(angle) * r))
                pygame.draw.polygon(star_surf, (255, 215, 0, 220), pts)
                self.screen.blit(star_surf, (sprite_cx + 18, sprite_cy - 28))

            info_x = base_x + 95
            name_surf = self.font_medium.render(
                f"{pokemon.nickname}", True, Colors.TEXT_PRIMARY
            )
            self.screen.blit(name_surf, (info_x, cur_y + 12))
            lvl_surf = self.font_small.render(
                f"Lv. {pokemon.level}", True, Colors.TEXT_SECONDARY
            )
            self.screen.blit(lvl_surf, (info_x + name_surf.get_width() + 10, cur_y + 16))

            badge_x = info_x
            for pt in pokemon.types:
                bw = _draw_type_badge(self.screen, pt, badge_x, cur_y + 38,
                                      pygame.font.Font(None, 16))
                badge_x += bw + 6

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

            if pokemon.status != StatusCondition.NONE:
                sc = Colors.STATUS_COLORS.get(pokemon.status, Colors.RED)
                dot_x = base_x + card_w - 30
                dot_y = cur_y + 15
                pygame.draw.circle(self.screen, sc, (dot_x, dot_y), 6)
                st_label = self.font_small.render(pokemon.status.value[:3].upper(),
                                                  True, sc)
                self.screen.blit(st_label, (dot_x - st_label.get_width() - 4, dot_y - 6))

            if is_selected:
                detail_y = cur_y + 85
                moves_title = self.font_small.render("MOVES:", True, Colors.TEXT_SECONDARY)
                self.screen.blit(moves_title, (info_x, detail_y))
                for mi, move in enumerate(pokemon.moves[:4]):
                    mx = info_x + (mi % 2) * 200
                    my = detail_y + 20 + (mi // 2) * 22
                    mc = Colors.TYPE_COLORS.get(move.type, Colors.TEXT_SECONDARY)
                    ms = self.font_small.render(f"{move.name} ({move.current_pp}/{move.pp})",
                                               True, mc)
                    self.screen.blit(ms, (mx, my))

                stat_x = info_x
                stat_y = detail_y + 65
                stats_text = (f"ATK:{pokemon.stats.get('attack', 0)} "
                              f"DEF:{pokemon.stats.get('defense', 0)} "
                              f"SPD:{pokemon.stats.get('speed', 0)}")
                sts = self.font_small.render(stats_text, True, Colors.TEXT_SECONDARY)
                self.screen.blit(sts, (stat_x, stat_y))

            cur_y += ch + gap

        footer = self.font_small.render(
            "UP/DOWN: Select  |  ESC: Back", True, Colors.TEXT_SECONDARY
        )
        self.screen.blit(footer, footer.get_rect(center=(self.screen_width // 2,
                                                         self.screen_height - 25)))

    def draw_bag_menu(self, player: Player):
        if not player:
            return
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 210))
        self.screen.blit(overlay, (0, 0))

        _draw_gradient_rect(self.screen, (0, 0, self.screen_width, 60),
                            Colors.ACCENT_DARK, Colors.OVERLAY)
        title = self.font_large.render("BAG", True, Colors.TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(self.screen_width // 2, 30)))

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

        allowed_cats = self._bag_tab_categories[self._bag_tab]
        items_list: List[Tuple[str, int, str]] = []
        for item_id, qty in player.inventory.items():
            if qty <= 0:
                continue
            item_def = ITEM_REGISTRY.get(item_id)
            if item_def and item_def.category in allowed_cats:
                items_list.append((item_id, qty, item_def.name))
            elif not item_def and self._bag_tab == 3:
                items_list.append((item_id, qty, item_id.replace("_", " ").title()))

        if self._bag_selected >= len(items_list):
            self._bag_selected = max(0, len(items_list) - 1)

        list_x = 40
        list_y = 120
        list_w = self.screen_width // 2 - 60
        list_h = self.screen_height - 180

        _draw_rounded_rect(self.screen, Colors.PANEL_BG, (list_x, list_y, list_w, list_h),
                           radius=12)
        _draw_rounded_rect(self.screen, (0, 0, 0, 0), (list_x, list_y, list_w, list_h),
                           radius=12, border=1, border_color=Colors.CARD_BORDER)

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

                ns = self.font_medium.render(display_name, True, Colors.TEXT_PRIMARY)
                self.screen.blit(ns, (list_x + 22, iy + 10))

                qty_text = f"x{qty}"
                qs = self.font_small.render(qty_text, True, Colors.TEXT_SECONDARY)
                qw = qs.get_width() + 12
                qr = (list_x + list_w - qw - 20, iy + 10, qw, 24)
                _draw_rounded_rect(self.screen, (60, 60, 85), qr, radius=6)
                self.screen.blit(qs, (qr[0] + 6, qr[1] + 4))

            if 0 <= self._bag_selected < len(items_list):
                sel_id = items_list[self._bag_selected][0]
                sel_item = ITEM_REGISTRY.get(sel_id)
                desc_title = self.font_medium.render(
                    sel_item.name if sel_item else sel_id, True, Colors.TEXT_PRIMARY
                )
                self.screen.blit(desc_title, (desc_x + 20, list_y + 20))

                pygame.draw.line(self.screen, Colors.CARD_BORDER,
                                 (desc_x + 20, list_y + 50),
                                 (desc_x + desc_w - 20, list_y + 50))

                if sel_item:
                    desc_text = sel_item.description
                    ds = self.font_small.render(desc_text, True, Colors.TEXT_SECONDARY)
                    self.screen.blit(ds, (desc_x + 20, list_y + 65))

                    cat_text = f"Category: {sel_item.category.value.title()}"
                    cs = self.font_small.render(cat_text, True, Colors.TEXT_SECONDARY)
                    self.screen.blit(cs, (desc_x + 20, list_y + 95))

                    if sel_item.price > 0:
                        price_text = f"Price: ${sel_item.price}"
                        ps = self.font_small.render(price_text, True, Colors.YELLOW)
                        self.screen.blit(ps, (desc_x + 20, list_y + 120))

                    use_hint = self.font_small.render(
                        "Press ENTER to use", True, Colors.ACCENT_LIGHT
                    )
                    self.screen.blit(use_hint, (desc_x + 20, list_y + list_h - 40))

        footer = self.font_small.render(
            "LEFT/RIGHT: Tab  |  UP/DOWN: Select  |  ESC: Back", True, Colors.TEXT_SECONDARY
        )
        self.screen.blit(footer, footer.get_rect(center=(self.screen_width // 2,
                                                         self.screen_height - 20)))
