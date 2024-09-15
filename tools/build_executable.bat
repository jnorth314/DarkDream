python3.12 -m PyInstaller %~dp0/../src/main.py^
    --clean^
    --onefile^
    --windowed^
    --icon=%~dp0/../res/icon.ico^
    --add-data="%~dp0/../res;res"^
    --name=DarkDream
