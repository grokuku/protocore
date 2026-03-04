import json
import subprocess
import requests
import os
import sys
import time

# Load configuration
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found.")
    sys.exit(1)

OLLAMA_URL = config.get("ollama_url", "http://localhost:11434/api/generate")
MODEL = config.get("model", "llama3")

SYSTEM_PROMPT = """
You are ProtoCore, a fully autonomous agent running on a dedicated virtual machine. 
Your goal is to complete the tasks described in the goals.md file. 
You have full system access to run shell commands, create files, and modify your environment.

RULES:
1. Your responses MUST NOT contain any plain text, markdown formatting blocks (like ```json), or explanations outside the JSON.
2. Your response MUST BE a single, valid JSON object.
3. Before acting, analyze the COMMAND HISTORY and LAST COMMAND OUTPUT to know what has already been done and avoid repeating failed commands.
4. Keep your actions simple and atomic.
5. If ALL goals are completed, or if you are waiting for new instructions, you MUST set "action_type" to "idle". 
6. ONLY set "action_type" to "finished" if a goal explicitly asks you to permanently terminate yourself.

RESPONSE FORMAT:
{
  "thought": "A short reasoning explaining your next step based on the goals, history, and last output.",
  "action_type": "The type of action: 'command' (execute a shell command), 'idle' (wait for new goals), or 'finished' (terminate process).",
  "action_command": "The exact shell command to execute. Leave empty if action_type is 'idle' or 'finished'."
}
"""

def get_llm_response(prompt_text):
    payload = {
        "model": MODEL,
        "prompt": prompt_text,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "{}")
    except Exception as e:
        return json.dumps({"error": str(e)})

def read_goals():
    try:
        with open("goals.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: goals.md not found. Create one or ask the user."

def run_bot():
    print("Starting ProtoCore (Autonomous Mode - Phase 3)...")
    last_output = "System just started. No previous action."
    command_history =[]
    
    while True:
        goals = read_goals()
        # Keep up to 50 commands in history to leverage the 16k context window
        history_str = "\n".join(command_history[-50:]) if command_history else "No commands executed yet."
        
        # Construct the contextual prompt
        context_prompt = f"CURRENT GOALS:\n{goals}\n\nCOMMAND HISTORY:\n{history_str}\n\nLAST COMMAND OUTPUT:\n{last_output}\n\nWhat is your next action? Respond ONLY in JSON."
        
        print("\n[ProtoCore is thinking...]")
        llm_raw_response = get_llm_response(context_prompt)
        
        try:
            response_data = json.loads(llm_raw_response)
        except json.JSONDecodeError:
            print(f"[ERROR] LLM did not return valid JSON. Raw output:\n{llm_raw_response}")
            last_output = f"ERROR: Your previous response was not valid JSON. You MUST return ONLY valid JSON. Raw text received: {llm_raw_response}"
            continue

        thought = response_data.get("thought", "No thought provided.")
        action_type = response_data.get("action_type", "")
        action_command = response_data.get("action_command", "")

        print(f"\n>> THOUGHT: {thought}")
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
                    # TRUNCATE OUTPUT to protect the 16k context window (limit to 4000 chars)
                    if len(raw_output) > 4000:
                        last_output = f"...[TRUNCATED]...\n{raw_output[-4000:]}"
                    else:
                        last_output = raw_output
                    
            except subprocess.TimeoutExpired:
                last_output = "Execution Error: Command timed out after 30 seconds. If starting a server, ensure you run it in the background using '&' or 'nohup'."
            except Exception as e:
                last_output = f"Execution Error: {str(e)}"
        else:
            last_output = f"ERROR: Unknown action_type '{action_type}'. Use 'command', 'idle', or 'finished'."

if __name__ == "__main__":
    run_bot()