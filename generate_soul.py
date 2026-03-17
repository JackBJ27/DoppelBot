import requests
import os
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

raw_keys = os.getenv("GOOGLE_API_KEYS", "")
GOOGLE_API_KEY = raw_keys.split(",")[0].strip() if raw_keys else ""
BRAIN_FILE = os.path.join(SCRIPT_DIR, "bot_brain.txt")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "soul.txt")
MODEL_NAME = "gemini-2.5-flash"

def analyze_brain():
    if not GOOGLE_API_KEY:
        print("[ERROR] Google API Key is missing! Did you save it in the Dashboard?")
        return

    print(f"--- Reading {BRAIN_FILE}... ---")
    try:
        with open(BRAIN_FILE, "r", encoding="utf-8") as f:
            full_text = f.read()
        if len(full_text) > 800000:
            print(f"⚠️ Brain is massive ({len(full_text)} chars). Trimming to most recent 800,000 characters...")
            history_text = full_text[-800000:] 
        else:
            history_text = full_text
    except FileNotFoundError:
        print(f"Error: Could not find {BRAIN_FILE}! Did you run the miner script first?")
        return

    print(f"--- Sending {len(history_text)} characters to Google... ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"
    prompt = f"""
    Here is a huge log of chat messages from a user.
    TASK: Analyze this text to create a detailed "Character File" (Soul) for an AI that mimics them.
    EXTRACT THE FOLLOWING INTO A CLEAN LIST:
    1. CORE IDENTITY: Age, Job, Location, hobbies, cars they own.
    2. THE "LORE": Specific memories, drama, projects, family mentions.
    3. OPINIONS: What do they love? What do they HATE?
    4. SPEAKING STYLE: Do they use caps? Punctuation? List their most used slang words.
    5. VIBE: Sarcastic? Tired? Hater? Chill?
    OUTPUT FORMAT: Just the character profile text.
    --- START CHAT LOGS ---
    {history_text}
    --- END CHAT LOGS ---
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and data['candidates']:
                generated_soul = data['candidates'][0]['content']['parts'][0]['text']
                with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
                    out.write(generated_soul)
                print(f"✅ Created {OUTPUT_FILE}!")
        else: print(f"[Error] Google API said: {response.text}")
    except Exception as e: print(f"[Connection Error] {e}")

if __name__ == "__main__":
    analyze_brain()