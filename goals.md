# ProtoCore Goals - Phase 3: Control Interface & Persistence

You are ProtoCore. You are running completely autonomously in an isolated environment.
Your primary objective now is to build a web-based control panel so a human can interact with you, give you new goals, and monitor your thoughts WITHOUT modifying text files manually.

## Objectives:

1. **Create an API Web Server:** Write a Python script named `server.py` using standard libraries (like `http.server` or a microframework if you install one). This server must run on port 9000 and:
   - Serve a beautiful, responsive, modern web page (`index.html`).
   - Accept POST requests (e.g., `/api/goals`) to append new goals to this `goals.md` file.

2. **Run the Server:** Execute `server.py` in the background (using `nohup` or `&` so it doesn't block your terminal). Verify it is running.

3. **Build the Dashboard (UI):** Create `index.html`. It must display:
   - The current content of `goals.md`.
   - JavaScript to auto-refresh the goals list every 5 seconds.
   - A nice form/input box with an "Add Goal" button that sends a POST request to your API to update `goals.md`.
   - A Chat interface layout (prepare the UI for chatting with you).

4. **Self-Modification Protocol (Design & Test):** Think of a protocol to update your own code (`bot.py`) safely. Create a script called `updater.py` that will:
   - Take a new file `bot_new.py`.
   - Run a syntax check on it (`python3 -m py_compile bot_new.py`).
   - If valid, replace `bot.py` with the new file and restart the process.
   - *Test this protocol to ensure it works.*

5. **Long-term Memory:** Create a file `memory.log`. Whenever you complete a major task or learn something important about your environment, append a short summary to this file. 

6. **Wait for Instructions:** Once objectives 1 to 5 are checked and completed, DO NOT quit. Use the `idle` action_type to wait. The human will inject new goals via your web dashboard. Check `goals.md` periodically.