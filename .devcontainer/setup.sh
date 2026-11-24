#!/usr/bin/env bash
# Runs once when the codespace is created. Ollama is optional and installed separately:
#   bash .devcontainer/ollama.sh
set -euo pipefail

curl -LsSf https://astral.sh/uv/install.sh | sh       # uv, into ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"
uv sync                                               # Python 3.14 + pydantic, ollama, pytest, ruff
sudo apt-get update -qq && sudo apt-get install -y -qq jq >/dev/null || true   # used by the agent hooks

echo "Ready. Try: uv run pytest -q"
