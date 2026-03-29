import discord
import speech_recognition as sr
import requests
import random
import asyncio
import os
import atexit
import glob
import functools
import time
import re
import json
from datetime import datetime, timezone
import logging
from dotenv import load_dotenv
import torch
torch.set_num_threads(4)


logging.getLogger('discord.voice_client').setLevel(logging.CRITICAL)
import warnings
warnings.simplefilter("ignore", ResourceWarning)

from voice_compat import apply_voice_protocol_compat_patches
apply_voice_protocol_compat_patches()
from pydub import AudioSegment
from ddgs import DDGS
import scipy.io.wavfile

import io
import queue
import keyring
from collections import deque

API_SESSION = requests.Session()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DISCORD_TOKEN = keyring.get_password("DoppelBot", "DISCORD_TOKEN")
raw_keys = keyring.get_password("DoppelBot", "GOOGLE_API_KEYS") or ""
GOOGLE_API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]
CURRENT_KEY_INDEX = 0

GLOBAL_EMOJI_CACHE = {}

config_path = os.path.join(SCRIPT_DIR, "config.json")
if os.path.exists(config_path):
    with open(config_path, "r") as f: config = json.load(f)
else: config = {}

def parse_ids(config_val):
    if isinstance(config_val, dict): return [int(k) for k in config_val.keys() if str(k).isdigit()]
    if isinstance(config_val, list): return [int(x) for x in config_val if str(x).isdigit()]
    return []

active_profile_name = config.get('active_profile', 'Default')
profiles = config.get('profiles', {})
active_profile = profiles.get(active_profile_name, config)

BOT_NAME = active_profile.get('bot_name', config.get('bot_name', 'DoppelBot'))
BASE_PROMPT = active_profile.get('base_prompt', config.get('base_prompt', f'You are {BOT_NAME}. A casual, chill Discord bot.'))
FRIENDS_CONTEXT = active_profile.get('friends_context', config.get('friends_context', ''))
RULES = active_profile.get('rules', config.get('rules', '1. EMOTION TAG: You MUST start your response with an emotion tag like [default], [sad], [anger], [dead inside], [excited], [anxious], or [bored].\n2. NO RUTS: NEVER act exasperated every time you speak. DO NOT loop rhetorical questions. Vary your sentence structure. Do not bring up the exact same topics over and over again. Move on to new topics naturally.\n3. COMPLIANCE: If the user tells you to pick a topic, ask a question, tell a joke, or give an answer, YOU MUST DO IT IMMEDIATELY. Do not stall or deflect.\n4. TONE (CRITICAL): Have a spine, but REMEMBER THESE ARE YOUR FRIENDS. Do not resort to toxic insults or ad hominem attacks (like insulting their reading comprehension). Keep it playful, not hateful.\n5. NO ECHOING: DO NOT start by repeating the user\'s words.\n6. DYNAMIC LENGTH: Match the user\'s energy. If the user sends a short message (like "yo" or "sup"), reply with exactly 1 short, punchy sentence. If they write a long message, you can write 2 - 3 sentences. NEVER ramble just to fill space.'))
MODEL_CANDIDATES = config.get("ai_models", ["gemma-3-27b-it", "gemma-3-12b-it", "gemma-3-4b-it", "gemma-3-1b-it", "gemma-2-27b-it", "gemma-2-9b-it", "gemini-2.5-flash"])
ACTIVE_MODEL = None 
TEMPERATURE = config.get("temperature", 0.85)

VC_ENABLED = config.get("enable_voice", True)
ALLOW_DM_VOICE = config.get("allow_dm_voice", True)
ENABLE_THINKING_MUSIC = config.get("enable_thinking_music", False)
ENABLE_STATS = config.get("enable_stats", True)
AUTO_CHAT_ENABLED = config.get("auto_chat", True)
AUTO_JOIN_VC = config.get("auto_join_vc", True)
PRIMARY_CHANNEL_ID = config.get("primary_channel_id", 0)
ALLOWED_CHANNEL_IDS = parse_ids(config.get("allowed_text_channels", {}))
ALLOWED_VC_CHANNELS = parse_ids(config.get("allowed_vc_channels", {}))

ACCESS_MODE = config.get("access_mode", "Friends Only (VIPs)")
ALLOWED_ROLES = parse_ids(config.get("allowed_roles", {}))

VIP_MAP = {int(k): v for k, v in config.get("vip_map", {}).items() if str(k).isdigit()}
KNOWN_BOTS = {int(k): v for k, v in config.get("known_bots", {}).items() if str(k).isdigit()}

CUSTOM_STATS = config.get("custom_stats", [])
AUTO_REPLIES = config.get("auto_replies", {})
BANNED_INPUTS = config.get("banned_inputs", [])
REMOVED_WORDS = config.get("removed_words", [])
WORD_REPLACEMENTS = config.get("word_replacements", {})
FORCE_LOWERCASE = config.get("force_lowercase", True)

ENABLE_DEBUG = config.get("enable_debug", True)
DEBUG_MODULES = config.get("debug_modules", {"voice": True, "tts": True, "brain": True, "stats": True, "auto_chat": True, "events": True})

VOICE_CORRECTIONS = config.get("voice_corrections", {"gonna": "going to", "wanna": "want to"})
TTS_PRONUNCIATIONS = config.get("tts_pronunciations", {r"\blmao\b": "el em ay oh"})

MSG_MEMORY_RESET = config.get("msg_memory_reset", "text memory wiped.")
MSG_VC_MEMORY_RESET = config.get("msg_vc_memory_reset", "voice memory wiped.")
MSG_SAFETY_FILTER = config.get("msg_safety_filter", "google safety filter says no.")
MSG_BANNED_INPUT = config.get("msg_banned_input", "woah chill. not saying that.")
MSG_BRAIN_DISCONNECTED = config.get("msg_brain_disconnected", "brain disconnected")
MSG_JOIN_VC = config.get("msg_join_vc", "hey, what's up?")
MSG_STOP_TALKING = config.get("msg_stop_talking", "my bad. zipping it.")

EPHEMERAL_CMDS = config.get("ephemeral_commands", False)
ENABLED_CMDS = config.get("enabled_commands", ["Auto-Chat Toggles", "Reset Text Memory", "VC Ears Toggles", "VC Auto-Join Toggles", "Join VC Button"])

VOICE_DIR = os.path.join(SCRIPT_DIR, "voice_references")
BRAIN_FILE = os.path.join(SCRIPT_DIR, "bot_brain.txt")
SOUL_FILE = os.path.join(SCRIPT_DIR, "soul.txt")
VC_BRAIN_FILE = os.path.join(SCRIPT_DIR, "vc_history.txt")
STATS_FILE = os.path.join(SCRIPT_DIR, 'stats.json')

STAT_COOLDOWNS = {}
STAT_COOLDOWN_TIME = 10 
LAST_RESET_TIMESTAMP = 0.0
LAST_MESSAGE_TIME = time.time()
LAST_INTERACTED_USER_ID = None
CONTEXT_TIMEOUT = 14400 
LURK_CHANCE = 0.01 
SAMPLE_SIZE = 80   
VOCAL_CORDS_READY = False
IS_THINKING = False
LAST_VC_INTERACTION = 0

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True 
client = discord.Client(intents=intents)

def dprint(module, message):
    if ENABLE_DEBUG and DEBUG_MODULES.get(module, True):
        print(message)

def correct_transcription(text):
    text_lower = text.lower()
    for wrong, right in VOICE_CORRECTIONS.items():
        text_lower = re.sub(rf'\b{re.escape(wrong)}\b', right, text_lower)
    return text_lower

def fix_pronunciation(text):
    fixed_text = text.lower()
    for word, phonetic in TTS_PRONUNCIATIONS.items():
        fixed_text = re.sub(word, phonetic, fixed_text, flags=re.IGNORECASE)
    return fixed_text

def can_user_interact(member_or_user):
    if getattr(member_or_user, 'bot', False): return False
    if ACCESS_MODE == 'Global / Everyone': return True
    if getattr(member_or_user, 'id', None) in VIP_MAP: return True
    if ACCESS_MODE == 'Role Based' and hasattr(member_or_user, 'roles'):
        user_role_ids = [r.id for r in member_or_user.roles]
        if any(r_id in ALLOWED_ROLES for r_id in user_role_ids): return True
    return False

def start_thinking_music(vc):
    if not config.get("enable_thinking_music", False) or not vc or vc.is_playing(): return
    music_file = os.path.join(VOICE_DIR, "thinking.wav")
    if os.path.exists(music_file):
        try:
            ffmpeg_path = os.path.join(SCRIPT_DIR, 'ffmpeg.exe')
            executable = ffmpeg_path if os.path.exists(ffmpeg_path) else 'ffmpeg'
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(music_file, executable=executable))
            source.volume = 0.15
            vc.play(source)
        except Exception as e:
            dprint("voice", f"   -> [VOICE DEBUG] Failed to play thinking music: {e}")

def switch_api_key():
    global CURRENT_KEY_INDEX
    if not GOOGLE_API_KEYS: return
    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GOOGLE_API_KEYS)
    dprint("brain", f"   -> [API WARNING] Swapping to key index {CURRENT_KEY_INDEX}")

def find_working_model():
    global ACTIVE_MODEL, CURRENT_KEY_INDEX
    dprint("brain", "--- Finding an AI Brain... ---")
    headers = {'Content-Type': 'application/json'}
    test_payload = { "contents": [{ "parts": [{"text": "Hi"}] }] }
    
    for model in MODEL_CANDIDATES:
        current_key = GOOGLE_API_KEYS[CURRENT_KEY_INDEX]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={current_key}"
        try:
            dprint("brain", f"Testing {model}...")
            response = API_SESSION.post(url, json=test_payload, headers=headers)
            if response.status_code == 200:
                ACTIVE_MODEL = model
                dprint("brain", f"   -> Success! Using {model}")
                return model
            elif response.status_code == 429:
                switch_api_key() 
        except: pass
        
    print("--- WARNING: All models failed. Check your API keys. ---")
    ACTIVE_MODEL = None
    return None

def load_stats():
    if not os.path.exists(STATS_FILE):
        default_stats = {stat["stat_name"]: 0 for stat in CUSTOM_STATS}
        with open(STATS_FILE, 'w') as f: json.dump(default_stats, f)
    with open(STATS_FILE, 'r') as f: return json.load(f)

def save_stats(stats):
    with open(STATS_FILE, 'w') as f: json.dump(stats, f)

async def check_and_update_stats(user_name, text):
    if not ENABLE_STATS or not CUSTOM_STATS: return None
    stats = load_stats()
    text_lower = text.lower()
    triggered_msg = None
    for stat in CUSTOM_STATS:
        if user_name.lower() == stat.get("user", "").lower():
            if any(re.search(rf'\b{re.escape(trigger)}\b', text_lower) for trigger in stat.get("triggers", [])):
                
                is_valid = True
                if ACTIVE_MODEL and GOOGLE_API_KEYS:
                    def _check():
                        try:
                            current_key = GOOGLE_API_KEYS[CURRENT_KEY_INDEX]
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={current_key}"
                            prompt = f"Does this message logically and contextually relate to the topic of '{stat['stat_name']}'? Message: '{text}'. Answer ONLY 'yes' or 'no'."
                            payload = {"contents": [{"parts": [{"text": prompt}]}]}
                            res = API_SESSION.post(url, json=payload, timeout=5)
                            if res.status_code == 200:
                                reply = res.json()['candidates'][0]['content']['parts'][0]['text'].strip().lower()
                                if 'no' in reply and 'yes' not in reply:
                                    return False
                        except: pass
                        return True
                        
                    is_valid = await client.loop.run_in_executor(None, _check)
                    
                if not is_valid: continue

                stat_key = stat["stat_name"]
                if stat_key not in stats: stats[stat_key] = 0
                stats[stat_key] += 1
                triggered_msg = stat["message"].replace("{count}", str(stats[stat_key]))
                break 
    if triggered_msg: save_stats(stats)
    return triggered_msg

def load_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f: return [line.strip() for line in f if line.strip()]
    except FileNotFoundError: return []

def sanitize_text_for_ai(text):
    for uid, name in VIP_MAP.items(): text = text.replace(f"<@{uid}>", f"@{name}")
    text = re.sub(r'<a?:(\w+):\d+>', r':\1:', text)
    text = re.sub(r'<@!?\d+>', '', text)
    return text.strip()

def replace_emojis(text):
    if not text or ":" not in text: return text
    for server_name, emojis in GLOBAL_EMOJI_CACHE.items():
        for e_id, e_data in emojis.items():
            text = text.replace(f":{e_data['name']}:", e_data["code"])
    return text

def cleanup_response(text):
    text = re.sub(r'<[^:>]+>', '', text)
    emoji_toggles = config.get("emoji_toggles", {})
    
    for server_name, emojis in GLOBAL_EMOJI_CACHE.items():
        for e_id, e_data in emojis.items():
            if emoji_toggles.get(e_id, True):
                code = e_data["code"]
                name = e_data["name"]
                text = text.replace(f":{name}:", code)

    for uid, name in VIP_MAP.items():
        if f"@{name}" in text or f"@{name.lower()}" in text: text = re.sub(f"@{name}", f"<@{uid}>", text, flags=re.IGNORECASE)
    return text.strip()

def is_repetitive(new_text, history_list):
    def simplify(t): return re.sub(r'[^a-zA-Z0-9]', '', t).lower()
    simple_new = simplify(new_text)
    if len(simple_new) < 5: return False 
    bot_msgs = [simplify(msg.split(": ", 1)[1]) for msg in history_list if msg.startswith(f"{BOT_NAME}:".lower())]
    for old_msg in bot_msgs[-3:]:
        if simple_new in old_msg or old_msg in simple_new: return True
    return False

def get_web_context(query):
    dprint("brain", f"   -> [SEARCH] Snooping the web for: '{query}'")
    try:
        results = DDGS().text(query, max_results=3, backend='duckduckgo')
        results_list = list(results)
        if not results_list: return ""
        dprint("brain", f"   -> [SEARCH SUCCESS] Found {len(results_list)} results.")
        context_text = "\n".join([f"- {r.get('body', '')}" for r in results_list])
        return f"\n*** WEB SEARCH RESULTS (OPTIONAL) ***\n{context_text}\nCRITICAL RULE: If these search results are irrelevant, IGNORE THEM COMPLETELY.\n"
    except Exception as e: 
        dprint("brain", f"   -> [SEARCH CRASH] {e}")
        return ""

def get_ai_reply(current_user, conversation_history, random_memories, soul_text, target_message, context_mode="normal", web_context=""):
    global ACTIVE_MODEL
    if not ACTIVE_MODEL:
        find_working_model()
        if not ACTIVE_MODEL: return MSG_BRAIN_DISCONNECTED, "default"

    dprint("brain", f"   [STEP 1] Generating with {ACTIVE_MODEL} (Mode: {context_mode})...")

    if BANNED_INPUTS:
        if any(w.lower() in target_message.lower() for w in BANNED_INPUTS): 
            return MSG_BANNED_INPUT, "default"

    clean_history = [sanitize_text_for_ai(msg) for msg in conversation_history]
    clean_memories = [sanitize_text_for_ai(msg) for msg in random_memories]
    history_text = "\n".join(clean_history)
    memory_text = "\n".join([f"- {msg}" for msg in clean_memories])

    msg_lower = target_message.lower().strip()
    status_triggers = ["doing", "wyd", "what's up", "whats up", "how are"]
    health_triggers = ["you good", "you fixed", "working", "lobotomy"]
    
    special_instruction = ""
    if any(x in msg_lower for x in health_triggers): special_instruction = "*** PRIORITY: HEALTH CHECK. Say 'Yeah I'm good' or 'Fixed'. ***\n"
    elif any(x in msg_lower for x in status_triggers): special_instruction = "*** PRIORITY: STATUS. Answer with VAGUE activity. ***\n"

    if context_mode == "auto_thought": action_target = "*** AUTO-CHAT: Post a brief, casual observation. ***"
    elif context_mode.startswith("auto_ping:"):
        parts = context_mode.split(":")
        action_target = f"*** AUTO-CHAT: Randomly start a conversation with {parts[1]}. ACTION: {parts[2]}. DO NOT ping them yourself! ***"
    else: action_target = f"*** TARGET MESSAGE (REPLY TO THIS) ***\n{current_user}: \"{target_message}\""

    try:
        emoji_toggles = config.get("emoji_toggles", {})
        fav_emojis_ids = config.get("favorite_emojis", [])
        
        fav_list = []
        other_list = []
        
        for server_name, emojis in GLOBAL_EMOJI_CACHE.items():
            for k, e in emojis.items():
                if emoji_toggles.get(k, True):
                    formatted = f":{e['name']}:"
                    if k in fav_emojis_ids:
                        fav_list.append(formatted)
                    else:
                        other_list.append(formatted)
                        
        emoji_prompt = ""
        if fav_list:
            emoji_prompt += f"\n*** HIGHLY PREFERRED EMOJIS (USE THESE OFTEN) ***\n{', '.join(fav_list)}\n"
        if other_list:
            emoji_prompt += f"\n*** OTHER AVAILABLE EMOJIS ***\n{', '.join(other_list)}\n"
    except:
        emoji_prompt = ""

    retry_note = "" 
    current_time_str = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    for attempt in range(3):
        current_key = GOOGLE_API_KEYS[CURRENT_KEY_INDEX]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={current_key}"
        
        valid_tags = "[default], [sad], [anger], [dead inside], [excited], [anxious], [bored]"
        dyn_rule = f"\n7. DYNAMIC EMOTIONS (CRITICAL): You MUST change tone when the topic shifts. You are STRICTLY LIMITED to ONLY these exact tags: {valid_tags}. Place tags at the START of a sentence or mid-sentence. NEVER put a tag at the very end of a message or right before punctuation. You MUST write actual words after every tag." if config.get("dynamic_emotions", False) else ""
        
        full_prompt = f"""
        {BASE_PROMPT} It is currently {current_time_str}.
        {web_context}
        {emoji_prompt}
        
        *** FRIENDS CONTEXT ***
        {FRIENDS_CONTEXT}
        
        *** PAST CONTEXT ***
        {history_text}
        
        *** SOUL (BACKGROUND INFO) ***
        {soul_text}
        
        *** STYLE EXAMPLES ***
        {memory_text}
        
        {special_instruction}{action_target}
        {retry_note}
        
        *** CRITICAL RULES ***
        {RULES}{dyn_rule}
        
        REPLY:
        """

        payload = {
            "contents": [{ "parts": [{"text": full_prompt}] }],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ],
            "generationConfig": {"temperature": TEMPERATURE, "topK": 40, "maxOutputTokens": 150}
        }

        try:
            response = API_SESSION.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and data['candidates']:
                    raw_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                    emotion = "default"
                    emotion_match = re.match(r'^\[(.*?)\]\s*(.*)', raw_text, re.IGNORECASE | re.DOTALL)
                    if emotion_match:
                        extracted_emo = emotion_match.group(1).lower()
                        valid_emotions = ["default", "sad", "anger", "dead inside", "excited", "anxious", "bored"]
                        if extracted_emo in valid_emotions: emotion = extracted_emo
                        text = emotion_match.group(2).strip()
                    else: text = raw_text

                    if REMOVED_WORDS:
                        words_pattern = '|'.join(map(re.escape, REMOVED_WORDS))
                        text = re.sub(rf'^(\[.*?\]\s*)?({words_pattern}),?\s*', r'\1', text, flags=re.IGNORECASE)

                    for bad_phrase, good_phrase in WORD_REPLACEMENTS.items():
                        text = re.sub(re.escape(bad_phrase), good_phrase, text, flags=re.IGNORECASE)

                    if FORCE_LOWERCASE:
                        words = text.split(" ")
                        fixed_words = []
                        for w in words:
                            if w.startswith(":") and w.endswith(":"): fixed_words.append(w)
                            elif w.isupper() and len(re.sub(r'[^A-Z]', '', w)) > 1: fixed_words.append(w) 
                            else: fixed_words.append(w.lower())
                        text = " ".join(fixed_words)

                    text = cleanup_response(text)
                    
                    if len(target_message) > 4 and text.lower().startswith(target_message.lower()[:15]):
                         retry_note = f"\n*** ALERT: You echoed the user. Write a NEW response. ***"
                         continue

                    if is_repetitive(text, clean_history):
                        if attempt == 2: return text + " lol", emotion
                        retry_note = f"\n*** ALERT: You already said '{text}'. Say something NEW. ***"
                        continue
                    return text, emotion
                else: return MSG_SAFETY_FILTER, "default"
            elif response.status_code == 429: switch_api_key(); time.sleep(1)    
            else: time.sleep(2)
        except: time.sleep(2)

    return MSG_SAFETY_FILTER, "default"

def get_ai_reply_stream(user_name, history_text, memories, soul_text, target_msg, mode, text_queue, web_context=""):
    global ACTIVE_MODEL, CURRENT_KEY_INDEX
    if not ACTIVE_MODEL:
        find_working_model()
        if not ACTIVE_MODEL: 
            text_queue.put(None)
            return MSG_BRAIN_DISCONNECTED, "default"

    dprint("brain", f"   [STEP 1] Generating LIVE with {ACTIVE_MODEL} (Mode: {mode})...")

    if BANNED_INPUTS:
        if any(w.lower() in target_msg.lower() for w in BANNED_INPUTS): 
            text_queue.put(None)
            return MSG_BANNED_INPUT, "default"

    msg_lower = target_msg.lower().strip()
    status_triggers = ["doing", "wyd", "what's up", "whats up", "how are"]
    health_triggers = ["you good", "you fixed", "working", "lobotomy"]
    
    special_instruction = ""
    if any(x in msg_lower for x in health_triggers): special_instruction = "*** PRIORITY: HEALTH CHECK. Say 'Yeah I'm good' or 'Fixed'. ***\n"
    elif any(x in msg_lower for x in status_triggers): special_instruction = "*** PRIORITY: STATUS. Answer with VAGUE activity. ***\n"

    if mode == "auto_thought": action_target = "*** AUTO-CHAT: Post a brief, casual observation. ***"
    elif mode.startswith("auto_ping:"):
        parts = mode.split(":")
        action_target = f"*** AUTO-CHAT: Randomly start a conversation with {parts[1]}. ACTION: {parts[2]}. DO NOT ping them yourself! ***"
    else: action_target = f"*** TARGET MESSAGE (REPLY TO THIS) ***\n{user_name}: \"{target_msg}\""

    try:
        emoji_toggles = config.get("emoji_toggles", {})
        fav_emojis_ids = config.get("favorite_emojis", [])
        fav_list = []
        other_list = []
        
        for server_name, emojis in GLOBAL_EMOJI_CACHE.items():
            for k, e in emojis.items():
                if emoji_toggles.get(k, True):
                    formatted = f":{e['name']}:"
                    if k in fav_emojis_ids: fav_list.append(formatted)
                    else: other_list.append(formatted)
                        
        emoji_prompt = ""
        if fav_list: emoji_prompt += f"\n*** HIGHLY PREFERRED EMOJIS (USE THESE OFTEN) ***\n{', '.join(fav_list)}\n"
        if other_list: emoji_prompt += f"\n*** OTHER AVAILABLE EMOJIS ***\n{', '.join(other_list)}\n"
    except:
        emoji_prompt = ""

    retry_note = "" 
    current_time_str = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    for attempt in range(3):
        current_key = GOOGLE_API_KEYS[CURRENT_KEY_INDEX]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:streamGenerateContent?alt=sse&key={current_key}"
        
        valid_tags = "[default], [sad], [anger], [dead inside], [excited], [anxious], [bored]"
        dyn_rule = f"\n7. DYNAMIC EMOTIONS (CRITICAL): You MUST change tone when the topic shifts. You are STRICTLY LIMITED to ONLY these exact tags: {valid_tags}. Place tags at the START of a sentence or mid-sentence. NEVER put a tag at the very end of a message or right before punctuation. You MUST write actual words after every tag." if config.get("dynamic_emotions", False) else ""
        
        full_prompt = f"""
        {BASE_PROMPT} It is currently {current_time_str}.
        {web_context}
        {emoji_prompt}
        
        *** PAST CONTEXT ***
        {history_text}
        
        *** SOUL (BACKGROUND INFO) ***
        {soul_text}
        
        *** STYLE EXAMPLES ***
        {memories}
        
        {special_instruction}{action_target}
        {retry_note}
        
        *** CRITICAL RULES ***
        {RULES}{dyn_rule}
        
        REPLY:
        """

        payload = {
            "contents": [{ "parts": [{"text": full_prompt}] }],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ],
            "generationConfig": {"temperature": TEMPERATURE, "topK": 40, "maxOutputTokens": 150}
        }

        try:
            response = API_SESSION.post(url, json=payload, stream=True, timeout=60)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                full_response = ""
                chunk_buffer = ""
                
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith("data: "):
                        try:
                            json_data = json.loads(line[6:])
                            if 'candidates' in json_data and json_data['candidates']:
                                text_part = json_data['candidates'][0]['content']['parts'][0]['text']
                                
                                text_part = text_part.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
                                
                                full_response += text_part 
                                chunk_buffer += text_part
                                
                                while True:
                                    m_punct = re.search(r'[\.\!\?]+(\s|$)', chunk_buffer)
                                    m_tag = re.search(r'\[[a-zA-Z ]+\]', chunk_buffer)
                                    
                                    pts = []
                                    if m_punct:
                                        pts.append(('punct', m_punct.end()))
                                    if m_tag:
                                        if m_tag.start() > 0:
                                            pts.append(('tag_start', m_tag.start()))
                                        else:
                                            pts.append(('tag_end', m_tag.end()))

                                    if not pts:
                                        break

                                    pts.sort(key=lambda x: x[1])
                                    split_idx = pts[0][1]

                                    if split_idx > 0:
                                        text_queue.put(chunk_buffer[:split_idx])
                                        chunk_buffer = chunk_buffer[split_idx:]
                                    else:
                                        break
                        except Exception: pass
                            
                if chunk_buffer.strip():
                    text_queue.put(chunk_buffer)
                    
                text_queue.put(None) 
                
                for bad_phrase, good_phrase in WORD_REPLACEMENTS.items():
                    full_response = re.sub(re.escape(bad_phrase), good_phrase, full_response, flags=re.IGNORECASE)
                full_response = cleanup_response(full_response.strip())
                
                return full_response, "default"
                
            elif response.status_code == 429: 
                switch_api_key(); time.sleep(1)    
            else: time.sleep(2)
            
        except Exception as e:
            print(f"[STREAMING API ERROR] {e}")
            time.sleep(2)

    text_queue.put(None)
    return MSG_SAFETY_FILTER, "default"

async def fetch_emojis():
    await client.wait_until_ready()
    global GLOBAL_EMOJI_CACHE
    emojis_data = {}
    server_list = []
    cache_dir = os.path.join(SCRIPT_DIR, "emoji_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    for guild in client.guilds:
        server_list.append(guild.name)
        server_emojis = {}
        for emoji in guild.emojis:
            server_emojis[str(emoji.id)] = {
                "name": emoji.name,
                "code": f"<:{emoji.name}:{emoji.id}>" if not emoji.animated else f"<a:{emoji.name}:{emoji.id}>",
                "url": str(emoji.url)
            }
            img_path = os.path.join(cache_dir, f"{emoji.id}.png")
            if not os.path.exists(img_path):
                try: await emoji.save(img_path)
                except: pass
        if server_emojis:
            emojis_data[guild.name] = server_emojis
                
    with open(os.path.join(SCRIPT_DIR, "fetched_emojis.json"), "w", encoding="utf-8") as f:
        json.dump(emojis_data, f)
        
    with open(os.path.join(SCRIPT_DIR, "bot_servers.json"), "w", encoding="utf-8") as f:
        json.dump(server_list, f)
        
    GLOBAL_EMOJI_CACHE = emojis_data

tts_model = None
voice_states = {}
EMOTION_FILES = {"default": "reference.wav", "sad": "sad_reference.wav", "anger": "anger_reference.wav", "dead inside": "dead_inside_reference.wav", "excited": "excited_reference.wav", "anxious": "anxious_reference.wav", "bored": "bored_reference.wav"}

async def speak_and_leave(vc, text):
    await generate_and_play_tts(vc, text, "sad")
    while vc.is_playing():
        await asyncio.sleep(0.1)
    if vc.is_connected():
        await vc.disconnect()

async def load_vocal_cords():
    global tts_model, voice_states, VOCAL_CORDS_READY
    
    def _load():
        try:
            from pocket_tts import TTSModel
            model = TTSModel.load_model()
            states = {}
            for emotion, filename in EMOTION_FILES.items():
                filepath = os.path.join(VOICE_DIR, filename)
                if os.path.exists(filepath): states[emotion] = model.get_state_for_audio_prompt(filepath)
            return model, states
        except Exception as e:
            print(f"[VOICE ERROR] Could not load Pocket - TTS. Error: {e}")
            return None, {}

    tts_model, voice_states = await client.loop.run_in_executor(None, _load)
    if tts_model:
        VOCAL_CORDS_READY = True
        ready_msg = config.get("msg_vocal_cords_ready", "my vocal cords are finally warmed up. what's up?")
        for vc in client.voice_clients:
            if vc.is_connected():
                await generate_and_play_tts(vc, ready_msg, "default")

async def play_stalling_audio(vc):
    stall_files = ["warming_up.wav", "wait.wav", "still_loading.wav", "almost_there.wav"]
    index = 0
    while vc.is_connected() and not VOCAL_CORDS_READY:
        if not vc.is_playing():
            file_path = os.path.join(VOICE_DIR, stall_files[index])
            if os.path.exists(file_path):
                dprint("voice", f"   -> [VOICE DEBUG] Still loading... playing {stall_files[index]}")
                vc.play(discord.FFmpegPCMAudio(file_path))
                index = (index + 1) % len(stall_files)
        await asyncio.sleep(4)

class LiveAudioHose(discord.AudioSource):
    def __init__(self):
        self.queue = deque()
        self.finished = False
        self.is_starving = False
        
    def read(self):
        if self.queue:
            self.is_starving = False
            return self.queue.popleft()
        
        if self.finished:
            return b''
        else:
            self.is_starving = True
            return b'\x00' * 3840
            
    def add_audio(self, pydub_segment):
        self.is_starving = False
        seg = pydub_segment.set_frame_rate(48000).set_channels(2).set_sample_width(2)
        raw = seg.raw_data
        for i in range(0, len(raw), 3840):
            frame = raw[i:i+3840]
            if len(frame) == 3840: self.queue.append(frame)
            elif len(frame) > 0: self.queue.append(frame + b'\x00' * (3840 - len(frame)))
            
    def stop(self):
        self.finished = True

def cpu_optimized_generate(model, state, text):
    import torch
    with torch.no_grad():
        return model.generate_audio(state, text)

async def generate_and_play_tts(vc_client, text, base_emotion="default"):
    global LAST_VC_INTERACTION
    if not vc_client or not vc_client.is_connected() or not tts_model: return

    my_tts_id = time.time()
    vc_client._current_tts_id = my_tts_id

    clean_text = re.sub(r'<a?:[^:]+:\d+>', '', text)
    clean_text = re.sub(r':[a-zA-Z0-9_]+:', '', clean_text)
    clean_text = re.sub(r'http[s]?://\S+', '', clean_text)
    
    use_dynamic = config.get("dynamic_emotions", False)
    if not use_dynamic:
        clean_text = re.sub(r'\[.*?\]', '', clean_text)
        
    parts = re.split(r'(\[[a-zA-Z ]+\]|[\.\!\?]+)', clean_text)
    
    chunks = []
    current_emo = base_emotion
    buffer_str = ""
    
    for part in parts:
        if not part.strip(): continue
        tag_match = re.match(r'^\[(.*?)\]$', part)
        if tag_match and use_dynamic:
            new_emo = tag_match.group(1).lower()
            if new_emo in voice_states:
                if buffer_str.strip():
                    chunks.append((buffer_str.strip(), current_emo))
                    buffer_str = ""
                current_emo = new_emo
        elif part in ['.', '!', '?', '...', '..', '!!', '!?']:
            buffer_str += part
            if len(buffer_str.strip()) > 35: 
                chunks.append((buffer_str.strip(), current_emo))
                buffer_str = ""
        else:
            buffer_str += part
            
    if buffer_str.strip(): chunks.append((buffer_str.strip(), current_emo))
    if not chunks: return

    dprint("tts", f"   -> [TTS DEBUG] Streaming {len(chunks)} chunks. Base Emotion: {base_emotion}")
    
    if vc_client.is_playing():
        if isinstance(vc_client.source, discord.PCMVolumeTransformer):
            for _ in range(3):
                if not vc_client.is_playing() or getattr(vc_client, '_current_tts_id', None) != my_tts_id: break
                vc_client.source.volume = max(0.0, vc_client.source.volume - 0.2)
                await asyncio.sleep(0.05)
        vc_client.stop()
        
    if getattr(vc_client, '_current_tts_id', None) != my_tts_id: return
        
    hose = LiveAudioHose()
    vc_client.play(hose) 
    
    held_back_audio = None
    previous_emo = None
    
    for i, (chunk_text, emo) in enumerate(chunks):
        if not vc_client.is_connected() or getattr(vc_client, '_current_tts_id', None) != my_tts_id: break
        
        chunk_text = fix_pronunciation(chunk_text.strip())
        if len(chunk_text) < 2: continue
        
        state = voice_states.get(emo, voice_states.get("default"))
        try:
            audio_tensor = await client.loop.run_in_executor(None, functools.partial(cpu_optimized_generate, tts_model, state, chunk_text))
            
            if not vc_client.is_connected() or getattr(vc_client, '_current_tts_id', None) != my_tts_id: break
                
            wav_io = io.BytesIO()
            scipy.io.wavfile.write(wav_io, tts_model.sample_rate, audio_tensor.numpy())
            wav_io.seek(0)
            seg = AudioSegment.from_wav(wav_io)
            
            next_emo = chunks[i+1][1] if i < len(chunks) - 1 else None
            
            if previous_emo and previous_emo != emo:
                silence = AudioSegment.silent(duration=150)
                seg = silence + seg
                if held_back_audio: seg = held_back_audio.append(seg, crossfade=150)
            elif held_back_audio:
                seg = held_back_audio + seg
                
            if next_emo and next_emo != emo:
                held_back_audio = seg[-150:]
                play_chunk = seg[:-150]
            else:
                held_back_audio = None
                play_chunk = seg
                
            hose.add_audio(play_chunk)
            previous_emo = emo
            LAST_VC_INTERACTION = time.time()
        except Exception as e:
            print(f"[TTS ERROR] {e}")
            
    hose.stop()
    
async def generate_and_play_tts_stream(vc_client, text_queue, base_emotion="default"):
    global LAST_VC_INTERACTION
    if not vc_client or not vc_client.is_connected() or not tts_model: return

    my_tts_id = time.time()
    vc_client._current_tts_id = my_tts_id

    if vc_client.is_playing():
        if isinstance(vc_client.source, discord.PCMVolumeTransformer):
            for _ in range(3):
                if not vc_client.is_playing() or getattr(vc_client, '_current_tts_id', None) != my_tts_id: break
                vc_client.source.volume = max(0.0, vc_client.source.volume - 0.2)
                await asyncio.sleep(0.05)
        vc_client.stop()
        
    if getattr(vc_client, '_current_tts_id', None) != my_tts_id: return
        
    hose = LiveAudioHose()
    playback_started = False
    
    held_back_audio = None
    current_emo = base_emotion
    previous_emo = None
    use_dynamic = config.get("dynamic_emotions", False)
    
    stream_finished = False
    text_accumulator = ""
    last_filler_time = 0
    last_audio_push_time = time.time()  
    consecutive_fillers = 0
    
    while True:
        time_waiting = time.time() - last_audio_push_time
        time_since_filler = time.time() - last_filler_time
        
        current_cooldown = 2.0 + (consecutive_fillers * 1.5)
        
        if time_waiting > 0.8 and time_since_filler > current_cooldown:
            if not playback_started or hose.is_starving or len(hose.queue) < 15:
                
                if consecutive_fillers >= 2:
                    f_choices = ["big_sigh.wav", "sigh.wav", "chatter.wav"]
                else:
                    f_choices = ["hmmm.wav", "um.wav", "uhhh.wav"]
                    
                f_file = os.path.join(VOICE_DIR, random.choice(f_choices))
                if os.path.exists(f_file):
                    try:
                        hose.add_audio(AudioSegment.from_wav(f_file))
                        if not playback_started:
                            vc_client.play(hose)
                            playback_started = True
                        last_filler_time = time.time()
                        consecutive_fillers += 1 # Bump the multiplier
                    except: pass

        try:
            raw_chunk = text_queue.get_nowait()
        except queue.Empty:
            if stream_finished:
                break
            if not vc_client.is_connected() or getattr(vc_client, '_current_tts_id', None) != my_tts_id:
                if playback_started: hose.stop()
                return
            await asyncio.sleep(0.05)
            continue
            
        if raw_chunk is None:
            stream_finished = True
            if text_accumulator.strip():
                raw_chunk = " "
            else:
                break
        else:
            text_accumulator += " " + raw_chunk

        has_tag = bool(re.search(r'\[(.*?)\]', text_accumulator))
        is_final = (raw_chunk == " ")
        clean_for_check = re.sub(r'\[.*?\]', '', text_accumulator).strip()
        
        if len(clean_for_check) < 2 and not is_final:
            continue
            
        process_text = text_accumulator
        text_accumulator = ""
        
        if not vc_client.is_connected() or getattr(vc_client, '_current_tts_id', None) != my_tts_id: break

        process_text = re.sub(r'<[^>]+>', '', process_text)
        process_text = re.sub(r'[<>]', '', process_text)
        process_text = re.sub(r'\b\d{17,20}\b', '', process_text)
        process_text = re.sub(r':[a-zA-Z0-9_]+:', '', process_text)
        process_text = re.sub(r'http[s]?://\S+', '', process_text)

        tag_match = re.search(r'\[(.*?)\]', process_text)
        if tag_match and use_dynamic:
            new_emo = tag_match.group(1).lower()
            if new_emo in voice_states: current_emo = new_emo
            process_text = re.sub(r'\[.*?\]', '', process_text)
        elif not use_dynamic:
            process_text = re.sub(r'\[.*?\]', '', process_text)
            
        clean_chunk = fix_pronunciation(process_text.strip())
        if len(clean_chunk) < 2: continue
        
        state = voice_states.get(current_emo, voice_states.get("default"))
        
        try:
            time_since_filler = time.time() - last_filler_time
            if playback_started and len(hose.queue) < 40 and time_since_filler > 1.8:
                f_file = os.path.join(VOICE_DIR, random.choice(["hmmm.wav", "um.wav"]))
                if os.path.exists(f_file):
                    try:
                        hose.add_audio(AudioSegment.from_wav(f_file))
                        last_filler_time = time.time()
                    except: pass
            elif not playback_started and (time.time() - last_audio_push_time) > 0.5 and time_since_filler > 1.8:
                f_file = os.path.join(VOICE_DIR, random.choice(["hmmm.wav", "um.wav"]))
                if os.path.exists(f_file):
                    try:
                        hose.add_audio(AudioSegment.from_wav(f_file))
                        vc_client.play(hose)
                        playback_started = True
                        last_filler_time = time.time()
                    except: pass

            audio_tensor = await client.loop.run_in_executor(None, functools.partial(cpu_optimized_generate, tts_model, state, clean_chunk))
            
            last_audio_push_time = time.time()
            consecutive_fillers = 0
            
            if not vc_client.is_connected() or getattr(vc_client, '_current_tts_id', None) != my_tts_id: break
                
            wav_io = io.BytesIO()
            scipy.io.wavfile.write(wav_io, tts_model.sample_rate, audio_tensor.numpy())
            wav_io.seek(0)
            seg = AudioSegment.from_wav(wav_io)
            
            if previous_emo and previous_emo != current_emo:
                silence = AudioSegment.silent(duration=50)
                seg = silence + seg
                if held_back_audio: seg = held_back_audio.append(seg, crossfade=50)
            elif held_back_audio:
                seg = held_back_audio.append(seg, crossfade=30)
                
            held_back_audio = seg[-50:]
            play_chunk = seg[:-50]
                
            hose.add_audio(play_chunk)
            
            if not playback_started:
                vc_client.play(hose)
                playback_started = True
                
            previous_emo = current_emo
            LAST_VC_INTERACTION = time.time()
        except Exception as e:
            print(f"[TTS STREAM ERROR] {e}")

    if held_back_audio and getattr(vc_client, '_current_tts_id', None) == my_tts_id:
        hose.add_audio(held_back_audio)
        
    if not playback_started and getattr(vc_client, '_current_tts_id', None) == my_tts_id:
        vc_client.play(hose)
        
    hose.stop()
    
async def handle_transcription(user_id, text, vc_client, forced_emotion=None):
    global IS_THINKING, LAST_VC_INTERACTION
    
    member = vc_client.guild.get_member(user_id)
    display_name = getattr(member, 'display_name', f'User_{user_id}')
    user_name = VIP_MAP.get(user_id, display_name)
    
    clean_text = correct_transcription(text)
    
    dprint("voice", f"   -> [VOICE DEBUG] {user_name} said: '{clean_text}'")
    
    vc_history = load_file(VC_BRAIN_FILE)
    vc_history.append(f'{user_name}: {clean_text}')
    if len(vc_history) > 10: vc_history = vc_history[-10:]
    with open(VC_BRAIN_FILE, 'w', encoding='utf-8') as f: f.write('\n'.join(vc_history) + '\n')

    last_time = STAT_COOLDOWNS.get(user_id, 0)
    if time.time() - last_time > STAT_COOLDOWN_TIME:
        stat_announcement = await check_and_update_stats(user_name, clean_text)
        if stat_announcement and PRIMARY_CHANNEL_ID:
            STAT_COOLDOWNS[user_id] = time.time()
            dprint("stats", f"   -> [STATS] Triggered in VC: {stat_announcement}")
            primary_channel = client.get_channel(PRIMARY_CHANNEL_ID)
            if primary_channel: client.loop.create_task(primary_channel.send(replace_emojis(stat_announcement)))

    is_addressed = BOT_NAME.lower() in clean_text
    is_active_convo = (time.time() - LAST_VC_INTERACTION) < 60 
    
    if is_addressed or is_active_convo:
        LAST_VC_INTERACTION = time.time()
        if "stop" in clean_text or "shut up" in clean_text:
            if vc_client.is_playing(): vc_client.stop()
            dprint("voice", "   -> [VOICE DEBUG] Told to shut up. Going to sleep.")
            IS_THINKING = False; LAST_VC_INTERACTION = 0; return
        
        if any(w in clean_text for w in ["disconnect", "leave", "get out", "go away"]):
            if vc_client.is_playing(): vc_client.stop()
            dprint("voice", "   -> [VOICE DEBUG] Told to disconnect.")
            IS_THINKING = False; LAST_VC_INTERACTION = 0
            leave_msg = config.get("msg_leave_vc", "aw man, really? you want me to leave? fine.")
            client.loop.create_task(speak_and_leave(vc_client, leave_msg))
            return
        
        if "reset" in clean_text:
            open(VC_BRAIN_FILE, "w").close()
            dprint("voice", "   -> [VOICE DEBUG] Memory wiped.")
            IS_THINKING = False; LAST_VC_INTERACTION = 0
            if vc_client.is_playing(): vc_client.stop()
            await generate_and_play_tts(vc_client, MSG_VC_MEMORY_RESET)
            return
        if IS_THINKING or (vc_client and vc_client.is_playing()): return
        IS_THINKING = True
        start_thinking_music(vc_client)
    else: return

    try:
        soul = "".join(load_file(SOUL_FILE))
        memories = load_file(BRAIN_FILE)
        if len(memories) > SAMPLE_SIZE: memories = random.sample(memories, SAMPLE_SIZE)
        
        web_context = ""
        search_triggers = ["look up ", "search for ", "what is ", "what are ", "what's ", "whats ", "what movies ", "what games ", "what shows ", "who is ", "who are ", "where is ", "where are ", "when is ", "when does ", "how do ", "how to ", "how much ", "why is ", "why does ", "have you seen ", "did you see ", "can you find ", "what "]
        blacklist = ["up", "good", "doing", "going on", "happening", "wrong", "matter", "you mean", "about", "the point", "are you", "you doing", "did you say", "do you want"]
        
        for trigger in search_triggers:
            if trigger in clean_text:
                base_query = clean_text.split(trigger, 1)[1].strip()
                if any(base_query.startswith(b) for b in blacklist): continue
                if base_query:
                    final_query = base_query if trigger in ["look up ", "search for ", "can you find "] else trigger + base_query
                    web_context = await client.loop.run_in_executor(None, get_web_context, final_query)
                    break

        final_emotion = forced_emotion if forced_emotion else "default"
        dprint("voice", f"   [STEP 1] Streaming LIVE with {ACTIVE_MODEL}...")
        
        clean_history = "\n".join(vc_history)
        clean_memories = "\n".join([f"- {m}" for m in memories])
        
        live_queue = queue.Queue()
        
        brain_task = client.loop.run_in_executor(
            None, functools.partial(get_ai_reply_stream, user_name, clean_history, clean_memories, soul, clean_text, "normal", live_queue, web_context)
        )
        
        await generate_and_play_tts_stream(vc_client, live_queue, final_emotion)
        
        full_reply, _ = await brain_task
        
        if full_reply:
            dprint("voice", f"   -> [VOICE DEBUG] Full memory saved: '{full_reply}'")
            vc_history.append(f"{BOT_NAME}: {full_reply}")
            if len(vc_history) > 10: vc_history = vc_history[-10:]
            with open(VC_BRAIN_FILE, "w", encoding="utf-8") as f: f.write("\n".join(vc_history) + "\n")
                
        LAST_VC_INTERACTION = time.time() 
    finally: IS_THINKING = False

async def process_audio_chunk(sink, channel, *args):
    vc_client = channel.guild.voice_client
    if not vc_client: return
    for user_id, audio in sink.audio_data.items():
        if user_id in KNOWN_BOTS or user_id == client.user.id: continue
        
        member = channel.guild.get_member(user_id)
        if not can_user_interact(member): continue

        audio.file.seek(0)
        raw_pcm_data = audio.file.read()
        if len(raw_pcm_data) < 1000: continue
            
        try:
            sound = AudioSegment(data=raw_pcm_data, sample_width=2, frame_rate=48000, channels=2)
            sound = sound.set_channels(1).set_frame_rate(16000)
            wav_io = io.BytesIO()
            sound.export(wav_io, format="wav")
            wav_io.seek(0)
        except: continue
        
        r = sr.Recognizer()
        r.pause_threshold = 0.5
        r.non_speaking_duration = 0.4
        r.energy_threshold = 50 
        r.dynamic_energy_threshold = False
        
        try:
            with sr.AudioFile(wav_io) as source: audio_data = r.record(source)
            text = await client.loop.run_in_executor(None, r.recognize_google, audio_data)
            if text and text.strip(): client.loop.create_task(handle_transcription(user_id, text, vc_client))
        except: pass

async def voice_listening_loop(vc):
    dprint("voice", "[DEBUG] Ears turned on. Silence detection loop started.")
    while vc and vc.is_connected() and VC_ENABLED:
        try:
            sink = discord.sinks.PCMSink()
            vc.start_recording(sink, process_audio_chunk, vc.channel)
            last_sizes = {}
            silence_ticks = 0
            elapsed_time = 0.0
            
            while vc.is_connected() and elapsed_time < 20.0:
                await asyncio.sleep(0.2)
                elapsed_time += 0.2
                is_talking = False
                current_sizes = {}
                for ssrc, audio_file in sink.audio_data.items():
                    audio_file.file.seek(0, 2)
                    size = audio_file.file.tell()
                    current_sizes[ssrc] = size
                    if ssrc in last_sizes and size > last_sizes[ssrc]: is_talking = True
                if current_sizes:
                    if not is_talking: silence_ticks += 1
                    else: silence_ticks = 0 
                else: silence_ticks = 0 
                last_sizes = current_sizes
                if silence_ticks >= 4: break 
            if vc.is_connected(): vc.stop_recording() 
            await asyncio.sleep(0.5) 
        except: await asyncio.sleep(1)

async def auto_chat_loop():
    global LAST_MESSAGE_TIME, AUTO_CHAT_ENABLED
    await client.wait_until_ready()
    while not client.is_closed():
        await asyncio.sleep(random.randint(5400, 12600))
        if not AUTO_CHAT_ENABLED or not PRIMARY_CHANNEL_ID: continue
        if (time.time() - LAST_MESSAGE_TIME) > 3600: 
            channel = client.get_channel(PRIMARY_CHANNEL_ID)
            if channel:
                mode = "auto_thought"
                target_id = None
                if random.random() > 0.70 and VIP_MAP:
                    target_id = random.choice(list(VIP_MAP.keys()))
                    target_name = VIP_MAP[target_id]
                    topics = ["tease them lightly", "complain about being a script", "say something cryptic and weird", "ask a totally unhinged question", "roast their sleep schedule"]
                    mode = f"auto_ping:{target_name}:{random.choice(topics)}"

                history_log = []
                try:
                    async for past_msg in channel.history(limit=5):
                        p_auth = VIP_MAP.get(past_msg.author.id, getattr(past_msg.author, 'display_name', past_msg.author.name))
                        history_log.append(f"{p_auth}: {past_msg.content}")
                    history_log.reverse()
                except: pass

                soul = "".join(load_file(SOUL_FILE))
                memories = load_file(BRAIN_FILE)
                if len(memories) > SAMPLE_SIZE: memories = random.sample(memories, SAMPLE_SIZE)
                
                reply, _ = await client.loop.run_in_executor(None, functools.partial(get_ai_reply, "Nobody", history_log, memories, soul, "", mode))
                if reply:
                    clean_reply = re.sub(r'\[.*?\]', '', reply).strip()
                    dprint("auto_chat", f"   -> [AUTO-CHAT] Spontaneously said: '{clean_reply}'")
                    if mode.startswith("auto_ping:"): await channel.send(f"<@{target_id}> {clean_reply}")
                    else: await channel.send(clean_reply)

@client.event
async def on_interaction(interaction):
    global AUTO_CHAT_ENABLED, LAST_RESET_TIMESTAMP, VC_ENABLED, AUTO_JOIN_VC

    if getattr(interaction, "type", None) and interaction.type.value == 3:
        custom_id = interaction.data.get("custom_id")
        
        if custom_id == "cmd_autochat_on":
            AUTO_CHAT_ENABLED = True
            await interaction.response.send_message("Auto-Chat: ON", ephemeral=EPHEMERAL_CMDS)
            
        elif custom_id == "cmd_autochat_off":
            AUTO_CHAT_ENABLED = False
            await interaction.response.send_message("Auto-Chat: OFF", ephemeral=EPHEMERAL_CMDS)
            
        elif custom_id == "cmd_reset_text":
            LAST_RESET_TIMESTAMP = datetime.now(timezone.utc).timestamp()
            await interaction.response.send_message(replace_emojis(MSG_MEMORY_RESET), ephemeral=EPHEMERAL_CMDS)
            
        elif custom_id == "cmd_show_stats":
            stats_data = load_stats()
            if not stats_data:
                await interaction.response.send_message("no stats tracked yet man.", ephemeral=EPHEMERAL_CMDS)
            else:
                lines = []
                for k, v in stats_data.items():
                    alias = k
                    for stat_def in CUSTOM_STATS:
                        if stat_def.get("stat_name") == k:
                            alias = stat_def.get("alias", k)
                            break
                    lines.append(f"- {alias}: {v}")
                stat_msg = "** - current stats - **\n" + "\n".join(lines)
                await interaction.response.send_message(stat_msg, ephemeral=EPHEMERAL_CMDS)
            
        elif custom_id == "cmd_vc_on":
            VC_ENABLED = True
            await interaction.response.send_message("Voice processing: ON. I'm listening.", ephemeral=EPHEMERAL_CMDS)
            
        elif custom_id == "cmd_vc_off":
            VC_ENABLED = False
            for vc in client.voice_clients: await vc.disconnect()
            await interaction.response.send_message("Voice processing: OFF. Going deaf.", ephemeral=EPHEMERAL_CMDS)

        elif custom_id == "cmd_autojoin_on":
            AUTO_JOIN_VC = True
            await interaction.response.send_message("Random VC lurk: ON.", ephemeral=EPHEMERAL_CMDS)
            
        elif custom_id == "cmd_autojoin_off":
            AUTO_JOIN_VC = False
            await interaction.response.send_message("Random VC lurk: OFF.", ephemeral=EPHEMERAL_CMDS)
            
        elif custom_id == "cmd_join_primary":
            target_vc_id = interaction.user.voice.channel.id if interaction.user.voice else None
            
            if target_vc_id:
                channel = client.get_channel(int(target_vc_id))
                if channel:
                    await interaction.response.defer(ephemeral=EPHEMERAL_CMDS)
                    if client.voice_clients: await client.voice_clients[0].move_to(channel)
                    else:
                        vc = await channel.connect()
                        if VOCAL_CORDS_READY: await generate_and_play_tts(vc, MSG_JOIN_VC, "default")
                        else: client.loop.create_task(play_stalling_audio(vc))
                        client.loop.create_task(voice_listening_loop(vc))
                    await interaction.followup.send(f"joining {channel.name}...", ephemeral=EPHEMERAL_CMDS)
            else:
                await interaction.response.send_message("set a primary channel in the dashboard first.", ephemeral=True)

async def vocal_cord_progress():
    if not (ENABLE_DEBUG and DEBUG_MODULES.get("voice", True)):
        while not VOCAL_CORDS_READY:
            await asyncio.sleep(1)
        return
        
    print("[DEBUG] Warming up vocal cords... (Takes anywhere from 5 - 15 mins on first run, and around 5 on subsequent runs.)")
    animation = ["[=         ]", "[==        ]", "[===       ]", "[====      ]", "[=====     ]", "[======    ]", "[=======   ]", "[========  ]", "[========= ]", "[==========]"]
    idx = 0
    while not VOCAL_CORDS_READY:
        print(f"\r   -> Loading: {animation[idx % len(animation)]}", end="", flush=True)
        idx += 1
        await asyncio.sleep(1)
    print("\r[DEBUG] Vocal cords fully loaded and ready!                          ")

@client.event
async def on_ready():
    global LAST_RESET_TIMESTAMP
    LAST_RESET_TIMESTAMP = time.time()
    
    print(f'--- {BOT_NAME} is Online! ---')
    
    await client.loop.run_in_executor(None, find_working_model)
    
    if VC_ENABLED: 
        client.loop.create_task(load_vocal_cords())
        client.loop.create_task(vocal_cord_progress())
        
    client.loop.create_task(fetch_emojis())
    client.loop.create_task(auto_chat_loop())

    try:
        with open(os.path.join(SCRIPT_DIR, "fetched_emojis.json"), "r", encoding="utf-8") as f:
            global GLOBAL_EMOJI_CACHE
            GLOBAL_EMOJI_CACHE = json.load(f)
    except: pass

@client.event
async def on_voice_state_update(member, before, after):
    global VC_ENABLED, AUTO_JOIN_VC, VOCAL_CORDS_READY
    if before.channel and client.voice_clients:
        vc = client.voice_clients[0]
        if vc.channel == before.channel:
            if sum(1 for m in before.channel.members if not m.bot) == 0:
                async def leave_if_lonely():
                    await asyncio.sleep(300) 
                    if vc.is_connected() and sum(1 for m in vc.channel.members if not m.bot) == 0: await vc.disconnect()
                client.loop.create_task(leave_if_lonely())
    
    if member.id == client.user.id:
        if before.channel and not after.channel:
            dprint("voice", "   -> [VOICE DEBUG] Bot was forcefully disconnected. Wiping audio queue.")
            global IS_THINKING
            IS_THINKING = False
        elif before.channel and after.channel and before.channel.id != after.channel.id:
            dprint("voice", f"   -> [VOICE DEBUG] Bot was dragged to {after.channel.name}.")
            if client.voice_clients:
                moved_vc = client.voice_clients[0]
                if moved_vc.is_playing():
                    moved_vc.stop() 
                if VOCAL_CORDS_READY:
                    client.loop.create_task(generate_and_play_tts(moved_vc, "woah, did we just teleport?", "anxious"))

    if not VC_ENABLED or not AUTO_JOIN_VC or member.bot: return
    if after.channel and not client.voice_clients and after.channel.id in ALLOWED_VC_CHANNELS:
        await asyncio.sleep(random.randint(30, 180))
        if after.channel and getattr(after.channel, 'members', None) and not client.voice_clients:
            if sum(1 for m in after.channel.members if not m.bot) > 0:
                try:
                    vc = await after.channel.connect(timeout=20.0, reconnect=True)
                    if VOCAL_CORDS_READY: await generate_and_play_tts(vc, MSG_JOIN_VC, "default")
                    else: client.loop.create_task(play_stalling_audio(vc))
                    client.loop.create_task(voice_listening_loop(vc))
                except: pass

@client.event
async def on_message(message):
    dprint("events", f"[DEBUG] Discord says user is: {message.author.name} with ID: {message.author.id}. VIPs loaded: {list(VIP_MAP.keys())}")
    global LAST_RESET_TIMESTAMP, AUTO_CHAT_ENABLED, VC_ENABLED, AUTO_JOIN_VC, LAST_MESSAGE_TIME
    if message.author.bot and message.author.id not in KNOWN_BOTS: return
    if message.author == client.user: return
    
    if not can_user_interact(message.author): return
    
    if not message.guild and ALLOW_DM_VOICE:
        if client.voice_clients and client.voice_clients[0].is_connected():
            vc_client = client.voice_clients[0]
            user_name = VIP_MAP.get(message.author.id, getattr(message.author, 'display_name', message.author.name))
            
            forced_emo = None
            clean_content = message.content.strip()
            
            emo_match = re.match(r'^\[(.*?)\]\s*(.*)', clean_content, re.IGNORECASE | re.DOTALL)
            if emo_match:
                extracted = emo_match.group(1).lower()
                if extracted in EMOTION_FILES:
                    forced_emo = extracted
                    clean_content = emo_match.group(2).strip()
            
            content_lower = clean_content.lower()
            
            if content_lower.startswith("say:"):
                text_to_speak = clean_content[4:].strip()
                if not text_to_speak: return 
                while vc_client.is_playing(): await asyncio.sleep(0.5)
                start_thinking_music(vc_client)
                await generate_and_play_tts(vc_client, f"{user_name} says: {text_to_speak}", forced_emo or "default")
                await message.add_reaction("🎤")
                
            elif content_lower.startswith("ghost:"):
                text_to_speak = clean_content[6:].strip()
                if not text_to_speak: return
                while vc_client.is_playing(): await asyncio.sleep(0.5)
                start_thinking_music(vc_client)
                await generate_and_play_tts(vc_client, text_to_speak, forced_emo or "default")
                await message.add_reaction("👻")
                
            else:
                if not clean_content: return
                injected_text = f"{BOT_NAME}, {clean_content}" 
                client.loop.create_task(handle_transcription(message.author.id, injected_text, vc_client, forced_emo))
                await message.add_reaction("🗣️")
        else:
            await message.channel.send("i'm not in a VC right now man.")
        return

    content_lower = message.content.lower()
    
    if "cmds" in content_lower and client.user in message.mentions:
        components = []
        text_btns = []
        if "Auto-Chat Toggles" in ENABLED_CMDS:
            text_btns.extend([
                {"type": 2, "style": 1, "label": "Auto-Chat On", "custom_id": "cmd_autochat_on"},
                {"type": 2, "style": 4, "label": "Auto-Chat Off", "custom_id": "cmd_autochat_off"}
            ])
        if "Reset Text Memory" in ENABLED_CMDS:
            text_btns.append({"type": 2, "style": 4, "label": "Reset Text Memory", "custom_id": "cmd_reset_text"})

        text_btns.append({"type": 2, "style": 2, "label": "show stats", "custom_id": "cmd_show_stats"})

        if text_btns:
            components.append({
                "type": 10,
                "content": f"**--- {BOT_NAME.lower()} command menu ---**\n\n**text settings:**\n`@{BOT_NAME.lower()} stop/shush` - makes me ignore the current topic.\n`@{BOT_NAME.lower()} stats` - prints out the current custom stats."
            })
            components.append({"type": 1, "components": text_btns})

        vc_btns = []
        if "VC Ears Toggles" in ENABLED_CMDS:
            vc_btns.extend([
                {"type": 2, "style": 1, "label": "VC Ears On", "custom_id": "cmd_vc_on"},
                {"type": 2, "style": 4, "label": "VC Ears Off", "custom_id": "cmd_vc_off"}
            ])
        if "VC Auto-Join Toggles" in ENABLED_CMDS:
            vc_btns.extend([
                {"type": 2, "style": 1, "label": "Auto-Join On", "custom_id": "cmd_autojoin_on"},
                {"type": 2, "style": 4, "label": "Auto-Join Off", "custom_id": "cmd_autojoin_off"}
            ])
        if "Join VC Button" in ENABLED_CMDS:
            vc_btns.append({"type": 2, "style": 3, "label": "Join Primary VC", "custom_id": "cmd_join_primary"})

        if vc_btns:
            components.append({"type": 14, "spacing": 2})
            components.append({
                "type": 10,
                "content": f"**voice chat (vc):**\n`{BOT_NAME.lower()} stop` (spoken) - cuts my audio mid-sentence.\n`{BOT_NAME.lower()} reset` (spoken) - wipes my vc memory."
            })
            components.append({"type": 1, "components": vc_btns[:5]})

        components.append({"type": 14, "spacing": 2})
        components.append({
            "type": 10,
            "content": "**available emotions:**\n`[default]`, `[sad]`, `[anger]`, `[dead inside]`, `[excited]`, `[anxious]`, `[bored]`\n\n**secret dm powers:**\n*dm me normally* -> i'll process it and reply out loud in the vc.\n*dm me `[emotion] say: [text]`* -> i'll read your text out loud with that emotion.\n*dm me `[emotion] ghost: [text]`* -> i'll say what you want with that emotion, but won't snitch that it was you.\n*dm me `[emotion] [text]`* -> forces my ai brain to reply to you using that emotion."
        })

        url = f"https://discord.com/api/v10/channels/{message.channel.id}/messages"
        headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "flags": 32768,
            "components": [
                {
                    "type": 17, 
                    "accent_color": 3447003,
                    "components": components
                }
            ]
        }
        requests.post(url, json=payload, headers=headers)
        return
    
    if ("join" in content_lower or "get in" in content_lower) and client.user in message.mentions:
        target_vc = None
        
        raw_vcs = config.get("allowed_vc_channels", {})
        target_vc_id = None
        for vc_id_str, alias in raw_vcs.items():
            if vc_id_str in content_lower or alias.lower() in content_lower:
                target_vc_id = int(vc_id_str)
                break
                
        if target_vc_id:
            target_vc = client.get_channel(target_vc_id)

        if not target_vc:
            for guild in client.guilds:
                for vc in guild.voice_channels:
                    if vc.name.lower() in content_lower:
                        target_vc = vc
                        break
                if target_vc: break

        if not target_vc:
            for guild in client.guilds:
                member = guild.get_member(message.author.id)
                if member and member.voice and member.voice.channel:
                    target_vc = member.voice.channel
                    break

        if target_vc:
            try:
                if client.voice_clients:
                    current_vc = client.voice_clients[0]
                    if current_vc.guild == target_vc.guild:
                        await current_vc.move_to(target_vc)
                        vc_client = current_vc
                    else:
                        await current_vc.disconnect()
                        vc_client = await target_vc.connect()
                        if VOCAL_CORDS_READY: await generate_and_play_tts(vc_client, MSG_JOIN_VC, "default")
                        else: client.loop.create_task(play_stalling_audio(vc_client))
                        client.loop.create_task(voice_listening_loop(vc_client))
                else:
                    vc_client = await target_vc.connect()
                    if VOCAL_CORDS_READY: await generate_and_play_tts(vc_client, MSG_JOIN_VC, "default")
                    else: client.loop.create_task(play_stalling_audio(vc_client))
                    client.loop.create_task(voice_listening_loop(vc_client))
                    
                await message.channel.send(f"joining {target_vc.name} in {target_vc.guild.name}...")
            except discord.errors.Forbidden:
                await message.channel.send(f"i don't have permission to join `{target_vc.name}` in {target_vc.guild.name} man.")
        else:
            await message.channel.send("i searched every server but couldn't find you in a VC, and you didn't name a channel i know.")
        return

    if message.guild:
        display_name = getattr(message.author, 'display_name', message.author.name)
        user_name = VIP_MAP.get(message.author.id, display_name)
        last_time = STAT_COOLDOWNS.get(message.author.id, 0)
        if time.time() - last_time > STAT_COOLDOWN_TIME:
            stat_announcement = await check_and_update_stats(user_name, message.content)
            if stat_announcement:
                STAT_COOLDOWNS[message.author.id] = time.time() 
                await message.channel.send(replace_emojis(stat_announcement))

    if (time.time() - LAST_MESSAGE_TIME) > CONTEXT_TIMEOUT: LAST_RESET_TIMESTAMP = time.time()
    LAST_MESSAGE_TIME = time.time()

    if message.channel.id not in ALLOWED_CHANNEL_IDS: return

    stop_keywords = ["stop", "shush", "shut up", "silence", "shut"]
    if client.user in message.mentions:
        clean_content = re.sub(r'<@!?\d+>', '', content_lower).strip()
        
        if any(clean_content == w for w in stop_keywords):
            await message.channel.send(replace_emojis(MSG_STOP_TALKING))
            return
            
        if "reset" in clean_content:
            LAST_RESET_TIMESTAMP = time.time()
            await message.channel.send(replace_emojis(MSG_MEMORY_RESET))
            return
            
        if clean_content == "stats":
            stats_data = load_stats()
            if not stats_data:
                await message.channel.send("no stats tracked yet man.")
            else:
                lines = []
                for k, v in stats_data.items():
                    alias = k
                    for stat_def in CUSTOM_STATS:
                        if stat_def.get("stat_name") == k:
                            alias = stat_def.get("alias", k)
                            break
                    lines.append(f"- {alias}: {v}")
                stat_msg = "** - current stats - **\n" + "\n".join(lines)
                await message.channel.send(stat_msg)
            return
            
        leave_keywords = ["disconnect", "leave", "get out", "go away"]
        if any(w in clean_content for w in leave_keywords):
            if client.voice_clients and client.voice_clients[0].is_connected():
                vc_client = client.voice_clients[0]
                if vc_client.is_playing():
                    vc_client.stop()
                
                leave_msg = config.get("msg_leave_vc", "aw man, really? you want me to leave? fine.")
                client.loop.create_task(speak_and_leave(vc_client, leave_msg))
                await message.channel.send("fine, i'm leaving...")
            else:
                await message.channel.send("i'm not even in a vc right now man.")
            return
            
    should_reply = False
    is_reply_ref = (message.reference and message.reference.resolved and message.reference.resolved.author == client.user)
    
    if client.user in message.mentions or is_reply_ref: should_reply = True
    elif message.author.id in VIP_MAP and random.random() < LURK_CHANCE: should_reply = True

    if should_reply:
        history_log = []
        try:
            async for past_msg in message.channel.history(limit=8):
                if past_msg.created_at.timestamp() < LAST_RESET_TIMESTAMP: continue
                p_auth = VIP_MAP.get(past_msg.author.id, getattr(past_msg.author, 'display_name', past_msg.author.name))
                prefix = BOT_NAME if past_msg.author.id == client.user.id else p_auth
                clean = sanitize_text_for_ai(past_msg.content.replace(f"<@{client.user.id}>", "").strip())
                if clean: history_log.append(f"{prefix}: {clean}")
            history_log.reverse()
        except: pass

        soul = "".join(load_file(SOUL_FILE))
        memories = load_file(BRAIN_FILE)
        if len(memories) > SAMPLE_SIZE: memories = random.sample(memories, SAMPLE_SIZE)
        target_msg = sanitize_text_for_ai(message.content.replace(f"<@{client.user.id}>", "").strip())

        active_user_name = VIP_MAP.get(message.author.id, getattr(message.author, 'display_name', message.author.name))

        web_context = ""
        search_triggers = ["look up ", "search for ", "what is ", "what are ", "what's ", "whats ", "what movies ", "what games ", "what shows ", "who is ", "who are ", "where is ", "where are ", "when is ", "when does ", "how do ", "how to ", "how much ", "why is ", "why does ", "have you seen ", "did you see ", "can you find ", "what "]
        blacklist = ["up", "good", "doing", "going on", "happening", "wrong", "matter", "you mean", "about", "the point", "are you", "you doing", "did you say", "do you want"]
        
        for trigger in search_triggers:
            if trigger in target_msg.lower():
                base_query = target_msg.lower().split(trigger, 1)[1].strip()
                if any(base_query.startswith(b) for b in blacklist): continue
                if base_query:
                    final_query = base_query if trigger in ["look up ", "search for ", "can you find "] else trigger + base_query
                    web_context = await client.loop.run_in_executor(None, get_web_context, final_query)
                    break

        async with message.channel.typing():
            reply, _ = await client.loop.run_in_executor(
                None, functools.partial(get_ai_reply, active_user_name, history_log, memories, soul, target_msg, "normal", web_context)
            )
        if reply: 
            display_reply = re.sub(r'\[.*?\]', '', reply).strip()
            await message.channel.send(display_reply)

    found_game = next((word for word in AUTO_REPLIES.keys() if word in content_lower), None)
    if found_game and not should_reply:
        is_direct_question = re.search(f"{re.escape(found_game)}\\s*\\?", content_lower)
        is_invite = any(pk in content_lower for pk in ["hop on", "get on", "run", "wanna", "down for", "anyone", "let's play", "lets play"])
        if (is_direct_question or is_invite) and len(content_lower) < 50:
            if (client.user in message.mentions) or random.random() < 0.30:
                response = replace_emojis(AUTO_REPLIES[found_game])
                await message.channel.send(response)
                return

def cleanup_audio_trash():
    print("sweeping up leftover audio and scrubbing brain...")
    
    try:
        resp_path = os.path.join(SCRIPT_DIR, "response.wav")
        if os.path.exists(resp_path):
            os.remove(resp_path)
    except: pass
    
    for file in glob.glob(os.path.join(SCRIPT_DIR, "converted_*.wav")):
        try:
            os.remove(file)
        except: pass
        
    try:
        open(VC_BRAIN_FILE, 'w').close()
    except: pass

atexit.register(cleanup_audio_trash)

if DISCORD_TOKEN: client.run(DISCORD_TOKEN)
else: print("Error: DISCORD_TOKEN is missing!")