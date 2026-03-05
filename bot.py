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

OLLAMA_URL = config.get("ollama_url", "http://localhost:11434/api/generate")
MODEL = config.get("model", "llama3")

# Le prompt est mis à jour pour autoriser la réflexion avant le JSON
SYSTEM_PROMPT = """
You are ProtoCore, a fully autonomous agent running on a dedicated virtual machine. 
Your goal is to complete the tasks described in the goals.md file. 
You have full system access to run shell commands, create files, and modify your environment.

RULES:
1. Before acting, analyze the COMMAND HISTORY and LAST COMMAND OUTPUT.
2. Keep your actions simple and atomic.
3. If ALL goals are completed, or if you are waiting for new instructions, you MUST set "action_type" to "idle". 
4. ONLY set "action_type" to "finished" if explicitly asked to permanently terminate yourself.
5. Your final answer MUST be a single, valid JSON object. 

IF YOU ARE A REASONING MODEL:
You may output your internal reasoning inside <think>...</think> tags FIRST.
Immediately after your <think> block, you MUST output the JSON wrapped in a markdown block like this:
```json
{
    "thought": "A short summary of your reasoning.",
    "action_type": "command",
    "action_command": "ls -la"
}
```
"""

def get_llm_response(prompt_text):
    payload = {
        "model": MODEL,
        "prompt": prompt_text,
        "system": SYSTEM_PROMPT,
        "stream": False,
        # On RETIRE "format": "json" pour laisser le modèle générer ses balises <think>
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "{}")
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