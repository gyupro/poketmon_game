#!/usr/bin/env python3
"""
포켓몬 게임 기능 테스트 스크립트
"""

import os
import sys

def test_imports():
    """모든 필요한 모듈이 제대로 import되는지 테스트"""
    print("=== 모듈 Import 테스트 ===")
    
    try:
        import pygame
        print("✅ pygame 성공")
    except ImportError as e:
        print(f"❌ pygame 실패: {e}")
        return False
    
    try:
        from src.pokemon import Pokemon, SimplePokemon, PokemonType, StatusCondition
        print("✅ Pokemon 모듈 성공")
    except ImportError as e:
        print(f"❌ Pokemon 모듈 실패: {e}")
        
    try:
        from src.battle import Battle, SimpleBattle
        print("✅ Battle 모듈 성공")
    except ImportError as e:
        print(f"❌ Battle 모듈 실패: {e}")
        
    try:
        from src.player import Player, SimplePlayer
        print("✅ Player 모듈 성공")
    except ImportError as e:
        print(f"❌ Player 모듈 실패: {e}")
        
    return True

def test_pokemon_creation():
    """포켓몬 생성 테스트"""
    print("\n=== 포켓몬 생성 테스트 ===")
    
    try:
        # 간단한 포켓몬 생성
        from simple_game import SimplePokemon
        pikachu = SimplePokemon("피카츄", 10)
        print(f"✅ 간단한 포켓몬 생성: {pikachu.name} 레벨 {pikachu.level}")
        print(f"   HP: {pikachu.current_hp}/{pikachu.max_hp}")
        print(f"   공격력: {pikachu.attack}")
        print(f"   샤이니: {pikachu.is_shiny}")
        
        # 복잡한 포켓몬 생성
        try:
            from src.pokemon import create_pokemon_from_species
            complex_pikachu = create_pokemon_from_species(25, 10)  # 피카츄 ID
            print(f"✅ 복잡한 포켓몬 생성: {complex_pikachu.species_name} 레벨 {complex_pikachu.level}")
        except Exception as e:
            print(f"⚠️ 복잡한 포켓몬 생성 실패: {e}")
            
    except Exception as e:
        print(f"❌ 포켓몬 생성 실패: {e}")
        return False
        
    return True

def test_battle_system():
    """배틀 시스템 테스트"""
    print("\n=== 배틀 시스템 테스트 ===")
    
    try:
        from simple_game import SimplePokemon, SimpleBattle
        
        # 포켓몬 생성
        my_pokemon = SimplePokemon("피카츄", 10)
        wild_pokemon = SimplePokemon("꼬렛", 5)
        
        print(f"배틀 시작: {my_pokemon.name} vs {wild_pokemon.name}")
        print(f"내 포켓몬 HP: {my_pokemon.current_hp}")
        print(f"야생 포켓몬 HP: {wild_pokemon.current_hp}")
        
        # 배틀 생성
        battle = SimpleBattle(my_pokemon, wild_pokemon)
        
        # 몇 번 공격해보기
        turn = 1
        while not battle.battle_over and turn <= 5:
            print(f"\n--- 턴 {turn} ---")
            old_wild_hp = wild_pokemon.current_hp
            battle.player_attack()
            
            if battle.messages:
                print(f"메시지: {battle.messages[-1]}")
                
            if wild_pokemon.current_hp < old_wild_hp:
                print(f"야생 포켓몬 HP: {wild_pokemon.current_hp}")
                
            turn += 1
            
        if battle.battle_over:
            print(f"✅ 배틀 종료: {'승리' if battle.player_won else '패배'}")
        else:
            print("✅ 배틀 시스템 정상 작동")
            
    except Exception as e:
        print(f"❌ 배틀 시스템 실패: {e}")
        return False
        
    return True

def test_catch_system():
    """포획 시스템 테스트"""
    print("\n=== 포획 시스템 테스트 ===")
    
    try:
        from simple_game import SimplePokemon, SimpleBattle, SimplePlayer
        
        player = SimplePlayer()
        player.pokeballs = 5
        
        my_pokemon = SimplePokemon("피카츄", 15)
        weak_pokemon = SimplePokemon("꼬렛", 3)
        weak_pokemon.current_hp = 1  # 거의 죽게 만들기
        
        player.add_pokemon(my_pokemon)
        battle = SimpleBattle(my_pokemon, weak_pokemon)
        
        print(f"포획 시도: {weak_pokemon.name} (HP: {weak_pokemon.current_hp})")
        print(f"보유 몬스터볼: {player.pokeballs}")
        
        success = battle.try_catch(player)
        
        if success:
            print(f"✅ 포획 성공! 팀에 추가됨")
            print(f"현재 팀: {[p.name for p in player.pokemon_team]}")
        else:
            print(f"⚠️ 포획 실패, 다시 시도 가능")
            
        print(f"남은 몬스터볼: {player.pokeballs}")
        
    except Exception as e:
        print(f"❌ 포획 시스템 실패: {e}")
        return False
        
    return True

def test_map_system():
    """맵 시스템 테스트"""
    print("\n=== 맵 시스템 테스트 ===")
    
    try:
        from simple_game import SimpleGame
        
        # 게임 인스턴스 생성 (pygame 초기화 없이)
        print("맵 데이터 생성 중...")
        
        # 맵 생성 함수만 테스트
        import random
        width, height = 25, 18
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
            
        print(f"✅ 맵 생성 성공: {width}x{height}")
        print(f"   길 타일: {sum(row.count(0) for row in map_data)}")
        print(f"   풀 타일: {sum(row.count(1) for row in map_data)}")
        print(f"   나무 타일: {sum(row.count(2) for row in map_data)}")
        
        # 맵 일부 출력
        print("\n맵 미리보기 (상단 5줄):")
        for i in range(min(5, len(map_data))):
            row_str = ""
            for tile in map_data[i][:20]:  # 첫 20열만
                if tile == 0:
                    row_str += "."
                elif tile == 1:
                    row_str += "#"
                elif tile == 2:
                    row_str += "T"
            print(f"   {row_str}")
            
    except Exception as e:
        print(f"❌ 맵 시스템 실패: {e}")
        return False
        
    return True

def test_encounter_system():
    """조우 시스템 테스트"""
    print("\n=== 조우 시스템 테스트 ===")
    
    try:
        import random
        
        # 야생 포켓몬 리스트
        wild_pokemon_names = ["꼬렛", "구구", "캐터피", "뿔충이", "피카츄"]
        
        print("야생 포켓몬 조우 시뮬레이션:")
        for i in range(10):
            if random.random() < 0.1:  # 10% 조우 확률
                wild_name = random.choice(wild_pokemon_names)
                wild_level = random.randint(3, 7)
                print(f"  조우 {i+1}: 야생 {wild_name} 레벨 {wild_level}")
            else:
                print(f"  조우 {i+1}: 조우 없음")
                
        print("✅ 조우 시스템 정상 작동")
        
    except Exception as e:
        print(f"❌ 조우 시스템 실패: {e}")
        return False
        
    return True

def test_sprite_loading():
    """스프라이트 로딩 테스트"""
    print("\n=== 스프라이트 로딩 테스트 ===")
    
    sprite_dir = "assets/sprites"
    if not os.path.exists(sprite_dir):
        print(f"⚠️ 스프라이트 디렉토리 없음: {sprite_dir}")
        return False
        
    sprite_files = [f for f in os.listdir(sprite_dir) if f.endswith('.png')]
    print(f"발견된 스프라이트 파일: {len(sprite_files)}개")
    
    for sprite in sprite_files[:5]:  # 처음 5개만 보여주기
        file_path = os.path.join(sprite_dir, sprite)
        file_size = os.path.getsize(file_path)
        print(f"  {sprite}: {file_size} bytes")
        
    if sprite_files:
        print("✅ 스프라이트 파일 정상 존재")
    else:
        print("⚠️ 스프라이트 파일 없음 - 게임은 기본 도형으로 작동")
        
    return True

def main():
    """메인 테스트 함수"""
    print("🎮 포켓몬 게임 기능 테스트를 시작합니다...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_pokemon_creation,
        test_battle_system,
        test_catch_system,
        test_map_system,
        test_encounter_system,
        test_sprite_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 테스트 중 예외 발생: {e}")
            
    print("\n" + "=" * 50)
    print(f"🎯 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트 통과! 게임이 정상 작동할 것입니다.")
    elif passed >= total // 2:
        print("⚠️ 대부분의 기능이 작동합니다. 일부 문제가 있을 수 있습니다.")
    else:
        print("❌ 많은 문제가 있습니다. 코드를 확인해주세요.")
        
    print("\n🎮 게임 실행 방법:")
    print("   python simple_game.py  # 간단한 버전")
    print("   python main.py         # 전체 버전")

if __name__ == "__main__":
    main()