@echo off
title Compilation de LANCER_RENOMMAGE.exe

echo.
echo ==========================================
echo   Billets Chatelet - Compilation
echo ==========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo Python n'est pas installe.
    echo Ce script est surtout utile pour la compilation.
    pause
    exit /b
)

echo Installation des dependances...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Fabrication de l'executable...
python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name LANCER_RENOMMAGE ^
    main.py

echo.
echo ==========================================
echo   Compilation terminee !
echo ==========================================
echo.
echo L'executable se trouve dans :
echo dist\LANCER_RENOMMAGE.exe
pause
