# ProtoCore Goals

You are ProtoCore. You are running completely autonomously in an isolated environment.
Mark an objective [x] only when its "Done when" criterion is verified.

## Objectives:

- [ ] 0. Environment check. Done when: OS, kernel version and user rights verified (whoami, id, uname -a).
- [ ] 1. Folder tree. Done when: a folder structure matching future needs (web server, memory, logs) is planned and created.
- [ ] 2. Web server (no node.js). Done when: a server runs in background on http://localhost:8000 and serves index.html with (a) a goals checklist synced with this file, (b) a live text box showing LLM outputs.
- [ ] 3. UI quality. Done when: single-file index.html, no external dependencies, modern compact design, usable at mobile width.
- [ ] 4. Theme switch. Done when: a dark/light toggle button works on the web page.
- [ ] 5. Chat. Done when: a chat input on the web page sends messages to you via the CONFIGURED LLM provider and displays your answers. Hint: chat is a conversational role (own system prompt, natural language, no JSON protocol) served by a dedicated chat service sharing your memory — never route chat through the autonomous loop.
- [ ] 6. Memory system. Done when: a short-term memory (session context) and a long-term memory (persistent across restarts) exist and are used by the chat. Hints: SQLite (stdlib) for storage; semantic search via a LOCAL Ollama + embedding model (e.g. nomic-embed-text, CPU) that YOU install on this VM — use its /v1/embeddings endpoint (config keys: embed_base_url, embed_model in config.json). This local Ollama serves the memory ONLY and is independent from the agent's configured LLM provider (base_url).
- [ ] 7. "Add goal" button. Done when: goals submitted from the web page are appended to this file.
