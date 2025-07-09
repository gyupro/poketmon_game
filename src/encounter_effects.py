"""
Enhanced encounter effects and visual indicators
"""

import pygame
import math
import random
from typing import Optional, Tuple


class EncounterEffects:
    """Manages visual effects for Pokemon encounters."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # Encounter transition effect
        self.encounter_transition_active = False
        self.transition_timer = 0.0
        self.transition_duration = 1.5
        self.transition_type = "spiral"  # spiral, flash, zoom
        
        # Grass rustling effect
        self.grass_particles = []
        self.max_grass_particles = 20
        
        # Exclamation mark for trainer battles
        self.exclamation_active = False
        self.exclamation_timer = 0.0
        self.exclamation_duration = 1.0
        self.exclamation_pos = (0, 0)
        
        # Screen flash effect
        self.flash_active = False
        self.flash_timer = 0.0
        self.flash_duration = 0.2
        self.flash_color = (255, 255, 255)
        
        # Shiny sparkle effect
        self.shiny_sparkles = []
        self.sparkle_duration = 2.0
        
    def start_encounter_transition(self, transition_type: str = "spiral"):
        """Start an encounter transition effect."""
        self.encounter_transition_active = True
        self.transition_timer = 0.0
        self.transition_type = transition_type
        
    def start_exclamation(self, pos: Tuple[int, int]):
        """Start trainer encounter exclamation effect."""
        self.exclamation_active = True
        self.exclamation_timer = 0.0
        self.exclamation_pos = pos
        
    def start_flash(self, color: Tuple[int, int, int] = (255, 255, 255)):
        """Start a screen flash effect."""
        self.flash_active = True
        self.flash_timer = 0.0
        self.flash_color = color
        
    def add_grass_rustle(self, x: int, y: int):
        """Add grass rustling particles at position."""
        for _ in range(5):
            particle = {
                'x': x + random.randint(-10, 10),
                'y': y,
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-3, -1),
                'life': 1.0,
                'size': random.randint(2, 4)
            }
            self.grass_particles.append(particle)
            
        # Limit particles
        if len(self.grass_particles) > self.max_grass_particles:
            self.grass_particles = self.grass_particles[-self.max_grass_particles:]
            
    def add_shiny_sparkle(self, x: int, y: int):
        """Add shiny Pokemon sparkle effect."""
        for i in range(8):
            angle = (math.pi * 2 * i) / 8
            sparkle = {
                'x': x,
                'y': y,
                'vx': math.cos(angle) * 3,
                'vy': math.sin(angle) * 3,
                'life': 1.0,
                'size': 6
            }
            self.shiny_sparkles.append(sparkle)
            
    def update(self, dt: float):
        """Update all effects."""
        # Update encounter transition
        if self.encounter_transition_active:
            self.transition_timer += dt
            if self.transition_timer >= self.transition_duration:
                self.encounter_transition_active = False
                
        # Update exclamation
        if self.exclamation_active:
            self.exclamation_timer += dt
            if self.exclamation_timer >= self.exclamation_duration:
                self.exclamation_active = False
                
        # Update flash
        if self.flash_active:
            self.flash_timer += dt
            if self.flash_timer >= self.flash_duration:
                self.flash_active = False
                
        # Update grass particles
        for particle in self.grass_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.2  # Gravity
            particle['life'] -= dt * 2
            
            if particle['life'] <= 0:
                self.grass_particles.remove(particle)
                
        # Update shiny sparkles
        for sparkle in self.shiny_sparkles[:]:
            sparkle['x'] += sparkle['vx']
            sparkle['y'] += sparkle['vy']
            sparkle['vx'] *= 0.95  # Deceleration
            sparkle['vy'] *= 0.95
            sparkle['life'] -= dt / self.sparkle_duration
            
            if sparkle['life'] <= 0:
                self.shiny_sparkles.remove(sparkle)
                
    def render(self):
        """Render all active effects."""
        # Render grass particles
        for particle in self.grass_particles:
            alpha = int(255 * particle['life'])
            color = (34, 139, 34)  # Green
            size = int(particle['size'] * particle['life'])
            if size > 0:
                pygame.draw.circle(self.screen, color, 
                                 (int(particle['x']), int(particle['y'])), size)
                
        # Render shiny sparkles
        for sparkle in self.shiny_sparkles:
            alpha = int(255 * sparkle['life'])
            # Draw star shape
            x, y = int(sparkle['x']), int(sparkle['y'])
            size = int(sparkle['size'] * sparkle['life'])
            if size > 0:
                # Four-pointed star
                points = [
                    (x, y - size),
                    (x + size//3, y - size//3),
                    (x + size, y),
                    (x + size//3, y + size//3),
                    (x, y + size),
                    (x - size//3, y + size//3),
                    (x - size, y),
                    (x - size//3, y - size//3)
                ]
                pygame.draw.polygon(self.screen, (255, 255, 0), points)
                pygame.draw.polygon(self.screen, (255, 255, 255), points, 1)
                
        # Render exclamation mark
        if self.exclamation_active:
            self._render_exclamation()
            
        # Render encounter transition
        if self.encounter_transition_active:
            self._render_transition()
            
        # Render flash
        if self.flash_active:
            self._render_flash()
            
    def _render_exclamation(self):
        """Render exclamation mark effect."""
        # Bounce animation
        bounce = abs(math.sin(self.exclamation_timer * 10)) * 10
        x, y = self.exclamation_pos
        y -= bounce + 40
        
        # Draw exclamation mark
        font = pygame.font.Font(None, 48)
        text = font.render("!", True, (255, 255, 0))
        outline = font.render("!", True, (0, 0, 0))
        
        # Draw outline
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            self.screen.blit(outline, (x + dx - text.get_width()//2, 
                                      y + dy - text.get_height()//2))
        
        # Draw main text
        self.screen.blit(text, (x - text.get_width()//2, 
                               y - text.get_height()//2))
        
    def _render_transition(self):
        """Render encounter transition effect."""
        progress = self.transition_timer / self.transition_duration
        
        if self.transition_type == "spiral":
            # Spiral wipe effect
            num_circles = 20
            max_radius = max(self.screen_width, self.screen_height)
            
            for i in range(num_circles):
                angle = i * 0.5 + progress * math.pi * 4
                radius = (1 - progress) * max_radius * (1 - i / num_circles)
                x = self.screen_width // 2 + math.cos(angle) * radius * 0.3
                y = self.screen_height // 2 + math.sin(angle) * radius * 0.3
                
                circle_radius = int(radius * 0.2)
                if circle_radius > 0:
                    pygame.draw.circle(self.screen, (0, 0, 0), 
                                     (int(x), int(y)), circle_radius)
                    
        elif self.transition_type == "zoom":
            # Zoom effect
            rect_width = int(self.screen_width * (1 - progress))
            rect_height = int(self.screen_height * (1 - progress))
            if rect_width > 0 and rect_height > 0:
                x = (self.screen_width - rect_width) // 2
                y = (self.screen_height - rect_height) // 2
                
                # Draw black bars
                pygame.draw.rect(self.screen, (0, 0, 0), 
                               (0, 0, self.screen_width, y))
                pygame.draw.rect(self.screen, (0, 0, 0), 
                               (0, y + rect_height, self.screen_width, 
                                self.screen_height - y - rect_height))
                pygame.draw.rect(self.screen, (0, 0, 0), 
                               (0, y, x, rect_height))
                pygame.draw.rect(self.screen, (0, 0, 0), 
                               (x + rect_width, y, 
                                self.screen_width - x - rect_width, rect_height))
                                
        elif self.transition_type == "flash":
            # Multiple flash effect
            if int(progress * 10) % 2 == 0:
                flash_surface = pygame.Surface((self.screen_width, self.screen_height))
                flash_surface.fill((255, 255, 255))
                flash_surface.set_alpha(128)
                self.screen.blit(flash_surface, (0, 0))
                
    def _render_flash(self):
        """Render screen flash effect."""
        alpha = int(255 * (1 - self.flash_timer / self.flash_duration))
        flash_surface = pygame.Surface((self.screen_width, self.screen_height))
        flash_surface.fill(self.flash_color)
        flash_surface.set_alpha(alpha)
        self.screen.blit(flash_surface, (0, 0))


class EncounterInfo:
    """Display information about encounters and chains."""
    
    def __init__(self):
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        
    def render(self, screen: pygame.Surface, encounter_data: dict, x: int = 10, y: int = 10):
        """Render encounter information HUD."""
        # Background
        info_height = 80
        info_width = 200
        bg_rect = pygame.Rect(x, y, info_width, info_height)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect)
        pygame.draw.rect(screen, (255, 255, 255), bg_rect, 2)
        
        # Area name
        area_text = self.font.render(f"Area: {encounter_data.get('area', 'Unknown')}", 
                                   True, (255, 255, 255))
        screen.blit(area_text, (x + 10, y + 5))
        
        # Chain info
        chain_species = encounter_data.get('chain_species')
        chain_count = encounter_data.get('chain_count', 0)
        
        if chain_species:
            chain_text = self.small_font.render(f"Chain: #{chain_species} x{chain_count}", 
                                              True, (255, 255, 0))
            screen.blit(chain_text, (x + 10, y + 30))
        else:
            no_chain_text = self.small_font.render("No active chain", 
                                                 True, (150, 150, 150))
            screen.blit(no_chain_text, (x + 10, y + 30))
            
        # Repel status
        repel_steps = encounter_data.get('repel_steps', 0)
        if repel_steps > 0:
            repel_text = self.small_font.render(f"Repel: {repel_steps} steps", 
                                              True, (100, 200, 255))
            screen.blit(repel_text, (x + 10, y + 50))