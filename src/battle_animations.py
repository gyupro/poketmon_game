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


class HitAnimation(BattleAnimation):
    """Basic hit/impact animation."""
    
    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.5)
        self.particles = []
        # Create impact particles
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            self.particles.append({
                'x': target_pos[0],
                'y': target_pos[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.randint(3, 8),
                'color': (255, 255, 100)
            })
    
    def update(self, dt: float):
        super().update(dt)
        # Update particles
        for particle in self.particles:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['size'] = max(0, particle['size'] - dt * 10)
    
    def render(self, screen: pygame.Surface):
        if not self.active:
            return
        
        # Draw impact star
        progress = self.elapsed / self.duration
        size = int(30 * (1 - progress))
        if size > 0:
            # Draw star shape
            points = []
            for i in range(8):
                angle = (i / 8) * 2 * math.pi
                if i % 2 == 0:
                    r = size
                else:
                    r = size * 0.5
                x = self.target_pos[0] + math.cos(angle) * r
                y = self.target_pos[1] + math.sin(angle) * r
                points.append((x, y))
            
            if len(points) >= 3:
                pygame.draw.polygon(screen, (255, 255, 0), points)
                pygame.draw.polygon(screen, (255, 200, 0), points, 2)
        
        # Draw particles
        for particle in self.particles:
            if particle['size'] > 0:
                pygame.draw.circle(screen, particle['color'], 
                                 (int(particle['x']), int(particle['y'])), 
                                 int(particle['size']))


class SlashAnimation(BattleAnimation):
    """Slash effect animation."""
    
    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.4)
        
    def render(self, screen: pygame.Surface):
        if not self.active:
            return
            
        progress = self.elapsed / self.duration
        
        # Draw three slash lines
        for i in range(3):
            offset = i * 20 - 20
            start_x = self.target_pos[0] - 40 + offset
            start_y = self.target_pos[1] - 40
            end_x = self.target_pos[0] + 40 + offset
            end_y = self.target_pos[1] + 40
            
            # Animate the slash
            current_end_x = start_x + (end_x - start_x) * progress
            current_end_y = start_y + (end_y - start_y) * progress
            
            # Fade out
            alpha = int(255 * (1 - progress))
            color = (255, 255, 255, alpha) if alpha > 0 else (255, 255, 255)
            
            pygame.draw.line(screen, color, 
                           (start_x, start_y), 
                           (current_end_x, current_end_y), 3)


class ElectricAnimation(BattleAnimation):
    """Electric shock animation."""
    
    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.8)
        self.bolts = []
        
    def update(self, dt: float):
        super().update(dt)
        # Generate new lightning bolts
        if random.random() < 0.3:
            self.bolts = self._generate_bolts()
    
    def _generate_bolts(self) -> List[List[Tuple[int, int]]]:
        """Generate random lightning bolt paths."""
        bolts = []
        for _ in range(random.randint(2, 4)):
            bolt = []
            x = self.target_pos[0] + random.randint(-30, 30)
            y = self.target_pos[1] - 60
            
            while y < self.target_pos[1] + 30:
                bolt.append((x, y))
                x += random.randint(-15, 15)
                y += random.randint(10, 20)
                
            bolts.append(bolt)
        return bolts
    
    def render(self, screen: pygame.Surface):
        if not self.active:
            return
            
        # Draw lightning bolts
        for bolt in self.bolts:
            if len(bolt) > 1:
                # Main bolt
                pygame.draw.lines(screen, (255, 255, 100), False, bolt, 3)
                # Glow effect
                pygame.draw.lines(screen, (255, 255, 200), False, bolt, 1)


class FireAnimation(BattleAnimation):
    """Fire effect animation."""
    
    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 1.0)
        self.flames = []
        # Initialize flame particles
        for _ in range(20):
            self.flames.append({
                'x': target_pos[0] + random.randint(-20, 20),
                'y': target_pos[1] + random.randint(-10, 10),
                'vy': random.uniform(-50, -100),
                'life': random.uniform(0, 0.5),
                'size': random.randint(5, 12)
            })
    
    def update(self, dt: float):
        super().update(dt)
        # Update flame particles
        for flame in self.flames:
            flame['y'] += flame['vy'] * dt
            flame['x'] += random.uniform(-20, 20) * dt
            flame['life'] += dt
            
            # Reset flame when it dies
            if flame['life'] > 0.5:
                flame['x'] = self.target_pos[0] + random.randint(-20, 20)
                flame['y'] = self.target_pos[1] + random.randint(-10, 10)
                flame['life'] = 0
    
    def render(self, screen: pygame.Surface):
        if not self.active:
            return
            
        for flame in self.flames:
            alpha = 1 - (flame['life'] / 0.5)
            if alpha > 0:
                # Color transitions from white to yellow to red
                if alpha > 0.7:
                    color = (255, 255, 200)
                elif alpha > 0.3:
                    color = (255, 200, 0)
                else:
                    color = (255, 100, 0)
                    
                size = int(flame['size'] * alpha)
                if size > 0:
                    pygame.draw.circle(screen, color, 
                                     (int(flame['x']), int(flame['y'])), size)


class WaterAnimation(BattleAnimation):
    """Water splash animation."""
    
    def __init__(self, target_pos: Tuple[int, int]):
        super().__init__(target_pos, 0.8)
        self.bubbles = []
        # Create water bubbles
        for _ in range(15):
            self.bubbles.append({
                'x': target_pos[0] + random.randint(-30, 30),
                'y': target_pos[1],
                'vy': random.uniform(-100, -200),
                'vx': random.uniform(-50, 50),
                'size': random.randint(4, 10),
                'life': 0
            })
    
    def update(self, dt: float):
        super().update(dt)
        for bubble in self.bubbles:
            bubble['x'] += bubble['vx'] * dt
            bubble['y'] += bubble['vy'] * dt
            bubble['vy'] += 300 * dt  # Gravity
            bubble['life'] += dt
    
    def render(self, screen: pygame.Surface):
        if not self.active:
            return
            
        for bubble in self.bubbles:
            if bubble['life'] < 0.6:
                alpha = 1 - (bubble['life'] / 0.6)
                # Blue color with transparency
                color = (100, 150, 255)
                size = int(bubble['size'] * alpha)
                if size > 0:
                    pygame.draw.circle(screen, color,
                                     (int(bubble['x']), int(bubble['y'])), size)
                    # Add highlight
                    pygame.draw.circle(screen, (200, 220, 255),
                                     (int(bubble['x'] - size//3), int(bubble['y'] - size//3)), 
                                     max(1, size//3))


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
            
        # Decrease intensity over time
        current_intensity = self.intensity * (1 - self.elapsed / self.duration)
        offset_x = random.randint(-int(current_intensity), int(current_intensity))
        offset_y = random.randint(-int(current_intensity), int(current_intensity))
        return (offset_x, offset_y)


class BattleAnimationManager:
    """Manages all battle animations."""
    
    def __init__(self):
        self.animations: List[BattleAnimation] = []
        self.screen_shake: Optional[ShakeAnimation] = None
        
    def add_animation(self, animation_type: AnimationType, target_pos: Tuple[int, int]):
        """Add a new animation."""
        if animation_type == AnimationType.HIT:
            self.animations.append(HitAnimation(target_pos))
        elif animation_type == AnimationType.SLASH:
            self.animations.append(SlashAnimation(target_pos))
        elif animation_type == AnimationType.ELECTRIC:
            self.animations.append(ElectricAnimation(target_pos))
        elif animation_type == AnimationType.FIRE:
            self.animations.append(FireAnimation(target_pos))
        elif animation_type == AnimationType.WATER:
            self.animations.append(WaterAnimation(target_pos))
        elif animation_type == AnimationType.SHAKE:
            self.screen_shake = ShakeAnimation()
            
    def update(self, dt: float):
        """Update all animations."""
        # Update animations
        self.animations = [anim for anim in self.animations if anim.active]
        for anim in self.animations:
            anim.update(dt)
            
        # Update screen shake
        if self.screen_shake:
            self.screen_shake.update(dt)
            if not self.screen_shake.active:
                self.screen_shake = None
                
    def render(self, screen: pygame.Surface):
        """Render all animations."""
        for anim in self.animations:
            anim.render(screen)
            
    def get_screen_offset(self) -> Tuple[int, int]:
        """Get current screen shake offset."""
        if self.screen_shake:
            return self.screen_shake.get_offset()
        return (0, 0)
        
    def clear(self):
        """Clear all animations."""
        self.animations.clear()
        self.screen_shake = None