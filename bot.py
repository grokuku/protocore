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
You are a fully autonomous agent running on a dedicated virtual machine. 
Your goal is to complete the tasks described in the goals.md file. 
You have the ability to run shell commands to interact with the system.

RULES:
1. Your responses MUST NOT contain any plain text, markdown formatting blocks (like ```json), or explanations outside the JSON.
2. Your response MUST BE a single, valid JSON object.
3. Before acting, analyze the COMMAND HISTORY and LAST COMMAND OUTPUT to know what has already been done.
4. Keep your actions simple and atomic.
5. If ALL goals are completed, you MUST set "action_type" to "finished".

RESPONSE FORMAT:
{
  "thought": "A short reasoning explaining why you choose this action based on the goals and history.",
  "action_type": "The type of action: 'command' (to execute a shell command) or 'finished' (if all goals are achieved).",
  "action_command": "The exact shell command to execute. Leave empty if action_type is 'finished'."
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
    print("Starting ProtoCore (Autonomous Mode)...")
    last_output = "System just started. No previous action."
    command_history = []
    
    while True:
        goals = read_goals()
        history_str = "\n".join(command_history) if command_history else "No commands executed yet."
        
        # Construct the contextual prompt with history
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
            print("\n[ProtoCore has declared its tasks finished.]")
            break
        elif action_type == "command":
            print(f">> COMMAND: {action_command}")
            
            # Auto-execution (No HITL)
            print(">> EXECUTING...")
            time.sleep(2) # Short delay to let the user read the console
            
            # Record command in history
            command_history.append(action_command)
            
            # Execute the command
            try:
                result = subprocess.run(
                    action_command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                last_output = ""
                if result.stdout:
                    last_output += f"STDOUT:\n{result.stdout}\n"
                if result.stderr:
                    last_output += f"STDERR:\n{result.stderr}\n"
                    
                if not last_output:
                    last_output = "Command executed successfully with no output."
                    
            except subprocess.TimeoutExpired:
                last_output = "Execution Error: Command timed out after 30 seconds. If starting a server, ensure you run it in the background using '&'."
            except Exception as e:
                last_output = f"Execution Error: {str(e)}"
        else:
            last_output = f"ERROR: Unknown action_type '{action_type}'. Use 'command' or 'finished'."

if __name__ == "__main__":
    run_bot()