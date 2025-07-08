#!/usr/bin/env python3
"""
Simple Pokemon Game - 간단하고 작동하는 버전
"""

import pygame
import random
import sys
import os
from typing import Optional, List, Tuple

# Initialize Pygame without sound
pygame.init()
try:
    pygame.mixer.quit()  # Disable sound completely
except:
    pass

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
BLUE = (0, 100, 200)
RED = (220, 20, 60)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
DARK_GREEN = (0, 100, 0)

class SimplePokemon:
    """간단한 포켓몬 클래스"""
    def __init__(self, name: str, level: int = 5):
        self.name = name
        self.level = level
        self.max_hp = level * 20
        self.current_hp = self.max_hp
        self.attack = level * 10
        self.is_shiny = random.random() < 0.001  # 0.1% 확률
        
    def attack_move(self, target):
        """간단한 공격"""
        damage = random.randint(self.attack // 2, self.attack)
        target.current_hp = max(0, target.current_hp - damage)
        return damage
        
    def is_fainted(self):
        return self.current_hp <= 0

class SimplePlayer:
    """간단한 플레이어 클래스"""
    def __init__(self):
        self.x = 10
        self.y = 10
        self.pokemon_team = []
        self.pokeballs = 10
        
    def add_pokemon(self, pokemon: SimplePokemon):
        if len(self.pokemon_team) < 6:
            self.pokemon_team.append(pokemon)
            
    def get_first_pokemon(self) -> Optional[SimplePokemon]:
        for pokemon in self.pokemon_team:
            if not pokemon.is_fainted():
                return pokemon
        return None

class SimpleBattle:
    """간단한 배틀 시스템"""
    def __init__(self, player_pokemon: SimplePokemon, wild_pokemon: SimplePokemon):
        self.player_pokemon = player_pokemon
        self.wild_pokemon = wild_pokemon
        self.battle_over = False
        self.player_won = False
        self.messages = []
        
    def player_attack(self):
        if self.battle_over:
            return
            
        damage = self.player_pokemon.attack_move(self.wild_pokemon)
        self.messages.append(f"{self.player_pokemon.name}이(가) {damage} 데미지를 입혔다!")
        
        if self.wild_pokemon.is_fainted():
            self.messages.append(f"야생 {self.wild_pokemon.name}을(를) 쓰러뜨렸다!")
            self.battle_over = True
            self.player_won = True
            return
            
        # 야생 포켓몬 공격
        damage = self.wild_pokemon.attack_move(self.player_pokemon)
        self.messages.append(f"야생 {self.wild_pokemon.name}이(가) {damage} 데미지를 입혔다!")
        
        if self.player_pokemon.is_fainted():
            self.messages.append(f"{self.player_pokemon.name}이(가) 쓰러졌다!")
            self.battle_over = True
            self.player_won = False
            
    def try_catch(self, player):
        if self.battle_over or player.pokeballs <= 0:
            return False
            
        player.pokeballs -= 1
        # 간단한 포획 공식
        catch_rate = max(0.1, 1.0 - (self.wild_pokemon.current_hp / self.wild_pokemon.max_hp))
        
        if random.random() < catch_rate:
            self.messages.append(f"{self.wild_pokemon.name}을(를) 포획했다!")
            player.add_pokemon(self.wild_pokemon)
            self.battle_over = True
            self.player_won = True
            return True
        else:
            self.messages.append(f"{self.wild_pokemon.name}이(가) 몬스터볼에서 나왔다!")
            # 야생 포켓몬 공격
            damage = self.wild_pokemon.attack_move(self.player_pokemon)
            self.messages.append(f"야생 {self.wild_pokemon.name}이(가) {damage} 데미지를 입혔다!")
            return False

class SimpleGame:
    """간단한 게임 메인 클래스"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("간단한 포켓몬 게임")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 32)
        
        # 게임 상태
        self.state = "starter_select"  # starter_select, world, battle
        self.player = SimplePlayer()
        self.battle = None
        self.starter_choice = 0
        self.message_timer = 0
        
        # 스타터 포켓몬
        self.starters = [
            SimplePokemon("이상해씨", 5),
            SimplePokemon("파이리", 5), 
            SimplePokemon("꼬부기", 5)
        ]
        
        # 야생 포켓몬 리스트
        self.wild_pokemon_names = ["꼬렛", "구구", "캐터피", "뿔충이", "피카츄"]
        
        # 맵 생성 (0=길, 1=풀, 2=나무, 3=물)
        self.map_data = self.generate_map()
        
    def generate_map(self):
        """간단한 맵 생성"""
        width, height = SCREEN_WIDTH // TILE_SIZE, SCREEN_HEIGHT // TILE_SIZE
        map_data = []
        
        for y in range(height):
            row = []
            for x in range(width):
                if x == 0 or y == 0 or x == width-1 or y == height-1:
                    row.append(2)  # 경계는 나무
                elif random.random() < 0.3:
                    row.append(1)  # 30% 확률로 풀
                else:
                    row.append(0)  # 나머지는 길
            map_data.append(row)
        return map_data
        
    def draw_map(self):
        """맵 그리기"""
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                if tile == 0:  # 길
                    pygame.draw.rect(self.screen, GRAY, rect)
                elif tile == 1:  # 풀
                    pygame.draw.rect(self.screen, GREEN, rect)
                    # 풀 텍스처
                    for i in range(4):
                        px = x * TILE_SIZE + random.randint(2, TILE_SIZE-2)
                        py = y * TILE_SIZE + random.randint(2, TILE_SIZE-2)
                        pygame.draw.circle(self.screen, DARK_GREEN, (px, py), 1)
                elif tile == 2:  # 나무
                    pygame.draw.rect(self.screen, BROWN, rect)
                    # 나무 텍스처
                    pygame.draw.circle(self.screen, DARK_GREEN, 
                                     (x * TILE_SIZE + TILE_SIZE//2, y * TILE_SIZE + TILE_SIZE//2), 
                                     TILE_SIZE//3)
                
                # 격자 그리기
                pygame.draw.rect(self.screen, BLACK, rect, 1)
    
    def draw_player(self):
        """플레이어 그리기"""
        px = self.player.x * TILE_SIZE + TILE_SIZE // 4
        py = self.player.y * TILE_SIZE + TILE_SIZE // 4
        pygame.draw.rect(self.screen, BLUE, (px, py, TILE_SIZE//2, TILE_SIZE//2))
        
    def draw_starter_selection(self):
        """스타터 선택 화면"""
        self.screen.fill(WHITE)
        
        title = self.big_font.render("스타터 포켓몬을 선택하세요!", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        for i, starter in enumerate(self.starters):
            y_pos = 150 + i * 100
            color = YELLOW if i == self.starter_choice else WHITE
            
            # 포켓몬 박스
            rect = pygame.Rect(SCREEN_WIDTH//2 - 100, y_pos, 200, 80)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            
            # 포켓몬 이름
            name_text = self.font.render(starter.name, True, BLACK)
            self.screen.blit(name_text, (rect.x + 10, rect.y + 10))
            
            # 레벨 표시
            level_text = self.font.render(f"레벨 {starter.level}", True, BLACK)
            self.screen.blit(level_text, (rect.x + 10, rect.y + 35))
            
        # 조작 안내
        guide = self.font.render("↑↓: 선택, Enter: 확인", True, BLACK)
        self.screen.blit(guide, (SCREEN_WIDTH//2 - guide.get_width()//2, 500))
        
    def draw_battle(self):
        """배틀 화면"""
        self.screen.fill(WHITE)
        
        # 배경
        pygame.draw.rect(self.screen, GREEN, (0, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT//2))
        
        # 내 포켓몬 (뒤에서)
        my_rect = pygame.Rect(100, SCREEN_HEIGHT - 150, 80, 80)
        pygame.draw.rect(self.screen, BLUE, my_rect)
        my_name = self.font.render(self.battle.player_pokemon.name, True, BLACK)
        self.screen.blit(my_name, (my_rect.x, my_rect.y - 25))
        
        # HP 바 (내 포켓몬)
        hp_ratio = self.battle.player_pokemon.current_hp / self.battle.player_pokemon.max_hp
        hp_color = GREEN if hp_ratio > 0.5 else YELLOW if hp_ratio > 0.2 else RED
        pygame.draw.rect(self.screen, BLACK, (my_rect.x, my_rect.y + 90, 80, 10))
        pygame.draw.rect(self.screen, hp_color, (my_rect.x + 1, my_rect.y + 91, int(78 * hp_ratio), 8))
        
        hp_text = self.font.render(f"{self.battle.player_pokemon.current_hp}/{self.battle.player_pokemon.max_hp}", 
                                  True, BLACK)
        self.screen.blit(hp_text, (my_rect.x, my_rect.y + 105))
        
        # 상대 포켓몬 (앞에서)
        enemy_rect = pygame.Rect(SCREEN_WIDTH - 180, 100, 80, 80)
        enemy_color = YELLOW if self.battle.wild_pokemon.is_shiny else RED
        pygame.draw.rect(self.screen, enemy_color, enemy_rect)
        enemy_name = self.font.render(f"야생 {self.battle.wild_pokemon.name}", True, BLACK)
        self.screen.blit(enemy_name, (enemy_rect.x - 20, enemy_rect.y - 25))
        
        # HP 바 (상대 포켓몬)
        enemy_hp_ratio = self.battle.wild_pokemon.current_hp / self.battle.wild_pokemon.max_hp
        enemy_hp_color = GREEN if enemy_hp_ratio > 0.5 else YELLOW if enemy_hp_ratio > 0.2 else RED
        pygame.draw.rect(self.screen, BLACK, (enemy_rect.x, enemy_rect.y + 90, 80, 10))
        pygame.draw.rect(self.screen, enemy_hp_color, (enemy_rect.x + 1, enemy_rect.y + 91, int(78 * enemy_hp_ratio), 8))
        
        enemy_hp_text = self.font.render(f"{self.battle.wild_pokemon.current_hp}/{self.battle.wild_pokemon.max_hp}", 
                                        True, BLACK)
        self.screen.blit(enemy_hp_text, (enemy_rect.x, enemy_rect.y + 105))
        
        # 메시지 박스
        msg_rect = pygame.Rect(50, SCREEN_HEIGHT - 100, SCREEN_WIDTH - 100, 80)
        pygame.draw.rect(self.screen, WHITE, msg_rect)
        pygame.draw.rect(self.screen, BLACK, msg_rect, 2)
        
        # 최근 메시지 표시
        if self.battle.messages:
            for i, msg in enumerate(self.battle.messages[-3:]):  # 최근 3개 메시지
                msg_text = self.font.render(msg, True, BLACK)
                self.screen.blit(msg_text, (msg_rect.x + 10, msg_rect.y + 10 + i * 20))
        
        # 배틀이 끝나지 않았으면 버튼 표시
        if not self.battle.battle_over:
            attack_text = self.font.render("A: 공격", True, BLACK)
            self.screen.blit(attack_text, (50, 50))
            
            catch_text = self.font.render(f"C: 포획 (몬스터볼: {self.player.pokeballs})", True, BLACK)
            self.screen.blit(catch_text, (200, 50))
            
            run_text = self.font.render("R: 도망", True, BLACK)
            self.screen.blit(run_text, (450, 50))
        else:
            continue_text = self.font.render("Space: 계속", True, BLACK)
            self.screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, 50))
    
    def draw_world(self):
        """월드 화면"""
        self.draw_map()
        self.draw_player()
        
        # UI 정보
        info_text = self.font.render("WASD: 이동, Space: 상호작용", True, BLACK)
        self.screen.blit(info_text, (10, 10))
        
        team_text = self.font.render(f"팀 포켓몬: {len(self.player.pokemon_team)}/6", True, BLACK)
        self.screen.blit(team_text, (10, 35))
        
        balls_text = self.font.render(f"몬스터볼: {self.player.pokeballs}", True, BLACK)
        self.screen.blit(balls_text, (10, 60))
        
    def handle_starter_input(self, event):
        """스타터 선택 입력 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.starter_choice = (self.starter_choice - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.starter_choice = (self.starter_choice + 1) % 3
            elif event.key == pygame.K_RETURN:
                chosen_starter = self.starters[self.starter_choice]
                self.player.add_pokemon(chosen_starter)
                self.state = "world"
                
    def handle_world_input(self, event):
        """월드 입력 처리"""
        if event.type == pygame.KEYDOWN:
            new_x, new_y = self.player.x, self.player.y
            
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                new_y = max(1, new_y - 1)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                new_y = min(len(self.map_data) - 2, new_y + 1)
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                new_x = max(1, new_x - 1)
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                new_x = min(len(self.map_data[0]) - 2, new_x + 1)
                
            # 이동 가능한지 확인 (나무가 아니면 이동 가능)
            if self.map_data[new_y][new_x] != 2:
                self.player.x, self.player.y = new_x, new_y
                
                # 풀에서 야생 포켓몬 조우
                if self.map_data[new_y][new_x] == 1 and random.random() < 0.1:  # 10% 확률
                    self.start_wild_battle()
                    
    def start_wild_battle(self):
        """야생 포켓몬 배틀 시작"""
        player_pokemon = self.player.get_first_pokemon()
        if not player_pokemon:
            return  # 포켓몬이 없으면 배틀 불가
            
        wild_name = random.choice(self.wild_pokemon_names)
        wild_level = random.randint(3, 7)
        wild_pokemon = SimplePokemon(wild_name, wild_level)
        
        self.battle = SimpleBattle(player_pokemon, wild_pokemon)
        self.battle.messages.append(f"야생 {wild_name}이(가) 나타났다!")
        self.state = "battle"
        
    def handle_battle_input(self, event):
        """배틀 입력 처리"""
        if event.type == pygame.KEYDOWN:
            if self.battle.battle_over:
                if event.key == pygame.K_SPACE:
                    self.state = "world"
                    self.battle = None
            else:
                if event.key == pygame.K_a:
                    self.battle.player_attack()
                elif event.key == pygame.K_c:
                    self.battle.try_catch(self.player)
                elif event.key == pygame.K_r:
                    self.battle.messages.append("도망쳤다!")
                    self.state = "world"
                    self.battle = None
    
    def run(self):
        """메인 게임 루프"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                if self.state == "starter_select":
                    self.handle_starter_input(event)
                elif self.state == "world":
                    self.handle_world_input(event)
                elif self.state == "battle":
                    self.handle_battle_input(event)
            
            # 화면 그리기
            if self.state == "starter_select":
                self.draw_starter_selection()
            elif self.state == "world":
                self.draw_world()
            elif self.state == "battle":
                self.draw_battle()
                
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("간단한 포켓몬 게임을 시작합니다...")
    try:
        game = SimpleGame()
        game.run()
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()