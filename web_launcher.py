import os
import json
import subprocess
import sys
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')
ENV_FILE = os.path.join(SCRIPT_DIR, '.env')

def get_mtime():
    c_time = os.path.getmtime(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else 0
    e_time = os.path.getmtime(ENV_FILE) if os.path.exists(ENV_FILE) else 0
    return max(c_time, e_time)

def load_env():
    keys = {'DISCORD_TOKEN': '', 'GOOGLE_API_KEYS': '', 'HF_TOKEN': ''}
    target = ENV_FILE if os.path.exists(ENV_FILE) else os.path.join(SCRIPT_DIR, 'env')
    if os.path.exists(target):
        with open(target, 'r') as f:
            for line in f:
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k in keys: keys[k] = v
    return keys

def save_env(discord, google, hf):
    with open(ENV_FILE, 'w') as f:
        f.write(f'DISCORD_TOKEN={discord}\nGOOGLE_API_KEYS={google}\nHF_TOKEN={hf}\n')

def load_config():
    default_config = {
        'bot_name': 'DoppelBot', 'available_models': ['gemma-3-27b-it', 'gemini-2.5-flash'], 'ai_models': [],
        'profiles': {'Default': {
            'auto_chat_behaviors': 'post a brief casual observation, tease them lightly, say something cryptic, ask an unhinged question'
        }}, 'active_profile': 'Default', 'custom_stats': [], 'favorite_emojis': [],
        'emoji_toggles': {}, 'banned_inputs': [], 'removed_words': [], 'enabled_emotions': {}, 'debug_modules': {},
        'word_replacements': {}, 'voice_corrections': {}, 'tts_pronunciations': {}, 'auto_replies': {},
        'vip_map': {}, 'allowed_roles': {}, 'allowed_text_channels': {}, 'allowed_vc_channels': {}, 'enabled_commands': [],
        'enable_thinking_music': False, 'theme': 'Dark', 'ui_scaling': 1.0, 'accent_color': '#d1d1d1', 'github_repo_url': 'JackBJ27/DoppelBot'
    }
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f: config = json.load(f)
        except: pass
    
    for k, v in default_config.items():
        if k not in config: config[k] = v
    if not config.get('profiles'): config['profiles'] = {'Default': {}}
    return config

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DoppelBot Web Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=League+Spartan:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        :root, body {
            --bg-window: #181818; --bg-scroll: #242424; --bg-frame: #2B2B2B; --text-bg: #1D1D1D;
            --text-color: #FFFFFF; --text-muted: #A5B1C2; --border-color: #444444;
            --accent: #d1d1d1; --json-key: #56B6C2; --json-val: #E5C07B;
        }

        body[data-theme="Light"] {
            --bg-window: #E0E0E0; --bg-scroll: #D6D6D6; --bg-frame: #CCCCCC; --text-bg: #BDBDBD;
            --text-color: #111111; --text-muted: #333333; --border-color: #888888;
            --json-key: #005A6B; --json-val: #855500; 
        }
        
        body { 
            background-color: var(--bg-window); color: var(--text-color); 
            font-family: 'League Spartan', sans-serif; transition: background-color 0.2s, color 0.2s; 
            margin: 0; padding: 0; overflow: hidden; font-size: 15px;
        }

        .app-wrapper { width: 100vw; height: 100vh; overflow: hidden; background-color: var(--bg-window); }
        .app-container { display: flex; flex-direction: column; transform-origin: top left; transition: transform 0.2s; }
        
        .main-split { flex-grow: 1; overflow: hidden; min-height: 0; padding-bottom: 20px; }
        
        .ctk-scroll { 
            background-color: var(--bg-scroll); border-radius: 8px; padding: 20px; 
            height: 100%; overflow-y: auto; overflow-x: hidden; transition: background-color 0.2s; 
            color: var(--text-color);
        }

        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-frame); border-radius: 8px; margin: 10px 0;}
        ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 8px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent); }
        
        .ctk-frame { background-color: var(--bg-frame); border-radius: 6px; padding: 15px; margin-bottom: 15px; border: 1px solid transparent; transition: background-color 0.2s; }
        .ctk-input { background-color: var(--text-bg); color: var(--text-color); border: 1px solid var(--border-color); border-radius: 4px; padding: 8px 12px; width: 100%; transition: 0.2s; font-family: 'League Spartan', sans-serif; font-size: 15px;}
        .ctk-input:focus { outline: none; border-color: var(--accent); }
        select.ctk-input { appearance: none; background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='gray'%3e%3cpath d='M7 10l5 5 5-5z'/%3e%3c/svg%3e"); background-repeat: no-repeat; background-position: right 10px center; background-size: 16px; }
        textarea.ctk-input { resize: vertical; }
        
        .ctk-title { font-weight: 700; font-size: 1.2rem; margin-bottom: 5px; color: var(--text-color); }
        .ctk-info { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 10px; font-weight: 500;}
        
        .text-info { color: var(--json-key) !important; }
        .text-warning { color: var(--json-val) !important; }
        .text-muted { color: var(--text-muted) !important; }

        .ctk-btn { background-color: var(--accent); color: #000; border: none; padding: 8px 16px; border-radius: 4px; font-weight: 700; cursor: pointer; transition: 0.2s; font-family: 'League Spartan', sans-serif;}
        .ctk-btn:hover { opacity: 0.8; }
        .ctk-btn-start { background-color: #C0392B; color: white; }
        .ctk-btn-start:hover { background-color: #922B21; }
        .ctk-btn-save { background-color: #2FA572; color: white; }
        .ctk-btn-save:hover { background-color: #1E7A52; }
        .ctk-btn-secondary { background-color: #57606f; color: white; }
        
        .ctk-check { accent-color: var(--accent); width: 16px; height: 16px; margin-right: 8px; cursor: pointer; }
        
        .nav-pills .nav-link { color: var(--text-color); border-radius: 6px; margin-bottom: 5px; text-align: left; padding: 10px 15px; font-weight: 600; transition: background-color 0.2s, color 0.2s; }
        .nav-pills .nav-link.active { background-color: var(--bg-scroll); font-weight: 700; }
        .nav-pills .nav-link:hover:not(.active) { background-color: var(--bg-frame); }
        
        .switch { position: relative; display: inline-block; width: 40px; height: 20px; margin-right: 10px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #555; transition: .4s; border-radius: 20px; }
        .slider:before { position: absolute; content: ""; height: 14px; width: 14px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: var(--accent); }
        input:checked + .slider:before { transform: translateX(20px); }

        .security-input { -webkit-text-security: disc; }
    </style>
</head>
<body>
    <div id="app" class="app-wrapper" :style="{'--accent': config.accent_color || '#d1d1d1'}">
        <div class="app-container" :style="{ transform: 'scale(' + config.ui_scaling + ')', width: (100 / config.ui_scaling) + '%', height: (100 / config.ui_scaling) + '%' }">
            
            <div class="d-flex justify-content-between align-items-center px-4 py-3 flex-shrink-0" style="background-color: var(--bg-window);">
                <div class="d-flex align-items-center gap-3">
                    <button class="ctk-btn ctk-btn-save" @click="saveData">💾 Save All</button>
                    <span class="ctk-info mb-0">{{ syncStatus }}</span>
                </div>
                <div class="d-flex align-items-center gap-3">
                    <span class="ctk-title mb-0">UI Scale:</span>
                    <select class="ctk-input" style="width: 100px; padding: 4px;" v-model.number="config.ui_scaling">
                        <option value="0.8">80%</option>
                        <option value="0.9">90%</option>
                        <option value="1.0">100%</option>
                        <option value="1.1">110%</option>
                        <option value="1.25">125%</option>
                        <option value="1.5">150%</option>
                    </select>
                </div>
            </div>

            <div class="px-4 pb-3 flex-shrink-0">
                <button class="ctk-btn ctk-btn-start w-100 py-3 fs-4" @click="startBot">START BOT</button>
            </div>

            <div class="row px-4 m-0 main-split" v-if="!loading">
                
                <div class="col-3 col-md-2 p-0 pe-3 d-flex flex-column h-100">
                    <div class="nav flex-column nav-pills" role="tablist" aria-orientation="vertical">
                        <button class="nav-link active" data-bs-toggle="pill" data-bs-target="#tab1">General & Keys</button>
                        <button class="nav-link" data-bs-toggle="pill" data-bs-target="#tab2">Brain & Personality</button>
                        <button class="nav-link" data-bs-toggle="pill" data-bs-target="#tab3">Voice Module</button>
                        <button class="nav-link" data-bs-toggle="pill" data-bs-target="#tab4">Actions & Stats</button>
                        <button class="nav-link" data-bs-toggle="pill" data-bs-target="#tab5">Advanced Settings</button>
                        <button class="nav-link" data-bs-toggle="pill" data-bs-target="#tab6">Help & How-To</button>
                        <button class="nav-link" data-bs-toggle="pill" data-bs-target="#tab7">Accessibility</button>
                    </div>
                    
                    <div class="mt-auto mb-2 text-center text-muted" style="font-size: 0.8rem;">
                        Copyright (c) 2026 JackBJ | Licensed under GPL-3.0
                    </div>
                </div>

                <div class="col-9 col-md-10 p-0 h-100">
                    <div class="tab-content ctk-scroll">
                        
                        <div class="tab-pane fade show active" id="tab1">
                            <div class="ctk-frame mb-4" v-if="showSetup">
                                <div class="ctk-info">1. Put your Discord 'messages' folder inside the bot folder.<br>2. Click 'Mine Discord Data' and wait.<br>3. Click 'Generate Soul' and wait.</div>
                                <div class="d-flex gap-2 mt-2">
                                    <button class="ctk-btn ctk-btn-secondary" @click="runScript('mine_discord_data.py')">1. Mine Discord Data</button>
                                    <button class="ctk-btn" @click="runScript('generate_soul.py')">2. Generate Soul</button>
                                </div>
                            </div>

                            <div class="ctk-title">Step 1: Your Secret Keys</div>
                            <div class="d-flex gap-2 mb-3">
                                <button class="ctk-btn ctk-btn-start" @click="verifyKeys">Verify My Keys</button>
                            </div>
                            <div class="ctk-frame">
                                <label class="ctk-info d-block">Discord Token</label>
                                <input type="text" class="ctk-input security-input mb-3" v-model="env.DISCORD_TOKEN" placeholder="Paste Token..." autocomplete="off">
                                <label class="ctk-info d-block">Google API Key</label>
                                <input type="text" class="ctk-input security-input mb-3" v-model="env.GOOGLE_API_KEYS" placeholder="Paste Key..." autocomplete="off">
                                <label class="ctk-info d-block">Hugging Face Token</label>
                                <input type="text" class="ctk-input security-input" v-model="env.HF_TOKEN" placeholder="Paste Token..." autocomplete="off">
                            </div>

                            <div class="ctk-title mt-4">Step 2: Core Bot Settings</div>
                            <div class="ctk-frame">
                                <label class="ctk-info d-block">Bot Name</label>
                                <input type="text" class="ctk-input mb-4" v-model="activeProfileData.bot_name">
                                
                                <label class="ctk-title d-block">AI Models</label>
                                <div class="ctk-info">Check the ones you want the bot to try using.</div>
                                <div class="d-flex flex-wrap gap-4 mb-3">
                                    <label class="d-flex align-items-center" v-for="mod in config.available_models" :key="mod">
                                        <input type="checkbox" class="ctk-check" :value="mod" v-model="config.ai_models"> {{ mod }}
                                    </label>
                                </div>
                                <div class="d-flex gap-2 mb-4">
                                    <input type="text" class="ctk-input w-50" v-model="newModel" placeholder="Add Custom Model...">
                                    <button class="ctk-btn" @click="addModel">Add</button>
                                </div>

                                <label class="ctk-info d-block">Main Text Channel ID</label>
                                <input type="text" class="ctk-input" v-model="config.primary_channel_id">
                            </div>

                            <div class="d-flex gap-4 mb-4">
                                <label class="d-flex align-items-center"><label class="switch"><input type="checkbox" v-model="config.auto_chat"><span class="slider"></span></label> Allow Auto-Chat</label>
                                <label class="d-flex align-items-center"><label class="switch"><input type="checkbox" v-model="config.enable_websearch"><span class="slider"></span></label> Web Search</label>
                                <label class="d-flex align-items-center"><label class="switch"><input type="checkbox" v-model="config.enable_debug"><span class="slider"></span></label> Terminal Debug Logging</label>
                            </div>

                            <div class="mb-4">
                                <div class="ctk-title">Bot Creativity: {{ config.temperature }}</div>
                                <input type="range" class="w-100" min="0.1" max="1.5" step="0.05" v-model="config.temperature">
                            </div>

                            <div class="ctk-title mt-4">Step 3: Access Control</div>
                            <div class="ctk-frame">
                                <label class="ctk-info d-block">Who is allowed to talk to the bot?</label>
                                <select class="ctk-input mb-3" v-model="config.access_mode">
                                    <option>Friends Only (VIPs)</option><option>Role Based</option><option>Global / Everyone</option>
                                </select>
                            </div>

                            <div class="row g-3">
                                <div class="col-6">
                                    <div class="ctk-title">Allowed Roles</div>
                                    <textarea class="ctk-input" rows="4" :value="dictToStr(config.allowed_roles)" @input="config.allowed_roles = strToDict($event.target.value)"></textarea>
                                </div>
                                <div class="col-6">
                                    <div class="ctk-title">Friends List</div>
                                    <textarea class="ctk-input" rows="4" :value="dictToStr(config.vip_map)" @input="config.vip_map = strToDict($event.target.value)"></textarea>
                                </div>
                                <div class="col-6">
                                    <div class="ctk-title">Allowed Text Channels</div>
                                    <textarea class="ctk-input" rows="4" :value="dictToStr(config.allowed_text_channels)" @input="config.allowed_text_channels = strToDict($event.target.value)"></textarea>
                                </div>
                                <div class="col-6">
                                    <div class="ctk-title">Allowed Voice Channels</div>
                                    <textarea class="ctk-input" rows="4" :value="dictToStr(config.allowed_vc_channels)" @input="config.allowed_vc_channels = strToDict($event.target.value)"></textarea>
                                </div>
                            </div>
                        </div>

                        <div class="tab-pane fade" id="tab2">
                            <div class="ctk-frame d-flex gap-3 align-items-end mb-4">
                                <div class="flex-grow-1">
                                    <label class="ctk-title d-block">Active Bot Profile</label>
                                    <select class="ctk-input" v-model="config.active_profile">
                                        <option v-for="key in Object.keys(config.profiles || {})" :key="key">{{ key }}</option>
                                    </select>
                                </div>
                                <div>
                                    <button class="ctk-btn ctk-btn-secondary" @click="createProfile">Create New</button>
                                </div>
                            </div>

                            <div class="ctk-title">Base Prompt (The Identity)</div>
                            <textarea class="ctk-input mb-4" rows="3" v-model="activeProfileData.base_prompt"></textarea>

                            <div class="ctk-title">Friends Context (The Gossip)</div>
                            <textarea class="ctk-input mb-4" rows="3" v-model="activeProfileData.friends_context"></textarea>

                            <div class="ctk-title">Strict Rules (The Guardrails)</div>
                            <textarea class="ctk-input mb-3" rows="3" v-model="activeProfileData.rules"></textarea>

                            <div class="ctk-title">Auto-Chat Behaviors (Comma separated)</div>
                            <div class="ctk-info">Topics the bot will randomly bring up on its own.</div>
                            <textarea class="ctk-input mb-3" rows="2" v-model="activeProfileData.auto_chat_behaviors"></textarea>

                            <label class="d-flex align-items-center mb-4"><label class="switch"><input type="checkbox" v-model="config.force_lowercase"><span class="slider"></span></label> Force Bulletproof Lowercase</label>

                            <div class="row g-3 mb-4">
                                <div class="col-6">
                                    <div class="ctk-title">Banned Input Phrases</div>
                                    <input type="text" class="ctk-input" :value="config.banned_inputs.join(', ')" @input="config.banned_inputs = $event.target.value.split(',').map(s=>s.trim())">
                                </div>
                                <div class="col-6">
                                    <div class="ctk-title">Auto-Removed Words</div>
                                    <input type="text" class="ctk-input" :value="config.removed_words.join(', ')" @input="config.removed_words = $event.target.value.split(',').map(s=>s.trim())">
                                </div>
                                <div class="col-12">
                                    <div class="ctk-title">Word Replacements (bad = good)</div>
                                    <textarea class="ctk-input" rows="3" :value="dictToStr(config.word_replacements)" @input="config.word_replacements = strToDict($event.target.value)"></textarea>
                                </div>
                            </div>

                            <div class="ctk-title mt-4">Custom Bot Responses</div>
                            <div class="row g-3">
                                <div class="col-6"><label class="ctk-info">Memory Reset (Triggered via reset command):</label><input type="text" class="ctk-input" v-model="activeProfileData.msg_memory_reset"></div>
                                <div class="col-6"><label class="ctk-info">Safety Filter Blocked Prompt:</label><input type="text" class="ctk-input" v-model="activeProfileData.msg_safety_filter"></div>
                                <div class="col-6"><label class="ctk-info">Banned Input Detected:</label><input type="text" class="ctk-input" v-model="activeProfileData.msg_banned_input"></div>
                                <div class="col-6"><label class="ctk-info">AI Brain/Model Unreachable:</label><input type="text" class="ctk-input" v-model="activeProfileData.msg_brain_disconnected"></div>
                                <div class="col-6"><label class="ctk-info">Voice Channel Join Greeting:</label><input type="text" class="ctk-input" v-model="activeProfileData.msg_join_vc"></div>
                                <div class="col-6"><label class="ctk-info">Stop/Shush Command Acknowledged:</label><input type="text" class="ctk-input" v-model="activeProfileData.msg_stop_talking"></div>
                                <div class="col-12"><label class="ctk-info">Vocal Cords Warmed Up Greeting:</label><input type="text" class="ctk-input" v-model="activeProfileData.msg_vocal_cords_ready"></div>
                            </div>
                        </div>

                        <div class="tab-pane fade" id="tab3">
                            <div class="ctk-title">Voice Module Settings</div>
                            <div class="d-flex gap-4 mt-3 mb-4">
                                <label class="d-flex align-items-center"><label class="switch"><input type="checkbox" v-model="config.enable_voice"><span class="slider"></span></label> Enable Voice</label>
                                <label class="d-flex align-items-center"><label class="switch"><input type="checkbox" v-model="config.auto_join_vc"><span class="slider"></span></label> Auto-Join VC</label>
                                <label class="d-flex align-items-center"><label class="switch"><input type="checkbox" v-model="config.allow_dm_voice"><span class="slider"></span></label> Allow DM-to-Voice</label>
                                <label class="d-flex align-items-center"><label class="switch"><input type="checkbox" v-model="config.enable_thinking_music"><span class="slider"></span></label> Thinking Music</label>
                            </div>

                            <div class="ctk-title mt-4">Allowed Voice Emotions</div>
                            <div class="ctk-frame d-flex flex-wrap gap-4 mb-4">
                                <label class="d-flex align-items-center" v-for="emo in ['sad', 'anger', 'dead inside', 'excited', 'anxious', 'bored']" :key="emo">
                                    <input type="checkbox" class="ctk-check" v-model="config.enabled_emotions[emo]"> <span class="text-uppercase fw-bold">{{ emo }}</span>
                                </label>
                            </div>

                            <div class="row g-4">
                                <div class="col-6">
                                    <div class="ctk-title">STT Corrections (Google Heard = Meant)</div>
                                    <textarea class="ctk-input" rows="6" :value="dictToStr(config.voice_corrections)" @input="config.voice_corrections = strToDict($event.target.value)"></textarea>
                                </div>
                                <div class="col-6">
                                    <div class="ctk-title">TTS Pronunciations (AI Reads = Sounds Like)</div>
                                    <textarea class="ctk-input" rows="6" :value="dictToStr(config.tts_pronunciations)" @input="config.tts_pronunciations = strToDict($event.target.value)"></textarea>
                                </div>
                            </div>
                        </div>

                        <div class="tab-pane fade" id="tab4">
                            <div class="ctk-title">Keyword Auto-Replies</div>
                            <textarea class="ctk-input mb-4" rows="4" :value="dictToStr(config.auto_replies)" @input="config.auto_replies = strToDict($event.target.value)"></textarea>

                            <div class="ctk-title">Stat Builder</div>
                            <label class="d-flex align-items-center mt-2 mb-3"><label class="switch"><input type="checkbox" v-model="config.enable_stats"><span class="slider"></span></label> Enable Custom Stats Globally</label>

                            <div class="ctk-frame mb-4">
<div class="row g-2">
                                    <div class="col-md-4"><label class="ctk-info">Stat ID (ex: rage_quits)</label><input type="text" class="ctk-input" id="s_id"></div>
                                    <div class="col-md-4"><label class="ctk-info">Stat Alias (ex: Rage Quits)</label><input type="text" class="ctk-input" id="s_alias"></div>
                                    <div class="col-md-4"><label class="ctk-info">Target User (Must match VIP name)</label><input type="text" class="ctk-input" id="s_usr"></div>
                                    <div class="col-md-12"><label class="ctk-info">Trigger Words (Comma separated)</label><input type="text" class="ctk-input" id="s_trig"></div>
                                    <div class="col-md-12"><label class="ctk-info">Bot Output Message (Use {count})</label><input type="text" class="ctk-input mb-2" id="s_msg"></div>
                                    <div class="col-md-12"><button class="ctk-btn ctk-btn-save" @click="addStat">Add Stat to Bot</button></div>
                                </div>
                            </div>

                            <div class="ctk-title">Current Stats File (Preview Only)</div>
                            <textarea class="ctk-input text-warning" rows="8" :value="JSON.stringify(config.custom_stats, null, 2)" readonly></textarea>
                        </div>

                        <div class="tab-pane fade" id="tab5">
                            <div class="ctk-title">Terminal Debugging Modules</div>
                            <div class="ctk-frame d-flex flex-wrap gap-4 mb-4">
                                <label class="d-flex align-items-center" v-for="mod in ['voice', 'tts', 'brain', 'stats', 'auto_chat', 'events']" :key="mod">
                                    <input type="checkbox" class="ctk-check" v-model="config.debug_modules[mod]"> {{ mod.toUpperCase() }} Logs
                                </label>
                            </div>

                            <div class="ctk-title mt-4">Cloud Updater</div>
                            <div class="ctk-frame d-flex gap-2 mb-4">
                                <input type="text" class="ctk-input flex-grow-1" v-model="config.github_repo_url" placeholder="JackBJ27/DoppelBot">
                                <button class="ctk-btn ctk-btn-start" @click="fetchGithub">Fetch</button>
                                <select class="ctk-input" style="width: 150px;" v-model="gitVersion">
                                    <option v-for="v in gitVersions" :key="v">{{ v }}</option>
                                </select>
                                <button class="ctk-btn ctk-btn-save" @click="updateGithub">Update</button>
                            </div>

                            <div class="ctk-title mt-4">Raw File Editor</div>
                            <div class="ctk-frame">
                                <div class="d-flex gap-2 mb-2">
                                    <select class="ctk-input w-50" v-model="selectedFile" @change="loadFileContent">
                                        <option>config.json</option><option>bot.py</option><option>soul.txt</option>
                                        <option>bot_brain.txt</option><option>vc_history.txt</option>
                                    </select>
                                    <button class="ctk-btn ctk-btn-start ms-auto" @click="saveFileContent">SAVE RAW FILE</button>
                                </div>
                                <textarea class="ctk-input text-info" rows="15" v-model="fileContent" style="white-space: pre; overflow-wrap: normal; overflow-x: scroll;"></textarea>
                            </div>
                        </div>

                        <div class="tab-pane fade" id="tab6">
                            <div class="ctk-title mb-4 fs-3 text-uppercase border-bottom border-secondary pb-2">Welcome to the DoppelBot Guide</div>
                            
                            <div class="ctk-frame" style="font-size: 1rem; line-height: 1.6;">
                                <p class="text-muted fst-italic">This goes over a broad overview of the DoppelBot Dashboard setup.</p>

                                <h5 class="mt-4 fw-bold" :style="{ color: actualTheme === 'Light' ? '#222' : (config.accent_color || '#d1d1d1') }">Getting Discord IDs:</h5>
                                <ul style="color: inherit">
                                    <li>Open Discord. Go to <strong>User Settings</strong> (the gear icon).</li>
                                    <li>Click on <strong>'Advanced'</strong> under App Settings.</li>
                                    <li>Turn ON <strong>'Developer Mode'</strong>.</li>
                                    <li>Now, you can right-click any user, text channel, or server and click <strong>'Copy ID'</strong>.</li>
                                    <li>Paste those long numbers into the General Tab where it asks for them.</li>
                                </ul>

                                <h5 class="mt-4 fw-bold" :style="{ color: actualTheme === 'Light' ? '#222' : (config.accent_color || '#d1d1d1') }">General & Keys Tab:</h5>
                                <ul style="color: inherit">
                                    <li><strong>Tokens:</strong> These are your passwords. DO NOT SHOW OR SHARE THESE WITH ANYONE!</li>
                                    <li><strong>Channels:</strong> Map out where the bot lives. It needs to know the text channels to read, and the voice channels it's allowed to enter.</li>
                                    <li><strong>Access Control:</strong> Select who can talk to the bot. You can limit it to only people explicitly named in your Friends List, specific server Roles, or make it Global.</li>
                                </ul>

                                <h5 class="mt-4 fw-bold" :style="{ color: actualTheme === 'Light' ? '#222' : (config.accent_color || '#d1d1d1') }">Brain & Personality Tab:</h5>
                                <ul style="color: inherit">
                                    <li><strong>Base Prompt:</strong> Think of this as the bot's core identity.</li>
                                    <li><strong>Context:</strong> Explain your friend group. <em>"Jack sends funny memes about cats. Dyl carries us in Fortnite."</em></li>
                                    <li><strong>Rules:</strong> Formatting constraints. <em>Ex: "Never use capital letters."</em></li>
                                    <li><strong>Auto-Chat Behaviors:</strong> What topics the bot will randomly chat about by itself.</li>
                                </ul>

                                <h5 class="mt-4 fw-bold" :style="{ color: actualTheme === 'Light' ? '#222' : (config.accent_color || '#d1d1d1') }">Voice Module Tab:</h5>
                                <ul style="color: inherit">
                                    <li>If this is your first time using the bot, click the <strong>'Show Initial Data Mining Tools'</strong> button at the bottom of the General tab.</li>
                                    <li>Run step 1, wait for it to finish. This will take a little bit. Next, run step 2 and wait for it to finish.</li>
                                    <li>Ensure you actually recorded all voice emotion <code>.wav</code> files, or uncheck the ones you skipped.</li>
                                    <li><strong>NOTE:</strong> You can optionally add files named <code>warming_up.wav</code>, <code>wait.wav</code>, <code>still_loading.wav</code>, and <code>almost_there.wav</code> to your script folder. The bot will play these to stall for time while the AI voice boots up!</li>
                                </ul>

                                <h5 class="mt-4 fw-bold" :style="{ color: actualTheme === 'Light' ? '#222' : (config.accent_color || '#d1d1d1') }">Stats Tab:</h5>
                                <p style="color: inherit">Want the bot to publicly shame your friend every time they complain about lag? Or when they send something sus in chat? Set a custom stat for it here.</p>

                                <h5 class="mt-4 fw-bold" :style="{ color: actualTheme === 'Light' ? '#222' : (config.accent_color || '#d1d1d1') }">Starting up & Using the Bot:</h5>
                                <ul style="color: inherit">
                                    <li>Hit the giant red <strong>START BOT</strong> button. A black terminal window will open. Leave it open.</li>
                                    <li>It will take up to 5-15 minutes on first start-up and will appear frozen. <strong>IT IS NOT</strong>. It is downloading the AI model files in the background. It will alert you when it's done.</li>
                                    <li>Mention the bot in Discord and type <code>cmds</code> to spawn a secret interactive control panel inside Discord!</li>
                                </ul>

                                <hr class="border-secondary my-4">

                                <h6 class="fw-bold text-muted">CREDITS & LICENSING:</h6>
                                <ul class="text-muted" style="font-size: 0.85rem;">
                                    <li>Voice-compat module sourced from the <em>'discord-brain-rot'</em> GitHub repository. Huge shoutout to GabrielAgrela for making the voice AI cloner possible after Discord enforced E2EE!</li>
                                    <li>Font <em>'League Spartan'</em> by Matt Bailey, Tyler Finck. Licensed under the SIL Open Font License, Version 1.1.</li>
                                </ul>
                            </div>
                        </div>

                        <div class="tab-pane fade" id="tab7">
                            <div class="ctk-title mb-4">Accessibility Settings</div>
                            
                            <label class="ctk-title d-block mb-1">Theme Mode</label>
                            <select class="ctk-input w-50 mb-4" v-model="config.theme">
                                <option>Dark</option><option>Light</option><option>System</option>
                            </select>

                            <label class="ctk-title d-block mb-1">Custom Accent Color (Hex)</label>
                            <div class="d-flex gap-3 align-items-center mb-4">
                                <input type="color" v-model="config.accent_color" style="height: 40px; width: 60px; background: none; border: none; cursor: pointer;">
                                <input type="text" class="ctk-input w-25" v-model="config.accent_color">
                            </div>

                            <label class="ctk-title d-block mb-1">UI Scaling</label>
                            <select class="ctk-input w-50 mb-4" v-model.number="config.ui_scaling">
                                <option value="0.8">80%</option>
                                <option value="0.9">90%</option>
                                <option value="1.0">100%</option>
                                <option value="1.1">110%</option>
                                <option value="1.25">125%</option>
                                <option value="1.5">150%</option>
                            </select>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const { createApp } = Vue;

        createApp({
            data() {
                return {
                    isSyncing: false,
                    loading: true,
                    env: { DISCORD_TOKEN: '', GOOGLE_API_KEYS: '', HF_TOKEN: '' },
                    config: { profiles: {'Default': {}}, active_profile: 'Default', available_models: [], ai_models: [], banned_inputs: [], removed_words: [], enabled_emotions: {}, debug_modules: {}, word_replacements: {}, vip_map: {}, allowed_roles: {}, allowed_text_channels: {}, allowed_vc_channels: {}, voice_corrections: {}, tts_pronunciations: {}, auto_replies: {}, custom_stats: [], theme: 'Dark', ui_scaling: 1.0, accent_color: '#d1d1d1', enable_thinking_music: false },
                    lastMtime: 0,
                    syncStatus: "Synced",
                    saveTimeout: null,
                    showSetup: false,
                    newModel: '',
                    gitVersions: ['main'],
                    gitVersion: 'main',
                    selectedFile: 'config.json',
                    fileContent: ''
                }
            },
            computed: {
                activeProfileData() {
                    const prof = this.config.active_profile || 'Default';
                    if (!this.config.profiles[prof]) this.config.profiles[prof] = {};
                    return this.config.profiles[prof];
                },
                actualTheme() {
                    if (this.config.theme === 'System') return window.matchMedia('(prefers-color-scheme: light)').matches ? 'Light' : 'Dark';
                    return this.config.theme;
                }
            },
            watch: {
                actualTheme: {
                    immediate: true,
                    handler(val) {
                        document.body.setAttribute('data-theme', val);
                    }
                }
            },
            methods: {
                dictToStr(obj) { 
                    if(!obj) return '';
                    return Object.entries(obj).map(([k,v]) => `${k} = ${v}`).join('\\n'); 
                },
                strToDict(str) { 
                    let obj = {}; 
                    str.split('\\n').forEach(line => { 
                        if(line.includes('=')) { 
                            let parts = line.split('='); 
                            obj[parts[0].trim()] = parts.slice(1).join('=').trim(); 
                        } 
                    }); 
                    return obj; 
                },
                
                async loadData() {
                    this.isSyncing = true;
                    const res = await fetch('/api/data');
                    const data = await res.json();
                    this.env = data.env;
                    this.config = data.config;
                    this.lastMtime = data.mtime;
                    this.showSetup = data.show_setup;
                    this.loading = false;
                    if(this.selectedFile === 'config.json') this.fileContent = JSON.stringify(this.config, null, 2);
                },
                
                async saveData() {
                    this.syncStatus = "Saving...";
                    this.config.bot_name = this.activeProfileData.bot_name;
                    this.config.base_prompt = this.activeProfileData.base_prompt;
                    this.config.friends_context = this.activeProfileData.friends_context;
                    this.config.rules = this.activeProfileData.rules;
                    this.config.auto_chat_behaviors = this.activeProfileData.auto_chat_behaviors;
                    this.config.msg_memory_reset = this.activeProfileData.msg_memory_reset;
                    this.config.msg_vc_memory_reset = this.activeProfileData.msg_vc_memory_reset;
                    this.config.msg_safety_filter = this.activeProfileData.msg_safety_filter;
                    this.config.msg_banned_input = this.activeProfileData.msg_banned_input;
                    this.config.msg_brain_disconnected = this.activeProfileData.msg_brain_disconnected;
                    this.config.msg_join_vc = this.activeProfileData.msg_join_vc;
                    this.config.msg_stop_talking = this.activeProfileData.msg_stop_talking;
                    this.config.msg_vocal_cords_ready = this.activeProfileData.msg_vocal_cords_ready;
                    
                    const res = await fetch('/api/save', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ env: this.env, config: this.config })
                    });
                    
                    if (res.ok) {
                        const data = await res.json();
                        this.lastMtime = data.mtime;
                        this.syncStatus = "Saved!";
                        if(this.selectedFile === 'config.json') this.fileContent = JSON.stringify(this.config, null, 2);
                        setTimeout(() => this.syncStatus = "Synced", 2000);
                    }
                },

                async startBot() {
                    await fetch('/api/run_script', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({script: 'bot.py'}) });
                    alert('Bot terminal launched!');
                },

                async runScript(name) {
                    await fetch('/api/run_script', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({script: name}) });
                    alert(name + ' launched!');
                },

                async verifyKeys() {
                    const res = await fetch('/api/verify_keys', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(this.env) });
                    const data = await res.json();
                    alert(data.message);
                },

                addModel() {
                    if(this.newModel && !this.config.available_models.includes(this.newModel)) {
                        this.config.available_models.push(this.newModel);
                        this.newModel = '';
                        this.saveData();
                    }
                },

                createProfile() {
                    const name = prompt("Enter new profile name:");
                    if(name && !this.config.profiles[name]) {
                        this.config.profiles[name] = {
                            bot_name: 'DoppelBot',
                            base_prompt: 'You are a casual bot.',
                            friends_context: '',
                            rules: '1. EMOTION TAG: You MUST start your response with an emotion tag like [default], [sad], [anger], [dead inside], [excited], [anxious], or [bored].\\n2. NO RUTS: NEVER act exasperated every time you speak. DO NOT loop rhetorical questions. Vary your sentence structure. Do not bring up the exact same topics over and over again. Move on to new topics naturally.\\n3. COMPLIANCE: If the user tells you to pick a topic, ask a question, tell a joke, or give an answer, YOU MUST DO IT IMMEDIATELY. Do not stall or deflect.\\n4. TONE (CRITICAL): Have a spine, but REMEMBER THESE ARE YOUR FRIENDS. Do not resort to toxic insults or ad hominem attacks (like insulting their reading comprehension). Keep it playful, not hateful.\\n5. NO ECHOING: DO NOT start by repeating the user\'s words.\\n6. DYNAMIC LENGTH: Match the user\'s energy. If the user sends a short message (like "yo" or "sup"), reply with exactly 1 short, punchy sentence. If they write a long message, you can write 2 - 3 sentences. NEVER ramble just to fill space.',
                            auto_chat_behaviors: 'post a brief casual observation',
                            msg_memory_reset: 'text memory wiped.',
                            msg_vc_memory_reset: 'voice memory wiped.',
                            msg_safety_filter: 'safety filter blocked this.',
                            msg_banned_input: 'not saying that.',
                            msg_brain_disconnected: 'brain disconnected.',
                            msg_join_vc: 'hey whats up',
                            msg_stop_talking: 'my bad.',
                            msg_vocal_cords_ready: 'vocal cords ready.'
                        };
                        this.config.active_profile = name;
                        this.saveData();
                    }
                },

                addStat() {
                    const id = document.getElementById('s_id').value;
                    const alias = document.getElementById('s_alias').value;
                    const usr = document.getElementById('s_usr').value;
                    const trig = document.getElementById('s_trig').value;
                    const msg = document.getElementById('s_msg').value;
                    if(id && trig) {
                        this.config.custom_stats.push({
                            stat_name: id.trim(),
                            alias: alias.trim() || id.trim(),
                            user: usr.trim(),
                            triggers: trig.split(',').map(s=>s.trim()).filter(Boolean),
                            message: msg.trim()
                        });
                        this.saveData();
                        document.getElementById('s_id').value = '';
                        document.getElementById('s_alias').value = '';
                        document.getElementById('s_usr').value = '';
                        document.getElementById('s_trig').value = '';
                        document.getElementById('s_msg').value = '';
                        alert('Stat added!');
                    }
                },

                async fetchGithub() {
                    try {
                        const repo = this.config.github_repo_url.replace(/\/$/, '');
                        const [tags, branches] = await Promise.all([
                            fetch(`https://api.github.com/repos/${repo}/tags`).then(r=>r.json()),
                            fetch(`https://api.github.com/repos/${repo}/branches`).then(r=>r.json())
                        ]);
                        let v = [];
                        if(Array.isArray(tags)) v.push(...tags.map(t=>t.name));
                        if(Array.isArray(branches)) v.push(...branches.map(b=>b.name));
                        if(v.length) {
                            this.gitVersions = v;
                            this.gitVersion = v[0];
                            alert(`Found ${v.length} versions!`);
                        }
                    } catch(e) { alert("Failed to fetch versions."); }
                },

                async updateGithub() {
                    const res = await fetch('/api/github_update', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({repo: this.config.github_repo_url, version: this.gitVersion})
                    });
                    const data = await res.json();
                    alert(data.message);
                },

                async loadFileContent() {
                    const res = await fetch(`/api/file?name=${this.selectedFile}`);
                    const data = await res.json();
                    this.fileContent = data.content;
                },

                async saveFileContent() {
                    const res = await fetch('/api/file', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({name: this.selectedFile, content: this.fileContent})
                    });
                    const data = await res.json();
                    alert(data.message);
                    if(this.selectedFile === 'config.json') this.loadData();
                },

                poll() {
                    fetch('/api/poll')
                        .then(r => r.json())
                        .then(data => {
                            if (data.mtime > this.lastMtime && !this.isSyncing) {
                                this.loadData();
                            }
                        })
                        .catch(() => {})
                        .finally(() => { setTimeout(this.poll, 2000); });
                }
            },
            mounted() {
                this.loadData().then(() => { this.poll(); });
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/data')
def api_data():
    return jsonify({
        'env': load_env(),
        'config': load_config(),
        'mtime': get_mtime(),
        'show_setup': not (os.path.exists(os.path.join(SCRIPT_DIR, "bot_brain.txt")) and os.path.getsize(os.path.join(SCRIPT_DIR, "bot_brain.txt")) > 10)
    })

@app.route('/api/save', methods=['POST'])
def api_save():
    data = request.json
    save_env(data['env'].get('DISCORD_TOKEN',''), data['env'].get('GOOGLE_API_KEYS',''), data['env'].get('HF_TOKEN',''))
    save_config(data['config'])
    return jsonify({'success': True, 'mtime': get_mtime()})

@app.route('/api/poll')
def api_poll():
    return jsonify({'mtime': get_mtime()})

@app.route('/api/run_script', methods=['POST'])
def api_run_script():
    script = request.json.get('script')
    if sys.platform.startswith('win'):
        cmd = f'start "DoppelBot Web Terminal" cmd /k "py -3.13 {script}"'
        subprocess.Popen(cmd, shell=True)
    return jsonify({'success': True})

@app.route('/api/verify_keys', methods=['POST'])
def api_verify():
    d = request.json.get('DISCORD_TOKEN', '').strip()
    g = request.json.get('GOOGLE_API_KEYS', '').strip()
    h = request.json.get('HF_TOKEN', '').strip()
    msg = ''
    if d:
        try:
            if requests.get('https://discord.com/api/v10/users/@me', headers={'Authorization': f'Bot {d}'}, timeout=5).status_code == 200: msg += '✅ Discord Valid\\n'
            else: msg += '❌ Discord Invalid\\n'
        except: msg += '❌ Discord Unreachable\\n'
    if g:
        try:
            if requests.get(f'https://generativelanguage.googleapis.com/v1beta/models?key={g.split(",")[0].strip()}', timeout=5).status_code == 200: msg += '✅ Google Valid\\n'
            else: msg += '❌ Google Invalid\\n'
        except: msg += '❌ Google Unreachable\\n'
    if h:
        try:
            if requests.get('https://huggingface.co/api/whoami-v2', headers={'Authorization': f'Bearer {h}'}, timeout=5).status_code == 200: msg += '✅ HF Valid'
            else: msg += '❌ HF Invalid'
        except: msg += '❌ HF Unreachable'
    return jsonify({'message': msg or 'No keys provided.'})

@app.route('/api/github_update', methods=['POST'])
def api_github():
    repo = request.json.get('repo', '').strip().strip('/')
    version = request.json.get('version', 'main')
    base_url = f'https://raw.githubusercontent.com/{repo}/{version}'
    try:
        r_bot = requests.get(f'{base_url}/bot.py')
        r_launch = requests.get(f'{base_url}/launcher.py')
        if r_bot.status_code == 200 and r_launch.status_code == 200:
            with open(os.path.join(SCRIPT_DIR, 'bot.py'), 'w', encoding='utf-8') as f: f.write(r_bot.text)
            with open(os.path.join(SCRIPT_DIR, 'launcher.py'), 'w', encoding='utf-8') as f: f.write(r_launch.text)
            return jsonify({'message': 'Update successful! Restart dashboard.'})
        return jsonify({'message': 'Failed to fetch files. Check repo name.'})
    except Exception as e: return jsonify({'message': str(e)})

@app.route('/api/file', methods=['GET', 'POST'])
def handle_file():
    name = request.args.get('name') if request.method == 'GET' else request.json.get('name')
    path = os.path.join(SCRIPT_DIR, name)
    if request.method == 'GET':
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: return jsonify({'content': f.read()})
        return jsonify({'content': f'// {name} does not exist yet.'})
    else:
        with open(path, 'w', encoding='utf-8') as f: f.write(request.json.get('content', ''))
        return jsonify({'message': 'File saved!'})

if __name__ == '__main__':
    app.run(port=5000, debug=False)