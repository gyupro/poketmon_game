"""
Battle Animation System - Visual effects for moves and attacks
"""

import pygame
import math
import random
from typing import Dict, List, Tuple, Optional
from enum import Enum


class AnimationType(Enum):
    """Types of battle animations."""
    HIT = "hit"
    SLASH = "slash"
    ELECTRIC = "electric"
    FIRE = "fire"
    WATER = "water"
    GRASS = "grass"
    PSYCHIC = "psychic"
    GHOST = "ghost"
    NORMAL = "normal"
    SHAKE = "shake"
    FLASH = "flash"
    ICE = "ice"
    FIGHTING = "fighting"
    POISON = "poison"
    GROUND = "ground"
    FLYING = "flying"
    BUG = "bug"
    ROCK = "rock"
    DRAGON = "dragon"
    DARK = "dark"
    STEEL = "steel"
    FAIRY = "fairy"


class BattleAnimation:
    """Base class for battle animations."""

    def __init__(self, target_pos: Tuple[int, int], duration: float = 1.0):
        self.target_pos = target_pos
        self.duration = duration
        self.elapsed = 0.0
        self.active = True

    def update(self, dt: float):
        """Update animation state."""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False

    def render(self, screen: pygame.Surface):
        """Render the animation."""
        pass

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out for smooth deceleration."""
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease in-out."""
        if t < 0.5:
            return 2 * t * t
        return 1 - (-2 * t + 2) ** 2 / 2

    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """Elastic ease-out for bouncy effects."""
        if t == 0 or t == 1:
            return t
        return math.pow(2, -10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1

    @staticmethod
    def ease_out_back(t: float) -> float:
        """Back ease-out with slight overshoot."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


class DamagePopup(BattleAnimation):
    """Floating damage number that rises, fades out, shows effectiveness text."""

    def __init__(self, target_pos: Tuple[int, int], damage: int,
                 is_critical: bool = False, effectiveness: float = 1.0):
        super().__init__(target_pos, 1.5)
        self.damage = damage
        self.is_critical = is_critical
        self.effectiveness = effectiveness
        self.start_y = target_pos[1]
        self.font_size = 40 if is_critical else 30
        self.float_distance = 90
        self.x_wobble = random.uniform(-0.5, 0.5)

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration
        eased = self.ease_out_cubic(progress)

        y_offset = -self.float_distance * eased
        x_wobble = math.sin(self.elapsed * 8) * 3 * self.x_wobble * (1 - progress)

        # Fade: hold full opacity until 40%, then fade
        if progress < 0.4:
            alpha = 255
        else:
            alpha = max(0, int(255 * (1 - (progress - 0.4) / 0.6)))

        if self.is_critical:
            color = (255, 50, 50)
            text = f"{self.damage}!"
        elif self.effectiveness > 1.0:
            color = (255, 180, 0)
            text = str(self.damage)
        elif self.effectiveness < 1.0:
            color = (150, 150, 170)
            text = str(self.damage)
        else:
            color = (255, 255, 255)
            text = str(self.damage)

        # Scale-in for critical hits: pop then settle
        if self.is_critical and progress < 0.15:
            scale = 1.0 + 0.6 * self.ease_out_elastic(progress / 0.15)
        elif self.is_critical:
            scale = 1.0 + 0.1 * max(0, 1 - (progress - 0.15) / 0.3)
        else:
            scale = 1.0 + 0.2 * max(0, 1 - progress * 4)

        size = max(14, int(self.font_size * scale))
        font = pygame.font.Font(None, size)

        x = self.target_pos[0] + x_wobble
        y = self.start_y + y_offset

        # Outline (thicker for better readability)
        outline_surface = font.render(text, True, (0, 0, 0))
        outline_surface.set_alpha(alpha)
        for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (-3, 0), (3, 0), (0, -3), (0, 3)]:
            rect = outline_surface.get_rect(center=(x + ox, y + oy))
            screen.blit(outline_surface, rect)

        # Main text
        text_surface = font.render(text, True, color)
        text_surface.set_alpha(alpha)
        rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, rect)

        # Glow behind critical hits
        if self.is_critical and alpha > 50:
            glow_size = size + 10
            glow_surf = pygame.Surface((glow_size * 2, glow_size), pygame.SRCALPHA)
            glow_font = pygame.font.Font(None, size)
            glow_text = glow_font.render(text, True, (255, 100, 100))
            glow_text.set_alpha(alpha // 4)
            gr = glow_text.get_rect(center=(glow_size, glow_size // 2))
            glow_surf.blit(glow_text, gr)

        # Effectiveness sub-text
        if self.effectiveness > 1.5:
            sub_alpha = alpha
            sub_font = pygame.font.Font(None, 22)
            eff_outline = sub_font.render("Super effective!", True, (0, 0, 0))
            eff_outline.set_alpha(sub_alpha)
            eff_text = sub_font.render("Super effective!", True, (255, 220, 50))
            eff_text.set_alpha(sub_alpha)
            eff_rect = eff_text.get_rect(center=(x, y + 22))
            for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                screen.blit(eff_outline, eff_outline.get_rect(center=(x + ox, y + 22 + oy)))
            screen.blit(eff_text, eff_rect)
        elif 0 < self.effectiveness < 1.0:
            sub_alpha = alpha
            sub_font = pygame.font.Font(None, 20)
            eff_outline = sub_font.render("Not very effective...", True, (0, 0, 0))
            eff_outline.set_alpha(sub_alpha)
            eff_text = sub_font.render("Not very effective...", True, (160, 160, 180))
            eff_text.set_alpha(sub_alpha)
            eff_rect = eff_text.get_rect(center=(x, y + 22))
            for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                screen.blit(eff_outline, eff_outline.get_rect(center=(x + ox, y + 22 + oy)))
            screen.blit(eff_text, eff_rect)


class HitAnimation(BattleAnimation):
    """Impact animation with expanding ring, star burst, and SRCALPHA particles."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.65)
        self.particles = []
        for _ in range(16):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 250)
            self.particles.append({
                'x': float(target_pos[0]),
                'y': float(target_pos[1]),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.uniform(3, 10),
                'color': random.choice([
                    (255, 255, 140),
                    (255, 230, 80),
                    (255, 200, 60),
                    (255, 180, 40),
                ]),
                'gravity': random.uniform(120, 250),
                'trail': [],
            })
        self.ring_count = 2

    def update(self, dt: float):
        super().update(dt)
        for particle in self.particles:
            # Store trail positions
            particle['trail'].append((particle['x'], particle['y']))
            if len(particle['trail']) > 4:
                particle['trail'].pop(0)
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['vy'] += particle['gravity'] * dt
            particle['size'] = max(0, particle['size'] - dt * 14)

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration

        # Multiple impact rings expanding outward
        for ring_i in range(self.ring_count):
            ring_delay = ring_i * 0.05
            ring_elapsed = max(0, self.elapsed - ring_delay)
            ring_progress = min(1.0, ring_elapsed / 0.25)
            max_radius = 35 + ring_i * 20
            ring_radius = int(max_radius * self.ease_out_cubic(ring_progress))
            ring_alpha = max(0, int((200 - ring_i * 60) * (1 - ring_progress)))
            if ring_radius > 0 and ring_alpha > 0:
                ring_surface = pygame.Surface(
                    (ring_radius * 2 + 6, ring_radius * 2 + 6), pygame.SRCALPHA)
                thickness = max(2, 4 - ring_i)
                pygame.draw.circle(
                    ring_surface,
                    (255, 255, 200, ring_alpha),
                    (ring_radius + 3, ring_radius + 3),
                    ring_radius, thickness)
                screen.blit(ring_surface,
                            (self.target_pos[0] - ring_radius - 3,
                             self.target_pos[1] - ring_radius - 3))

        # Animated impact star (spins and shrinks)
        if progress < 0.35:
            star_progress = progress / 0.35
            size = int(30 * (1 - star_progress))
            rotation = star_progress * math.pi * 0.5
            if size > 2:
                points = []
                for i in range(10):
                    angle = (i / 10) * 2 * math.pi - math.pi / 2 + rotation
                    r = size if i % 2 == 0 else size * 0.35
                    px = self.target_pos[0] + math.cos(angle) * r
                    py = self.target_pos[1] + math.sin(angle) * r
                    points.append((px, py))
                if len(points) >= 3:
                    alpha_val = int(255 * (1 - star_progress))
                    surf_size = size * 3
                    star_surface = pygame.Surface(
                        (surf_size, surf_size), pygame.SRCALPHA)
                    offset_points = [
                        (p[0] - self.target_pos[0] + surf_size // 2,
                         p[1] - self.target_pos[1] + surf_size // 2)
                        for p in points]
                    # Glow layer
                    pygame.draw.polygon(
                        star_surface,
                        (255, 255, 180, alpha_val // 3),
                        offset_points)
                    # Core layer
                    pygame.draw.polygon(
                        star_surface,
                        (255, 255, 100, alpha_val),
                        offset_points)
                    screen.blit(star_surface,
                                (self.target_pos[0] - surf_size // 2,
                                 self.target_pos[1] - surf_size // 2))

        # Particles with trails
        for particle in self.particles:
            if particle['size'] > 0.5:
                alpha_val = max(0, int(255 * (1 - progress)))
                s = int(particle['size'])
                if s > 0:
                    r, g, b = particle['color']
                    # Trail
                    for ti, (tx, ty) in enumerate(particle['trail']):
                        trail_alpha = alpha_val * (ti + 1) // (len(particle['trail']) + 2)
                        trail_size = max(1, s * (ti + 1) // (len(particle['trail']) + 1))
                        if trail_size > 0 and trail_alpha > 0:
                            ts = pygame.Surface(
                                (trail_size * 2, trail_size * 2), pygame.SRCALPHA)
                            pygame.draw.circle(
                                ts, (r, g, b, trail_alpha),
                                (trail_size, trail_size), trail_size)
                            screen.blit(ts,
                                        (int(tx) - trail_size,
                                         int(ty) - trail_size))
                    # Main particle
                    particle_surface = pygame.Surface(
                        (s * 2 + 2, s * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(
                        particle_surface, (r, g, b, alpha_val),
                        (s + 1, s + 1), s)
                    # Bright core
                    core_s = max(1, s // 2)
                    pygame.draw.circle(
                        particle_surface,
                        (255, 255, 255, min(255, alpha_val + 50)),
                        (s + 1, s + 1), core_s)
                    screen.blit(particle_surface,
                                (int(particle['x']) - s - 1,
                                 int(particle['y']) - s - 1))


class SlashAnimation(BattleAnimation):
    """Multi-slash animation with staggered trails and glow effects."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.5)
        self.slash_trails = []
        offsets = [-1, 0, 1]
        angles = [-35, 10, -55]
        for i, (off_mult, ang_adj) in enumerate(zip(offsets, angles)):
            cx, cy = target_pos
            angle_rad = math.radians(ang_adj)
            length = 55
            dx = math.cos(angle_rad) * length
            dy = math.sin(angle_rad) * length
            offset_perp = off_mult * 16
            self.slash_trails.append({
                'start': (cx - dx + offset_perp, cy - dy + offset_perp * 0.5),
                'end': (cx + dx + offset_perp, cy + dy + offset_perp * 0.5),
                'delay': i * 0.07,
                'width_main': random.randint(3, 5),
                'width_glow': random.randint(8, 12),
            })

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        for trail in self.slash_trails:
            local_elapsed = max(0, self.elapsed - trail['delay'])
            if local_elapsed <= 0:
                continue
            trail_duration = self.duration - trail['delay']
            if trail_duration <= 0:
                continue
            local_progress = min(1.0, local_elapsed / trail_duration)

            sx, sy = trail['start']
            ex, ey = trail['end']

            # The slash draws quickly, then fades
            draw_progress = min(1.0, local_progress * 2.5)
            fade_progress = max(0, (local_progress - 0.35) / 0.65) if local_progress > 0.35 else 0

            eased_draw = self.ease_out_cubic(draw_progress)
            cx = sx + (ex - sx) * eased_draw
            cy = sy + (ey - sy) * eased_draw

            alpha = max(0, int(255 * (1 - fade_progress)))
            if alpha <= 0:
                continue

            # Calculate bounding box
            min_x = int(min(sx, cx)) - 15
            min_y = int(min(sy, cy)) - 15
            max_x = int(max(sx, cx)) + 15
            max_y = int(max(sy, cy)) + 15
            w = max(1, max_x - min_x)
            h = max(1, max_y - min_y)

            slash_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            local_start = (sx - min_x, sy - min_y)
            local_end = (cx - min_x, cy - min_y)

            # Outer glow
            pygame.draw.line(
                slash_surface,
                (200, 200, 255, alpha // 4),
                local_start, local_end, trail['width_glow'])

            # Mid glow
            pygame.draw.line(
                slash_surface,
                (220, 220, 255, alpha // 2),
                local_start, local_end, trail['width_glow'] // 2 + 2)

            # Main slash line
            pygame.draw.line(
                slash_surface,
                (255, 255, 255, alpha),
                local_start, local_end, trail['width_main'])

            # Bright core
            pygame.draw.line(
                slash_surface,
                (255, 255, 255, min(255, alpha + 30)),
                local_start, local_end, max(1, trail['width_main'] // 2))

            screen.blit(slash_surface, (min_x, min_y))

            # Spark at the tip
            if draw_progress < 0.9:
                spark_alpha = int(alpha * 0.7)
                spark_size = 6
                spark_surf = pygame.Surface(
                    (spark_size * 2, spark_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    spark_surf, (255, 255, 220, spark_alpha),
                    (spark_size, spark_size), spark_size)
                pygame.draw.circle(
                    spark_surf, (255, 255, 255, min(255, spark_alpha + 40)),
                    (spark_size, spark_size), max(1, spark_size // 2))
                screen.blit(spark_surf,
                            (int(cx) - spark_size, int(cy) - spark_size))


class ElectricAnimation(BattleAnimation):
    """Electric shock with flash overlay, multi-layer lightning bolts."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.85)
        self.bolts: List[List[Tuple[int, int]]] = []
        self.bolt_timer = 0.0
        self.flash_intensity = 0
        self.bolt_regen_interval = 0.04

    def update(self, dt: float):
        super().update(dt)
        self.bolt_timer += dt
        if self.bolt_timer > self.bolt_regen_interval:
            self.bolt_timer = 0
            self.bolts = self._generate_bolts()
            self.flash_intensity = 220

        self.flash_intensity = max(0, self.flash_intensity - 900 * dt)

    def _generate_bolts(self) -> List[List[Tuple[int, int]]]:
        """Generate random lightning bolt paths with branching."""
        bolts = []
        count = random.randint(3, 6)
        for _ in range(count):
            bolt = []
            x = self.target_pos[0] + random.randint(-30, 30)
            y = self.target_pos[1] - 80

            while y < self.target_pos[1] + 40:
                bolt.append((x, y))
                x += random.randint(-22, 22)
                y += random.randint(8, 16)
            bolt.append((x, y))
            bolts.append(bolt)

            # Occasional branch from a mid-point
            if len(bolt) > 3 and random.random() < 0.4:
                branch_start = random.randint(1, len(bolt) - 2)
                bx, by = bolt[branch_start]
                branch = [(bx, by)]
                for _ in range(random.randint(2, 4)):
                    bx += random.randint(-18, 18)
                    by += random.randint(6, 14)
                    branch.append((bx, by))
                bolts.append(branch)

        return bolts

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration
        base_alpha = max(0, int(255 * (1 - progress * 0.7)))

        # Flash overlay around target (larger, more intense)
        if self.flash_intensity > 0:
            flash_radius = 80
            flash_surface = pygame.Surface(
                (flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
            intensity = int(min(self.flash_intensity, 255))
            # Outer glow
            pygame.draw.circle(
                flash_surface,
                (255, 255, 120, min(intensity // 3, 85)),
                (flash_radius, flash_radius), flash_radius)
            # Inner glow
            pygame.draw.circle(
                flash_surface,
                (255, 255, 180, min(intensity // 2, 127)),
                (flash_radius, flash_radius), flash_radius // 2)
            screen.blit(flash_surface,
                        (self.target_pos[0] - flash_radius,
                         self.target_pos[1] - flash_radius))

        # Draw lightning bolts with three layers
        for bolt in self.bolts:
            if len(bolt) < 2:
                continue

            # Calculate bounds for the bolt surface
            xs = [p[0] for p in bolt]
            ys = [p[1] for p in bolt]
            pad = 12
            min_x = min(xs) - pad
            min_y = min(ys) - pad
            max_x = max(xs) + pad
            max_y = max(ys) + pad
            w = max(1, max_x - min_x)
            h = max(1, max_y - min_y)

            bolt_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            local_points = [(p[0] - min_x, p[1] - min_y) for p in bolt]

            for i in range(len(local_points) - 1):
                p1 = local_points[i]
                p2 = local_points[i + 1]
                # Layer 1: Outer glow
                pygame.draw.line(
                    bolt_surface,
                    (255, 255, 80, base_alpha // 4),
                    p1, p2, 9)
                # Layer 2: Main bolt
                pygame.draw.line(
                    bolt_surface,
                    (255, 255, 50, base_alpha),
                    p1, p2, 3)
                # Layer 3: Bright core
                pygame.draw.line(
                    bolt_surface,
                    (255, 255, 240, min(255, base_alpha + 30)),
                    p1, p2, 1)

            screen.blit(bolt_surface, (min_x, min_y))

        # Small electric sparks around the target
        if progress < 0.8:
            spark_count = random.randint(2, 5)
            for _ in range(spark_count):
                sx = self.target_pos[0] + random.randint(-35, 35)
                sy = self.target_pos[1] + random.randint(-35, 35)
                spark_size = random.randint(2, 4)
                spark_alpha = max(0, int(200 * (1 - progress)))
                spark_surf = pygame.Surface(
                    (spark_size * 2, spark_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    spark_surf,
                    (255, 255, 150, spark_alpha),
                    (spark_size, spark_size), spark_size)
                screen.blit(spark_surf, (sx - spark_size, sy - spark_size))


class FireAnimation(BattleAnimation):
    """Fire effect with layered flames: white-core-to-red gradient, respawning."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 1.0)
        self.flames = []
        for _ in range(30):
            self.flames.append(self._new_flame())

    def _new_flame(self) -> dict:
        return {
            'x': self.target_pos[0] + random.uniform(-28, 28),
            'y': self.target_pos[1] + random.uniform(-5, 18),
            'vy': random.uniform(-90, -160),
            'vx': random.uniform(-18, 18),
            'life': random.uniform(0, 0.3),
            'max_life': random.uniform(0.35, 0.65),
            'size': random.uniform(5, 15),
            'wobble_phase': random.uniform(0, 2 * math.pi),
            'wobble_speed': random.uniform(8, 15),
        }

    def update(self, dt: float):
        super().update(dt)
        # Determine if we should still spawn new flames
        overall_progress = self.elapsed / self.duration
        for flame in self.flames:
            flame['y'] += flame['vy'] * dt
            wobble = math.sin(flame['wobble_phase'] + self.elapsed * flame['wobble_speed'])
            flame['x'] += (flame['vx'] + wobble * 12) * dt
            flame['life'] += dt

            if flame['life'] > flame['max_life']:
                if overall_progress < 0.75:
                    new_flame = self._new_flame()
                    new_flame['life'] = 0
                    flame.update(new_flame)
                else:
                    flame['life'] = flame['max_life']

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        overall_progress = self.elapsed / self.duration
        # Fade out in the last 25%
        if overall_progress > 0.75:
            fade = 1 - (overall_progress - 0.75) / 0.25
        else:
            fade = 1.0
        fade = max(0, min(1, fade))

        for flame in self.flames:
            life_ratio = min(1.0, flame['life'] / flame['max_life'])
            alpha = max(0, int(255 * (1 - life_ratio * life_ratio) * fade))

            if alpha <= 0:
                continue

            # Color gradient: white core -> bright yellow -> orange -> deep red
            if life_ratio < 0.15:
                r_c, g_c, b_c = 255, 255, 230
            elif life_ratio < 0.3:
                t = (life_ratio - 0.15) / 0.15
                r_c = 255
                g_c = int(255 - t * 30)
                b_c = int(230 - t * 150)
            elif life_ratio < 0.55:
                t = (life_ratio - 0.3) / 0.25
                r_c = 255
                g_c = int(225 - t * 80)
                b_c = int(80 - t * 50)
            elif life_ratio < 0.8:
                t = (life_ratio - 0.55) / 0.25
                r_c = int(255 - t * 30)
                g_c = int(145 - t * 80)
                b_c = int(30 - t * 10)
            else:
                t = (life_ratio - 0.8) / 0.2
                r_c = int(225 - t * 30)
                g_c = int(65 - t * 40)
                b_c = int(20 - t * 5)

            size = max(1, int(flame['size'] * (1 - life_ratio * 0.6)))
            flame_surface = pygame.Surface(
                (size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)

            # Outer glow for young flames
            if life_ratio < 0.4:
                glow_alpha = alpha // 4
                glow_size = size + 3
                pygame.draw.circle(
                    flame_surface,
                    (r_c, g_c, min(255, b_c + 40), glow_alpha),
                    (size + 2, size + 2), glow_size)

            # Main flame circle
            pygame.draw.circle(
                flame_surface,
                (r_c, g_c, b_c, alpha),
                (size + 2, size + 2), size)

            # White-hot core for very young flames
            if life_ratio < 0.2:
                core_size = max(1, size // 2)
                core_alpha = int(alpha * (1 - life_ratio / 0.2))
                pygame.draw.circle(
                    flame_surface,
                    (255, 255, 255, core_alpha),
                    (size + 2, size + 2), core_size)

            screen.blit(flame_surface,
                        (int(flame['x']) - size - 2,
                         int(flame['y']) - size - 2))


class WaterAnimation(BattleAnimation):
    """Water splash with central wave ring, droplets with highlights and gravity."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.9)
        self.drops = []
        for _ in range(22):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(120, 280)
            self.drops.append({
                'x': float(target_pos[0] + random.randint(-15, 15)),
                'y': float(target_pos[1]),
                'vy': -abs(math.sin(angle)) * speed - 50,
                'vx': math.cos(angle) * speed * 0.5,
                'size': random.randint(4, 11),
                'life': 0.0,
                'shade': random.choice([
                    (60, 130, 255),
                    (80, 160, 255),
                    (100, 180, 255),
                    (50, 110, 230),
                ]),
            })
        self.wave_rings = [
            {'radius': 0.0, 'speed': 130, 'delay': 0.0},
            {'radius': 0.0, 'speed': 100, 'delay': 0.08},
        ]

    def update(self, dt: float):
        super().update(dt)
        for ring in self.wave_rings:
            local_elapsed = max(0, self.elapsed - ring['delay'])
            if local_elapsed > 0:
                ring['radius'] = local_elapsed * ring['speed']

        for drop in self.drops:
            drop['x'] += drop['vx'] * dt
            drop['y'] += drop['vy'] * dt
            drop['vy'] += 380 * dt  # gravity
            drop['life'] += dt

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration

        # Central splash wave rings
        for ring in self.wave_rings:
            local_elapsed = max(0, self.elapsed - ring['delay'])
            if local_elapsed <= 0:
                continue
            ring_progress = min(1.0, local_elapsed / 0.5)
            wave_alpha = int(180 * (1 - ring_progress))
            radius = int(ring['radius'])
            if radius > 2 and wave_alpha > 0:
                wave_w = radius * 2 + 6
                wave_h = radius + 6
                if wave_w > 0 and wave_h > 0:
                    wave_surface = pygame.Surface(
                        (wave_w, wave_h), pygame.SRCALPHA)
                    # Outer ring
                    pygame.draw.ellipse(
                        wave_surface,
                        (100, 180, 255, wave_alpha // 2),
                        (3, 3, radius * 2, radius), 4)
                    # Inner ring
                    pygame.draw.ellipse(
                        wave_surface,
                        (150, 210, 255, wave_alpha),
                        (3, 3, radius * 2, radius), 2)
                    screen.blit(wave_surface,
                                (self.target_pos[0] - radius - 3,
                                 self.target_pos[1] - radius // 2 - 3))

        # Water droplets
        for drop in self.drops:
            if drop['life'] < 0.75:
                life_ratio = drop['life'] / 0.75
                alpha = max(0, int(230 * (1 - life_ratio)))
                size = max(1, int(drop['size'] * (1 - life_ratio * 0.4)))
                r, g, b = drop['shade']

                drop_surface = pygame.Surface(
                    (size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)

                # Subtle glow
                if size > 3:
                    pygame.draw.circle(
                        drop_surface,
                        (r, g, b, alpha // 4),
                        (size + 2, size + 2), size + 2)

                # Main droplet
                pygame.draw.circle(
                    drop_surface,
                    (r, g, b, alpha),
                    (size + 2, size + 2), size)

                # Highlight (specular)
                hl_size = max(1, size // 3)
                hl_offset = max(1, size // 3)
                pygame.draw.circle(
                    drop_surface,
                    (210, 235, 255, min(255, alpha + 20)),
                    (size + 2 - hl_offset, size + 2 - hl_offset), hl_size)

                screen.blit(drop_surface,
                            (int(drop['x']) - size - 2,
                             int(drop['y']) - size - 2))


class GrassAnimation(BattleAnimation):
    """Leaf particles with rotation, color variation, and gravity."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.85)
        self.leaves = []
        for _ in range(18):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(70, 180)
            self.leaves.append({
                'x': float(target_pos[0] + random.randint(-12, 12)),
                'y': float(target_pos[1] + random.randint(-8, 8)),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 50,
                'rotation': random.uniform(0, 360),
                'rot_speed': random.uniform(-400, 400),
                'size': random.randint(4, 9),
                'shade': random.choice([
                    (70, 190, 50),
                    (90, 210, 70),
                    (55, 170, 35),
                    (110, 225, 80),
                    (80, 200, 60),
                    (130, 235, 100),
                ]),
                'elongation': random.uniform(1.5, 2.5),
            })

    def update(self, dt: float):
        super().update(dt)
        for leaf in self.leaves:
            leaf['x'] += leaf['vx'] * dt
            leaf['y'] += leaf['vy'] * dt
            leaf['vy'] += 130 * dt  # gravity
            leaf['vx'] *= (1 - 0.5 * dt)  # air resistance
            leaf['rotation'] += leaf['rot_speed'] * dt

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration
        # Hold alpha for a bit then fade
        if progress < 0.3:
            alpha = 255
        else:
            alpha = max(0, int(255 * (1 - (progress - 0.3) / 0.7)))

        for leaf in self.leaves:
            size = leaf['size']
            if size < 1 or alpha <= 0:
                continue

            w = int(size * leaf['elongation'])
            h = size
            leaf_surface = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)

            r, g, b = leaf['shade']
            # Main leaf body
            pygame.draw.ellipse(
                leaf_surface, (r, g, b, alpha),
                (1, 1, w, h))
            # Leaf vein (center line lighter)
            vein_color = (min(255, r + 40), min(255, g + 30), min(255, b + 20), alpha // 2)
            pygame.draw.line(
                leaf_surface, vein_color,
                (1, h // 2 + 1), (w, h // 2 + 1), 1)

            rotated = pygame.transform.rotate(leaf_surface, leaf['rotation'])
            rect = rotated.get_rect(center=(int(leaf['x']), int(leaf['y'])))
            screen.blit(rotated, rect)


class PsychicAnimation(BattleAnimation):
    """Expanding concentric colored rings with eased animation."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 1.0)
        self.rings = []
        colors = [
            (220, 80, 200),
            (180, 60, 220),
            (240, 100, 180),
            (160, 50, 240),
            (200, 70, 210),
        ]
        for i in range(5):
            self.rings.append({
                'delay': i * 0.12,
                'max_radius': 55 + i * 12,
                'color': colors[i % len(colors)],
                'thickness': max(2, 4 - i),
            })

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        for ring in self.rings:
            local_elapsed = max(0, self.elapsed - ring['delay'])
            if local_elapsed <= 0:
                continue
            ring_duration = self.duration - ring['delay']
            if ring_duration <= 0:
                continue
            local_progress = min(1.0, local_elapsed / ring_duration)

            eased = self.ease_out_cubic(local_progress)
            radius = int(ring['max_radius'] * eased)
            alpha = max(0, int(200 * (1 - local_progress * local_progress)))

            if radius > 2 and alpha > 0:
                surf_size = radius * 2 + 8
                ring_surface = pygame.Surface(
                    (surf_size, surf_size), pygame.SRCALPHA)
                center = surf_size // 2
                r, g, b = ring['color']

                # Filled glow behind
                pygame.draw.circle(
                    ring_surface,
                    (r, g, b, alpha // 5),
                    (center, center), radius)
                # Ring outline
                pygame.draw.circle(
                    ring_surface,
                    (r, g, b, alpha),
                    (center, center), radius, ring['thickness'])
                # Inner bright edge
                if radius > 4:
                    pygame.draw.circle(
                        ring_surface,
                        (min(255, r + 60), min(255, g + 60), min(255, b + 60), alpha // 2),
                        (center, center), radius - 1, 1)

                screen.blit(ring_surface,
                            (self.target_pos[0] - center,
                             self.target_pos[1] - center))


class IceAnimation(BattleAnimation):
    """Ice crystal shards with frost ring."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.8)
        self.shards = []
        for _ in range(14):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 200)
            self.shards.append({
                'x': float(target_pos[0]),
                'y': float(target_pos[1]),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 30,
                'rotation': random.uniform(0, 360),
                'rot_speed': random.uniform(-200, 200),
                'size': random.randint(4, 10),
                'shade': random.choice([
                    (180, 220, 255),
                    (150, 200, 255),
                    (200, 235, 255),
                    (160, 210, 250),
                ]),
            })

    def update(self, dt: float):
        super().update(dt)
        for shard in self.shards:
            shard['x'] += shard['vx'] * dt
            shard['y'] += shard['vy'] * dt
            shard['vy'] += 100 * dt
            shard['rotation'] += shard['rot_speed'] * dt
            shard['vx'] *= (1 - 1.5 * dt)

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration

        # Frost ring
        if progress < 0.5:
            ring_p = progress / 0.5
            radius = int(50 * self.ease_out_cubic(ring_p))
            ring_alpha = max(0, int(180 * (1 - ring_p)))
            if radius > 2:
                ring_surf = pygame.Surface(
                    (radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    ring_surf, (180, 220, 255, ring_alpha),
                    (radius + 2, radius + 2), radius, 3)
                screen.blit(ring_surf,
                            (self.target_pos[0] - radius - 2,
                             self.target_pos[1] - radius - 2))

        alpha = max(0, int(255 * (1 - progress)))
        for shard in self.shards:
            size = shard['size']
            if size < 2 or alpha <= 0:
                continue
            r, g, b = shard['shade']
            # Diamond-shaped shard
            shard_surf = pygame.Surface((size * 2, size * 3), pygame.SRCALPHA)
            points = [
                (size, 0),
                (size * 2, size),
                (size, size * 3),
                (0, size),
            ]
            pygame.draw.polygon(shard_surf, (r, g, b, alpha), points)
            # Bright center line
            pygame.draw.line(
                shard_surf, (230, 245, 255, alpha),
                (size, 1), (size, size * 3 - 1), 1)
            rotated = pygame.transform.rotate(shard_surf, shard['rotation'])
            rect = rotated.get_rect(center=(int(shard['x']), int(shard['y'])))
            screen.blit(rotated, rect)


class FightingAnimation(BattleAnimation):
    """Fist impact with shockwave and debris."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.55)
        self.debris = []
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 220)
            self.debris.append({
                'x': float(target_pos[0]),
                'y': float(target_pos[1]),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.randint(3, 7),
            })

    def update(self, dt: float):
        super().update(dt)
        for d in self.debris:
            d['x'] += d['vx'] * dt
            d['y'] += d['vy'] * dt
            d['vy'] += 200 * dt

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration

        # Shockwave ring
        if progress < 0.4:
            ring_p = progress / 0.4
            radius = int(50 * self.ease_out_cubic(ring_p))
            ring_alpha = max(0, int(200 * (1 - ring_p)))
            if radius > 2:
                ring_surf = pygame.Surface(
                    (radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    ring_surf, (255, 160, 60, ring_alpha),
                    (radius + 2, radius + 2), radius, 4)
                screen.blit(ring_surf,
                            (self.target_pos[0] - radius - 2,
                             self.target_pos[1] - radius - 2))

        # Impact flash
        if progress < 0.15:
            flash_alpha = int(200 * (1 - progress / 0.15))
            flash_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(
                flash_surf, (255, 200, 100, flash_alpha), (30, 30), 30)
            screen.blit(flash_surf,
                        (self.target_pos[0] - 30, self.target_pos[1] - 30))

        # Debris particles
        alpha = max(0, int(255 * (1 - progress)))
        for d in self.debris:
            size = max(1, int(d['size'] * (1 - progress * 0.5)))
            if size > 0 and alpha > 0:
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.rect(
                    s, (200, 150, 80, alpha),
                    (0, 0, size * 2, size * 2))
                screen.blit(s, (int(d['x']) - size, int(d['y']) - size))


class PoisonAnimation(BattleAnimation):
    """Poison bubbles rising and popping."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.85)
        self.bubbles = []
        for _ in range(12):
            self.bubbles.append({
                'x': target_pos[0] + random.randint(-25, 25),
                'y': float(target_pos[1] + random.randint(-5, 15)),
                'vy': random.uniform(-60, -120),
                'vx': random.uniform(-15, 15),
                'size': random.randint(4, 12),
                'life': random.uniform(0, 0.2),
                'max_life': random.uniform(0.4, 0.7),
                'shade': random.choice([
                    (160, 50, 200),
                    (140, 30, 180),
                    (180, 60, 220),
                ]),
            })

    def update(self, dt: float):
        super().update(dt)
        for b in self.bubbles:
            b['y'] += b['vy'] * dt
            b['x'] += b['vx'] * dt + math.sin(self.elapsed * 6 + b['size']) * 8 * dt
            b['life'] += dt

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration
        fade = max(0, 1 - max(0, (progress - 0.7) / 0.3))

        for b in self.bubbles:
            if b['life'] > b['max_life']:
                continue
            life_ratio = b['life'] / b['max_life']
            alpha = max(0, int(200 * (1 - life_ratio) * fade))
            size = b['size']
            if size < 2 or alpha <= 0:
                continue

            r, g, bb_ = b['shade']
            surf = pygame.Surface((size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)
            # Bubble body
            pygame.draw.circle(
                surf, (r, g, bb_, alpha),
                (size + 2, size + 2), size)
            # Bubble outline
            pygame.draw.circle(
                surf, (r + 30, g + 30, min(255, bb_ + 30), alpha),
                (size + 2, size + 2), size, 1)
            # Highlight
            hl = max(1, size // 3)
            pygame.draw.circle(
                surf, (220, 180, 255, alpha // 2),
                (size - hl + 2, size - hl + 2), hl)
            screen.blit(surf,
                        (int(b['x']) - size - 2, int(b['y']) - size - 2))


class GroundAnimation(BattleAnimation):
    """Ground/earthquake with rising rock pillars and dust."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.7)
        self.pillars = []
        for i in range(5):
            self.pillars.append({
                'x': target_pos[0] + (i - 2) * 22,
                'height': random.randint(20, 50),
                'width': random.randint(12, 20),
                'delay': abs(i - 2) * 0.04,
            })
        self.dust = []
        for _ in range(10):
            self.dust.append({
                'x': float(target_pos[0] + random.randint(-40, 40)),
                'y': float(target_pos[1] + random.randint(-5, 5)),
                'vx': random.uniform(-40, 40),
                'vy': random.uniform(-30, -70),
                'size': random.randint(4, 9),
            })

    def update(self, dt: float):
        super().update(dt)
        for d in self.dust:
            d['x'] += d['vx'] * dt
            d['y'] += d['vy'] * dt

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration

        for pillar in self.pillars:
            local_elapsed = max(0, self.elapsed - pillar['delay'])
            if local_elapsed <= 0:
                continue
            p = min(1.0, local_elapsed / 0.2)
            rise = self.ease_out_cubic(p)
            fade_p = max(0, (progress - 0.5) / 0.5) if progress > 0.5 else 0
            alpha = max(0, int(255 * (1 - fade_p)))
            h = int(pillar['height'] * rise)
            w = pillar['width']
            if h > 0 and alpha > 0:
                surf = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(
                    surf, (160, 130, 90, alpha), (0, 0, w, h))
                pygame.draw.rect(
                    surf, (180, 150, 110, alpha), (2, 0, w - 4, h), 1)
                screen.blit(surf,
                            (pillar['x'] - w // 2,
                             self.target_pos[1] - h))

        # Dust clouds
        alpha = max(0, int(180 * (1 - progress)))
        for d in self.dust:
            size = max(1, int(d['size'] * (1 - progress * 0.3)))
            if size > 0 and alpha > 0:
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    surf, (180, 160, 120, alpha),
                    (size, size), size)
                screen.blit(surf,
                            (int(d['x']) - size, int(d['y']) - size))


class FlyingAnimation(BattleAnimation):
    """Wind gust with swooping arcs and feathers."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.6)
        self.arcs = []
        for i in range(4):
            self.arcs.append({
                'y_offset': (i - 1.5) * 18,
                'delay': i * 0.05,
                'amplitude': random.uniform(15, 30),
            })
        self.feathers = []
        for _ in range(6):
            self.feathers.append({
                'x': float(target_pos[0] + random.randint(-30, 30)),
                'y': float(target_pos[1] + random.randint(-20, 20)),
                'vx': random.uniform(60, 140),
                'vy': random.uniform(-40, 40),
                'rotation': random.uniform(0, 360),
                'rot_speed': random.uniform(-200, 200),
                'size': random.randint(3, 6),
            })

    def update(self, dt: float):
        super().update(dt)
        for f in self.feathers:
            f['x'] += f['vx'] * dt
            f['y'] += f['vy'] * dt
            f['vy'] += 50 * dt
            f['rotation'] += f['rot_speed'] * dt

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration
        alpha = max(0, int(220 * (1 - progress)))

        # Wind arcs
        for arc in self.arcs:
            local_elapsed = max(0, self.elapsed - arc['delay'])
            if local_elapsed <= 0:
                continue
            arc_progress = min(1.0, local_elapsed * 3)
            sweep = self.ease_out_cubic(arc_progress)

            points = []
            for t in range(20):
                frac = t / 19.0
                if frac > sweep:
                    break
                ax = self.target_pos[0] - 50 + frac * 100
                ay = (self.target_pos[1] + arc['y_offset'] +
                      math.sin(frac * math.pi) * arc['amplitude'])
                points.append((int(ax), int(ay)))

            if len(points) > 1:
                arc_alpha = max(0, int(alpha * (1 - arc_progress * 0.5)))
                # Draw on SRCALPHA surface
                min_x = min(p[0] for p in points) - 5
                min_y = min(p[1] for p in points) - 5
                max_x = max(p[0] for p in points) + 5
                max_y = max(p[1] for p in points) + 5
                w = max(1, max_x - min_x)
                h = max(1, max_y - min_y)
                surf = pygame.Surface((w, h), pygame.SRCALPHA)
                local_pts = [(p[0] - min_x, p[1] - min_y) for p in points]
                if len(local_pts) > 1:
                    pygame.draw.lines(
                        surf, (200, 230, 255, arc_alpha),
                        False, local_pts, 3)
                screen.blit(surf, (min_x, min_y))

        # Feathers
        for f in self.feathers:
            size = f['size']
            if alpha <= 0:
                continue
            surf = pygame.Surface((size * 3, size * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(
                surf, (220, 230, 245, alpha),
                (0, 0, size * 3, size * 2))
            rotated = pygame.transform.rotate(surf, f['rotation'])
            rect = rotated.get_rect(center=(int(f['x']), int(f['y'])))
            screen.blit(rotated, rect)


class GhostAnimation(BattleAnimation):
    """Ghostly wisps with fading shadow balls."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.9)
        self.wisps = []
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(20, 50)
            self.wisps.append({
                'angle': angle,
                'dist': dist,
                'speed': random.uniform(2, 4),
                'size': random.randint(6, 14),
                'phase': random.uniform(0, 2 * math.pi),
            })

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration

        # Central shadow pulse
        if progress < 0.6:
            pulse_p = progress / 0.6
            radius = int(35 * self.ease_out_cubic(pulse_p))
            pulse_alpha = max(0, int(150 * (1 - pulse_p)))
            if radius > 2:
                surf = pygame.Surface(
                    (radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    surf, (60, 20, 80, pulse_alpha),
                    (radius + 2, radius + 2), radius)
                screen.blit(surf,
                            (self.target_pos[0] - radius - 2,
                             self.target_pos[1] - radius - 2))

        alpha = max(0, int(220 * (1 - progress)))
        for wisp in self.wisps:
            a = wisp['angle'] + self.elapsed * wisp['speed']
            d = wisp['dist'] + math.sin(self.elapsed * 3 + wisp['phase']) * 10
            wx = self.target_pos[0] + math.cos(a) * d
            wy = self.target_pos[1] + math.sin(a) * d
            size = wisp['size']
            wisp_alpha = max(0, int(alpha * (0.5 + 0.5 * math.sin(self.elapsed * 5 + wisp['phase']))))

            if size > 1 and wisp_alpha > 0:
                surf = pygame.Surface(
                    (size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    surf, (100, 50, 150, wisp_alpha),
                    (size + 2, size + 2), size)
                pygame.draw.circle(
                    surf, (150, 80, 200, wisp_alpha // 2),
                    (size + 2, size + 2), max(1, size // 2))
                screen.blit(surf, (int(wx) - size - 2, int(wy) - size - 2))


class DragonAnimation(BattleAnimation):
    """Dragon energy with spiraling flames and power ring."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.9)
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'angle': random.uniform(0, 2 * math.pi),
                'dist': random.uniform(5, 15),
                'speed': random.uniform(3, 6),
                'size': random.randint(4, 10),
                'expand_speed': random.uniform(40, 80),
            })

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration
        alpha = max(0, int(255 * (1 - progress * 0.8)))

        # Power ring
        if progress < 0.5:
            ring_p = progress / 0.5
            radius = int(45 * self.ease_out_cubic(ring_p))
            ring_alpha = max(0, int(180 * (1 - ring_p)))
            if radius > 2:
                surf = pygame.Surface(
                    (radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    surf, (100, 50, 200, ring_alpha),
                    (radius + 2, radius + 2), radius, 3)
                screen.blit(surf,
                            (self.target_pos[0] - radius - 2,
                             self.target_pos[1] - radius - 2))

        # Spiraling energy particles
        for p in self.particles:
            a = p['angle'] + self.elapsed * p['speed']
            d = p['dist'] + self.elapsed * p['expand_speed']
            px = self.target_pos[0] + math.cos(a) * d
            py = self.target_pos[1] + math.sin(a) * d
            size = max(1, int(p['size'] * (1 - progress * 0.5)))

            # Dragon colors: deep purple and indigo
            p_alpha = max(0, int(alpha * (1 - d / 100)))
            if size > 0 and p_alpha > 0:
                surf = pygame.Surface(
                    (size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    surf, (120, 50, 200, p_alpha),
                    (size + 1, size + 1), size)
                pygame.draw.circle(
                    surf, (180, 100, 255, p_alpha // 2),
                    (size + 1, size + 1), max(1, size // 2))
                screen.blit(surf, (int(px) - size - 1, int(py) - size - 1))


class DarkAnimation(BattleAnimation):
    """Dark pulse with shadow waves."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.7)
        self.waves = []
        for i in range(3):
            self.waves.append({
                'delay': i * 0.1,
                'max_radius': 40 + i * 15,
            })

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration

        # Dark flash
        if progress < 0.15:
            flash_alpha = int(180 * (1 - progress / 0.15))
            flash_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(
                flash_surf, (30, 0, 50, flash_alpha), (40, 40), 40)
            screen.blit(flash_surf,
                        (self.target_pos[0] - 40, self.target_pos[1] - 40))

        for wave in self.waves:
            local_elapsed = max(0, self.elapsed - wave['delay'])
            if local_elapsed <= 0:
                continue
            wp = min(1.0, local_elapsed / 0.4)
            radius = int(wave['max_radius'] * self.ease_out_cubic(wp))
            wave_alpha = max(0, int(180 * (1 - wp)))

            if radius > 2 and wave_alpha > 0:
                surf = pygame.Surface(
                    (radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    surf, (40, 10, 60, wave_alpha // 2),
                    (radius + 2, radius + 2), radius)
                pygame.draw.circle(
                    surf, (80, 20, 100, wave_alpha),
                    (radius + 2, radius + 2), radius, 2)
                screen.blit(surf,
                            (self.target_pos[0] - radius - 2,
                             self.target_pos[1] - radius - 2))


class SteelAnimation(BattleAnimation):
    """Metallic shards with shine effect."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.55)
        self.shards = []
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 200)
            self.shards.append({
                'x': float(target_pos[0]),
                'y': float(target_pos[1]),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'rotation': random.uniform(0, 360),
                'rot_speed': random.uniform(-300, 300),
                'size': random.randint(4, 8),
            })

    def update(self, dt: float):
        super().update(dt)
        for s in self.shards:
            s['x'] += s['vx'] * dt
            s['y'] += s['vy'] * dt
            s['vy'] += 150 * dt
            s['rotation'] += s['rot_speed'] * dt

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration
        alpha = max(0, int(255 * (1 - progress)))

        # Central flash
        if progress < 0.2:
            flash_alpha = int(220 * (1 - progress / 0.2))
            surf = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(
                surf, (200, 210, 220, flash_alpha), (25, 25), 25)
            screen.blit(surf,
                        (self.target_pos[0] - 25, self.target_pos[1] - 25))

        for shard in self.shards:
            size = shard['size']
            if size < 2 or alpha <= 0:
                continue
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            # Metallic angular shard
            points = [
                (size, 0),
                (size * 2, size),
                (size, size * 2),
                (0, size),
            ]
            pygame.draw.polygon(
                surf, (180, 190, 210, alpha), points)
            # Shine
            pygame.draw.polygon(
                surf, (220, 230, 245, alpha // 2), points, 1)
            rotated = pygame.transform.rotate(surf, shard['rotation'])
            rect = rotated.get_rect(center=(int(shard['x']), int(shard['y'])))
            screen.blit(rotated, rect)


class FairyAnimation(BattleAnimation):
    """Fairy sparkle with twinkling stars and pink glow."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.9)
        self.sparkles = []
        for _ in range(16):
            self.sparkles.append({
                'x': target_pos[0] + random.randint(-40, 40),
                'y': target_pos[1] + random.randint(-40, 40),
                'phase': random.uniform(0, 2 * math.pi),
                'speed': random.uniform(4, 8),
                'size': random.randint(3, 7),
                'color': random.choice([
                    (255, 150, 200),
                    (255, 180, 220),
                    (255, 200, 240),
                    (240, 140, 190),
                ]),
                'vy': random.uniform(-30, -60),
            })

    def update(self, dt: float):
        super().update(dt)
        for s in self.sparkles:
            s['y'] += s['vy'] * dt

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration

        # Pink glow
        if progress < 0.6:
            glow_p = progress / 0.6
            radius = int(40 * self.ease_out_cubic(glow_p))
            glow_alpha = max(0, int(100 * (1 - glow_p)))
            if radius > 2:
                surf = pygame.Surface(
                    (radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    surf, (255, 150, 200, glow_alpha),
                    (radius + 2, radius + 2), radius)
                screen.blit(surf,
                            (self.target_pos[0] - radius - 2,
                             self.target_pos[1] - radius - 2))

        alpha = max(0, int(255 * (1 - progress)))
        for s in self.sparkles:
            twinkle = 0.5 + 0.5 * math.sin(self.elapsed * s['speed'] + s['phase'])
            s_alpha = int(alpha * twinkle)
            size = s['size']
            if size < 1 or s_alpha <= 0:
                continue

            r, g, b = s['color']
            # 4-pointed star
            surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            cx, cy = size * 2, size * 2
            points = []
            for i in range(8):
                angle = (i / 8) * 2 * math.pi - math.pi / 2
                rad = size * 1.5 if i % 2 == 0 else size * 0.4
                points.append((cx + math.cos(angle) * rad,
                               cy + math.sin(angle) * rad))
            if len(points) >= 3:
                pygame.draw.polygon(surf, (r, g, b, s_alpha), points)
                # Bright center
                pygame.draw.circle(
                    surf, (255, 255, 255, s_alpha),
                    (cx, cy), max(1, size // 3))
            screen.blit(surf,
                        (int(s['x']) - size * 2, int(s['y']) - size * 2))


class BugAnimation(BattleAnimation):
    """Bug swarm with small darting insects."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.75)
        self.bugs = []
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            self.bugs.append({
                'x': float(target_pos[0] + random.randint(-30, 30)),
                'y': float(target_pos[1] + random.randint(-20, 20)),
                'angle': angle,
                'speed': random.uniform(80, 160),
                'size': random.randint(3, 6),
                'turn_timer': 0.0,
                'turn_interval': random.uniform(0.08, 0.2),
            })

    def update(self, dt: float):
        super().update(dt)
        for bug in self.bugs:
            bug['x'] += math.cos(bug['angle']) * bug['speed'] * dt
            bug['y'] += math.sin(bug['angle']) * bug['speed'] * dt
            bug['turn_timer'] += dt
            if bug['turn_timer'] > bug['turn_interval']:
                bug['turn_timer'] = 0
                bug['angle'] += random.uniform(-1.5, 1.5)

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration
        alpha = max(0, int(230 * (1 - progress)))

        for bug in self.bugs:
            size = bug['size']
            if size < 1 or alpha <= 0:
                continue
            surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            # Body
            pygame.draw.circle(
                surf, (80, 140, 40, alpha),
                (size + 1, size + 1), size)
            # Wing hints
            pygame.draw.circle(
                surf, (140, 200, 100, alpha // 2),
                (size - 1, size - 1), max(1, size // 2))
            screen.blit(surf,
                        (int(bug['x']) - size - 1, int(bug['y']) - size - 1))


class RockAnimation(BattleAnimation):
    """Rock slide with tumbling boulders."""

    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.65)
        self.rocks = []
        for _ in range(8):
            self.rocks.append({
                'x': float(target_pos[0] + random.randint(-20, 20)),
                'y': float(target_pos[1] - 80),
                'vy': random.uniform(150, 280),
                'vx': random.uniform(-30, 30),
                'size': random.randint(6, 14),
                'rotation': random.uniform(0, 360),
                'rot_speed': random.uniform(-200, 200),
                'landed': False,
                'land_time': 0.0,
            })

    def update(self, dt: float):
        super().update(dt)
        for rock in self.rocks:
            if not rock['landed']:
                rock['y'] += rock['vy'] * dt
                rock['x'] += rock['vx'] * dt
                rock['rotation'] += rock['rot_speed'] * dt
                if rock['y'] >= self.target_pos[1]:
                    rock['y'] = self.target_pos[1]
                    rock['landed'] = True
                    rock['land_time'] = self.elapsed

    def render(self, screen: pygame.Surface):
        if not self.active:
            return

        progress = self.elapsed / self.duration
        alpha = max(0, int(255 * (1 - max(0, (progress - 0.5) / 0.5))))

        for rock in self.rocks:
            size = rock['size']
            if size < 2 or alpha <= 0:
                continue

            surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            # Irregular rock shape (hexagon-ish)
            points = []
            for i in range(6):
                a = (i / 6) * 2 * math.pi
                r = size * random.uniform(0.75, 1.0)
                points.append((size + 1 + math.cos(a) * r,
                               size + 1 + math.sin(a) * r))
            pygame.draw.polygon(
                surf, (140, 120, 90, alpha), points)
            pygame.draw.polygon(
                surf, (170, 150, 110, alpha), points, 1)

            rotated = pygame.transform.rotate(surf, rock['rotation'])
            rect = rotated.get_rect(center=(int(rock['x']), int(rock['y'])))
            screen.blit(rotated, rect)

            # Dust puff on landing
            if rock['landed']:
                dust_elapsed = self.elapsed - rock['land_time']
                if dust_elapsed < 0.3:
                    dust_p = dust_elapsed / 0.3
                    dust_alpha = max(0, int(150 * (1 - dust_p)))
                    dust_r = int(size * 2 * self.ease_out_cubic(dust_p))
                    if dust_r > 1:
                        d_surf = pygame.Surface(
                            (dust_r * 2 + 2, dust_r + 2), pygame.SRCALPHA)
                        pygame.draw.ellipse(
                            d_surf, (180, 160, 130, dust_alpha),
                            (1, 1, dust_r * 2, dust_r))
                        screen.blit(d_surf,
                                    (int(rock['x']) - dust_r - 1,
                                     int(rock['y']) - dust_r // 2))


class VSScreenAnimation:
    """VS screen shown at battle start with diagonal split panels."""

    def __init__(self, screen_width: int, screen_height: int, duration: float = 2.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.duration = duration
        self.elapsed = 0.0
        self.active = True

    def update(self, dt: float):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False

    def render(self, screen: pygame.Surface, player_name: str = "", opponent_name: str = ""):
        if not self.active:
            return

        progress = self.elapsed / self.duration

        # Phase 1: Panels slide in (0-0.3)
        # Phase 2: VS text scale-in (0.25-0.65)
        # Phase 3: Hold (0.65-0.75)
        # Phase 4: Fade out (0.75-1.0)

        overlay = pygame.Surface(
            (self.screen_width, self.screen_height), pygame.SRCALPHA)

        if progress < 0.75:
            alpha = 255
        else:
            alpha = max(0, int(255 * (1 - (progress - 0.75) / 0.25)))

        # Slide factor
        if progress < 0.3:
            slide = BattleAnimation.ease_out_cubic(progress / 0.3)
        else:
            slide = 1.0

        # Left panel (player side - blue gradient)
        left_width = int(self.screen_width * 0.55 * slide)
        if left_width > 0:
            points_left = [
                (0, 0),
                (left_width, 0),
                (left_width - 100, self.screen_height),
                (0, self.screen_height),
            ]
            # Dark blue base
            pygame.draw.polygon(overlay, (30, 60, 140, alpha), points_left)
            # Lighter stripe
            stripe_w = max(0, left_width - 30)
            if stripe_w > 20:
                stripe_points = [
                    (0, 0),
                    (stripe_w, 0),
                    (stripe_w - 100, self.screen_height),
                    (0, self.screen_height),
                ]
                pygame.draw.polygon(overlay, (45, 80, 170, alpha), stripe_points)

        # Right panel (opponent side - red gradient)
        right_start = self.screen_width - int(self.screen_width * 0.55 * slide)
        if right_start < self.screen_width:
            points_right = [
                (right_start + 100, 0),
                (self.screen_width, 0),
                (self.screen_width, self.screen_height),
                (right_start, self.screen_height),
            ]
            # Dark red base
            pygame.draw.polygon(overlay, (140, 30, 30, alpha), points_right)
            # Lighter stripe
            stripe_start = right_start + 30
            if stripe_start < self.screen_width:
                stripe_points = [
                    (stripe_start + 100, 0),
                    (self.screen_width, 0),
                    (self.screen_width, self.screen_height),
                    (stripe_start, self.screen_height),
                ]
                pygame.draw.polygon(overlay, (170, 45, 45, alpha), stripe_points)

        # Diagonal divider line
        if slide > 0.5:
            div_alpha = min(alpha, 200)
            mid_x = self.screen_width // 2
            pygame.draw.line(
                overlay, (255, 255, 200, div_alpha),
                (mid_x + 50, -5), (mid_x - 50, self.screen_height + 5), 4)

        screen.blit(overlay, (0, 0))

        # VS text with scale-in animation
        if 0.2 < progress < 0.9:
            if progress < 0.45:
                vs_progress = (progress - 0.2) / 0.25
                vs_scale = BattleAnimation.ease_out_back(min(1.0, vs_progress))
            else:
                vs_scale = 1.0
            vs_alpha = alpha

            size = max(24, int(100 * vs_scale))
            vs_font = pygame.font.Font(None, size)

            cx = self.screen_width // 2
            cy = self.screen_height // 2

            # Shadow layers for depth
            for offset in [4, 3, 2]:
                shadow = vs_font.render("VS", True, (0, 0, 0))
                shadow.set_alpha(max(0, vs_alpha - offset * 30))
                sr = shadow.get_rect(center=(cx + offset, cy + offset))
                screen.blit(shadow, sr)

            # Main VS text (golden)
            vs_text = vs_font.render("VS", True, (255, 220, 50))
            vs_text.set_alpha(vs_alpha)
            vr = vs_text.get_rect(center=(cx, cy))
            screen.blit(vs_text, vr)

            # Bright outline
            vs_outline = vs_font.render("VS", True, (255, 240, 150))
            vs_outline.set_alpha(vs_alpha // 3)
            screen.blit(vs_outline, vs_outline.get_rect(center=(cx, cy)))

        # Player and opponent names
        if 0.3 < progress < 0.9:
            name_progress = min(1.0, (progress - 0.3) / 0.15)
            name_alpha = int(alpha * BattleAnimation.ease_out_cubic(name_progress))
            name_font = pygame.font.Font(None, 36)

            if player_name:
                # Slide in from left
                x_offset = int(30 * (1 - BattleAnimation.ease_out_cubic(name_progress)))
                pt_shadow = name_font.render(player_name, True, (0, 0, 0))
                pt_shadow.set_alpha(name_alpha)
                screen.blit(pt_shadow,
                            pt_shadow.get_rect(
                                center=(self.screen_width // 4 - x_offset + 2,
                                        self.screen_height // 2 + 62)))
                pt = name_font.render(player_name, True, (255, 255, 255))
                pt.set_alpha(name_alpha)
                screen.blit(pt,
                            pt.get_rect(
                                center=(self.screen_width // 4 - x_offset,
                                        self.screen_height // 2 + 60)))

            if opponent_name:
                # Slide in from right
                x_offset = int(30 * (1 - BattleAnimation.ease_out_cubic(name_progress)))
                ot_shadow = name_font.render(opponent_name, True, (0, 0, 0))
                ot_shadow.set_alpha(name_alpha)
                screen.blit(ot_shadow,
                            ot_shadow.get_rect(
                                center=(self.screen_width * 3 // 4 + x_offset + 2,
                                        self.screen_height // 2 + 62)))
                ot = name_font.render(opponent_name, True, (255, 255, 255))
                ot.set_alpha(name_alpha)
                screen.blit(ot,
                            ot.get_rect(
                                center=(self.screen_width * 3 // 4 + x_offset,
                                        self.screen_height // 2 + 60)))


class ShakeAnimation:
    """Screen shake effect."""

    def __init__(self, intensity: float = 10, duration: float = 0.5):
        self.intensity = intensity
        self.duration = duration
        self.elapsed = 0.0
        self.active = True

    def update(self, dt: float):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False

    def get_offset(self) -> Tuple[int, int]:
        """Get current shake offset."""
        if not self.active:
            return (0, 0)

        current_intensity = self.intensity * (1 - self.elapsed / self.duration)
        offset_x = random.randint(-int(current_intensity), int(current_intensity))
        offset_y = random.randint(-int(current_intensity), int(current_intensity))
        return (offset_x, offset_y)


# Animation type to class mapping
_ANIMATION_CLASS_MAP: Dict[AnimationType, type] = {
    AnimationType.HIT: HitAnimation,
    AnimationType.SLASH: SlashAnimation,
    AnimationType.ELECTRIC: ElectricAnimation,
    AnimationType.FIRE: FireAnimation,
    AnimationType.WATER: WaterAnimation,
    AnimationType.GRASS: GrassAnimation,
    AnimationType.PSYCHIC: PsychicAnimation,
    AnimationType.GHOST: GhostAnimation,
    AnimationType.NORMAL: HitAnimation,
    AnimationType.ICE: IceAnimation,
    AnimationType.FIGHTING: FightingAnimation,
    AnimationType.POISON: PoisonAnimation,
    AnimationType.GROUND: GroundAnimation,
    AnimationType.FLYING: FlyingAnimation,
    AnimationType.BUG: BugAnimation,
    AnimationType.ROCK: RockAnimation,
    AnimationType.DRAGON: DragonAnimation,
    AnimationType.DARK: DarkAnimation,
    AnimationType.STEEL: SteelAnimation,
    AnimationType.FAIRY: FairyAnimation,
}


class BattleAnimationManager:
    """Manages all battle animations."""

    def __init__(self):
        self.animations: List[BattleAnimation] = []
        self.screen_shake: Optional[ShakeAnimation] = None
        self.damage_popups: List[DamagePopup] = []
        self.vs_screen: Optional[VSScreenAnimation] = None

    def add_animation(self, animation_type: AnimationType, target_pos: Tuple[int, int]):
        """Add a new animation."""
        if animation_type == AnimationType.SHAKE:
            self.screen_shake = ShakeAnimation()
        elif animation_type == AnimationType.FLASH:
            # Flash is handled via shake with low intensity
            self.screen_shake = ShakeAnimation(intensity=3, duration=0.3)
        else:
            anim_class = _ANIMATION_CLASS_MAP.get(animation_type, HitAnimation)
            self.animations.append(anim_class(target_pos))

    def add_damage_popup(self, target_pos: Tuple[int, int], damage: int,
                         is_critical: bool = False, effectiveness: float = 1.0):
        """Add a floating damage number."""
        self.damage_popups.append(
            DamagePopup(target_pos, damage, is_critical, effectiveness)
        )

    def start_vs_screen(self, screen_width: int, screen_height: int):
        """Start the VS screen animation."""
        self.vs_screen = VSScreenAnimation(screen_width, screen_height)

    def update(self, dt: float):
        """Update all animations."""
        self.animations = [a for a in self.animations if a.active]
        for anim in self.animations:
            anim.update(dt)

        self.damage_popups = [p for p in self.damage_popups if p.active]
        for popup in self.damage_popups:
            popup.update(dt)

        if self.screen_shake:
            self.screen_shake.update(dt)
            if not self.screen_shake.active:
                self.screen_shake = None

        if self.vs_screen:
            self.vs_screen.update(dt)
            if not self.vs_screen.active:
                self.vs_screen = None

    def render(self, screen: pygame.Surface):
        """Render all animations."""
        for anim in self.animations:
            anim.render(screen)
        for popup in self.damage_popups:
            popup.render(screen)

    def render_vs_screen(self, screen: pygame.Surface,
                         player_name: str = "", opponent_name: str = ""):
        """Render VS screen if active."""
        if self.vs_screen:
            self.vs_screen.render(screen, player_name, opponent_name)

    def get_screen_offset(self) -> Tuple[int, int]:
        """Get current screen shake offset."""
        if self.screen_shake:
            return self.screen_shake.get_offset()
        return (0, 0)

    def has_vs_screen(self) -> bool:
        """Check if VS screen is active."""
        return self.vs_screen is not None and self.vs_screen.active

    def clear(self):
        """Clear all animations."""
        self.animations.clear()
        self.damage_popups.clear()
        self.screen_shake = None
        self.vs_screen = None
