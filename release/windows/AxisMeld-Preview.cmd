@echo off
start "" /D "%~dp0" "%~dp0blender.exe" --factory-startup --python "%~dp0axismeld_preview_launcher.py"
