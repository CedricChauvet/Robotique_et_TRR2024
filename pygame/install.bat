@echo off
echo ════════════════════════════════════
echo   COMPILATION SIMULATEUR JAMBE
echo ════════════════════════════════════
echo.

REM Verifier les dependances
echo [1/4] Verification des modules...
pip install pygame paho-mqtt pyinstaller

REM Nettoyer les anciens builds
echo.
echo [2/4] Nettoyage...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "*.spec" del /q *.spec

REM Compiler
echo.
echo [3/4] Compilation en cours...
pyinstaller --onefile ^
    --windowed ^
    --name="SimulateurJambe" ^
    --icon=NONE ^
    --add-data "README.md;." ^
    --hidden-import=pygame ^
    --hidden-import=paho.mqtt.client ^
    --collect-all pygame ^
    2_drag_n_drop.py

REM Verifier le resultat
echo.
echo [4/4] Verification...
if exist "dist\SimulateurJambe.exe" (
    echo.
    echo ════════════════════════════════════
    echo   ✅ COMPILATION REUSSIE !
    echo ════════════════════════════════════
    echo.
    echo Fichier cree : dist\SimulateurJambe.exe
    echo Taille : 
    dir "dist\SimulateurJambe.exe" | find "SimulateurJambe.exe"
    echo.
    echo Vous pouvez maintenant :
    echo - Copier dist\SimulateurJambe.exe ou vous voulez
    echo - L'executer directement
    echo.
) else (
    echo.
    echo ❌ ERREUR : La compilation a echoue
    echo Consultez les messages ci-dessus
    echo.
)

pause