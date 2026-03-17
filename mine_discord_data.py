import os
import json
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_FOLDER = os.path.join(SCRIPT_DIR, "messages") 
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "bot_brain.txt")

def clean_text(text):
    if not text: return None
    text = re.sub(r'http\S+', '', text)
    if len(text) < 5: return None
    text = text.replace('\n', ' ').replace('\r', '')
    return text.strip()

def mine_messages():
    print(f"--- Mining Discord Data from: {ROOT_FOLDER} ---")
    if not os.path.exists(ROOT_FOLDER):
        print(f"[ERROR] Could not find the 'messages' folder. Did you extract your Discord data and put the 'messages' folder here?")
        return
    total_count = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        for root, dirs, files in os.walk(ROOT_FOLDER):
            for file in files:
                if file == "messages.json":
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for msg in data:
                                    content = msg.get("Contents", "")
                                    cleaned = clean_text(content)
                                    if cleaned:
                                        outfile.write(f"{cleaned}\n")
                                        total_count += 1
                    except Exception:
                        continue
    print(f"--- SUCCESS! ---")
    print(f"Extracted {total_count} messages into '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    mine_messages()