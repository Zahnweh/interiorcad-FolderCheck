@echo off
setlocal
echo === interiorcad FolderCheck - Windows Build ===
cd /d "%~dp0"

echo Pruefe Abhaengigkeiten...
pip install pyinstaller pillow --quiet
if errorlevel 1 (
    echo FEHLER: pip nicht gefunden. Bitte Python 3.9+ installieren.
    pause & exit /b 1
)

echo Erstelle App-Icon...
python make_icon.py
if errorlevel 1 (
    echo FEHLER: Icon-Erstellung fehlgeschlagen.
    pause & exit /b 1
)

echo Baue App (das dauert 1-2 Minuten)...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller --name "interiorcad FolderCheck" --onefile --windowed --icon icon.ico --add-data "icon.png;." --collect-all tkinter --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import tkinter.filedialog --hidden-import tkinter.messagebox --clean --noconfirm main.py

if errorlevel 1 (
    echo FEHLER: PyInstaller fehlgeschlagen.
    pause & exit /b 1
)

echo.
echo Fertig!
echo   EXE: %~dp0dist\interiorcad FolderCheck.exe
echo.
start "" "%~dp0dist\"
pause
