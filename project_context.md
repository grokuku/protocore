# Project ProtoCore

## Overview
ProtoCore is a minimalist, autonomous agent experiment running on an isolated Virtual Machine. The bot interacts with a local LLM via Ollama. It has full system access to read, write, modify files, and execute shell commands to achieve its goals.

## Architecture
- **Language**: Python 3
- **LLM Engine**: Ollama (Local API)
- **Core Loop**: Observe -> Think (LLM) -> Act (Shell) -> Loop.
- **Prompting Strategy**: JSON-first. The LLM is forced to output a strictly structured JSON containing its thought process and the shell command to execute.

## Current State
- Initialization phase.
- Temporary "Human-in-the-Loop" (HITL) security measure is active: every shell command requires manual validation before execution.

## Files
- `bot.py`: The main cognitive loop.
- `config.json`: LLM configuration (URL, model).
- `goals.md`: The dynamic list of objectives.