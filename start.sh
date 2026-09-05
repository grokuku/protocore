#!/usr/bin/env bash
# ProtoCore - demarrage : verifie les dependances minimales et lance bot.py
# Politique : le provider LLM est EXTERNE (config.json) - on n'installe JAMAIS de moteur d'inference.
set -e
cd "$(dirname "$0")"

[ -f config.json ] || { echo "[ERREUR] config.json introuvable."; exit 1; }

SUDO=""
[ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo"

# 1. Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ProtoCore] Python 3 introuvable - installation..."
    if command -v apt-get >/dev/null 2>&1; then
        $SUDO env DEBIAN_FRONTEND=noninteractive apt-get update -qq
        $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3
    elif command -v dnf >/dev/null 2>&1; then $SUDO dnf install -y -q python3
    elif command -v pacman >/dev/null 2>&1; then $SUDO pacman -S --noconfirm python
    else echo "[ERREUR] Aucun gestionnaire connu - installe python3 manuellement (ex: brew install python3)."; exit 1; fi
fi

# 2. requests (seule dependance non-stdlib)
if ! python3 -c "import requests" >/dev/null 2>&1; then
    echo "[ProtoCore] 'requests' manquant - installation..."
    if command -v apt-get >/dev/null 2>&1; then $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-requests
    elif command -v dnf >/dev/null 2>&1; then $SUDO dnf install -y -q python3-requests
    elif command -v pacman >/dev/null 2>&1; then $SUDO pacman -S --noconfirm python-requests
    else python3 -m pip install --user requests 2>/dev/null || python3 -m pip install --user --break-system-packages requests
    fi
fi

# 3. Provider joignable ? (warning seulement - le provider est un choix de deploiement)
if python3 -c "import json,urllib.request;urllib.request.urlopen(json.load(open('config.json'))['base_url'].rstrip('/')+'/models',timeout=3)" >/dev/null 2>&1; then
    echo "[ProtoCore] Provider LLM joignable."
else
    echo "[WARN] Provider LLM injoignable ou non configure (config.json: base_url) - le bot refusera de demarrer tant que les placeholders sont en place."
fi

echo "[ProtoCore] Demarrage..."
exec python3 bot.py
