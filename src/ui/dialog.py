"""
Dialog UI - Dialog box rendering with typewriter effect and bounce arrow
"""

import pygame
import math
from typing import List

from .components import (
    Colors, _draw_rounded_rect, _draw_shadow,
)


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
