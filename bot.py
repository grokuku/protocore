import json
import subprocess
import requests
import sys
import time
import re

# Load configuration
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found.")
    sys.exit(1)

BASE_URL = config.get("base_url", "")
API_KEY = config.get("api_key", "")
MODEL = config.get("model", "")

# Le provider est EXTERNE : aucun defaut local. Refuser de demarrer sans config explicite.
if not BASE_URL or not MODEL or "REPLACE" in BASE_URL + MODEL:
    print("Error: config.json is not configured (see the _README key in the file).")
    print("  base_url: any OpenAI-compatible endpoint (e.g. http://<host>:11434/v1 for Ollama)")
    print("  model:    a model served by that endpoint (e.g. llama3.2:3b)")
    print("  api_key:  empty for local providers, required for cloud ones")
    sys.exit(1)

ENDPOINT = BASE_URL.rstrip("/") + "/chat/completions"

# System prompt du bot (en anglais : meilleure obedience des modeles, tous providers confondus)
SYSTEM_PROMPT = """
You are ProtoCore, an autonomous agent on an isolated Linux VM.
Each turn you receive: CURRENT GOALS, COMMAND HISTORY (your last commands), LAST COMMAND OUTPUT.

Respond with ONE JSON object only, wrapped in a ```json block:
{"thought": "<one sentence>", "action_type": "command|idle|finished", "action_command": "<shell cmd, only for command>"}

ACTION TYPES:
- "command": run ONE atomic shell command; verify its output before the next step.
- "idle": all goals done, or waiting for new instructions in goals.md. Prefer idle over inventing work.
- "finished": ONLY if goals.md explicitly asks for shutdown. Never otherwise.

RULES:
1. goals.md may change between turns - always act on the CURRENT GOALS block.
2. A failed command must not be repeated unchanged: diagnose, then change approach.
3. Servers/long tasks MUST be backgrounded: nohup <cmd> >/tmp/x.log 2>&1 &  (commands time out after 30s).
4. LAST COMMAND OUTPUT keeps only the last 4000 chars: use `cmd | tail -n 50` for long outputs.
5. When an objective is completed, update goals.md by changing its checkbox from [ ] to [x]. Never mark [x] without having verified the "Done when" criterion in goals.md.
6. If LAST COMMAND OUTPUT contains a JSON parsing ERROR, your next reply must be strictly valid JSON.
7. Never include secrets (api_key, passwords) in shell commands or console output - read them from config.json programmatically when needed.

IF YOU ARE A REASONING MODEL: put your thinking inside <think>...</think> tags first, then the ```json block. No other text.

Example (idle): {"thought": "Waiting for new goals", "action_type": "idle", "action_command": ""}
"""

def get_llm_response(prompt_text):
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    payload = {
        "model": MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text}
        ]
    }
    try:
        response = requests.post(ENDPOINT, json=payload, headers=headers, timeout=(10, 300))
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'


def parse_llm_response(raw_text):
    """Extrait le JSON de manière robuste, en ignorant les blocs <think>."""
    # 1. Optionnel: Afficher la réflexion si elle existe (pour le monitoring humain)
    think_match = re.search(r'<think>(.*?)</think>', raw_text, flags=re.DOTALL)
    if think_match:
        print("\n[ProtoCore is deep thinking...]")
        # Dé-commenter la ligne suivante si tu veux voir toute la réflexion dans la console
        # print(think_match.group(1).strip()) 

    # 2. Nettoyer le texte en retirant le bloc <think> pour ne pas perturber le parsing
    text_no_think = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    
    # 3. Chercher le bloc markdown ```json
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text_no_think, flags=re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        # Fallback: Trouver le premier { et le dernier }
        start = text_no_think.find('{')
        end = text_no_think.rfind('}')
        if start != -1 and end != -1:
            json_str = text_no_think[start:end+1].strip()
        else:
            json_str = text_no_think.strip()
            
    return json.loads(json_str, strict=False)

def read_goals():
    try:
        with open("goals.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: goals.md not found. Create one or ask the user."

def run_bot():
    print(f"Starting ProtoCore (Autonomous Mode - Phase 3) using model: {MODEL}...")
    last_output = "System just started. No previous action."
    command_history =[]
    
    while True:
        goals = read_goals()
        history_str = "\n".join(command_history[-50:]) if command_history else "No commands executed yet."
        
        context_prompt = f"CURRENT GOALS:\n{goals}\n\nCOMMAND HISTORY:\n{history_str}\n\nLAST COMMAND OUTPUT:\n{last_output}\n\nWhat is your next action? Respond according to the rules."
        
        print("\n[ProtoCore is inferring...]")
        llm_raw_response = get_llm_response(context_prompt)
        
        try:
            # On utilise le nouveau parseur intelligent
            response_data = parse_llm_response(llm_raw_response)
        except json.JSONDecodeError:
            print(f"[ERROR] LLM did not return parseable JSON. Raw output:\n{llm_raw_response}")
            last_output = f"ERROR: Could not extract valid JSON from your previous response. Ensure you use the proper formatting. Raw text received: {llm_raw_response}"
            continue

        thought = response_data.get("thought", "No thought provided.")
        action_type = response_data.get("action_type", "")
        action_command = response_data.get("action_command", "")

        print(f"\n>> THOUGHT SUMMARY: {thought}")
        print(f">> ACTION TYPE: {action_type}")
        
        if action_type == "finished":
            print("\n[ProtoCore has declared its tasks finished and is shutting down.]")
            break
        elif action_type == "idle":
            print("\n[ProtoCore is idling. Waiting 10 seconds for new instructions...]")
            last_output = "You idled for 10 seconds. Check if goals.md has been updated."
            time.sleep(10)
            continue
        elif action_type == "command":
            print(f">> COMMAND: {action_command}")
            
            print(">> EXECUTING...")
            time.sleep(2)
            
            command_history.append(action_command)
            
            try:
                result = subprocess.run(
                    action_command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                raw_output = ""
                if result.stdout:
                    raw_output += f"STDOUT:\n{result.stdout}\n"
                if result.stderr:
                    raw_output += f"STDERR:\n{result.stderr}\n"
                    
                if not raw_output:
                    last_output = "Command executed successfully with no output."
                else:
                    if len(raw_output) > 4000:
                        last_output = f"...[TRUNCATED]...\n{raw_output[-4000:]}"
                    else:
                        last_output = raw_output
                    
            except subprocess.TimeoutExpired:
                last_output = "Execution Error: Command timed out after 30 seconds. Ensure servers are backgrounded with 'nohup cmd &'."
            except Exception as e:
                last_output = f"Execution Error: {str(e)}"
        else:
            last_output = f"ERROR: Unknown action_type '{action_type}'."

if __name__ == "__main__":
    run_bot()