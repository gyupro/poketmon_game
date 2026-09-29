"""친구에게 보낼 실행 패키지(zip) 생성: game 폴더 + Godot 실행 파일 + play.bat

사용법: python tools/make_package.py   →  dist/pokemon_online.zip
"""
import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GODOT = r"C:\Godot\Godot_v4.4.1-stable_win64.exe"
OUT = os.path.join(ROOT, "dist", "pokemon_online.zip")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    game = os.path.join(ROOT, "game")
    for base, dirs, files in os.walk(game):
        dirs[:] = [d for d in dirs if d not in ("editor", "shader_cache")]
        for f in files:
            full = os.path.join(base, f)
            z.write(full, os.path.join("pokemon_online", os.path.relpath(full, ROOT)))
    z.write(GODOT, os.path.join("pokemon_online", "Godot.exe"))
    z.write(os.path.join(ROOT, "play.bat"), os.path.join("pokemon_online", "play.bat"))
print("created", OUT, os.path.getsize(OUT) // (1024 * 1024), "MB")
