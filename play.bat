@echo off
cd /d "%~dp0"
if exist "Godot.exe" (
  start "" "Godot.exe" --path game
) else (
  start "" "C:\Godot\Godot_v4.4.1-stable_win64.exe" --path game
)
