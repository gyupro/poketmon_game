"""처음 받은 저장소를 실행 가능한 상태로 만든다.

1. pret/pokered 역어셈블리를 pokered_src/ 로 받는다 (없을 때만)
2. 원작 음원을 WAV 로 렌더링한다 (tools/audio_render.py)
3. 맵·그래픽·포켓몬·대사 데이터를 변환한다 (tools/convert.py)
4. Godot 로 에셋을 임포트한다 (Godot 경로를 인자로 주면)

사용법: python tools/setup.py ["C:\\Godot\\Godot_v4.4.1-stable_win64_console.exe"]
필요: git, Python 3.10+, pip install pillow numpy
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
POKERED_COMMIT = "d2704a63c26f9ba046ade877445216b3de0519a4"


def run(cmd):
    print(">", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def main():
    if not os.path.isdir(os.path.join(ROOT, "pokered_src")):
        # 변환기가 검증된 버전으로 고정
        run(["git", "clone", "https://github.com/pret/pokered", "pokered_src"])
        subprocess.check_call(["git", "checkout", "-q", POKERED_COMMIT], cwd=os.path.join(ROOT, "pokered_src"))
    run([sys.executable, "tools/audio_render.py"])
    run([sys.executable, "tools/convert.py"])
    if len(sys.argv) > 1:
        run([sys.argv[1], "--headless", "--path", "game", "--import"])
    else:
        print("Godot 경로를 주지 않아 임포트는 건너뜀. Godot 에디터로 game/project.godot 을 한 번 열어 주세요.")
    print("완료! play.bat 또는 Godot 로 game/project.godot 실행")


if __name__ == "__main__":
    main()
