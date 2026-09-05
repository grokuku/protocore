#!/usr/bin/env bash
# ProtoCore - installe le projet depuis GitHub sans git (tarball)
# Usage : curl -fsSL https://raw.githubusercontent.com/grokuku/protocore/main/install.sh | bash
#         destination custom : ... | bash -s -- /opt/protocore
# Non-interactif (CI) : PROTOCORE_URL=... PROTOCORE_MODEL=... PROTOCORE_KEY=... ... | bash
# Les dependances (python3, requests) sont installees par start.sh ; le provider LLM est EXTERNE.
set -e

REPO_URL="https://github.com/grokuku/protocore"
DEST="${1:-$HOME/protocore}"
TARBALL="/tmp/protocore-main.tar.gz"

if [ -d "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ]; then
    echo "[ERREUR] $DEST existe deja et n'est pas vide."
    echo "         Choisis une autre destination : ... | bash -s -- /chemin/protocore"
    exit 1
fi

# --- Provider LLM : demande interactivement (stdin est le pipe du script, on lit /dev/tty) ---
esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

BASE_URL="${PROTOCORE_URL:-}"
MODEL="${PROTOCORE_MODEL:-}"
API_KEY="${PROTOCORE_KEY:-}"

if [ -t 2 ] && { [ -z "$BASE_URL" ] || [ -z "$MODEL" ]; }; then
    echo "[ProtoCore] Configuration du provider LLM (OpenAI-compatible) :"
    while [ -z "$BASE_URL" ]; do
        read -r -p "  base_url (ex: http://192.168.1.50:11434/v1 pour Ollama) : " BASE_URL < /dev/tty
    done
    while [ -z "$MODEL" ]; do
        read -r -p "  model    (ex: llama3.2:3b) : " MODEL < /dev/tty
    done
    read -r -p "  api_key  (vide si provider local) : " API_KEY < /dev/tty || true
elif [ -z "$BASE_URL" ] || [ -z "$MODEL" ]; then
    echo "[INFO] Pas de terminal interactif : config.json garde ses placeholders (a editer avant ./start.sh)"
    echo "       ou relance avec PROTOCORE_URL / PROTOCORE_MODEL / PROTOCORE_KEY."
fi

if [ -n "$BASE_URL" ]; then
    BASE_URL="${BASE_URL%/}"
    case "$BASE_URL" in
        http://*|https://*) ;;
        *) echo "[ERREUR] base_url doit commencer par http:// ou https://"; exit 1 ;;
    esac
fi

echo "[ProtoCore] Telechargement depuis $REPO_URL ..."
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$REPO_URL/archive/refs/heads/main.tar.gz" -o "$TARBALL"
elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TARBALL" "$REPO_URL/archive/refs/heads/main.tar.gz"
else
    echo "[ERREUR] Ni curl ni wget disponibles - installe l'un des deux puis relance."
    exit 1
fi

mkdir -p "$DEST"
tar -xzf "$TARBALL" -C "$DEST" --strip-components=1
rm -f "$TARBALL"
chmod +x "$DEST/start.sh"

if [ -n "$BASE_URL" ] && [ -n "$MODEL" ]; then
    cat > "$DEST/config.json" <<EOF
{
    "_README": "Configure base_url and model, then run ./start.sh (or start.bat). base_url = ANY OpenAI-compatible endpoint: Ollama http://<host>:11434/v1, LM Studio http://<host>:1234/v1, vLLM http://<host>:8000/v1, OpenRouter https://openrouter.ai/api/v1. model = a model served by that endpoint (e.g. llama3.2:3b, qwen2.5:7b). api_key = empty for local providers, required for cloud ones. The bot refuses to start while values still contain REPLACE_ME.",
    "base_url": "$(esc "$BASE_URL")",
    "model": "$(esc "$MODEL")",
    "api_key": "$(esc "$API_KEY")"
}
EOF
    echo "[ProtoCore] config.json genere : $BASE_URL / $MODEL"
fi

echo "[ProtoCore] Installe dans $DEST"

if [ -n "$BASE_URL" ] && [ -n "$MODEL" ]; then
    if [ -t 2 ]; then
        read -r -p "Lancer ProtoCore maintenant ? [Y/n] " _go < /dev/tty || _go=""
        case "$_go" in
            n*|N*) echo "[ProtoCore] Lancement ulterieur : cd $DEST && ./start.sh" ;;
            *) echo "[ProtoCore] Demarrage..." ; exec "$DEST/start.sh" ;;
        esac
    else
        echo "[ProtoCore] Lancement ulterieur : cd $DEST && ./start.sh"
    fi
else
    echo "Prochaines etapes :"
    echo "  1. edite $DEST/config.json  (base_url + model - tout est explique dans la cle _README)"
    echo "  2. cd $DEST && ./start.sh"
fi
