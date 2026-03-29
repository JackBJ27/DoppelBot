import customtkinter as ctk
import tkinter.colorchooser as colorchooser
import tkinter.filedialog as fd
from PIL import Image
import json
import os
import subprocess
import sys
import webbrowser
import requests
import zipfile
import time
import psutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_FILE = os.path.join(SCRIPT_DIR, 'LeagueSpartan-VariableFont_wght.ttf')
if os.path.exists(FONT_FILE):
    ctk.FontManager.load_font(FONT_FILE)

APP_FONT = ('League Spartan', 14)
BOLD_FONT = ('League Spartan', 15, 'bold')
TITLE_FONT = ('League Spartan', 18, 'bold')
INFO_FONT = ('League Spartan', 13)

BG_WINDOW = ('#E0E0E0', '#181818')
BG_SCROLL = ('#D6D6D6', '#242424')
BG_FRAME = ('#CCCCCC', '#2B2B2B')
UNSELECTED_TRACK = ('#666666', '#555555')
CHECK_BORDER = ('#444444', '#888888')
TEXT_BG = ('#BDBDBD', '#1D1D1D') 

CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')
ENV_FILE = os.path.join(SCRIPT_DIR, '.env')
BRAIN_FILE = os.path.join(SCRIPT_DIR, 'bot_brain.txt')
SOUL_FILE = os.path.join(SCRIPT_DIR, 'soul.txt')
VC_FILE = os.path.join(SCRIPT_DIR, 'vc_history.txt')
BOT_SERVERS_FILE = os.path.join(SCRIPT_DIR, 'bot_servers.json')

def show_popup(title, message):
    popup = ctk.CTkToplevel()
    popup.title(title)
    popup.geometry('450x350')
    popup.attributes('-topmost', True)
    popup.grab_set()
    lbl = ctk.CTkLabel(popup, text=message, font=APP_FONT, wraplength=400, fg_color=BG_WINDOW)
    lbl.pack(pady=20, padx=20)
    btn = ctk.CTkButton(popup, text='Got it', width=100, command=popup.destroy, font=BOLD_FONT)
    btn.pack(pady=10)

def ensure_files_exist():
    for f in [BRAIN_FILE, SOUL_FILE, VC_FILE]:
        if not os.path.exists(f):
            open(f, 'w', encoding='utf-8').close()

import keyring

def load_env():
    return {
        'DISCORD_TOKEN': keyring.get_password("DoppelBot", "DISCORD_TOKEN") or '',
        'GOOGLE_API_KEYS': keyring.get_password("DoppelBot", "GOOGLE_API_KEYS") or '',
        'HF_TOKEN': keyring.get_password("DoppelBot", "HF_TOKEN") or ''
    }

def save_env(discord, google, hf):
    if discord: keyring.set_password("DoppelBot", "DISCORD_TOKEN", discord)
    if google: keyring.set_password("DoppelBot", "GOOGLE_API_KEYS", google)
    if hf: keyring.set_password("DoppelBot", "HF_TOKEN", hf)

def load_config():
    ensure_files_exist()
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
        else:
            user_config = {}
    except:
        user_config = {}

    default_config = {
        'bot_name': 'DoppelBot',
        'available_models': ['gemma-3-27b-it', 'gemma-3-12b-it', 'gemma-3-4b-it', 'gemma-3-1b-it', 'gemma-2-27b-it', 'gemma-2-9b-it', 'gemini-2.5-flash'],
        'ai_models': ['gemma-3-27b-it', 'gemma-3-12b-it', 'gemma-3-4b-it', 'gemma-3-1b-it', 'gemma-2-27b-it', 'gemma-2-9b-it', 'gemini-2.5-flash'],
        'enable_voice': True,
        'allow_dm_voice': True,
        'enable_thinking_music': False,
        'dynamic_emotions': False,
        'enable_stats': True,
        'auto_chat': True,
        'auto_join_vc': True,
        'enable_websearch': True,
        'enable_debug': True,
        'force_lowercase': True,
        'temperature': 0.85,
        'primary_channel_id': 0,
        'access_mode': 'Friends Only (VIPs)',
        'allowed_roles': {},
        'allowed_text_channels': {},
        'allowed_vc_channels': {},
        'base_prompt': 'You are DoppelBot. A casual, chill Discord bot. You talk like a normal person.',
        'friends_context': 'The people in this server are your friends.',
        'rules': '1. EMOTION TAG: You MUST start your response with an emotion tag like [default], [sad], [anger], [dead inside], [excited], [anxious], or [bored].\n2. NO RUTS: NEVER act exasperated every time you speak. DO NOT loop rhetorical questions. Vary your sentence structure. Do not bring up the exact same topics over and over again. Move on to new topics naturally.\n3. COMPLIANCE: If the user tells you to pick a topic, ask a question, tell a joke, or give an answer, YOU MUST DO IT IMMEDIATELY. Do not stall or deflect.\n4. TONE (CRITICAL): Have a spine, but REMEMBER THESE ARE YOUR FRIENDS. Do not resort to toxic insults or ad hominem attacks (like insulting their reading comprehension). Keep it playful, not hateful.\n5. NO ECHOING: DO NOT start by repeating the user\'s words.\n6. DYNAMIC LENGTH: Match the user\'s energy. If the user sends a short message (like "yo" or "sup"), reply with exactly 1 short, punchy sentence. If they write a long message, you can write 2 - 3 sentences. NEVER ramble just to fill space.',
        'auto_chat_behaviors': 'post a brief casual observation, tease them lightly, say something cryptic, ask an unhinged question',
        'msg_memory_reset': 'text memory wiped.',
        'msg_vc_memory_reset': 'voice memory wiped.',
        'msg_safety_filter': 'google safety filter says no.',
        'msg_banned_input': 'woah chill. not saying that.',
        'msg_brain_disconnected': 'brain disconnected.',
        'msg_join_vc': "hey, what's up?",
        'msg_stop_talking': 'my bad. zipping it.',
        'msg_vocal_cords_ready': "my vocal cords are finally warmed up. what's up?",
        'msg_leave_vc': 'aw man, really? you want me to leave? fine. i didnt want to be here anyways.',
        'debug_modules': {'voice': True, 'tts': True, 'brain': True, 'stats': True, 'auto_chat': True, 'events': True},
        'voice_corrections': {"gonna": "going to", "wanna": "want to"},
        'tts_pronunciations': {r"\blmao\b": "el em ay oh"},
        'vip_map': {},
        'emoji_toggles': {},
        'favorite_emojis': [],
        'removed_words': ['LMFAO', 'lmfao', 'Lol', 'LOL', 'Seriously', 'dude', 'Dude', 'so', 'So', 'yeah', 'Yeah', 'well', 'Well', 'oh', 'Oh', 'Bruh'],
        'banned_inputs': ['n-word', 'slur'],
        'word_replacements': {"you're still on about": "we are talking about", "that's... concerning": "that's crazy"},
        'auto_replies': {'fortnite': 'bad game'},
        'enabled_emotions': {'sad': True, 'anger': True, 'dead inside': True, 'excited': True, 'anxious': True, 'bored': True},
        'ephemeral_commands': False,
        'enabled_commands': ['Auto-Chat Toggles', 'Reset Text Memory', 'VC Ears Toggles', 'VC Auto-Join Toggles', 'Join VC Button'],
        'theme': 'Dark',
        'ui_scaling': 1.0,
        'accent_color': '#d1d1d1',
        'github_repo_url': 'JackBJ27/DoppelBot'
    }

    needs_save = False
    
    if 'allowed_channels' in user_config and isinstance(user_config['allowed_channels'], list):
        if 'allowed_text_channels' not in user_config or not user_config['allowed_text_channels']:
            user_config['allowed_text_channels'] = {str(x): f'Channel {x}' for x in user_config['allowed_channels']}
        del user_config['allowed_channels']
        needs_save = True

    if 'council_channel_id' in user_config:
        if not user_config.get('primary_channel_id'):
            user_config['primary_channel_id'] = user_config['council_channel_id']
        del user_config['council_channel_id']
        needs_save = True

    for key, value in default_config.items():
        if key not in user_config:
            user_config[key] = value
            needs_save = True

    if 'profiles' not in user_config or not user_config['profiles']:
        user_config['profiles'] = {
            'Default': {
                'bot_name': user_config.get('bot_name', 'DoppelBot'),
                'base_prompt': user_config.get('base_prompt', ''),
                'friends_context': user_config.get('friends_context', ''),
                'rules': user_config.get('rules', ''),
                'auto_chat_behaviors': user_config.get('auto_chat_behaviors', 'post a brief casual observation, tease them lightly, say something cryptic, ask an unhinged question'),
                'msg_memory_reset': user_config.get('msg_memory_reset', 'text memory wiped.'),
                'msg_vc_memory_reset': user_config.get('msg_vc_memory_reset', 'voice memory wiped.'),
                'msg_safety_filter': user_config.get('msg_safety_filter', 'google safety filter says no.'),
                'msg_banned_input': user_config.get('msg_banned_input', 'woah chill. not saying that.'),
                'msg_brain_disconnected': user_config.get('msg_brain_disconnected', 'brain disconnected.'),
                'msg_join_vc': user_config.get('msg_join_vc', "hey, what's up?"),
                'msg_stop_talking': user_config.get('msg_stop_talking', 'my bad. zipping it.'),
                'msg_vocal_cords_ready': user_config.get('msg_vocal_cords_ready', "my vocal cords are finally warmed up. what's up?"),
                'msg_leave_vc': user_config.get('msg_leave_vc', 'aw man, really? you want me to leave? fine. i didnt want to be here anyways.')
            }
        }
        user_config['active_profile'] = 'Default'
        needs_save = True

    if needs_save:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(user_config, f, indent=2)

    return user_config

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def run_script(script_name):
    if not os.path.exists(os.path.join(SCRIPT_DIR, script_name)):
        show_popup('Error', f'Could not find {script_name}!')
        return

    if script_name == 'bot.py':
        for p in psutil.process_iter(['name', 'cmdline']):
            try:
                if p.info['cmdline'] and any('bot.py' in arg for arg in p.info['cmdline']):
                    name = p.info['name'].lower()
                    if 'python' in name or 'py.exe' in name or 'py' in name:
                        show_popup('Notice', 'The bot is already running! Check your taskbar for the open terminal window.')
                        return
            except: pass

    if sys.platform.startswith('win'):
        cmd_chain = f'py -3.13 -c "import dotenv" 2>nul || py -3.13 -m pip install -q -r requirements.txt & py -3.13 {script_name}'
        subprocess.Popen(f'start "DoppelBot Terminal" cmd /k "{cmd_chain}"', shell=True)

def generate_adaptive_color(hex_color):
    hex_color = hex_color.lstrip('#')
    try:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        lr = int(max(0, r * 0.55))
        lg = int(max(0, g * 0.55))
        lb = int(max(0, b * 0.55))
        light_variant = f'#{lr:02x}{lg:02x}{lb:02x}'
        return (light_variant, f'#{hex_color}')
    except:
        return ('#555555', '#d1d1d1')

def get_contrasting_text_color(adaptive_color):
    try:
        light_hex = adaptive_color[0].lstrip('#')
        dark_hex = adaptive_color[1].lstrip('#')
        
        lr, lg, lb = tuple(int(light_hex[i:i+2], 16) for i in (0, 2, 4))
        l_lum = (0.299 * lr + 0.587 * lg + 0.114 * lb) / 255
        text_for_light = 'black' if l_lum > 0.4 else 'white'
        
        dr, dg, db = tuple(int(dark_hex[i:i+2], 16) for i in (0, 2, 4))
        d_lum = (0.299 * dr + 0.587 * dg + 0.114 * db) / 255
        text_for_dark = 'black' if d_lum > 0.5 else 'white'
        
        return (text_for_light, text_for_dark)
    except:
        return ('black', 'white')

ctk.set_default_color_theme('blue')

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.config_data = load_config()
        self.keys_data = load_env()
        
        self.history = [json.loads(json.dumps(self.config_data))]
        self.history_idx = 0
        self.last_saved_state = json.dumps(self.config_data, sort_keys=True)
        self.is_reloading = False
        self.smart_textboxes = []
        
        self._momentum_active = False
        self._last_scroll_time = 0
        
        ctk.set_appearance_mode(self.config_data.get('theme', 'Dark'))
        ctk.set_widget_scaling(self.config_data.get('ui_scaling', 1.0))
        
        self.title('DoppelBot Dashboard')
        self.geometry('1050x850')

        self.save_btns = []
        self.start_btns = []
        self.switches = []
        self.sliders = []
        self.option_menus = []
        self._scale_job = None
        self._srv_refresh_job = None

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill='both', expand=True)

        self.tab_general = self.tabview.add('General & Keys')
        self.tab_brain = self.tabview.add('Brain & Personality')
        self.tab_voice = self.tabview.add('Voice Module')
        self.tab_stats = self.tabview.add('Actions & Stats')
        self.tab_advanced = self.tabview.add('Advanced Settings')
        self.tab_howto = self.tabview.add('Help & How-To')
        self.tab_accessibility = self.tabview.add('Accessibility')

        self.build_general_tab()
        self.build_brain_tab()
        self.build_voice_tab()
        self.build_stats_tab()
        self.build_advanced_tab()
        self.build_howto_tab()
        self.build_accessibility_tab()

        self.build_controls()
        
        self.update_undo_redo_buttons()
        self.auto_save_loop()
        self.bot_status_loop()
        self.reload_ui_from_config()
        self.after(3000, self.check_for_updates)

    def make_smart_textbox(self, textbox):
        self.smart_textboxes.append(textbox)
        textbox._user_resized = False
        
        def _on_mousewheel(event, is_up=None):
            if sys.platform.startswith('win'): is_up = event.delta > 0
            else: is_up = (event.num == 4)
            
            now = time.time()
            if self._momentum_active and (now - self._last_scroll_time < 0.4):
                self._last_scroll_time = now
                return 
                
            yview = textbox._textbox.yview()
            if (is_up and yview[0] <= 0.0) or (not is_up and yview[1] >= 1.0):
                self._momentum_active = True
                self._last_scroll_time = now
                return 

            self._momentum_active = False
            if sys.platform.startswith('win'):
                textbox._textbox.yview_scroll(int(-1*(event.delta/120)), "units")
            else:
                textbox._textbox.yview_scroll(-1 if is_up else 1, "units")
            return "break"
            
        if sys.platform.startswith('win'):
            textbox._textbox.bind("<MouseWheel>", _on_mousewheel)
        else:
            textbox._textbox.bind("<Button-4>", lambda e: _on_mousewheel(e, True))
            textbox._textbox.bind("<Button-5>", lambda e: _on_mousewheel(e, False))

        grip = ctk.CTkLabel(textbox, text="↘", font=("Arial", 16, "bold"), text_color="gray50", cursor="size_nw_se")
        grip.place(relx=1.0, rely=1.0, anchor="se", x=-18, y=-2)

        grip.bind("<Enter>", lambda e: grip.configure(text_color="white"))
        grip.bind("<Leave>", lambda e: grip.configure(text_color="gray50"))

        def start_resize(event):
            textbox._user_resized = True 
            grip.startY = event.y_root
            grip.startH = textbox.cget("height")

        def drag_resize(event):
            delta = event.y_root - grip.startY
            new_height = max(60, grip.startH + delta)
            textbox.configure(height=new_height)

        grip.bind("<ButtonPress-1>", start_resize)
        grip.bind("<B1-Motion>", drag_resize)

        def _auto_resize(event=None):
            if textbox._user_resized: return
            try:
                display_lines = textbox._textbox.count("1.0", "end", "displaylines")
                lines = display_lines[0] if display_lines else 1
                new_height = max(80, min(500, lines * 18 + 20))
                if textbox.cget("height") != new_height:
                    textbox.configure(height=new_height)
            except: pass

        textbox._textbox.bind("<KeyRelease>", lambda e: self.after(10, _auto_resize), add="+")
        textbox._textbox.bind("<Configure>", lambda e: self.after(10, _auto_resize), add="+")
        self.after(200, _auto_resize)

    def auto_save_loop(self):
        current_mtime = os.path.getmtime(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else 0
        if not hasattr(self, 'last_file_mtime'):
            self.last_file_mtime = current_mtime

        server_online = False
        try:
            requests.get('http://127.0.0.1:5000/api/poll', timeout=0.2)
            server_online = True
        except:
            pass

        if server_online and current_mtime > self.last_file_mtime:
            self.is_reloading = True
            self.reload_ui_from_config()
            self.last_file_mtime = current_mtime
            self.lbl_autosave_status.configure(text=f"Live Web Sync: {time.strftime('%I:%M:%S %p')}")
            self.is_reloading = False
        elif not self.is_reloading:
            self.save_all_silent()
            self.last_file_mtime = os.path.getmtime(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else 0

        self.after(5000, self.auto_save_loop)

    def bot_status_loop(self):
        is_running = False
        for p in psutil.process_iter(['name', 'cmdline']):
            try:
                if p.info['cmdline'] and any('bot.py' in arg for arg in p.info['cmdline']):
                    name = p.info['name'].lower()
                    if 'python' in name or 'py.exe' in name or 'py' in name:
                        is_running = True
                        break
            except: pass

        if hasattr(self, 'btn_start_bot'):
            if is_running:
                self.btn_start_bot.configure(text='BOT IS RUNNING (TERMINAL OPEN)', fg_color='#2FA572', hover_color='#1E7A52')
                self._was_running = True
            else:
                self.btn_start_bot.configure(text='START BOT')
                # If it just stopped running, reset the color back to whatever theme you have selected
                if getattr(self, '_was_running', False):
                    self._was_running = False
                    self.apply_color_profile(self.config_data.get('color_profile', 'Standard'))

        self.after(2000, self.bot_status_loop)

    def save_all_silent(self):
        try:
            save_env(self.entry_discord.get(), self.entry_google.get(), self.entry_hf.get())
            active_prof = self.config_data.get('active_profile', 'Default')
            if 'profiles' not in self.config_data:
                self.config_data['profiles'] = {}
            if active_prof not in self.config_data['profiles']:
                self.config_data['profiles'][active_prof] = {}
                
            self.config_data['profiles'][active_prof]['bot_name'] = self.entry_name.get()
            self.config_data['profiles'][active_prof]['base_prompt'] = self.text_base.get('1.0', 'end-1c')
            self.config_data['profiles'][active_prof]['friends_context'] = self.text_context.get('1.0', 'end-1c')
            self.config_data['profiles'][active_prof]['rules'] = self.text_rules.get('1.0', 'end-1c')
            self.config_data['profiles'][active_prof]['auto_chat_behaviors'] = self.text_auto_chat.get('1.0', 'end-1c')
            self.config_data['profiles'][active_prof]['msg_memory_reset'] = self.entry_msg_reset_text.get().strip()
            self.config_data['profiles'][active_prof]['msg_vc_memory_reset'] = self.entry_msg_reset_vc.get().strip()
            self.config_data['profiles'][active_prof]['msg_safety_filter'] = self.entry_msg_safety.get().strip()
            self.config_data['profiles'][active_prof]['msg_banned_input'] = self.entry_msg_banned.get().strip()
            self.config_data['profiles'][active_prof]['msg_brain_disconnected'] = self.entry_msg_brain.get().strip()
            self.config_data['profiles'][active_prof]['msg_join_vc'] = self.entry_msg_join.get().strip()
            self.config_data['profiles'][active_prof]['msg_stop_talking'] = self.entry_msg_stop.get().strip()
            self.config_data['profiles'][active_prof]['msg_vocal_cords_ready'] = self.entry_msg_vocal_ready.get().strip()
            self.config_data['profiles'][active_prof]['msg_leave_vc'] = self.entry_msg_leave_vc.get().strip()
            
            self.config_data['bot_name'] = self.entry_name.get()
            self.config_data['base_prompt'] = self.text_base.get('1.0', 'end-1c')
            self.config_data['friends_context'] = self.text_context.get('1.0', 'end-1c')
            self.config_data['rules'] = self.text_rules.get('1.0', 'end-1c')
            self.config_data['auto_chat_behaviors'] = self.text_auto_chat.get('1.0', 'end-1c')
            self.config_data['msg_memory_reset'] = self.entry_msg_reset_text.get().strip()
            self.config_data['msg_vc_memory_reset'] = self.entry_msg_reset_vc.get().strip()
            self.config_data['msg_safety_filter'] = self.entry_msg_safety.get().strip()
            self.config_data['msg_banned_input'] = self.entry_msg_banned.get().strip()
            self.config_data['msg_brain_disconnected'] = self.entry_msg_brain.get().strip()
            self.config_data['msg_join_vc'] = self.entry_msg_join.get().strip()
            self.config_data['msg_stop_talking'] = self.entry_msg_stop.get().strip()
            self.config_data['msg_vocal_cords_ready'] = self.entry_msg_vocal_ready.get().strip()
            self.config_data['msg_leave_vc'] = self.entry_msg_leave_vc.get().strip()
            
            active_mods = []
            for m, var in self.model_vars.items():
                if var.get(): active_mods.append(m)
            active_mods.sort(key=lambda x: (0 if 'gemma' in x.lower() else 1, x))
            self.config_data['ai_models'] = active_mods
            
            try: self.config_data['primary_channel_id'] = int(self.entry_main_txt.get())
            except: self.config_data['primary_channel_id'] = 0
            
            self.config_data['access_mode'] = self.access_menu.get()
            self.config_data['allowed_roles'] = self.text_to_dict(self.text_allow_roles.get('1.0', 'end-1c'))
            self.config_data['allowed_text_channels'] = self.text_to_dict(self.text_allow_txt.get('1.0', 'end-1c'))
            self.config_data['allowed_vc_channels'] = self.text_to_dict(self.text_allow_vc.get('1.0', 'end-1c'))
            
            self.config_data['auto_chat'] = self.var_autochat.get()
            self.config_data['enable_websearch'] = self.var_websearch.get()
            self.config_data['enable_debug'] = self.var_debug.get()
            self.config_data['temperature'] = float(self.slider_temp.get())
            self.config_data['ephemeral_commands'] = self.var_ephemeral.get()
            self.config_data['enabled_commands'] = [c for c, var in self.cmd_vars.items() if var.get()]

            vip_map = {}
            for line in self.text_friends.get('1.0', 'end-1c').split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    if k.strip().isdigit(): vip_map[k.strip()] = v.strip()
            self.config_data['vip_map'] = vip_map
            
            if hasattr(self, 'emoji_vars') and self.emoji_vars:
                self.config_data['emoji_toggles'] = {k: v.get() for k, v in self.emoji_vars.items()}
                
            self.config_data['force_lowercase'] = self.var_lowercase.get()
            self.config_data['banned_inputs'] = [x.strip() for x in self.entry_banned.get().split(',') if x.strip()]
            self.config_data['removed_words'] = [x.strip() for x in self.entry_removed.get().split(',') if x.strip()]
            
            reps = {}
            for line in self.text_replacements.get('1.0', 'end-1c').split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    reps[k.strip()] = v.strip()
            self.config_data['word_replacements'] = reps

            self.config_data['enable_voice'] = self.var_voice.get()
            self.config_data['auto_join_vc'] = self.var_autojoin.get()
            self.config_data['allow_dm_voice'] = self.var_dm_voice.get()
            self.config_data['enable_thinking_music'] = self.var_thinking_music.get()
            self.config_data['dynamic_emotions'] = self.var_dyn_emotions.get()
            self.config_data['enabled_emotions'] = {emo: var.get() for emo, var in self.emo_vars.items()}
            self.config_data['debug_modules'] = {mod: var.get() for mod, var in self.debug_vars.items()}
            
            stt_reps = {}
            for line in self.text_stt_corrections.get('1.0', 'end-1c').split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    stt_reps[k.strip().lower()] = v.strip().lower()
            self.config_data['voice_corrections'] = stt_reps

            tts_reps = {}
            for line in self.text_tts_pronunciations.get('1.0', 'end-1c').split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    tts_reps[k.strip()] = v.strip() 
            self.config_data['tts_pronunciations'] = tts_reps

            self.config_data['enable_stats'] = self.var_stats.get()
            replies = {}
            for line in self.text_auto_replies.get('1.0', 'end-1c').split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    replies[k.strip().lower()] = v.strip()
            self.config_data['auto_replies'] = replies

            current_state_str = json.dumps(self.config_data, sort_keys=True)
            if current_state_str != self.last_saved_state:
                save_config(self.config_data)
                self.push_history(self.config_data)
                self.last_saved_state = current_state_str
                self.lbl_autosave_status.configure(text=f"Auto-saved: {time.strftime('%I:%M:%S %p')}")
        except Exception as e:
            pass

    def push_history(self, state):
        state_copy = json.loads(json.dumps(state))
        if self.history_idx < len(self.history) - 1:
            self.history = self.history[:self.history_idx + 1]
        
        if not self.history or json.dumps(self.history[-1], sort_keys=True) != json.dumps(state_copy, sort_keys=True):
            self.history.append(state_copy)
            self.history_idx += 1
            if len(self.history) > 50:
                self.history.pop(0)
                self.history_idx -= 1
        self.update_undo_redo_buttons()

    def undo(self):
        self.save_all_silent() 
        if self.history_idx > 0:
            self.history_idx -= 1
            self.apply_history_state()

    def redo(self):
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self.apply_history_state()

    def force_sync(self):
        self.reload_ui_from_config()
        self.lbl_autosave_status.configure(text=f"Force synced: {time.strftime('%I:%M:%S %p')}")

    def apply_history_state(self):
        self.is_reloading = True
        state = self.history[self.history_idx]
        self.config_data = json.loads(json.dumps(state))
        save_config(self.config_data)
        self.last_saved_state = json.dumps(self.config_data, sort_keys=True)
        self.reload_ui_from_config()
        self.update_undo_redo_buttons()
        self.lbl_autosave_status.configure(text=f"State restored: {time.strftime('%I:%M:%S %p')}")
        self.is_reloading = False

    def update_undo_redo_buttons(self):
        if hasattr(self, 'btn_undo'):
            if self.history_idx > 0: self.btn_undo.configure(state='normal')
            else: self.btn_undo.configure(state='disabled')
            
        if hasattr(self, 'btn_redo'):
            if self.history_idx < len(self.history) - 1: self.btn_redo.configure(state='normal')
            else: self.btn_redo.configure(state='disabled')

    def add_to_textbox(self, entry_id, entry_name, textbox):
        i = entry_id.get().strip()
        n = entry_name.get().strip()
        if i and n:
            textbox.insert('end', f'{i} = {n}\n')
            entry_id.delete(0, 'end')
            entry_name.delete(0, 'end')
            self.save_all_silent()
            textbox._textbox.event_generate("<KeyRelease>")

    def toggle_vis(self, entry, btn):
        if entry.cget('show') == '*':
            entry.configure(show='')
            btn.configure(text='Hide')
        else:
            entry.configure(show='*')
            btn.configure(text='👁')

    def open_url(self, url):
        webbrowser.open(url)

    def verify_keys(self):
        discord_token = self.entry_discord.get().strip()
        google_key = self.entry_google.get().strip()
        hf_token = self.entry_hf.get().strip()
        
        msg = ''
        
        if discord_token:
            try:
                r = requests.get('https://discord.com/api/v10/users/@me', headers={'Authorization': f'Bot {discord_token}'}, timeout=5)
                if r.status_code == 200: msg += '✅ Discord Token is VALID.\n\n'
                else: msg += '❌ Discord Token is INVALID.\n\n'
            except: msg += '❌ Failed to reach Discord servers.\n\n'
        else: msg += '❌ Discord Token is MISSING.\n\n'
            
        if google_key:
            first_key = google_key.split(',')[0].strip()
            try:
                r = requests.get(f'https://generativelanguage.googleapis.com/v1beta/models?key={first_key}', timeout=5)
                if r.status_code == 200: msg += '✅ Google API Key is VALID.\n\n'
                else: msg += '❌ Google API Key is INVALID.\n\n'
            except: msg += '❌ Failed to reach Google servers.\n\n'
        else: msg += '❌ Google API Key is MISSING.\n\n'
            
        if hf_token:
            try:
                r = requests.get('https://huggingface.co/api/whoami-v2', headers={'Authorization': f'Bearer {hf_token}'}, timeout=5)
                if r.status_code == 200: msg += '✅ Hugging Face Token is VALID.\n\n'
                else: msg += '❌ Hugging Face Token is INVALID.\n\n'
            except: msg += '❌ Failed to reach Hugging Face servers.\n\n'
        else: msg += '❌ Hugging Face Token is MISSING.\n\n'

        show_popup('Key Verification', msg)

    def refresh_server_list(self):
        if hasattr(self, '_srv_refresh_job') and self._srv_refresh_job:
            self.after_cancel(self._srv_refresh_job)
            
        self.server_list_box.configure(state='normal')
        self.server_list_box.delete('1.0', 'end')
        if os.path.exists(BOT_SERVERS_FILE):
            try:
                with open(BOT_SERVERS_FILE, 'r', encoding='utf-8') as f:
                    servers = json.load(f)
                    if servers:
                        self.server_list_box.insert('1.0', 'The bot is currently active in these servers:\n\n' + '\n'.join([f'- {s}' for s in servers]))
                    else:
                        self.server_list_box.insert('1.0', 'The bot is not in any servers yet.')
            except:
                self.server_list_box.insert('1.0', 'Error loading server list.')
        else:
            self.server_list_box.insert('1.0', 'Start the bot once to fetch the server list!')
            
        self.server_list_box._textbox.event_generate("<KeyRelease>")
        self.server_list_box.configure(state='disabled')
        
        self._srv_refresh_job = self.after(5000, self.refresh_server_list)

    def refresh_model_list(self):
        for widget in self.model_list_frame.winfo_children():
            widget.destroy()
            
        self.model_vars = {}
        available = self.config_data.get('available_models', [])
        active_models = self.config_data.get('ai_models', [])
        
        for m in available:
            var = ctk.BooleanVar(value=(m in active_models))
            chk = ctk.CTkCheckBox(self.model_list_frame, text=m, variable=var, font=APP_FONT, bg_color=BG_FRAME, border_color=CHECK_BORDER)
            chk.pack(anchor='w', padx=20, pady=2)
            self.model_vars[m] = var
            self.switches.append(chk)
            
        self.apply_accent_color(self.config_data.get('accent_color', '#d1d1d1'))

    def add_custom_model(self):
        new_mod = self.entry_new_model.get().strip()
        if new_mod:
            available = self.config_data.get('available_models', [])
            if new_mod not in available:
                available.append(new_mod)
                self.config_data['available_models'] = available
                save_config(self.config_data)
                self.refresh_model_list()
                self.entry_new_model.delete(0, 'end')
                self.save_all_silent()

    def switch_profile(self, profile_name):
        self.save_all_silent() 
        self.config_data['active_profile'] = profile_name
        save_config(self.config_data)
        self.reload_ui_from_config(full_reload=False)
        
    def create_profile(self):
        new_name = self.entry_new_prof.get().strip()
        if not new_name: return
        if new_name in self.config_data.get('profiles', {}):
            show_popup('Error', 'Profile already exists!')
            return
            
        self.save_all_silent()
        
        self.config_data['profiles'][new_name] = {
            'bot_name': 'DoppelBot',
            'base_prompt': 'You are a casual, chill Discord bot.',
            'friends_context': 'The people in this server are your friends.',
            'rules': '1. EMOTION TAG: You MUST start your response with an emotion tag like [default], [sad], [anger], [dead inside], [excited], [anxious], or [bored].\n2. NO RUTS: NEVER act exasperated every time you speak. DO NOT loop rhetorical questions. Vary your sentence structure. Do not bring up the exact same topics over and over again. Move on to new topics naturally.\n3. COMPLIANCE: If the user tells you to pick a topic, ask a question, tell a joke, or give an answer, YOU MUST DO IT IMMEDIATELY. Do not stall or deflect.\n4. TONE (CRITICAL): Have a spine, but REMEMBER THESE ARE YOUR FRIENDS. Do not resort to toxic insults or ad hominem attacks (like insulting their reading comprehension). Keep it playful, not hateful.\n5. NO ECHOING: DO NOT start by repeating the user\'s words.\n6. DYNAMIC LENGTH: Match the user\'s energy. If the user sends a short message (like "yo" or "sup"), reply with exactly 1 short, punchy sentence. If they write a long message, you can write 2 - 3 sentences. NEVER ramble just to fill space.',
            'auto_chat_behaviors': 'post a brief casual observation',
            'msg_memory_reset': 'text memory wiped.',
            'msg_vc_memory_reset': 'voice memory wiped.',
            'msg_safety_filter': 'google safety filter says no.',
            'msg_banned_input': 'woah chill. not saying that.',
            'msg_brain_disconnected': 'brain disconnected.',
            'msg_join_vc': "hey, what's up?",
            'msg_stop_talking': 'my bad. zipping it.',
            'msg_vocal_cords_ready': "my vocal cords are finally warmed up. what's up?"
        }
        
        self.config_data['active_profile'] = new_name
        save_config(self.config_data)
        self.entry_new_prof.delete(0, 'end')
        self.reload_ui_from_config(full_reload=False)
        
    def delete_profile(self):
        current = self.config_data.get('active_profile')
        if current == 'Default' or len(self.config_data.get('profiles', {})) <= 1:
            show_popup('Error', 'Cannot delete the Default or last remaining profile.')
            return
            
        del self.config_data['profiles'][current]
        self.config_data['active_profile'] = list(self.config_data['profiles'].keys())[0]
        save_config(self.config_data)
        self.reload_ui_from_config(full_reload=False)

    def build_general_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_general, fg_color=BG_SCROLL)
        scroll.pack(fill='both', expand=True)
        
        self.setup_container = ctk.CTkFrame(scroll, fg_color=BG_SCROLL)
        self.setup_container.pack(fill='x', pady=(0, 10))

        self.setup_btn = ctk.CTkButton(self.setup_container, text='Show Initial Data Mining Tools (First Time Setup)', fg_color=('#D9D9D9', '#57606f'), text_color=('black', 'white'), hover_color=('#BFBFBF', '#2f3542'), font=BOLD_FONT, command=self.toggle_setup)
        self.setup_btn.pack(pady=5)

        self.setup_frame = ctk.CTkFrame(self.setup_container, fg_color=BG_FRAME)

        instructions = "1. Put your Discord 'messages' folder directly inside the bot folder.\n2. Click 'Mine Discord Data' and wait for the terminal window to close.\n3. Click 'Generate Soul' and wait for it to finish analyzing you."
        ctk.CTkLabel(self.setup_frame, text=instructions, justify='left', font=APP_FONT, fg_color=BG_FRAME).pack(pady=15, padx=20)

        btn_frame = ctk.CTkFrame(self.setup_frame, fg_color=BG_FRAME)
        btn_frame.pack(pady=10)
        mb = ctk.CTkButton(btn_frame, text='1. Mine Discord Data', font=BOLD_FONT, command=lambda: run_script('mine_discord_data.py'))
        mb.pack(side='left', padx=10)
        sb = ctk.CTkButton(btn_frame, text='2. Generate Soul', font=BOLD_FONT, command=lambda: run_script('generate_soul.py'))
        sb.pack(side='left', padx=10)
        self.save_btns.extend([mb, sb])
        
        help_text = "HOW TO GET IDs: Open Discord -> Settings -> Advanced -> Turn ON 'Developer Mode'. Then you can right-click any channel, user, or server and click 'Copy ID'."
        help_lbl = ctk.CTkLabel(scroll, text=help_text, font=INFO_FONT, text_color=('gray20', '#A5B1C2'), wraplength=900, fg_color=BG_SCROLL)
        help_lbl.pack(pady=(0, 15))

        ctk.CTkLabel(scroll, text='Step 1: Your Secret Keys', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(10, 5))
        
        btn_frame_keys = ctk.CTkFrame(scroll, fg_color=BG_SCROLL)
        btn_frame_keys.pack(pady=(0, 10))
        
        verify_btn = ctk.CTkButton(btn_frame_keys, text='Verify My Keys', font=BOLD_FONT, command=self.verify_keys)
        verify_btn.pack(side='left', padx=5)
        self.start_btns.append(verify_btn)
        

        key_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        key_frame.pack(fill='x', padx=20, pady=5)
        
        ctk.CTkLabel(key_frame, text='Discord Token (From Discord Developer Portal -> Your Bot -> Bot Tab -> Reset Token)', font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10, pady=(5,0))
        df = ctk.CTkFrame(key_frame, fg_color=BG_FRAME)
        df.pack(fill='x', padx=10, pady=(0, 10))
        self.entry_discord = ctk.CTkEntry(df, show='*', placeholder_text='Paste Discord Token here...', font=APP_FONT, fg_color=TEXT_BG)
        self.entry_discord.pack(side='left', fill='x', expand=True)
        self.btn_vis_discord = ctk.CTkButton(df, text='👁', width=45, font=APP_FONT, fg_color=('#D9D9D9', '#57606f'), text_color=('black', 'white'), hover_color=('#BFBFBF', '#2f3542'), command=lambda: self.toggle_vis(self.entry_discord, self.btn_vis_discord))
        self.btn_vis_discord.pack(side='right', padx=(5, 0))
        
        ctk.CTkLabel(key_frame, text="Google API Key (From Google AI Studio -> Create API Key. This powers the bot's brain)", font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10)
        gf = ctk.CTkFrame(key_frame, fg_color=BG_FRAME)
        gf.pack(fill='x', padx=10, pady=(0, 10))
        self.entry_google = ctk.CTkEntry(gf, show='*', placeholder_text='Paste Google Key here...', font=APP_FONT, fg_color=TEXT_BG)
        self.entry_google.pack(side='left', fill='x', expand=True)
        self.btn_vis_google = ctk.CTkButton(gf, text='👁', width=45, font=APP_FONT, fg_color=('#D9D9D9', '#57606f'), text_color=('black', 'white'), hover_color=('#BFBFBF', '#2f3542'), command=lambda: self.toggle_vis(self.entry_google, self.btn_vis_google))
        self.btn_vis_google.pack(side='right', padx=(5, 0))
        
        ctk.CTkLabel(key_frame, text="Hugging Face Token (Create an account on Hugging Face -> Settings -> Access Tokens -> 'Write' token)", font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10)
        hf = ctk.CTkFrame(key_frame, fg_color=BG_FRAME)
        hf.pack(fill='x', padx=10, pady=(0, 10))
        self.entry_hf = ctk.CTkEntry(hf, show='*', placeholder_text='Paste Hugging Face Token here...', font=APP_FONT, fg_color=TEXT_BG)
        self.entry_hf.pack(side='left', fill='x', expand=True)
        self.btn_vis_hf = ctk.CTkButton(hf, text='👁', width=45, font=APP_FONT, fg_color=('#D9D9D9', '#57606f'), text_color=('black', 'white'), hover_color=('#BFBFBF', '#2f3542'), command=lambda: self.toggle_vis(self.entry_hf, self.btn_vis_hf))
        self.btn_vis_hf.pack(side='right', padx=(5, 0))

        ctk.CTkLabel(scroll, text='Step 2: Core Bot Settings', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(20, 5))
        set_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        set_frame.pack(fill='x', padx=20, pady=5)

        ctk.CTkLabel(set_frame, text='Bot Name (What should we call this creation?)', font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10, pady=(5,0))
        self.entry_name = ctk.CTkEntry(set_frame, placeholder_text='ex: DoppelBot', font=APP_FONT, fg_color=TEXT_BG)
        self.entry_name.pack(fill='x', padx=10, pady=(0, 10))
        
        ctk.CTkLabel(set_frame, text='AI Models (Check the ones you want the bot to try using)', font=TITLE_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10, pady=(15, 0))
        model_info = "NOTE: You MUST use the exact API model-name (e.g. 'gemini-2.5-flash'), not the normal name.\n\ngemma vs gemini:\ngemini is google's flagship model. it's fast and smart, but has strict safety filters that block edgy jokes.\ngemma models are open weights. they have better rate limits for free tiers and refuse less prompts, making them great for casual banter."
        ctk.CTkLabel(set_frame, text=model_info, font=INFO_FONT, text_color=('gray20', 'gray75'), justify='left', fg_color=BG_FRAME).pack(anchor='w', padx=10, pady=(0, 5))
        
        link_frame = ctk.CTkFrame(set_frame, fg_color=BG_FRAME)
        link_frame.pack(anchor='w', padx=10, pady=(0, 10))
        l1 = ctk.CTkLabel(link_frame, text="Current Gemini Models List", text_color="#3B8ED0", font=INFO_FONT, cursor="hand2", fg_color=BG_FRAME)
        l1.pack(side='left', padx=(0, 15))
        l1.bind("<Button-1>", lambda e: self.open_url("https://ai.google.dev/gemini-api/docs/models"))
        
        l2 = ctk.CTkLabel(link_frame, text="Current Gemma Models List", text_color="#3B8ED0", font=INFO_FONT, cursor="hand2", fg_color=BG_FRAME)
        l2.pack(side='left')
        l2.bind("<Button-1>", lambda e: self.open_url("https://huggingface.co/collections/google/gemma-3-release"))
        
        self.model_list_frame = ctk.CTkFrame(set_frame, fg_color=BG_FRAME)
        self.model_list_frame.pack(fill='x', padx=10)
        
        add_mod_frame = ctk.CTkFrame(set_frame, fg_color=BG_FRAME)
        add_mod_frame.pack(fill='x', padx=10, pady=10)
        self.entry_new_model = ctk.CTkEntry(add_mod_frame, placeholder_text='ex: gemini-1.5-pro', font=APP_FONT, width=200, fg_color=TEXT_BG)
        self.entry_new_model.pack(side='left', padx=(0, 5))
        btn_add_mod = ctk.CTkButton(add_mod_frame, text='Add Custom Model', font=BOLD_FONT, command=self.add_custom_model)
        btn_add_mod.pack(side='left')
        self.save_btns.append(btn_add_mod)
        
        ctk.CTkLabel(set_frame, text='Main Text Channel ID (The primary channel where the bot is allowed to randomly auto-chat)', font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10, pady=(15,0))
        self.entry_main_txt = ctk.CTkEntry(set_frame, placeholder_text='ex: 123456789012345678', font=APP_FONT, fg_color=TEXT_BG)
        self.entry_main_txt.pack(fill='x', padx=10, pady=(0, 10))

        tog_frame = ctk.CTkFrame(scroll, fg_color=BG_SCROLL)
        tog_frame.pack(fill='x', padx=20, pady=10)
        
        self.var_autochat = ctk.BooleanVar()
        self.var_websearch = ctk.BooleanVar()
        self.var_debug = ctk.BooleanVar()
        
        chat_sw = ctk.CTkSwitch(tog_frame, text='Allow Auto-Chat (Bot will randomly talk on its own)', variable=self.var_autochat, font=APP_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        chat_sw.pack(side='left', padx=10)
        web_sw = ctk.CTkSwitch(tog_frame, text='Allow Web Search (Bot can google things if asked)', variable=self.var_websearch, font=APP_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        web_sw.pack(side='left', padx=10)
        dbg_sw = ctk.CTkSwitch(tog_frame, text='Terminal Debug Logging', variable=self.var_debug, font=APP_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        dbg_sw.pack(side='left', padx=10)
        self.switches.extend([chat_sw, web_sw, dbg_sw])

        ctk.CTkLabel(scroll, text='Bot Creativity (Left = Logical & Boring, Right = Unhinged & Creative)', font=BOLD_FONT, fg_color=BG_SCROLL).pack(pady=(15,0))
        self.slider_temp = ctk.CTkSlider(scroll, from_=0.1, to=1.5, number_of_steps=14, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        self.slider_temp.pack(fill='x', padx=40, pady=5)
        self.sliders.append(self.slider_temp)

        ctk.CTkLabel(scroll, text='Step 3: Access Control', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(20, 5))
        access_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        access_frame.pack(fill='x', padx=20, pady=5)
        
        ctk.CTkLabel(access_frame, text='Who is allowed to talk to the bot?', font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10, pady=(5,0))
        self.access_menu = ctk.CTkOptionMenu(access_frame, values=['Friends Only (VIPs)', 'Role Based', 'Global / Everyone'], font=APP_FONT)
        self.access_menu.pack(fill='x', padx=10, pady=(0, 10))
        self.option_menus.append(self.access_menu)

        def create_mapping_ui(parent, title, explanation):
            ctk.CTkLabel(parent, text=title, font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(20, 0))
            ctk.CTkLabel(parent, text=explanation, font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack()
            
            input_frame = ctk.CTkFrame(parent, fg_color=BG_FRAME)
            input_frame.pack(fill='x', padx=20, pady=5)
            
            e_id = ctk.CTkEntry(input_frame, placeholder_text='ID (ex: 123456789)', font=APP_FONT, width=200, fg_color=TEXT_BG)
            e_id.pack(side='left', padx=5)
            e_name = ctk.CTkEntry(input_frame, placeholder_text='Name (ex: General Chat)', font=APP_FONT, width=200, fg_color=TEXT_BG)
            e_name.pack(side='left', padx=5)
            
            textbox = ctk.CTkTextbox(parent, height=80, font=APP_FONT, fg_color=TEXT_BG)
            self.make_smart_textbox(textbox)
            
            add_btn = ctk.CTkButton(input_frame, text='Add to List', font=BOLD_FONT, command=lambda: self.add_to_textbox(e_id, e_name, textbox))
            add_btn.pack(side='left', padx=5)
            self.save_btns.append(add_btn)
            
            textbox.pack(fill='x', padx=20, pady=5)
            return textbox

        self.text_allow_roles = create_mapping_ui(scroll, 'Allowed Roles (For Role Based mode)', 'Add the IDs of the roles allowed to interact with the bot.')
        self.text_allow_txt = create_mapping_ui(scroll, 'Allowed Text Channels', 'Add the IDs of the text channels the bot is allowed to read and respond in.')
        self.text_allow_vc = create_mapping_ui(scroll, 'Allowed Voice Channels', 'Add the IDs of the voice channels the bot is allowed to join.')
        self.text_friends = create_mapping_ui(scroll, 'Friends List', "Add your friends' User IDs and their names so the bot knows who is talking.")

        server_header = ctk.CTkFrame(scroll, fg_color=BG_SCROLL)
        server_header.pack(fill='x', pady=(20, 5))
        ctk.CTkLabel(server_header, text='Step 4: Bot Server Presence (Read-Only)', font=TITLE_FONT, fg_color=BG_SCROLL).pack(side='left')
        
        btn_refresh_srv = ctk.CTkButton(server_header, text='Refresh Manual', font=BOLD_FONT, width=100, command=self.refresh_server_list)
        btn_refresh_srv.pack(side='right', padx=20)
        self.save_btns.append(btn_refresh_srv)

        server_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        server_frame.pack(fill='x', padx=20, pady=5)
        self.server_list_box = ctk.CTkTextbox(server_frame, height=80, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.server_list_box)
        self.server_list_box.pack(fill='x', padx=10, pady=10)
        self.refresh_server_list()

        ctk.CTkLabel(scroll, text='Step 5: Command Menu (/cmds) Settings', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(20, 5))
        cmd_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        cmd_frame.pack(fill='x', padx=20, pady=5)

        self.var_ephemeral = ctk.BooleanVar()
        e_sw = ctk.CTkSwitch(cmd_frame, text='Make Bot Responses Ephemeral (Only you can see command replies)', variable=self.var_ephemeral, font=APP_FONT, bg_color=BG_FRAME, fg_color=UNSELECTED_TRACK)
        e_sw.pack(anchor='w', padx=10, pady=10)
        self.switches.append(e_sw)

        ctk.CTkLabel(cmd_frame, text='Visible Buttons in Menu:', font=BOLD_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10, pady=(10, 0))

        self.cmd_vars = {}
        cmds = ['Auto-Chat Toggles', 'Reset Text Memory', 'VC Ears Toggles', 'VC Auto-Join Toggles', 'Join VC Button']
        for c in cmds:
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(cmd_frame, text=c, variable=var, font=APP_FONT, bg_color=BG_FRAME, border_color=CHECK_BORDER)
            chk.pack(anchor='w', padx=20, pady=5)
            self.cmd_vars[c] = var
            self.switches.append(chk)


    def toggle_setup(self):
        if self.setup_frame.winfo_ismapped():
            self.setup_frame.pack_forget()
        else:
            self.setup_frame.pack(fill='x', padx=20, pady=10)

    def build_brain_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_brain, fg_color=BG_SCROLL)
        scroll.pack(fill='both', expand=True)
        
        prof_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        prof_frame.pack(fill='x', padx=20, pady=(10, 10))
        
        ctk.CTkLabel(prof_frame, text='Active Bot Profile', font=TITLE_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10, pady=(10, 0))
        
        ctrl_frame = ctk.CTkFrame(prof_frame, fg_color=BG_FRAME)
        ctrl_frame.pack(fill='x', padx=10, pady=10)
        
        self.profile_menu = ctk.CTkOptionMenu(ctrl_frame, values=list(self.config_data.get('profiles', {}).keys()), command=self.switch_profile, font=APP_FONT)
        self.profile_menu.pack(side='left', padx=(0, 10))
        self.option_menus.append(self.profile_menu)
        
        self.entry_new_prof = ctk.CTkEntry(ctrl_frame, placeholder_text='New profile name...', font=APP_FONT, fg_color=TEXT_BG)
        self.entry_new_prof.pack(side='left', padx=(0, 10))
        
        btn_add_prof = ctk.CTkButton(ctrl_frame, text='Create Profile', font=BOLD_FONT, command=self.create_profile)
        btn_add_prof.pack(side='left', padx=(0, 10))
        self.save_btns.append(btn_add_prof)
        
        btn_del_prof = ctk.CTkButton(ctrl_frame, text='Delete Profile', font=BOLD_FONT, fg_color=('#D9D9D9', '#57606f'), text_color=('black', 'white'), hover_color=('#BFBFBF', '#2f3542'), command=self.delete_profile)
        btn_del_prof.pack(side='left')
        
        ctk.CTkLabel(scroll, text='Base Prompt (The Identity)', font=TITLE_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(10,0))
        ctk.CTkLabel(scroll, text='Tell the bot exactly who it is, how old it is, and its general vibe.', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        self.text_base = ctk.CTkTextbox(scroll, height=80, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.text_base)
        self.text_base.pack(fill='x', padx=20, pady=5)

        ctk.CTkLabel(scroll, text='Friends Context (The Gossip)', font=TITLE_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(15,0))
        ctk.CTkLabel(scroll, text='Explain inside jokes, who is dating who, who is bad at video games, etc.', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        self.text_context = ctk.CTkTextbox(scroll, height=80, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.text_context)
        self.text_context.pack(fill='x', padx=20, pady=5)

        ctk.CTkLabel(scroll, text='Strict Rules (The Guardrails)', font=TITLE_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(15,0))
        ctk.CTkLabel(scroll, text='Things the bot MUST do. (ex: "Never use punctuation", "Always insult Jack").', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        self.text_rules = ctk.CTkTextbox(scroll, height=80, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.text_rules)
        self.text_rules.pack(fill='x', padx=20, pady=5)
        
        ctk.CTkLabel(scroll, text='Auto-Chat Behaviors (Comma separated)', font=TITLE_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(15,0))
        ctk.CTkLabel(scroll, text='Topics the bot will randomly bring up on its own when auto-chat is enabled.', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        self.text_auto_chat = ctk.CTkTextbox(scroll, height=60, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.text_auto_chat)
        self.text_auto_chat.pack(fill='x', padx=20, pady=5)

        self.var_lowercase = ctk.BooleanVar()
        lc_sw = ctk.CTkSwitch(scroll, text='Force Bulletproof Lowercase (Only allows Emojis and ALL CAPS words)', variable=self.var_lowercase, font=APP_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        lc_sw.pack(anchor='w', padx=20, pady=10)
        self.switches.append(lc_sw)

        ctk.CTkLabel(scroll, text='Pre-Generation Filters', font=TITLE_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(15,0))
        ctk.CTkLabel(scroll, text='Banned Input Phrases (Bot refuses to reply if user says these. Comma separated.)', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        self.entry_banned = ctk.CTkEntry(scroll, font=APP_FONT, fg_color=TEXT_BG)
        self.entry_banned.pack(fill='x', padx=20, pady=5)

        ctk.CTkLabel(scroll, text='Post-Generation Scrubber', font=TITLE_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(15,0))
        ctk.CTkLabel(scroll, text='Auto-Removed Words (Words the AI uses too much that get deleted. Comma separated)', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        self.entry_removed = ctk.CTkEntry(scroll, font=APP_FONT, fg_color=TEXT_BG)
        self.entry_removed.pack(fill='x', padx=20, pady=5)
        
        ctk.CTkLabel(scroll, text='Word Replacements (Format -> bad_phrase = good_phrase)', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(10,0))
        self.text_replacements = ctk.CTkTextbox(scroll, height=80, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.text_replacements)
        self.text_replacements.pack(fill='x', padx=20, pady=5)

        ctk.CTkLabel(scroll, text='Custom Bot Responses (The Catchphrases)', font=TITLE_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(25,0))
        ctk.CTkLabel(scroll, text='Change what the bot says in hardcoded scenarios.', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(0, 10))

        def create_response_entry(parent, label_text, attr_name):
            ctk.CTkLabel(parent, text=label_text, font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
            entry = ctk.CTkEntry(parent, font=APP_FONT, fg_color=TEXT_BG)
            entry.pack(fill='x', padx=20, pady=(0, 10))
            setattr(self, attr_name, entry)

        create_response_entry(scroll, 'Safety Filter Blocked Prompt:', 'entry_msg_safety')
        create_response_entry(scroll, 'Banned Input Detected:', 'entry_msg_banned')
        create_response_entry(scroll, 'AI Brain/Model Unreachable:', 'entry_msg_brain')
        ctk.CTkLabel(scroll, text='Pro Tip: To use custom server emojis in these responses, just type :emoji_name:.', font=INFO_FONT, text_color=('#3B8ED0', '#3B8ED0'), fg_color=BG_SCROLL).pack(pady=(10, 5))

        create_response_entry(scroll, 'Text Memory Reset Acknowledged:', 'entry_msg_reset_text')
        create_response_entry(scroll, 'VC Memory Reset Acknowledged:', 'entry_msg_reset_vc')
        create_response_entry(scroll, 'Voice Channel Join Greeting:', 'entry_msg_join')
        create_response_entry(scroll, 'Stop/Shush Command Acknowledged:', 'entry_msg_stop')
        create_response_entry(scroll, 'Vocal Cords Warmed Up Greeting:', 'entry_msg_vocal_ready')
        create_response_entry(scroll, 'Disconnect/Leave VC Command Acknowledged:', 'entry_msg_leave_vc')

        ctk.CTkLabel(scroll, text='Server Emoji Syncer & Picker', font=TITLE_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(25,0))
        ctk.CTkLabel(scroll, text='Uncheck emojis to stop the bot from using them. Click the Star (★) to make it a favorite!', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        
        btn_frame = ctk.CTkFrame(scroll, fg_color=BG_SCROLL)
        btn_frame.pack(anchor='w', padx=20, pady=5)
        
        btn_refresh_emojis = ctk.CTkButton(btn_frame, text='Refresh Emojis', font=BOLD_FONT, command=self.refresh_emojis)
        btn_refresh_emojis.pack(side='left', padx=(0, 10))
        self.start_btns.append(btn_refresh_emojis)

        btn_sel_all = ctk.CTkButton(btn_frame, text='Select All', font=BOLD_FONT, fg_color=('#D9D9D9', '#57606f'), text_color=('black', 'white'), hover_color=('#BFBFBF', '#2f3542'), command=self.select_all_emojis)
        btn_sel_all.pack(side='left', padx=(0, 10))
        
        btn_desel_all = ctk.CTkButton(btn_frame, text='Deselect All', font=BOLD_FONT, fg_color=('#D9D9D9', '#57606f'), text_color=('black', 'white'), hover_color=('#BFBFBF', '#2f3542'), command=self.deselect_all_emojis)
        btn_desel_all.pack(side='left')

        self.emoji_wrapper = ctk.CTkFrame(scroll, fg_color=BG_FRAME, height=250)
        self.emoji_wrapper.pack(fill='x', padx=20, pady=5)
        self.emoji_wrapper.pack_propagate(False)

        self.emoji_frame = ctk.CTkScrollableFrame(self.emoji_wrapper, fg_color=BG_FRAME)
        self.emoji_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        def _emoji_scroll(event, is_up=None):
            if sys.platform.startswith('win'): is_up = event.delta > 0
            else: is_up = (event.num == 4)
            
            now = time.time()
            if self._momentum_active and (now - self._last_scroll_time < 0.4):
                self._last_scroll_time = now
                return 
                
            yview = self.emoji_frame._parent_canvas.yview()
            if (is_up and yview[0] <= 0.0) or (not is_up and yview[1] >= 1.0):
                self._momentum_active = True
                self._last_scroll_time = now
                return

            self._momentum_active = False
            if sys.platform.startswith('win'):
                self.emoji_frame._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            else:
                self.emoji_frame._parent_canvas.yview_scroll(-1 if is_up else 1, "units")
            return "break"
        
        if sys.platform.startswith('win'): self.emoji_frame._parent_canvas.bind("<MouseWheel>", _emoji_scroll)
        else:
            self.emoji_frame._parent_canvas.bind("<Button-4>", lambda e: _emoji_scroll(e, True))
            self.emoji_frame._parent_canvas.bind("<Button-5>", lambda e: _emoji_scroll(e, False))

        grip = ctk.CTkLabel(self.emoji_wrapper, text="↘", font=("Arial", 16, "bold"), text_color="gray50", cursor="size_nw_se", bg_color=BG_FRAME)
        grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)

        def start_resize(event):
            grip.startY = event.y_root
            grip.startH = self.emoji_wrapper.winfo_height()

        def drag_resize(event):
            delta = event.y_root - grip.startY
            new_height = max(100, grip.startH + delta)
            self.emoji_wrapper.configure(height=new_height)

        grip.bind("<ButtonPress-1>", start_resize)
        grip.bind("<B1-Motion>", drag_resize)
        grip.bind("<Enter>", lambda e: grip.configure(text_color="white"))
        grip.bind("<Leave>", lambda e: grip.configure(text_color="gray50"))

        self.emoji_vars = {}

    def select_all_emojis(self):
        for var in self.emoji_vars.values():
            var.set(True)
        self.save_all_silent()

    def deselect_all_emojis(self):
        for var in self.emoji_vars.values():
            var.set(False)
        self.save_all_silent()

    def refresh_emojis(self):
        for widget in self.emoji_frame.winfo_children():
            widget.destroy()
        
        self.emoji_vars = {}
        emoji_file = os.path.join(SCRIPT_DIR, 'fetched_emojis.json')
        if not os.path.exists(emoji_file):
            ctk.CTkLabel(self.emoji_frame, text='No emojis found! Run the bot first so it can scan the server.', font=APP_FONT, fg_color=BG_FRAME).pack()
            return
            
        with open(emoji_file, 'r', encoding='utf-8') as f:
            try: fetched_emojis = json.load(f)
            except: fetched_emojis = {}
            
        row = 0
        fav_list = self.config_data.get('favorite_emojis', [])
        
        for server_name, emojis in fetched_emojis.items():
            if not emojis: continue
            
            header_frame = ctk.CTkFrame(self.emoji_frame, fg_color=BG_FRAME)
            header_frame.grid(row=row, column=0, columnspan=3, pady=(15, 5), sticky='ew', padx=10)
            
            lbl = ctk.CTkLabel(header_frame, text=f"== {server_name} ==", font=TITLE_FONT, text_color="#2FA572")
            lbl.pack(side='left', padx=(0, 15))
            
            def make_toggler(srv_emojis, state):
                def _t():
                    for eid in srv_emojis.keys():
                        if eid in self.emoji_vars:
                            self.emoji_vars[eid].set(state)
                    self.save_all_silent()
                return _t

            b1 = ctk.CTkButton(header_frame, text='All', width=40, height=24, font=INFO_FONT, fg_color=('#D9D9D9', '#57606f'), text_color=('black', 'white'), hover_color=('#BFBFBF', '#2f3542'), command=make_toggler(emojis, True))
            b1.pack(side='left', padx=(0, 5))
            
            b2 = ctk.CTkButton(header_frame, text='None', width=40, height=24, font=INFO_FONT, fg_color=('#D9D9D9', '#57606f'), text_color=('black', 'white'), hover_color=('#BFBFBF', '#2f3542'), command=make_toggler(emojis, False))
            b2.pack(side='left')
            
            row += 1
            
            col = 0
            for e_id, e_data in emojis.items():
                var = ctk.BooleanVar(value=self.config_data.get('emoji_toggles', {}).get(e_id, True))
                self.emoji_vars[e_id] = var
                
                frame = ctk.CTkFrame(self.emoji_frame, fg_color=BG_FRAME)
                frame.grid(row=row, column=col, padx=10, pady=5, sticky='w')

                is_fav = e_id in fav_list
                def toggle_fav(e_id=e_id, btn=None):
                    favs = self.config_data.get('favorite_emojis', [])
                    if e_id in favs:
                        favs.remove(e_id)
                        btn.configure(text="☆", text_color="gray50")
                    else:
                        favs.append(e_id)
                        btn.configure(text="★", text_color="#F39C12")
                    self.config_data['favorite_emojis'] = favs
                    self.save_all_silent()

                star_btn = ctk.CTkButton(frame, text="★" if is_fav else "☆", width=30, fg_color="transparent", hover_color=BG_FRAME, text_color="#F39C12" if is_fav else "gray50", font=("Arial", 18))
                star_btn.configure(command=lambda e=e_id, b=star_btn: toggle_fav(e, b))
                star_btn.pack(side='left', padx=(0, 2))
                
                img_path = os.path.join(SCRIPT_DIR, 'emoji_cache', f'{e_id}.png')
                if os.path.exists(img_path):
                    try:
                        img = ctk.CTkImage(Image.open(img_path), size=(24, 24))
                        img_lbl = ctk.CTkLabel(frame, image=img, text='', fg_color=BG_FRAME)
                        img_lbl.pack(side='left', padx=(0, 5))
                    except: pass
                    
                chk = ctk.CTkCheckBox(frame, text=f":{e_data['name']}:", variable=var, font=APP_FONT, bg_color=BG_FRAME, border_color=CHECK_BORDER)
                chk.pack(side='left', padx=(0, 5))
                self.switches.append(chk)
                
                col += 1
                if col > 2:
                    col = 0
                    row += 1
            if col != 0: row += 1
                
        self.apply_accent_color(self.config_data.get('accent_color', '#d1d1d1'))

    def build_voice_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_voice, fg_color=BG_SCROLL)
        scroll.pack(fill='both', expand=True)

        ctk.CTkLabel(scroll, text='Voice Module Settings', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=10)
        self.var_voice = ctk.BooleanVar()
        self.var_autojoin = ctk.BooleanVar()
        self.var_dm_voice = ctk.BooleanVar()
        self.var_thinking_music = ctk.BooleanVar()
        self.var_dyn_emotions = ctk.BooleanVar()
        
        vf = ctk.CTkFrame(scroll, fg_color=BG_SCROLL)
        vf.pack()
        v_sw = ctk.CTkSwitch(vf, text='Enable Voice Module Completely', variable=self.var_voice, font=APP_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        v_sw.pack(side='left', padx=20)
        j_sw = ctk.CTkSwitch(vf, text='Auto-Join Voice Channels when active', variable=self.var_autojoin, font=APP_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        j_sw.pack(side='left', padx=20)
        self.switches.extend([v_sw, j_sw])

        dm_sw = ctk.CTkSwitch(scroll, text='Allow DM-to-Voice Commands (Users can DM bot to make it speak)', variable=self.var_dm_voice, font=APP_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        dm_sw.pack(pady=15)
        self.switches.append(dm_sw)
        
        tm_sw = ctk.CTkSwitch(scroll, text='Play Thinking Music (Plays thinking.wav from voice_references folder)', variable=self.var_thinking_music, font=APP_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        tm_sw.pack(pady=(0, 15))
        self.switches.append(tm_sw)
        
        dyn_sw = ctk.CTkSwitch(scroll, text='Change emotions mid-sentence (Dynamic Emotions)', variable=self.var_dyn_emotions, font=APP_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        dyn_sw.pack(pady=(0, 15))
        self.switches.append(dyn_sw)

        ctk.CTkLabel(scroll, text='Allowed Voice Emotions', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(30, 5))
        ctk.CTkLabel(scroll, text='Uncheck emotions if you did not record a .wav file for them, otherwise the bot will crash.', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=(0, 10))
        
        self.emo_vars = {}
        emo_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        emo_frame.pack()
        emotions = ['sad', 'anger', 'dead inside', 'excited', 'anxious', 'bored']
        for i, e in enumerate(emotions):
            var = ctk.BooleanVar()
            self.emo_vars[e] = var
            chk = ctk.CTkCheckBox(emo_frame, text=e.upper(), variable=var, font=BOLD_FONT, bg_color=BG_FRAME, border_color=CHECK_BORDER)
            chk.grid(row=i//3, column=i%3, padx=20, pady=15)
            self.switches.append(chk)
            
        ctk.CTkLabel(scroll, text='Speech-to-Text Corrections (What Google Hears -> What you meant)', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(30, 5))
        ctk.CTkLabel(scroll, text='Fix commonly misheard words (Format -> wrong = right)', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=(0, 10))
        
        self.text_stt_corrections = ctk.CTkTextbox(scroll, height=80, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.text_stt_corrections)
        self.text_stt_corrections.pack(fill='x', padx=20, pady=5)

        ctk.CTkLabel(scroll, text='TTS Pronunciation Fixes (What the AI reads -> How it should sound)', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(30, 5))
        ctk.CTkLabel(scroll, text=r'Fix phonetic pronunciations (Format -> \bword\b = phonetic)', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=(0, 10))
        
        self.text_tts_pronunciations = ctk.CTkTextbox(scroll, height=80, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.text_tts_pronunciations)
        self.text_tts_pronunciations.pack(fill='x', padx=20, pady=5)

    def build_stats_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_stats, fg_color=BG_SCROLL)
        scroll.pack(fill='both', expand=True)

        ctk.CTkLabel(scroll, text='Keyword Auto-Replies', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(10, 0))
        ctk.CTkLabel(scroll, text='Bot will instantly reply with a specific message if it sees a keyword (Format -> keyword = reply)', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=(0, 10))
        self.text_auto_replies = ctk.CTkTextbox(scroll, height=80, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.text_auto_replies)
        self.text_auto_replies.pack(fill='x', padx=20, pady=5)

        ctk.CTkLabel(scroll, text='Stat Builder', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(20, 0))
        ctk.CTkLabel(scroll, text='Track how many times a specific friend says specific things.', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=(0, 10))

        self.var_stats = ctk.BooleanVar()
        s_sw = ctk.CTkSwitch(scroll, text='Enable Custom Stats Globally', variable=self.var_stats, font=BOLD_FONT, bg_color=BG_SCROLL, fg_color=UNSELECTED_TRACK)
        s_sw.pack(pady=10)
        self.switches.append(s_sw)

        f = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        f.pack(fill='x', padx=20, pady=10)
        
        ctk.CTkLabel(f, text='Stat ID (Internal name. No spaces. ex: rage_quits)', font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10, pady=(5,0))
        self.stat_name = ctk.CTkEntry(f, font=APP_FONT, fg_color=TEXT_BG)
        self.stat_name.pack(fill='x', padx=10, pady=(0, 5))
        
        ctk.CTkLabel(f, text='Stat Alias (Display name. ex: Rage Quits)', font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10)
        self.stat_alias = ctk.CTkEntry(f, font=APP_FONT, fg_color=TEXT_BG)
        self.stat_alias.pack(fill='x', padx=10, pady=(0, 5))
        
        ctk.CTkLabel(f, text='Target User (Must match a Name from your Friends List exactly)', font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10)
        self.stat_user = ctk.CTkEntry(f, font=APP_FONT, fg_color=TEXT_BG)
        self.stat_user.pack(fill='x', padx=10, pady=(0, 5))
        
        ctk.CTkLabel(f, text='Trigger Words (Comma separated. ex: lag, alt f4, rigged)', font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10)
        self.stat_triggers = ctk.CTkEntry(f, font=APP_FONT, fg_color=TEXT_BG)
        self.stat_triggers.pack(fill='x', padx=10, pady=(0, 5))
        
        ctk.CTkLabel(f, text='Bot Output Message (What the bot says. Use {count} for the number)', font=APP_FONT, fg_color=BG_FRAME).pack(anchor='w', padx=10)
        self.stat_msg = ctk.CTkEntry(f, font=APP_FONT, fg_color=TEXT_BG)
        self.stat_msg.pack(fill='x', padx=10, pady=(0, 10))

        ab = ctk.CTkButton(f, text='Add Stat to Bot', font=BOLD_FONT, command=self.add_stat)
        ab.pack(pady=15)
        self.save_btns.append(ab)

        ctk.CTkLabel(scroll, text='Current Stats File (Preview Only)', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(20, 0))
        self.stat_preview = ctk.CTkTextbox(scroll, height=200, font=APP_FONT, fg_color=TEXT_BG)
        self.make_smart_textbox(self.stat_preview)
        self.stat_preview.pack(fill='x', padx=20, pady=10)
        

    def build_advanced_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_advanced, fg_color=BG_SCROLL)
        scroll.pack(fill='both', expand=True)
        
        ctk.CTkLabel(scroll, text='Terminal Debugging Modules', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(10, 0))
        ctk.CTkLabel(scroll, text='Toggle which specific systems print debug messages to the terminal.\n(Note: The Master "Terminal Debug Logging" switch in General Tab must be ON).', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=(0, 15))

        self.debug_vars = {}
        dbg_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        dbg_frame.pack(fill='x', padx=20, pady=5)
        
        modules = ['voice', 'tts', 'brain', 'stats', 'auto_chat', 'events']
        for i, mod in enumerate(modules):
            var = ctk.BooleanVar()
            self.debug_vars[mod] = var
            chk = ctk.CTkCheckBox(dbg_frame, text=f"{mod.upper()} Logs", variable=var, font=APP_FONT, bg_color=BG_FRAME, border_color=CHECK_BORDER)
            chk.grid(row=i//3, column=i%3, padx=20, pady=10, sticky='w')
            self.switches.append(chk)

        ctk.CTkLabel(scroll, text=' - ' * 20, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=20)

        ctk.CTkLabel(scroll, text='Cloud Updater', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(10, 0))
        ctk.CTkLabel(scroll, text='Pull the complete DoppelBot repository straight from GitHub (updates all core scripts, bots, and UI).\nBecause all your data is safely tucked away in config.json, updating will NOT delete your settings!', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=(0, 15))

        upd_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        upd_frame.pack(fill='x', padx=20, pady=5)
        
        self.entry_repo = ctk.CTkEntry(upd_frame, placeholder_text='GitHub Repo (Format -> Username/Repository)', font=APP_FONT, fg_color=TEXT_BG)
        self.entry_repo.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        btn_fetch = ctk.CTkButton(upd_frame, text='Fetch Versions', font=BOLD_FONT, command=self.fetch_versions)
        btn_fetch.pack(side='left', padx=(0, 10))
        self.start_btns.append(btn_fetch)

        self.version_menu = ctk.CTkOptionMenu(upd_frame, values=['main'], font=APP_FONT)
        self.version_menu.pack(side='left', padx=(0, 10))
        self.option_menus.append(self.version_menu)
        
        btn_update = ctk.CTkButton(upd_frame, text='Update to Version', font=BOLD_FONT, command=self.update_from_github)
        btn_update.pack(side='right')
        self.save_btns.append(btn_update)

        ctk.CTkLabel(scroll, text=' - ' * 20, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=20)

        ctk.CTkLabel(scroll, text='Local ZIP Updater', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(0, 10))
        ctk.CTkLabel(scroll, text='Downloaded a release manually? Use this to safely extract and apply bot.py and launcher.py.', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=(0, 10))
        
        btn_zip = ctk.CTkButton(scroll, text='Update from ZIP', font=BOLD_FONT, command=self.update_from_zip)
        btn_zip.pack()
        self.save_btns.append(btn_zip)

        ctk.CTkLabel(scroll, text=' - ' * 20, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=20)

        ctk.CTkLabel(scroll, text='Raw File Editor', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(0, 10))
        
        top_frame = ctk.CTkFrame(scroll, fg_color=BG_FRAME)
        top_frame.pack(fill='x', pady=5)
        self.file_selector = ctk.CTkOptionMenu(top_frame, values=['config.json', 'bot.py', 'soul.txt', 'bot_brain.txt', 'vc_history.txt'], command=self.load_advanced_file, font=APP_FONT)
        self.file_selector.pack(side='left', padx=10)
        self.option_menus.append(self.file_selector)
        
        btn = ctk.CTkButton(top_frame, text='SAVE RAW FILE', font=BOLD_FONT, command=self.save_advanced_file)
        btn.pack(side='right', padx=10)
        self.start_btns.append(btn)
        
        self.advanced_text = ctk.CTkTextbox(scroll, font=APP_FONT, height=400, fg_color=TEXT_BG, undo=True)
        self.make_smart_textbox(self.advanced_text)
        self.advanced_text.pack(pady=10, fill='both', expand=True, padx=10)

    def check_for_updates(self):
        repo_path = self.config_data.get('github_repo_url', 'JackBJ27/DoppelBot').strip().strip('/')
        if not repo_path or '/' not in repo_path: return
            
        try:
            latest = requests.get(f'https://api.github.com/repos/{repo_path}/commits/main', timeout=5).json()
            latest_sha = latest['sha'][:7]
            commit_msg = latest['commit']['message'].split('\n')[0]
            
            saved_sha = self.config_data.get('last_commit_hash', '')
            
            if latest_sha != saved_sha and saved_sha != '':
                self.prompt_update(repo_path, latest_sha, commit_msg)
            elif saved_sha == '':
                # First time running this feature, save it silently so it doesn't nag immediately
                self.config_data['last_commit_hash'] = latest_sha
                save_config(self.config_data)
        except: pass

    def prompt_update(self, repo_path, latest_sha, commit_msg):
        popup = ctk.CTkToplevel(self)
        popup.title('Update Available!')
        popup.geometry('500x250')
        popup.attributes('-topmost', True)
        popup.grab_set()
        
        msg = f"A new DoppelBot update was found on GitHub!\n\nLatest Commit: {commit_msg}\n\nWould you like to download and install this update now?"
        lbl = ctk.CTkLabel(popup, text=msg, font=APP_FONT, wraplength=450, fg_color=BG_WINDOW)
        lbl.pack(pady=20, padx=20)
        
        btn_frame = ctk.CTkFrame(popup, fg_color=BG_WINDOW)
        btn_frame.pack(pady=10)
        
        def do_update():
            popup.destroy()
            self.perform_github_update(repo_path, latest_sha)
            
        btn_yes = ctk.CTkButton(btn_frame, text='Yes, Update Now', font=BOLD_FONT, fg_color='#2FA572', hover_color='#1E7A52', command=do_update)
        btn_yes.pack(side='left', padx=10)
        
        btn_no = ctk.CTkButton(btn_frame, text='Not Right Now', font=BOLD_FONT, fg_color='#C0392B', hover_color='#922B21', command=popup.destroy)
        btn_no.pack(side='left', padx=10)

    def fetch_versions(self):
        repo_path = self.entry_repo.get().strip().strip('/')
        if not repo_path or '/' not in repo_path:
            show_popup('Error', 'Please enter your GitHub repo format as Username/Repository.\nExample: JackBJ27/DoppelBot')
            return
            
        try:
            commits = requests.get(f'https://api.github.com/repos/{repo_path}/commits', timeout=5).json()
            versions = []
            
            if isinstance(commits, list):
                for c in commits[:15]: # Get last 15 commits to keep the menu clean
                    sha = c['sha'][:7]
                    msg = c['commit']['message'].split('\n')[0][:40] 
                    versions.append(f"{sha} - {msg}")
            
            if not versions: versions = ['main']
            
            self.version_menu.configure(values=versions)
            self.version_menu.set(versions[0])
            show_popup('Success', f'Found {len(versions)} recent commits in {repo_path}!')
        except:
            show_popup('Error', 'Failed to fetch commits. Check repo name or rate limits.')
            self.version_menu.configure(values=['main'])
            self.version_menu.set('main')

    def update_from_github(self):
        repo_path = self.entry_repo.get().strip().strip('/')
        if not repo_path or '/' not in repo_path:
            show_popup('Error', 'Please enter your GitHub repo format as Username/Repository.\nExample: JackBJ27/DoppelBot')
            return
            
        raw_version = self.version_menu.get()
        version = raw_version.split(' - ')[0] if ' - ' in raw_version else raw_version
        
        self.perform_github_update(repo_path, version)

    def perform_github_update(self, repo_path, version):
        self.config_data['github_repo_url'] = repo_path
        save_config(self.config_data)
        
        zip_url = f'https://api.github.com/repos/{repo_path}/zipball/{version}'
        
        try:
            r = requests.get(zip_url, stream=True)
            if r.status_code == 200:
                temp_zip = os.path.join(SCRIPT_DIR, 'temp_update.zip')
                with open(temp_zip, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                self._extract_update_zip(temp_zip)
                os.remove(temp_zip)
                
                self.config_data['last_commit_hash'] = version
                save_config(self.config_data)
                
                show_popup('Success', f'All files updated to version "{version}"! Please close and re-open the dashboard.')
            else:
                show_popup('Error', f'Could not fetch repository. Status code: {r.status_code}')
        except Exception as e:
            show_popup('Error', f'Something crashed:\n{e}')

    def update_from_zip(self):
        zip_path = fd.askopenfilename(title='Select Update ZIP', filetypes=[('ZIP Files', '*.zip')])
        if not zip_path: return
        
        try:
            self._extract_update_zip(zip_path)
            show_popup('Success', 'Updated all files from ZIP successfully! Please restart the dashboard.')
        except Exception as e:
            show_popup('Error', f'Failed to extract ZIP:\n{e}')

    def _extract_update_zip(self, zip_path):
        safe_files = ['config.json', '.env', 'bot_brain.txt', 'soul.txt', 'vc_history.txt', 'bot_servers.json', 'stats.json', 'fetched_emojis.json']
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            top_level_items = set(item.split('/')[0] for item in z.namelist() if item)
            has_root_dir = len(top_level_items) == 1 and next(iter(top_level_items)) + '/' in z.namelist()
            root_dir = next(iter(top_level_items)) + '/' if has_root_dir else ""

            for file_info in z.infolist():
                if file_info.is_dir(): continue
                
                target_path = file_info.filename
                if has_root_dir and target_path.startswith(root_dir):
                    target_path = target_path[len(root_dir):]
                    
                if not target_path: continue 
                
                filename = os.path.basename(target_path)
                if filename in safe_files: continue
                    
                if 'voice_references' in target_path and target_path.endswith('.wav'): continue
                if 'emoji_cache' in target_path: continue

                abs_target = os.path.join(SCRIPT_DIR, target_path)
                os.makedirs(os.path.dirname(abs_target), exist_ok=True)
                
                with z.open(file_info) as source, open(abs_target, 'wb') as target:
                    target.write(source.read())

    def build_howto_tab(self):
        guide = """WELCOME TO THE DOPPELBOT GUIDE

(Check readme for more info, but this goes over a broad overview of the DoppelBot Dashboard.)

1. Getting Discord IDs:
   - Open Discord. Go to User Settings (the gear icon).
   - Click on 'Advanced' under App Settings.
   - Turn ON 'Developer Mode'.
   - Now, you can right-click any user, text channel, or server and click 'Copy ID'.
   - Paste those long numbers into the General Tab where it asks for them.

2. General & Keys Tab:
   - Tokens: These are your passwords. DO NOT SHOW OR SHARE THESE WITH ANYONE! 
   - Channels: Map out where the bot lives. It needs to know the text channels to read, and the voice channels it's allowed to enter.
   - Access Control: Select who can talk to the bot. You can limit it to only people explicitly named in your Friends List, specific server Roles, or make it Global.

3. Brain & Personality Tab:
   - Base Prompt: Think of this as the bot's core identity. 
   - Context: Explain your friend group. "Jack sends funny memes about cats. Dyl carries us in Fortnite."
   - Rules: Formatting constraints. Ex: "Never use capital letters."
   - Auto-Chat Behaviors: What topics the bot will randomly chat about by itself.
   
4. Voice Module Tab:
   - If this is your first time using the bot, click the 'Show Initial Data Mining Tools' button at the bottom.
   - Run step 1, wait for it to finish. This will take a little bit if you have many messages. Please be patient and do NOT close the terminal. It will alert you when it's done. Next, run step 2 and wait for it to finish. This will also take a few minutes - do NOT close the terminal. It will alert you when completed.
   - Ensure you actually recorded all voice emotion .wav files, or uncheck the ones you skipped.
   - NOTE: You can optionally add files named "warming_up.wav", "wait.wav", "still_loading.wav", and "almost_there.wav" to your voice_references folder. The bot will play these to stall for time while the AI boots up! You can ALSO add "uhhh.wav", "um.wav", "hmmm.wav", "sigh.wav", "big_sigh.wav", and "chatter.wav" to make the bot naturally stutter and sigh when the AI is thinking mid-sentence!

5. Stats Tab:
   - Want the bot to publicly shame your friend every time they complain about lag? Or when they send something sus in chat? Set a stat for it here.
   
6. Starting up & Using the Bot:
   - Hit the giant red START BOT button at the bottom. A black terminal window will open. Leave it open. That is the bot's brain running. It will take up to 5-15 minutes on first start-up and will appear frozen. IT IS NOT - it is gathering the AI model files in the background - do NOT close or restart the terminal, it will take a bit but will alert you when it's done when it says "Vocal Cords are warmed up."
   - Mention the bot in Discord and type "cmds" to spawn a secret interactive control panel inside Discord!
   
CREDITS & LICENSING:
- Voice-compat module sourced from the 'discord-brain-rot' GitHub repository. Huge shoutout to the creator (GabrielAgrela) for making the voice AI cloner possible after Discord enforced E2EE!
- Font 'League Spartan' by Matt Bailey, Tyler Finck. Licensed under the SIL Open Font License, Version 1.1."""
        
        textbox = ctk.CTkTextbox(self.tab_howto, font=APP_FONT, wrap='word', fg_color=TEXT_BG)
        self.make_smart_textbox(textbox)
        textbox.pack(fill='both', expand=True, padx=20, pady=20)
        textbox.insert('1.0', guide)
        textbox.configure(state='disabled')

    def build_accessibility_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_accessibility, fg_color=BG_SCROLL)
        scroll.pack(fill='both', expand=True)

        ctk.CTkLabel(scroll, text='Accessibility Settings', font=TITLE_FONT, fg_color=BG_SCROLL).pack(pady=(10, 0))
        ctk.CTkLabel(scroll, text='Customize the dashboard to your visual needs.', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(pady=(0, 20))

        ctk.CTkLabel(scroll, text='Theme Mode', font=BOLD_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        self.theme_menu = ctk.CTkOptionMenu(scroll, values=['Dark', 'Light', 'System'], command=self.change_appearance_mode, font=APP_FONT)
        self.theme_menu.pack(fill='x', padx=20, pady=(5, 25))
        self.option_menus.append(self.theme_menu)
        
        ctk.CTkLabel(scroll, text='Color Blindness Profile', font=BOLD_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        ctk.CTkLabel(scroll, text='(Changes accent colors for better visibility)', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        self.color_menu = ctk.CTkOptionMenu(scroll, values=['Standard', 'High Contrast', 'Protanopia / Deuteranopia', 'Tritanopia'], command=self.apply_color_profile, font=APP_FONT)
        self.color_menu.pack(fill='x', padx=20, pady=(5, 25))
        self.option_menus.append(self.color_menu)

        ctk.CTkLabel(scroll, text='Custom Accent Color', font=BOLD_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20, pady=(15, 0))
        ctk.CTkLabel(scroll, text='(Changes the color of all sliders, checkboxes, and toggles)', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)

        color_frame = ctk.CTkFrame(scroll, fg_color=BG_SCROLL)
        color_frame.pack(fill='x', padx=20, pady=(5, 25))

        btn_color = ctk.CTkButton(color_frame, text='Pick Color', font=APP_FONT, command=self.pick_color)
        btn_color.pack(side='left', padx=(0, 10))
        self.save_btns.append(btn_color) 

        self.lbl_current_color = ctk.CTkLabel(color_frame, text=f"Current: {self.config_data.get('accent_color', '#d1d1d1')}", font=APP_FONT, fg_color=BG_SCROLL)
        self.lbl_current_color.pack(side='left')

        ctk.CTkLabel(scroll, text='UI & Font Size Scale', font=BOLD_FONT, fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        ctk.CTkLabel(scroll, text='(Scales the entire app so text stays perfectly readable)', font=INFO_FONT, text_color=('gray20', 'gray75'), fg_color=BG_SCROLL).pack(anchor='w', padx=20)
        
        self.scale_menu = ctk.CTkOptionMenu(scroll, values=['80%', '90%', '100%', '110%', '125%', '150%'], command=self.change_scaling, font=APP_FONT)
        self.scale_menu.pack(fill='x', padx=30, pady=(5, 15))
        self.option_menus.append(self.scale_menu)

    def pick_color(self):
        color = colorchooser.askcolor(title='Choose Accent Color')[1]
        if color:
            self.apply_accent_color(color)
            self.lbl_current_color.configure(text=f"Current: {color}")

    def apply_color_profile(self, profile):
        self.config_data['color_profile'] = profile
        save_config(self.config_data)

        c_start = {'fg_color': '#C0392B', 'hover_color': '#922B21'}
        c_save = {'fg_color': '#2FA572', 'hover_color': '#1E7A52'}
        c_switch = {'progress_color': '#1f538d', 'button_color': '#3B8ED0', 'button_hover_color': '#36719F'}

        if profile == 'High Contrast':
            c_start = {'fg_color': '#FFFF00', 'hover_color': '#CCCC00'}
            c_save = {'fg_color': '#00FFFF', 'hover_color': '#00CCCC'}
            c_switch = {'progress_color': '#FFFF00', 'button_color': 'white', 'button_hover_color': '#DDDDDD'}
        elif profile == 'Protanopia / Deuteranopia': 
            c_start = {'fg_color': '#0055FF', 'hover_color': '#0033CC'}
            c_save = {'fg_color': '#FFCC00', 'hover_color': '#CCA300'}
            c_switch = {'progress_color': '#0055FF', 'button_color': '#FFCC00', 'button_hover_color': '#CCA300'}
        elif profile == 'Tritanopia': 
            c_start = {'fg_color': '#FF0000', 'hover_color': '#CC0000'}
            c_save = {'fg_color': '#00FFFF', 'hover_color': '#00CCCC'}
            c_switch = {'progress_color': '#FF0000', 'button_color': '#00FFFF', 'button_hover_color': '#00CCCC'}

        self.start_btns = [b for b in self.start_btns if b.winfo_exists()]
        self.save_btns = [b for b in self.save_btns if b.winfo_exists()]
        self.switches = [s for s in self.switches if s.winfo_exists()]
        self.sliders = [s for s in self.sliders if s.winfo_exists()]
        self.option_menus = [o for o in self.option_menus if o.winfo_exists()]

        for btn in self.start_btns:
            btn.configure(**c_start)
        for btn in self.save_btns:
            btn.configure(**c_save)
        for sw in self.switches:
            if isinstance(sw, ctk.CTkCheckBox):
                sw.configure(fg_color=c_switch['progress_color'], hover_color=c_switch['button_hover_color'])
            else:
                sw.configure(progress_color=c_switch['progress_color'], button_color=c_switch['button_color'], button_hover_color=c_switch['button_hover_color'])
        for sl in self.sliders:
            sl.configure(button_color=c_switch['progress_color'], button_hover_color=c_switch['button_hover_color'], progress_color=c_switch['progress_color'])
        for om in self.option_menus:
            om.configure(fg_color=c_switch['button_color'], button_color=c_switch['button_color'], button_hover_color=c_switch['button_hover_color'], dropdown_fg_color=BG_FRAME, dropdown_text_color=('black', 'white'), dropdown_hover_color=CHECK_BORDER)

    def apply_accent_color(self, color):
        self.config_data['accent_color'] = color
        save_config(self.config_data)
        
        dynamic_color = generate_adaptive_color(color)
        text_col = get_contrasting_text_color(dynamic_color)
        
        c_start = {'fg_color': '#C0392B', 'hover_color': '#922B21'}

        self.start_btns = [b for b in self.start_btns if b.winfo_exists()]
        self.save_btns = [b for b in self.save_btns if b.winfo_exists()]
        self.switches = [s for s in self.switches if s.winfo_exists()]
        self.sliders = [s for s in self.sliders if s.winfo_exists()]
        self.option_menus = [o for o in self.option_menus if o.winfo_exists()]

        for btn in self.start_btns:
            btn.configure(**c_start)
        for btn in self.save_btns:
            btn.configure(fg_color=dynamic_color, hover_color=dynamic_color, text_color=text_col)
        for sw in self.switches:
            if isinstance(sw, ctk.CTkCheckBox):
                sw.configure(fg_color=dynamic_color, hover_color=dynamic_color)
            else:
                sw.configure(progress_color=dynamic_color, button_color=dynamic_color, button_hover_color=dynamic_color)
        for sl in self.sliders:
            sl.configure(button_color=dynamic_color, button_hover_color=dynamic_color, progress_color=dynamic_color)
        for om in self.option_menus:
            om.configure(fg_color=dynamic_color, button_color=dynamic_color, button_hover_color=dynamic_color, text_color=text_col, dropdown_fg_color=BG_FRAME, dropdown_text_color=('black', 'white'), dropdown_hover_color=CHECK_BORDER)

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)
        self.config_data['theme'] = new_mode
        save_config(self.config_data)

    def change_scaling(self, val):
        scale_float = float(val.strip('%')) / 100.0
        ctk.set_widget_scaling(scale_float)
        self.config_data['ui_scaling'] = scale_float
        save_config(self.config_data)
        
        if hasattr(self, 'scale_menu') and self.scale_menu.get() != val:
            self.scale_menu.set(val)
        if hasattr(self, 'ctrl_scale_menu') and self.ctrl_scale_menu.get() != val:
            self.ctrl_scale_menu.set(val)

    def build_controls(self):
        ctrl_frame = ctk.CTkFrame(self, fg_color=BG_WINDOW)
        ctrl_frame.pack(fill='x', padx=20, pady=(0, 10))

        top_ctrl = ctk.CTkFrame(ctrl_frame, fg_color=BG_WINDOW)
        top_ctrl.pack(fill='x', pady=(0, 5))

        self.btn_undo = ctk.CTkButton(top_ctrl, text='↶ Undo', width=70, font=BOLD_FONT, command=self.undo, state='disabled')
        self.btn_undo.pack(side='left', padx=(0, 5))
        
        self.btn_redo = ctk.CTkButton(top_ctrl, text='↷ Redo', width=70, font=BOLD_FONT, command=self.redo, state='disabled')
        self.btn_redo.pack(side='left', padx=(0, 5))

        self.btn_save_main = ctk.CTkButton(top_ctrl, text='💾 Save All', width=90, font=BOLD_FONT, command=self.manual_save_btn, fg_color='#2FA572', hover_color='#1E7A52')
        self.btn_save_main.pack(side='left', padx=(5, 10))
        
        self.lbl_autosave_status = ctk.CTkLabel(top_ctrl, text='Waiting for changes...', font=INFO_FONT, text_color=('gray40', 'gray75'), fg_color=BG_WINDOW)
        self.lbl_autosave_status.pack(side='left')

        slider_frame = ctk.CTkFrame(ctrl_frame, fg_color=BG_WINDOW)
        slider_frame.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(slider_frame, text='UI Scale:', font=BOLD_FONT, fg_color=BG_WINDOW).pack(side='left', padx=(0, 10))
        
        self.ctrl_scale_menu = ctk.CTkOptionMenu(slider_frame, values=['80%', '90%', '100%', '110%', '125%', '150%'], command=self.change_scaling, font=APP_FONT)
        self.ctrl_scale_menu.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.option_menus.append(self.ctrl_scale_menu)

        copy_lbl = ctk.CTkLabel(ctrl_frame, text='Copyright (c) 2026 JackBJ | Licensed under GPL-3.0', font=INFO_FONT, text_color=('gray40', 'gray75'), fg_color=BG_WINDOW)
        copy_lbl.pack(pady=(0, 2))

        self.btn_start_bot = ctk.CTkButton(ctrl_frame, text='START BOT', height=50, font=('League Spartan', 18, 'bold'), command=lambda: run_script('bot.py'))
        self.btn_start_bot.pack(fill='x', pady=(0, 5))
        self.start_btns.append(self.btn_start_bot)
        
    def manual_save_btn(self):
        self.save_all_silent()
        show_popup('Saved', 'All settings have been manually saved!')
        
    def dict_to_text(self, d):
        if isinstance(d, list): return '\n'.join([f'{x} = Channel Name' for x in d])
        return '\n'.join([f'{k} = {v}' for k, v in d.items()])

    def text_to_dict(self, text):
        res = {}
        for line in text.split('\n'):
            if '=' in line:
                k, v = line.split('=', 1)
                if k.strip().isdigit(): res[k.strip()] = v.strip()
        return res

    def reload_ui_from_config(self, full_reload=True):
        self.config_data = load_config()
        self.keys_data = load_env()

        active_prof = self.config_data.get('active_profile', 'Default')
        profiles = self.config_data.get('profiles', {})
        prof_data = profiles.get(active_prof, self.config_data)

        if hasattr(self, 'profile_menu'):
            self.profile_menu.configure(values=list(profiles.keys()))
            self.profile_menu.set(active_prof)
            
        self.entry_discord.delete(0, 'end'); self.entry_discord.insert(0, self.keys_data.get('DISCORD_TOKEN', ''))
        self.entry_google.delete(0, 'end'); self.entry_google.insert(0, self.keys_data.get('GOOGLE_API_KEYS', ''))
        self.entry_hf.delete(0, 'end'); self.entry_hf.insert(0, self.keys_data.get('HF_TOKEN', ''))

        self.entry_name.delete(0, 'end'); self.entry_name.insert(0, prof_data.get('bot_name', 'DoppelBot'))
        self.entry_main_txt.delete(0, 'end'); self.entry_main_txt.insert(0, str(self.config_data.get('primary_channel_id', '')))
        
        self.text_allow_roles.delete('1.0', 'end'); self.text_allow_roles.insert('1.0', self.dict_to_text(self.config_data.get('allowed_roles', {})))
        self.text_allow_txt.delete('1.0', 'end'); self.text_allow_txt.insert('1.0', self.dict_to_text(self.config_data.get('allowed_text_channels', {})))
        self.text_allow_vc.delete('1.0', 'end'); self.text_allow_vc.insert('1.0', self.dict_to_text(self.config_data.get('allowed_vc_channels', {})))

        self.var_autochat.set(self.config_data.get('auto_chat', True))
        self.var_websearch.set(self.config_data.get('enable_websearch', True))
        self.var_debug.set(self.config_data.get('enable_debug', True))
        self.slider_temp.set(self.config_data.get('temperature', 0.85))

        self.access_menu.set(self.config_data.get('access_mode', 'Friends Only (VIPs)'))

        self.var_ephemeral.set(self.config_data.get('ephemeral_commands', False))
        enabled_cmds = self.config_data.get('enabled_commands', ['Auto-Chat Toggles', 'Reset Text Memory', 'VC Ears Toggles', 'VC Auto-Join Toggles', 'Join VC Button'])
        for c, var in self.cmd_vars.items():
            var.set(c in enabled_cmds)

        f_text = '\n'.join([f'{k} = {v}' for k, v in self.config_data.get('vip_map', {}).items()])
        self.text_friends.delete('1.0', 'end'); self.text_friends.insert('1.0', f_text)

        self.text_base.delete('1.0', 'end')
        self.text_base.insert('1.0', prof_data.get('base_prompt') or 'You are DoppelBot. A casual, chill Discord bot. You talk like a normal person.')
        self.text_context.delete('1.0', 'end')
        self.text_context.insert('1.0', prof_data.get('friends_context') or 'The people in this server are your friends.')
        self.text_rules.delete('1.0', 'end')
        self.text_rules.insert('1.0', prof_data.get('rules') or '1. FORMATTING: You MUST write entirely in lowercase.\n2. NO ECHOING: DO NOT start by repeating the user\'s words.\n3. EMOTION TAG: You MUST start your response with an emotion tag like [default] or [sad].\n4. DYNAMIC LENGTH: Match the user\'s energy. If the user sends a short message, reply with 1 short sentence.')
        
        self.text_auto_chat.delete('1.0', 'end')
        self.text_auto_chat.insert('1.0', prof_data.get('auto_chat_behaviors', self.config_data.get('auto_chat_behaviors', 'post a brief casual observation, tease them lightly, say something cryptic, ask an unhinged question')))

        self.entry_msg_reset_text.delete(0, 'end'); self.entry_msg_reset_text.insert(0, prof_data.get('msg_memory_reset', self.config_data.get('msg_memory_reset', 'text memory wiped.')))
        self.entry_msg_reset_vc.delete(0, 'end'); self.entry_msg_reset_vc.insert(0, prof_data.get('msg_vc_memory_reset', self.config_data.get('msg_vc_memory_reset', 'voice memory wiped.')))
        self.entry_msg_safety.delete(0, 'end'); self.entry_msg_safety.insert(0, prof_data.get('msg_safety_filter', self.config_data.get('msg_safety_filter', 'google safety filter says no.')))
        self.entry_msg_banned.delete(0, 'end'); self.entry_msg_banned.insert(0, prof_data.get('msg_banned_input', self.config_data.get('msg_banned_input', 'woah chill. not saying that.')))
        self.entry_msg_brain.delete(0, 'end'); self.entry_msg_brain.insert(0, prof_data.get('msg_brain_disconnected', self.config_data.get('msg_brain_disconnected', 'brain disconnected')))
        self.entry_msg_join.delete(0, 'end'); self.entry_msg_join.insert(0, prof_data.get('msg_join_vc', self.config_data.get('msg_join_vc', "uh suh dudes, what's up?")))
        self.entry_msg_stop.delete(0, 'end'); self.entry_msg_stop.insert(0, prof_data.get('msg_stop_talking', self.config_data.get('msg_stop_talking', 'my bad. zipping it.')))
        self.entry_msg_vocal_ready.delete(0, 'end'); self.entry_msg_vocal_ready.insert(0, prof_data.get('msg_vocal_cords_ready', self.config_data.get('msg_vocal_cords_ready', "my vocal cords are finally warmed up. what's up?")))
        self.entry_msg_leave_vc.delete(0, 'end'); self.entry_msg_leave_vc.insert(0, prof_data.get('msg_leave_vc', self.config_data.get('msg_leave_vc', 'aw man, really? you want me to leave? fine.')))

        self.var_lowercase.set(self.config_data.get('force_lowercase', True))
        self.entry_banned.delete(0, 'end'); self.entry_banned.insert(0, ', '.join(self.config_data.get('banned_inputs', ['n-word', 'slur'])))
        self.entry_removed.delete(0, 'end'); self.entry_removed.insert(0, ', '.join(self.config_data.get('removed_words', [])))
        self.text_replacements.delete('1.0', 'end'); self.text_replacements.insert('1.0', self.dict_to_text(self.config_data.get('word_replacements', {"you're still on about": "we are talking about", "that's... concerning": "that's crazy"})))

        self.var_voice.set(self.config_data.get('enable_voice', True))
        self.var_autojoin.set(self.config_data.get('auto_join_vc', True))
        self.var_dm_voice.set(self.config_data.get('allow_dm_voice', True))
        self.var_thinking_music.set(self.config_data.get('enable_thinking_music', False))
        
        if hasattr(self, 'var_dyn_emotions'):
            self.var_dyn_emotions.set(self.config_data.get('dynamic_emotions', False))
        
        enabled_emos = self.config_data.get('enabled_emotions', {})
        for emo, var in self.emo_vars.items():
            var.set(enabled_emos.get(emo, True))

        enabled_dbgs = self.config_data.get('debug_modules', {})
        for mod, var in self.debug_vars.items():
            var.set(enabled_dbgs.get(mod, True))

        v_corr = self.config_data.get('voice_corrections', {"gonna": "going to", "wanna": "want to"})
        self.text_stt_corrections.delete('1.0', 'end')
        self.text_stt_corrections.insert('1.0', self.dict_to_text(v_corr))
        
        t_pron = self.config_data.get('tts_pronunciations', {r"\blmao\b": "el em ay oh"})
        self.text_tts_pronunciations.delete('1.0', 'end')
        self.text_tts_pronunciations.insert('1.0', self.dict_to_text(t_pron))

        self.var_stats.set(self.config_data.get('enable_stats', True))
        self.text_auto_replies.delete('1.0', 'end'); self.text_auto_replies.insert('1.0', self.dict_to_text(self.config_data.get('auto_replies', {'fortnite': 'imagine fortnite :ahhhh:', 'valorant': 'imagine valorant :sadge:'})))
        self.stat_preview.delete('1.0', 'end'); self.stat_preview.insert('1.0', json.dumps(self.config_data.get('custom_stats', []), indent=2))
        
        self.theme_menu.set(self.config_data.get('theme', 'Dark'))
        
        current_scale = self.config_data.get('ui_scaling', 1.0)
        scale_str = f"{int(round(current_scale * 100))}%"
        if hasattr(self, 'scale_menu'): self.scale_menu.set(scale_str)
        if hasattr(self, 'ctrl_scale_menu'): self.ctrl_scale_menu.set(scale_str)
            
        self.apply_accent_color(self.config_data.get('accent_color', '#d1d1d1'))
        
        self.refresh_model_list()
        self.load_advanced_file(self.file_selector.get())
        
        if hasattr(self, 'entry_repo'):
            self.entry_repo.delete(0, 'end')
            self.entry_repo.insert(0, self.config_data.get('github_repo_url', 'JackBJ27/DoppelBot'))

        if full_reload:
            self.refresh_server_list()
        
        brain_ok = os.path.exists(BRAIN_FILE) and os.path.getsize(BRAIN_FILE) > 10
        soul_ok = os.path.exists(SOUL_FILE) and os.path.getsize(SOUL_FILE) > 10

        if brain_ok and soul_ok:
            self.setup_frame.pack_forget()
        else:
            self.setup_frame.pack(fill='x', padx=20, pady=10)

        for tb in self.smart_textboxes:
            try: tb._textbox.event_generate("<KeyRelease>")
            except: pass

        self.last_saved_state = json.dumps(self.config_data, sort_keys=True)

    def add_stat(self):
        new_stat = {
            'stat_name': self.stat_name.get().strip(),
            'alias': getattr(self, 'stat_alias', self.stat_name).get().strip() or self.stat_name.get().strip(),
            'user': self.stat_user.get().strip(),
            'triggers': [x.strip() for x in self.stat_triggers.get().split(',') if x.strip()],
            'message': self.stat_msg.get().strip()
        }
        if not new_stat['stat_name'] or not new_stat['triggers']:
            show_popup('Error', 'You need at least a name and some triggers.')
            return
        stats_list = self.config_data.get('custom_stats', [])
        stats_list.append(new_stat)
        self.config_data['custom_stats'] = stats_list
        save_config(self.config_data)
        self.stat_name.delete(0, 'end'); self.stat_alias.delete(0, 'end'); self.stat_user.delete(0, 'end'); self.stat_triggers.delete(0, 'end'); self.stat_msg.delete(0, 'end')
        self.stat_preview.delete('1.0', 'end'); self.stat_preview.insert('1.0', json.dumps(self.config_data.get('custom_stats', []), indent=2))
        self.save_all_silent()
        self.stat_preview._textbox.event_generate("<KeyRelease>")
        show_popup('Added', 'Stat added to config!')

    def load_advanced_file(self, filename):
        path = os.path.join(SCRIPT_DIR, filename)
        self.advanced_text.delete('1.0', 'end')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: self.advanced_text.insert('1.0', f.read())
        else: self.advanced_text.insert('1.0', f'// {filename} does not exist yet.')
        self.current_advanced_file = path
        self.advanced_text._textbox.event_generate("<KeyRelease>")

    def save_advanced_file(self):
        with open(self.current_advanced_file, 'w', encoding='utf-8') as f:
            f.write(self.advanced_text.get('1.0', 'end-1c'))
        if 'config.json' in self.current_advanced_file: self.reload_ui_from_config()
        show_popup('Saved', f'Overwrote {os.path.basename(self.current_advanced_file)} successfully.')

if __name__ == '__main__':
    app = App()
    app.mainloop()
