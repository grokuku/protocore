# Project ProtoCore

## Overview
ProtoCore is a minimalist, autonomous agent experiment running on an isolated Virtual Machine. The bot interacts with an external LLM through an OpenAI-compatible API configured in config.json. The base project ships NO inference engine — users point it at any provider (local Ollama, LM Studio, vLLM, OpenRouter, OpenAI...). It has full system access to read, write, modify files, and execute shell commands to achieve its goals.

## Architecture
- **Language**: Python 3
- **LLM Provider**: external, OpenAI-compatible, fully configured via config.json (base_url, model, api_key). No inference engine in the base project — deployment choice only.
- **Memory Embeddings**: local Ollama + embedding model (e.g. nomic-embed-text) installed on the VM at runtime, CPU-only. Independent from the agent's LLM provider.
- **Core Loop**: Observe -> Think (LLM) -> Act (Shell) -> Loop.
- **Prompting Strategy**: JSON-first. The LLM is forced to output a strictly structured JSON containing its thought process and the shell command to execute.
- **Short-term Memory**: The bot maintains a `command_history` list during its execution cycle to avoid loops.

## Current State
- **Phase 1 (Validation)**: COMPLETED. The bot successfully demonstrated its ability to explore the environment and create files with manual validation.
- **Phase 2 (Autonomy)**: ACTIVE. 
    - The "Human-in-the-Loop" (HITL) safety measure has been REMOVED. 
    - The bot now executes commands automatically after a 2-second delay.
    - Objective: Self-modification of `goals.md` and setting up a dashboard.

## Files
- `bot.py`: The main cognitive loop (Now with auto-execution and timeout handling).
- `config.json`: LLM configuration (base_url OpenAI-compatible, model, api_key). Shipped with placeholders + _README — must be configured before first run (validated at startup).
- `start.sh` / `start.bat`: Dependency check (python3, requests) + provider reachability warning + launch.
- `goals.md`: The dynamic list of objectives (Target of self-modification).
- `protocore.log`: (Created by the bot) Action logs.
- `index.html`: (Created by the bot) Web dashboard.

## Key Learnings
- **Short-term memory**: Without an execution history, the agent enters an infinite loop of repeating the first successful task.
- **Timeout management**: Background tasks (like `http.server`) require explicit shell backgrounding (`&`) or the Python script will hang.