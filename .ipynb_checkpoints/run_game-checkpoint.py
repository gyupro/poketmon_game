#!/usr/bin/env python3
"""
포켓몬 게임 실행 스크립트 - 오디오 문제 해결
"""

import os
import sys

# 오디오 드라이버 비활성화 (WSL 환경용)
os.environ['SDL_AUDIODRIVER'] = 'dummy'

# Pygame 경고 메시지 숨기기
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

def run_simple_game():
    """간단한 게임 실행"""
    print("🎮 간단한 포켓몬 게임을 실행합니다...")
    print("=" * 50)
    print("게임 조작법:")
    print("  스타터 선택: ↑↓ 키로 선택, Enter로 확인")
    print("  이동: WASD 키")
    print("  배틀: A(공격), C(포획), R(도망)")
    print("  게임 종료: 창 닫기")
    print("=" * 50)
    
    try:
        from simple_game import SimpleGame
        game = SimpleGame()
        game.run()
    except Exception as e:
        print(f"❌ 게임 실행 실패: {e}")
        import traceback
        traceback.print_exc()

def run_full_game():
    """전체 게임 실행"""
    print("🎮 전체 포켓몬 게임을 실행합니다...")
    print("=" * 50)
    
    try:
        from src.game import Game
        game = Game()
        game.run()
    except Exception as e:
        print(f"❌ 게임 실행 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("포켓몬 게임 런처")
    print("=" * 30)
    print("1. 간단한 게임 (추천)")
    print("2. 전체 게임")
    print("3. 종료")
    
    while True:
        choice = input("\n선택하세요 (1-3): ").strip()
        
        if choice == "1":
            run_simple_game()
            break
        elif choice == "2":
            run_full_game()
            break
        elif choice == "3":
            print("게임을 종료합니다.")
            break
        else:
            print("올바른 번호를 입력하세요 (1-3)")

if __name__ == "__main__":
    main()