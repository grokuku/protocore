@echo off
rem ProtoCore - demarrage : verifie les dependances minimales et lance bot.py
rem Politique : le provider LLM est EXTERNE (config.json) - on n'installe JAMAIS de moteur d'inference.
cd /d "%~dp0"
if not exist config.json (echo [ERREUR] config.json introuvable. & pause & exit /b 1)

rem 1. Python 3
where py >nul 2>nul
if not errorlevel 1 (
    set "PY=py -3"
    goto :have_py
)
where python >nul 2>nul
if not errorlevel 1 (
    set "PY=python"
    goto :have_py
)
echo [ProtoCore] Python 3 introuvable - installation via winget...
winget install -e --id Python.Python.3 --accept-source-agreements --accept-package-agreements
where py >nul 2>nul
if not errorlevel 1 (
    set "PY=py -3"
    goto :have_py
)
where python >nul 2>nul
if not errorlevel 1 (
    set "PY=python"
    goto :have_py
)
echo [ERREUR] Python toujours introuvable. Rouvre un terminal (mise a jour du PATH) ou installe manuellement.
pause
exit /b 1

:have_py
rem 2. requests (seule dependance non-stdlib)
%PY% -c "import requests" >nul 2>nul
if errorlevel 1 %PY% -m pip install requests

rem 3. Provider joignable ? (warning seulement)
%PY% -c "import json,urllib.request;urllib.request.urlopen(json.load(open('config.json'))['base_url'].rstrip('/')+'/models',timeout=3)" >nul 2>nul
if errorlevel 1 echo [WARN] Provider LLM injoignable ou non configure (config.json: base_url) - le bot refusera de demarrer tant que les placeholders sont en place.

echo [ProtoCore] Demarrage...
%PY% bot.py
pause
