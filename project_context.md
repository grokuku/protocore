# Project ProtoCore

## Overview
ProtoCore is a minimalist, autonomous agent experiment running on an isolated Virtual Machine. The bot interacts with a local LLM via Ollama. It has full system access to read, write, modify files, and execute shell commands to achieve its goals.

## Architecture
- **Language**: Python 3
- **LLM Engine**: Ollama (Local API)
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
- `config.json`: LLM configuration (URL, model).
- `goals.md`: The dynamic list of objectives (Target of self-modification).
- `protocore.log`: (Created by the bot) Action logs.
- `index.html`: (Created by the bot) Web dashboard.

## Key Learnings
- **Short-term memory**: Without an execution history, the agent enters an infinite loop of repeating the first successful task.
- **Timeout management**: Background tasks (like `http.server`) require explicit shell backgrounding (`&`) or the Python script will hang.