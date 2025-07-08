"""
UI Components - Comprehensive UI system for Pokemon game
"""

import pygame
import os
from typing import Optional, List, Tuple, Dict, Callable
from enum import Enum
from .player import Player
from .battle import Battle, BattleState, BattleAction
from .pokemon import Pokemon, StatusCondition, PokemonType


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


class Colors:
    """Pokemon-style color palette."""
    # Basic colors
    WHITE = (248, 248, 248)
    BLACK = (0, 0, 0)
    RED = (248, 80, 80)
    GREEN = (112, 248, 168)
    BLUE = (104, 144, 240)
    YELLOW = (248, 208, 48)
    GRAY = (168, 168, 168)
    DARK_GRAY = (96, 96, 96)
    
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
        PokemonType.FAIRY: (238, 153, 172)
    }
    
    # UI colors
    MENU_BG = (248, 248, 248)
    MENU_BORDER = (96, 96, 96)
    BUTTON_NORMAL = (224, 224, 224)
    BUTTON_HOVER = (200, 200, 200)
    BUTTON_PRESSED = (176, 176, 176)
    HP_GREEN = (96, 248, 96)
    HP_YELLOW = (248, 224, 56)
    HP_RED = (248, 88, 56)
    EXP_BLUE = (64, 200, 248)
    TEXT_DARK = (64, 64, 64)
    TEXT_LIGHT = (248, 248, 248)


class Button:
    """Reusable button component."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 font: pygame.font.Font, callback: Optional[Callable] = None,
                 color_normal=None, color_hover=None, color_pressed=None,
                 text_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.callback = callback
        
        self.color_normal = color_normal or Colors.BUTTON_NORMAL
        self.color_hover = color_hover or Colors.BUTTON_HOVER
        self.color_pressed = color_pressed or Colors.BUTTON_PRESSED
        self.text_color = text_color or Colors.TEXT_DARK
        
        self.current_color = self.color_normal
        self.is_hovered = False
        self.is_pressed = False
        self.enabled = True
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events. Returns True if button was clicked."""
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
        """Draw the button."""
        # Draw button background
        pygame.draw.rect(screen, self.current_color, self.rect)
        pygame.draw.rect(screen, Colors.MENU_BORDER, self.rect, 2)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class DialogBox:
    """Dialog box for displaying text with typewriter effect."""
    
    def __init__(self, x: int, y: int, width: int, height: int, font: pygame.font.Font):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.padding = 16
        
        self.text = ""
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0
        self.char_delay = 30  # milliseconds per character
        self.is_complete = False
        
        self.lines: List[str] = []
        self.max_lines = 3
    
    def set_text(self, text: str):
        """Set new text to display."""
        self.text = text
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0
        self.is_complete = False
        self._wrap_text()
    
    def _wrap_text(self):
        """Wrap text to fit within dialog box."""
        words = self.text.split(' ')
        self.lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " " if current_line else word + " "
            text_width = self.font.size(test_line)[0]
            
            if text_width > self.rect.width - 2 * self.padding:
                if current_line:
                    self.lines.append(current_line.strip())
                    current_line = word + " "
                else:
                    self.lines.append(word)
                    current_line = ""
            else:
                current_line = test_line
        
        if current_line:
            self.lines.append(current_line.strip())
    
    def update(self, dt: float):
        """Update typewriter effect."""
        if not self.is_complete:
            self.char_timer += dt * 1000  # Convert to milliseconds
            
            while self.char_timer >= self.char_delay and self.char_index < len(self.text):
                self.char_index += 1
                self.char_timer -= self.char_delay
                self.displayed_text = self.text[:self.char_index]
            
            if self.char_index >= len(self.text):
                self.is_complete = True
    
    def skip_animation(self):
        """Skip typewriter animation."""
        self.displayed_text = self.text
        self.char_index = len(self.text)
        self.is_complete = True
    
    def draw(self, screen: pygame.Surface):
        """Draw the dialog box."""
        # Draw background
        pygame.draw.rect(screen, Colors.MENU_BG, self.rect)
        pygame.draw.rect(screen, Colors.MENU_BORDER, self.rect, 3)
        
        # Draw text
        y_offset = self.padding
        displayed_lines = self._get_displayed_lines()
        
        for line in displayed_lines[-self.max_lines:]:
            text_surface = self.font.render(line, True, Colors.TEXT_DARK)
            screen.blit(text_surface, (self.rect.x + self.padding, self.rect.y + y_offset))
            y_offset += self.font.get_height() + 4
    
    def _get_displayed_lines(self) -> List[str]:
        """Get lines to display based on current character index."""
        if not self.displayed_text:
            return []
        
        words = self.displayed_text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " " if current_line else word + " "
            text_width = self.font.size(test_line)[0]
            
            if text_width > self.rect.width - 2 * self.padding:
                if current_line:
                    lines.append(current_line.strip())
                    current_line = word + " "
                else:
                    lines.append(word)
                    current_line = ""
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines


class HealthBar:
    """Animated health bar component."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.current_hp = 100
        self.max_hp = 100
        self.display_hp = 100  # For smooth animation
        self.animation_speed = 100  # HP per second
    
    def set_hp(self, current: int, maximum: int):
        """Set HP values."""
        self.current_hp = max(0, current)
        self.max_hp = max(1, maximum)
    
    def update(self, dt: float):
        """Update HP animation."""
        if self.display_hp != self.current_hp:
            change = self.animation_speed * dt
            if self.display_hp > self.current_hp:
                self.display_hp = max(self.current_hp, self.display_hp - change)
            else:
                self.display_hp = min(self.current_hp, self.display_hp + change)
    
    def draw(self, screen: pygame.Surface, show_text: bool = True):
        """Draw the health bar."""
        # Calculate percentages
        current_percent = self.current_hp / self.max_hp if self.max_hp > 0 else 0
        display_percent = self.display_hp / self.max_hp if self.max_hp > 0 else 0
        
        # Determine color
        if current_percent > 0.5:
            bar_color = Colors.HP_GREEN
        elif current_percent > 0.25:
            bar_color = Colors.HP_YELLOW
        else:
            bar_color = Colors.HP_RED
        
        # Draw background
        pygame.draw.rect(screen, Colors.DARK_GRAY, self.rect)
        
        # Draw health bar
        if display_percent > 0:
            health_rect = pygame.Rect(self.rect.x, self.rect.y,
                                    int(self.rect.width * display_percent), self.rect.height)
            pygame.draw.rect(screen, bar_color, health_rect)
        
        # Draw border
        pygame.draw.rect(screen, Colors.BLACK, self.rect, 2)
        
        # Draw HP text if requested
        if show_text:
            font = pygame.font.Font(None, 16)
            hp_text = f"{int(self.current_hp)}/{self.max_hp}"
            text_surface = font.render(hp_text, True, Colors.TEXT_DARK)
            text_rect = text_surface.get_rect(midleft=(self.rect.right + 8, self.rect.centery))
            screen.blit(text_surface, text_rect)


class ExperienceBar:
    """Experience bar component."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.current_exp = 0
        self.needed_exp = 100
        self.display_exp = 0
        self.animation_speed = 200  # EXP per second
    
    def set_exp(self, current: int, needed: int):
        """Set experience values."""
        self.current_exp = max(0, current)
        self.needed_exp = max(1, needed)
    
    def update(self, dt: float):
        """Update EXP animation."""
        if self.display_exp != self.current_exp:
            change = self.animation_speed * dt
            if self.display_exp < self.current_exp:
                self.display_exp = min(self.current_exp, self.display_exp + change)
            else:
                self.display_exp = max(self.current_exp, self.display_exp - change)
    
    def draw(self, screen: pygame.Surface):
        """Draw the experience bar."""
        # Calculate percentage
        display_percent = self.display_exp / self.needed_exp if self.needed_exp > 0 else 0
        
        # Draw background
        pygame.draw.rect(screen, Colors.DARK_GRAY, self.rect)
        
        # Draw exp bar
        if display_percent > 0:
            exp_rect = pygame.Rect(self.rect.x, self.rect.y,
                                 int(self.rect.width * display_percent), self.rect.height)
            pygame.draw.rect(screen, Colors.EXP_BLUE, exp_rect)
        
        # Draw border
        pygame.draw.rect(screen, Colors.BLACK, self.rect, 2)


class PokemonInfoPanel:
    """Panel displaying Pokemon information in battle."""
    
    def __init__(self, x: int, y: int, width: int, height: int, is_player: bool = False):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_player = is_player
        self.pokemon: Optional[Pokemon] = None
        
        # Create sub-components
        hp_y = y + 35
        self.health_bar = HealthBar(x + 10, hp_y, width - 60, 12)
        if is_player:
            self.exp_bar = ExperienceBar(x + 10, hp_y + 20, width - 20, 6)
        else:
            self.exp_bar = None
    
    def set_pokemon(self, pokemon: Pokemon):
        """Set the Pokemon to display."""
        self.pokemon = pokemon
        if pokemon:
            self.health_bar.set_hp(pokemon.current_hp, pokemon.stats["hp"])
            if self.is_player and self.exp_bar:
                # Calculate experience for current level
                current_level_exp = pokemon.get_exp_for_level(pokemon.level)
                next_level_exp = pokemon.get_exp_for_level(pokemon.level + 1)
                current_exp = pokemon.exp - current_level_exp
                needed_exp = next_level_exp - current_level_exp
                self.exp_bar.set_exp(current_exp, needed_exp)
    
    def update(self, dt: float):
        """Update animations."""
        if self.pokemon:
            self.health_bar.set_hp(self.pokemon.current_hp, self.pokemon.stats["hp"])
            self.health_bar.update(dt)
            if self.exp_bar:
                self.exp_bar.update(dt)
    
    def draw(self, screen: pygame.Surface):
        """Draw the info panel."""
        if not self.pokemon:
            return
        
        # Draw background
        pygame.draw.rect(screen, Colors.MENU_BG, self.rect)
        pygame.draw.rect(screen, Colors.MENU_BORDER, self.rect, 2)
        
        # Draw Pokemon name and level
        font = pygame.font.Font(None, 20)
        name_text = f"{self.pokemon.nickname} Lv.{self.pokemon.level}"
        text_surface = font.render(name_text, True, Colors.TEXT_DARK)
        screen.blit(text_surface, (self.rect.x + 10, self.rect.y + 8))
        
        # Draw status condition if any
        if self.pokemon.status != StatusCondition.NONE:
            status_text = self.pokemon.status.value.upper()[:3]
            status_color = Colors.RED
            if self.pokemon.status in [StatusCondition.PARALYZED]:
                status_color = Colors.YELLOW
            elif self.pokemon.status in [StatusCondition.ASLEEP, StatusCondition.FROZEN]:
                status_color = Colors.BLUE
            elif self.pokemon.status in [StatusCondition.POISONED, StatusCondition.BADLY_POISONED]:
                status_color = Colors.TYPE_COLORS[PokemonType.POISON]
            
            status_surface = font.render(status_text, True, status_color)
            screen.blit(status_surface, (self.rect.right - 40, self.rect.y + 8))
        
        # Draw health bar
        self.health_bar.draw(screen, show_text=True)
        
        # Draw experience bar for player
        if self.is_player and self.exp_bar:
            self.exp_bar.draw(screen)


class BattleMenu:
    """Battle action menu."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 24)
        
        # Menu states
        self.current_menu = "main"  # main, fight, bag, pokemon
        self.selected_index = 0
        self.battle: Optional[Battle] = None
        
        # Create buttons for main menu
        button_width = (width - 60) // 2
        button_height = 40
        self.main_buttons = [
            Button(x + 20, y + 20, button_width, button_height, "FIGHT", self.font),
            Button(x + 40 + button_width, y + 20, button_width, button_height, "BAG", self.font),
            Button(x + 20, y + 70, button_width, button_height, "POKEMON", self.font),
            Button(x + 40 + button_width, y + 70, button_width, button_height, "RUN", self.font)
        ]
    
    def set_battle(self, battle: Battle):
        """Set the battle reference."""
        self.battle = battle
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Tuple[BattleAction, Dict]]:
        """Handle input events. Returns action if one is selected."""
        if not self.battle or self.battle.is_over:
            return None
        
        if self.current_menu == "main":
            # Handle button clicks
            for i, button in enumerate(self.main_buttons):
                if button.handle_event(event):
                    if i == 0:  # FIGHT
                        self.current_menu = "fight"
                        self.selected_index = 0
                    elif i == 1:  # BAG
                        return (BattleAction.BAG, {})
                    elif i == 2:  # POKEMON
                        return (BattleAction.POKEMON, {})
                    elif i == 3:  # RUN
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
                        move_index = moves[self.selected_index][0]
                        self.current_menu = "main"
                        return (BattleAction.FIGHT, {"move_index": move_index})
        
        return None
    
    def draw(self, screen: pygame.Surface):
        """Draw the battle menu."""
        # Draw background
        pygame.draw.rect(screen, Colors.MENU_BG, self.rect)
        pygame.draw.rect(screen, Colors.MENU_BORDER, self.rect, 3)
        
        if self.current_menu == "main":
            # Draw main action buttons
            for button in self.main_buttons:
                button.draw(screen)
        
        elif self.current_menu == "fight":
            # Draw move selection
            if self.battle and self.battle.player_pokemon:
                moves = self.battle.get_valid_moves()
                
                # Draw title
                title_text = "Choose a move:"
                title_surface = self.font.render(title_text, True, Colors.TEXT_DARK)
                screen.blit(title_surface, (self.rect.x + 20, self.rect.y + 10))
                
                # Draw moves in 2x2 grid
                for i, (move_index, move) in enumerate(moves):
                    x = self.rect.x + 20 + (i % 2) * (self.rect.width // 2 - 20)
                    y = self.rect.y + 40 + (i // 2) * 35
                    
                    # Highlight selected move
                    if i == self.selected_index:
                        select_rect = pygame.Rect(x - 5, y - 2, self.rect.width // 2 - 30, 30)
                        pygame.draw.rect(screen, Colors.BUTTON_HOVER, select_rect)
                        pygame.draw.rect(screen, Colors.MENU_BORDER, select_rect, 2)
                    
                    # Draw move name
                    move_text = move.name
                    move_surface = self.font.render(move_text, True, Colors.TEXT_DARK)
                    screen.blit(move_surface, (x, y))
                    
                    # Draw PP
                    pp_text = f"{move.current_pp}/{move.max_pp}"
                    pp_surface = self.font.render(pp_text, True, Colors.DARK_GRAY)
                    screen.blit(pp_surface, (x + 150, y))
                
                # Draw move type and power for selected move
                if 0 <= self.selected_index < len(moves):
                    _, selected_move = moves[self.selected_index]
                    info_y = self.rect.y + self.rect.height - 30
                    
                    # Type
                    type_color = Colors.TYPE_COLORS.get(selected_move.type, Colors.GRAY)
                    type_text = selected_move.type.value.upper()
                    type_surface = self.font.render(type_text, True, type_color)
                    screen.blit(type_surface, (self.rect.x + 20, info_y))
                    
                    # Power
                    if selected_move.category != "status":
                        power_text = f"Power: {selected_move.power}"
                        power_surface = self.font.render(power_text, True, Colors.TEXT_DARK)
                        screen.blit(power_surface, (self.rect.x + 120, info_y))


class UI:
    """Main UI manager for the game."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # Initialize fonts
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 48)
        self.font_huge = pygame.font.Font(None, 72)
        
        # Current UI state
        self.state = UIState.MAIN_MENU
        
        # Initialize components
        self._init_battle_ui()
        self._init_menu_ui()
        
        # Sprite cache
        self.sprite_cache: Dict[str, pygame.Surface] = {}
        
        # Transition effect
        self.transition_alpha = 0
        self.transition_speed = 500  # Alpha per second
        self.transitioning = False
    
    def _init_battle_ui(self):
        """Initialize battle UI components."""
        # Dialog box at bottom
        self.battle_dialog = DialogBox(40, self.screen_height - 160, 
                                     self.screen_width - 80, 120, self.font_medium)
        
        # Battle menu above dialog
        self.battle_menu = BattleMenu(40, self.screen_height - 320,
                                    self.screen_width - 80, 140)
        
        # Pokemon info panels
        self.player_info_panel = PokemonInfoPanel(50, self.screen_height - 480, 280, 90, True)
        self.opponent_info_panel = PokemonInfoPanel(self.screen_width - 330, 50, 280, 70, False)
        
        # Pokemon sprite positions
        self.player_sprite_pos = (150, self.screen_height - 350)
        self.opponent_sprite_pos = (self.screen_width - 250, 150)
    
    def _init_menu_ui(self):
        """Initialize menu UI components."""
        # Main menu buttons
        button_width = 200
        button_height = 50
        center_x = self.screen_width // 2 - button_width // 2
        
        self.main_menu_buttons = [
            Button(center_x, 250, button_width, button_height, "New Game", 
                   self.font_medium, callback=None),  # Will be handled in handle_event
            Button(center_x, 320, button_width, button_height, "Continue", 
                   self.font_medium, callback=None),  # TODO: Implement save/load
            Button(center_x, 390, button_width, button_height, "Options", 
                   self.font_medium, callback=lambda: self.change_state(UIState.OPTIONS_MENU)),
            Button(center_x, 460, button_width, button_height, "Quit", 
                   self.font_medium, callback=lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)))
        ]
        
        # Pause menu dialog
        self.pause_dialog = DialogBox(self.screen_width // 4, self.screen_height // 4,
                                    self.screen_width // 2, self.screen_height // 2,
                                    self.font_medium)
    
    def load_sprite(self, sprite_path: str, size: Optional[Tuple[int, int]] = None) -> Optional[pygame.Surface]:
        """Load and cache a sprite."""
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
            else:
                print(f"Warning: Sprite not found: {sprite_path}")
                return None
        except Exception as e:
            print(f"Error loading sprite {sprite_path}: {e}")
            return None
    
    def change_state(self, new_state: UIState):
        """Change UI state with transition."""
        self.state = new_state
        self.transitioning = True
        self.transition_alpha = 255
    
    def update(self, dt: float):
        """Update UI animations."""
        # Update transition
        if self.transitioning and self.transition_alpha > 0:
            self.transition_alpha = max(0, self.transition_alpha - self.transition_speed * dt)
            if self.transition_alpha == 0:
                self.transitioning = False
        
        # Update components based on state
        if self.state == UIState.BATTLE:
            self.battle_dialog.update(dt)
            self.player_info_panel.update(dt)
            self.opponent_info_panel.update(dt)
    
    def handle_event(self, event: pygame.event.Event, game) -> bool:
        """Handle UI events. Returns True if event was handled."""
        if self.state == UIState.MAIN_MENU:
            for i, button in enumerate(self.main_menu_buttons):
                if button.handle_event(event):
                    if i == 0:  # New Game
                        game.create_new_game()
                        return True
                    elif button.callback:
                        button.callback()
                    return True
        
        elif self.state == UIState.BATTLE:
            # Handle battle menu input
            action = self.battle_menu.handle_event(event)
            if action and game.current_battle:
                action_type, params = action
                game.current_battle.set_player_action(action_type, **params)
                return True
            
            # Skip dialog animation on space/enter
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    if not self.battle_dialog.is_complete:
                        self.battle_dialog.skip_animation()
                        return True
        
        return False
    
    def draw_main_menu(self):
        """Draw main menu screen."""
        # Gradient background
        for y in range(self.screen_height):
            # Create a gradient from dark blue to light blue
            color_value = int(30 + (100 * y / self.screen_height))
            color = (color_value, color_value, min(255, color_value + 50))
            pygame.draw.line(self.screen, color, (0, y), (self.screen_width, y))
        
        # Title with shadow effect
        title_text = "POKEMON"
        # Shadow
        shadow_surface = self.font_huge.render(title_text, True, Colors.BLACK)
        shadow_rect = shadow_surface.get_rect(center=(self.screen_width // 2 + 3, 120 + 3))
        self.screen.blit(shadow_surface, shadow_rect)
        # Main title
        title_surface = self.font_huge.render(title_text, True, Colors.YELLOW)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 120))
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle with better styling
        subtitle_text = "Adventure Awaits!"
        subtitle_surface = self.font_medium.render(subtitle_text, True, Colors.WHITE)
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen_width // 2, 180))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Draw buttons with improved styling
        for button in self.main_menu_buttons:
            button.draw(self.screen)
        
        # Version with better positioning
        version_text = "v1.0.0"
        version_surface = self.font_small.render(version_text, True, Colors.WHITE)
        self.screen.blit(version_surface, (10, self.screen_height - 30))
        
        # Add decorative elements
        # Draw some stars
        import random
        random.seed(42)  # Fixed seed for consistent star positions
        for i in range(20):
            star_x = random.randint(0, self.screen_width)
            star_y = random.randint(0, self.screen_height // 2)
            pygame.draw.circle(self.screen, Colors.WHITE, (star_x, star_y), 2)
            pygame.draw.circle(self.screen, Colors.YELLOW, (star_x, star_y), 1)
    
    def draw_battle(self, battle: Battle):
        """Draw battle screen."""
        # Battle background
        self._draw_battle_background()
        
        # Update components with battle data
        self.battle_menu.set_battle(battle)
        self.player_info_panel.set_pokemon(battle.player_pokemon)
        self.opponent_info_panel.set_pokemon(battle.opponent_pokemon)
        
        # Update dialog with latest battle messages
        if battle.battle_log:
            latest_message = battle.battle_log[-1]
            if self.battle_dialog.text != latest_message:
                self.battle_dialog.set_text(latest_message)
        
        # Draw Pokemon sprites
        self._draw_pokemon_sprite(battle.player_pokemon, self.player_sprite_pos, True)
        self._draw_pokemon_sprite(battle.opponent_pokemon, self.opponent_sprite_pos, False)
        
        # Draw info panels
        self.player_info_panel.draw(self.screen)
        self.opponent_info_panel.draw(self.screen)
        
        # Draw battle UI
        if battle.state == BattleState.SELECTING_ACTION or battle.state == BattleState.SELECTING_MOVE:
            self.battle_menu.draw(self.screen)
        
        # Draw dialog box
        self.battle_dialog.draw(self.screen)
        
        # Draw type effectiveness indicator if in battle
        if battle.state == BattleState.TURN_EXECUTION and battle.last_used_move:
            self._draw_type_effectiveness(battle)
    
    def _draw_battle_background(self):
        """Draw battle background."""
        # Enhanced sky gradient
        for i in range(self.screen_height // 2):
            ratio = i / (self.screen_height // 2)
            # Sky blue to light blue gradient
            blue_value = int(135 + (120 * ratio))
            green_value = int(206 + (49 * ratio))
            red_value = int(135 + (120 * ratio))
            color = (red_value, green_value, blue_value)
            pygame.draw.line(self.screen, color, (0, i), (self.screen_width, i))
        
        # Enhanced ground with texture
        ground_color = (144, 208, 144)
        ground_rect = pygame.Rect(0, self.screen_height // 2, self.screen_width, self.screen_height // 2)
        pygame.draw.rect(self.screen, ground_color, ground_rect)
        
        # Add ground texture
        for i in range(0, self.screen_width, 40):
            for j in range(self.screen_height // 2, self.screen_height, 40):
                # Add grass patches
                patch_color = (124, 188, 124)
                pygame.draw.circle(self.screen, patch_color, (i + 20, j + 20), 15)
        
        # Enhanced battle platforms with shadows
        # Player platform
        player_platform = pygame.Rect(100, self.screen_height - 250, 200, 80)
        # Shadow
        shadow_platform = pygame.Rect(105, self.screen_height - 245, 200, 80)
        pygame.draw.ellipse(self.screen, (80, 120, 80), shadow_platform)
        # Main platform
        pygame.draw.ellipse(self.screen, (120, 176, 120), player_platform)
        pygame.draw.ellipse(self.screen, (96, 144, 96), player_platform, 3)
        # Highlight
        highlight_platform = pygame.Rect(110, self.screen_height - 240, 180, 60)
        pygame.draw.ellipse(self.screen, (140, 196, 140), highlight_platform, 2)
        
        # Opponent platform
        opponent_platform = pygame.Rect(self.screen_width - 300, 250, 200, 80)
        # Shadow
        shadow_platform = pygame.Rect(self.screen_width - 295, 255, 200, 80)
        pygame.draw.ellipse(self.screen, (80, 120, 80), shadow_platform)
        # Main platform
        pygame.draw.ellipse(self.screen, (120, 176, 120), opponent_platform)
        pygame.draw.ellipse(self.screen, (96, 144, 96), opponent_platform, 3)
        # Highlight
        highlight_platform = pygame.Rect(self.screen_width - 290, 260, 180, 60)
        pygame.draw.ellipse(self.screen, (140, 196, 140), highlight_platform, 2)
    
    def _draw_pokemon_sprite(self, pokemon: Pokemon, position: Tuple[int, int], is_back: bool):
        """Draw Pokemon sprite."""
        if not pokemon:
            return
        
        # Try to load sprite
        sprite_filename = f"{pokemon.species_id}_{'back' if is_back else 'normal'}.png"
        sprite_path = os.path.join("assets", "sprites", sprite_filename)
        
        sprite = self.load_sprite(sprite_path, (128, 128))
        if sprite:
            sprite_rect = sprite.get_rect(center=position)
            self.screen.blit(sprite, sprite_rect)
        else:
            # Fallback to colored circle with better visuals
            pokemon_color = Colors.TYPE_COLORS.get(pokemon.types[0], Colors.GRAY)
            
            # Draw main body
            pygame.draw.circle(self.screen, pokemon_color, position, 48)
            pygame.draw.circle(self.screen, Colors.BLACK, position, 48, 3)
            
            # Draw inner circle for depth
            inner_color = tuple(min(255, c + 30) for c in pokemon_color)
            pygame.draw.circle(self.screen, inner_color, position, 32)
            
            # Draw Pokemon name
            name_surface = self.font_small.render(pokemon.species_name, True, Colors.WHITE)
            name_rect = name_surface.get_rect(center=position)
            self.screen.blit(name_surface, name_rect)
            
            # Draw "Missing Sprite" indicator
            missing_text = self.font_small.render("(No Sprite)", True, Colors.WHITE)
            missing_rect = missing_text.get_rect(center=(position[0], position[1] + 20))
            self.screen.blit(missing_text, missing_rect)
    
    def _draw_type_effectiveness(self, battle: Battle):
        """Draw type effectiveness indicator."""
        # This would show "Super effective!", "Not very effective...", etc.
        pass
    
    def draw_world_hud(self, player: Player):
        """Draw HUD for world exploration."""
        # Enhanced player info panel with rounded corners effect
        panel_rect = pygame.Rect(10, 10, 320, 110)
        
        # Draw shadow
        shadow_rect = pygame.Rect(13, 13, 320, 110)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow_rect)
        
        # Draw main panel
        pygame.draw.rect(self.screen, Colors.MENU_BG, panel_rect)
        pygame.draw.rect(self.screen, Colors.MENU_BORDER, panel_rect, 3)
        
        # Draw inner border for depth
        inner_rect = pygame.Rect(15, 15, 310, 100)
        pygame.draw.rect(self.screen, Colors.WHITE, inner_rect, 1)
        
        # Player name with icon
        name_text = f"Trainer: {player.name}"
        name_surface = self.font_small.render(name_text, True, Colors.TEXT_DARK)
        self.screen.blit(name_surface, (25, 25))
        
        # Draw trainer icon
        pygame.draw.circle(self.screen, Colors.BLUE, (290, 35), 12)
        pygame.draw.circle(self.screen, Colors.WHITE, (290, 35), 8)
        
        # Money with coin icon
        money_text = f"Money: ${player.money:,}"
        money_surface = self.font_small.render(money_text, True, Colors.TEXT_DARK)
        self.screen.blit(money_surface, (25, 50))
        
        # Draw coin icon
        pygame.draw.circle(self.screen, Colors.YELLOW, (185, 55), 6)
        pygame.draw.circle(self.screen, Colors.TEXT_DARK, (185, 55), 6, 1)
        
        # Active Pokemon info
        if player.active_pokemon:
            pokemon_text = f"{player.active_pokemon.nickname} Lv.{player.active_pokemon.level}"
            pokemon_surface = self.font_small.render(pokemon_text, True, Colors.TEXT_DARK)
            self.screen.blit(pokemon_surface, (25, 75))
            
            # Enhanced health bar with border and background
            hp_percent = player.active_pokemon.current_hp / player.active_pokemon.stats["hp"]
            hp_color = Colors.HP_GREEN if hp_percent > 0.5 else Colors.HP_YELLOW if hp_percent > 0.25 else Colors.HP_RED
            
            # HP bar background
            hp_bar_bg = pygame.Rect(200, 78, 90, 12)
            pygame.draw.rect(self.screen, Colors.DARK_GRAY, hp_bar_bg)
            pygame.draw.rect(self.screen, Colors.BLACK, hp_bar_bg, 1)
            
            # HP bar fill
            if hp_percent > 0:
                hp_bar_fill = pygame.Rect(201, 79, int(88 * hp_percent), 10)
                pygame.draw.rect(self.screen, hp_color, hp_bar_fill)
            
            # HP text
            hp_text = f"{player.active_pokemon.current_hp}/{player.active_pokemon.stats['hp']}"
            hp_surface = self.font_small.render(hp_text, True, Colors.TEXT_DARK)
            self.screen.blit(hp_surface, (205, 95))
        
        # Draw controls hint
        controls_text = "WASD/Arrows: Move | Space: Interact | P: Pokemon | I: Items"
        controls_surface = self.font_small.render(controls_text, True, Colors.GRAY)
        self.screen.blit(controls_surface, (10, self.screen_height - 25))
    
    def draw_pokemon_menu(self, player: Player):
        """Draw Pokemon party menu."""
        # Background
        self.screen.fill(Colors.MENU_BG)
        
        # Title
        title_surface = self.font_large.render("POKEMON", True, Colors.TEXT_DARK)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 40))
        self.screen.blit(title_surface, title_rect)
        
        # Pokemon slots
        slot_width = 350
        slot_height = 80
        start_x = (self.screen_width - slot_width) // 2
        start_y = 100
        
        for i, pokemon in enumerate(player.pokemon_team):
            y = start_y + i * (slot_height + 10)
            slot_rect = pygame.Rect(start_x, y, slot_width, slot_height)
            
            # Background color based on status
            bg_color = Colors.WHITE
            if pokemon.is_fainted:
                bg_color = Colors.GRAY
            elif pokemon.status != StatusCondition.NONE:
                bg_color = (255, 230, 230)
            
            pygame.draw.rect(self.screen, bg_color, slot_rect)
            pygame.draw.rect(self.screen, Colors.MENU_BORDER, slot_rect, 2)
            
            # Pokemon sprite area
            sprite_rect = pygame.Rect(start_x + 10, y + 10, 60, 60)
            pygame.draw.rect(self.screen, Colors.BUTTON_NORMAL, sprite_rect)
            pygame.draw.rect(self.screen, Colors.BLACK, sprite_rect, 1)
            
            # Pokemon info
            info_x = start_x + 85
            
            # Name and level
            name_text = f"{pokemon.nickname} Lv.{pokemon.level}"
            name_surface = self.font_medium.render(name_text, True, Colors.TEXT_DARK)
            self.screen.blit(name_surface, (info_x, y + 10))
            
            # Types
            type_y = y + 35
            for j, ptype in enumerate(pokemon.types):
                type_color = Colors.TYPE_COLORS.get(ptype, Colors.GRAY)
                type_text = ptype.value.upper()
                type_surface = self.font_small.render(type_text, True, type_color)
                self.screen.blit(type_surface, (info_x + j * 80, type_y))
            
            # HP
            hp_text = f"HP: {pokemon.current_hp}/{pokemon.stats['hp']}"
            hp_surface = self.font_small.render(hp_text, True, Colors.TEXT_DARK)
            self.screen.blit(hp_surface, (info_x, y + 55))
            
            # HP bar
            hp_bar_rect = pygame.Rect(info_x + 80, y + 58, 150, 10)
            hp_percent = pokemon.current_hp / pokemon.stats["hp"]
            hp_color = Colors.HP_GREEN if hp_percent > 0.5 else Colors.HP_YELLOW if hp_percent > 0.25 else Colors.HP_RED
            
            pygame.draw.rect(self.screen, Colors.DARK_GRAY, hp_bar_rect)
            if hp_percent > 0:
                fill_rect = pygame.Rect(hp_bar_rect.x, hp_bar_rect.y,
                                      int(hp_bar_rect.width * hp_percent), hp_bar_rect.height)
                pygame.draw.rect(self.screen, hp_color, fill_rect)
            pygame.draw.rect(self.screen, Colors.BLACK, hp_bar_rect, 1)
            
            # Status condition
            if pokemon.status != StatusCondition.NONE:
                status_text = pokemon.status.value.upper()
                status_surface = self.font_small.render(status_text, True, Colors.RED)
                self.screen.blit(status_surface, (start_x + slot_width - 80, y + 10))
        
        # Instructions
        inst_text = "Press ESC to return"
        inst_surface = self.font_small.render(inst_text, True, Colors.GRAY)
        inst_rect = inst_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
        self.screen.blit(inst_surface, inst_rect)
    
    def draw_bag_menu(self, player: Player):
        """Draw bag/inventory menu."""
        # Background
        self.screen.fill(Colors.MENU_BG)
        
        # Title
        title_surface = self.font_large.render("BAG", True, Colors.TEXT_DARK)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 40))
        self.screen.blit(title_surface, title_rect)
        
        # Category tabs
        categories = ["ITEMS", "MEDICINE", "POKEBALLS", "KEY ITEMS"]
        tab_width = self.screen_width // len(categories)
        
        for i, category in enumerate(categories):
            tab_rect = pygame.Rect(i * tab_width, 80, tab_width, 40)
            tab_color = Colors.BUTTON_HOVER if i == 0 else Colors.BUTTON_NORMAL  # First tab selected
            pygame.draw.rect(self.screen, tab_color, tab_rect)
            pygame.draw.rect(self.screen, Colors.MENU_BORDER, tab_rect, 2)
            
            cat_surface = self.font_medium.render(category, True, Colors.TEXT_DARK)
            cat_rect = cat_surface.get_rect(center=tab_rect.center)
            self.screen.blit(cat_surface, cat_rect)
        
        # Item list area
        list_rect = pygame.Rect(50, 140, self.screen_width - 100, self.screen_height - 200)
        pygame.draw.rect(self.screen, Colors.WHITE, list_rect)
        pygame.draw.rect(self.screen, Colors.MENU_BORDER, list_rect, 2)
        
        # Draw items
        y_offset = 160
        for item_name, quantity in player.inventory.items():
            if quantity > 0:
                # Item name
                item_text = f"{item_name}"
                item_surface = self.font_medium.render(item_text, True, Colors.TEXT_DARK)
                self.screen.blit(item_surface, (70, y_offset))
                
                # Quantity
                qty_text = f"x{quantity}"
                qty_surface = self.font_medium.render(qty_text, True, Colors.GRAY)
                self.screen.blit(qty_surface, (self.screen_width - 150, y_offset))
                
                y_offset += 35
                
                if y_offset > self.screen_height - 80:
                    break
        
        # Instructions
        inst_text = "Press ESC to return"
        inst_surface = self.font_small.render(inst_text, True, Colors.GRAY)
        inst_rect = inst_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
        self.screen.blit(inst_surface, inst_rect)
    
    def draw_transition(self):
        """Draw transition overlay."""
        if self.transition_alpha > 0:
            overlay = pygame.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(self.transition_alpha)
            overlay.fill(Colors.BLACK)
            self.screen.blit(overlay, (0, 0))
    
    def draw(self, game):
        """Main draw method."""
        if self.state == UIState.MAIN_MENU:
            self.draw_main_menu()
        
        elif self.state == UIState.GAME_WORLD:
            # Game will draw the world, we just add HUD
            self.draw_world_hud(game.player)
        
        elif self.state == UIState.BATTLE:
            if game.current_battle:
                self.draw_battle(game.current_battle)
        
        elif self.state == UIState.POKEMON_MENU:
            self.draw_pokemon_menu(game.player)
        
        elif self.state == UIState.BAG_MENU:
            self.draw_bag_menu(game.player)
        
        # Always draw transition on top
        self.draw_transition()