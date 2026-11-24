#!/usr/bin/env bash
# Optional: a local model server for quiz generation and the blind-student judge.
# CPU only in Codespaces: small models are fine, qwen3:8b is slow.
set -euo pipefail

command -v ollama >/dev/null || curl -fsSL https://ollama.com/install.sh | sh
pgrep -x ollama >/dev/null || (nohup ollama serve >/tmp/ollama.log 2>&1 &)
sleep 3
ollama pull "${EVAL_MODEL:-llama3.2:3b}"
echo "Ollama is running. Models:" && ollama list
