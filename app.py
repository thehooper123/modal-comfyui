"""
FitSweetTreat Video Automation App
Full pipeline: Prompt -> n8n (Bella/George/TTS/Video) -> Social Media Posting
"""

import os
import sys
import json
import time
import sqlite3
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from dataclasses import dataclass, asdict
import hashlib
import mimetypes

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "app_database.db"
CREDS_PATH = ROOT_DIR / "credentials.vault"
TEMP_DIR = ROOT_DIR / "temp"
OUTPUT_DIR = ROOT_DIR / "output"
ASSETS_DIR = ROOT_DIR / "assets"

# n8n endpoints
N8N_CHAT_WEBHOOK = os.getenv("N8N_CHAT_WEBHOOK", "http://localhost:5678/webhook/chat-trigger")
N8N_CALLBACK_WEBHOOK = os.getenv("N8N_CALLBACK_WEBHOOK", "http://localhost:5000/n8n-callback")

# Fallback to Modal ComfyUI if n8n fails
COMFYUI_URL = "https://chlevin135--modal-comfyui-ui.modal.run"
KOKORO_URL = "http://localhost:8000"
BG_MUSIC_URL = "https://www.chosic.com/wp-content/uploads/2021/07/The-Wait-Extreme-Music.mp3"
GEMINI_MODEL = "gemini-2.5-flash"

GEORGE_SYSTEM_PROMPT = (
    "You are George, a video production expert for FitSweetTreat, a healthy food short-form channel.\n"
    "Given a food recipe prompt, produce a structured 3-scene video script as JSON.\n\n"
    "Output ONLY valid JSON matching this exact schema. No markdown, no code fences, no extra text:\n"
    "{\n"
    "  \"recipe_name\": \"Short dish name\",\n"
    "  \"script\": \"Full narration across all 3 scenes\",\n"
    "  \"video_scenes\": [\n"
    "    {\n"
    "      \"scene\": 1,\n"
    "      \"voiceText\": \"Hi, I'm George, this is FitSweetTreat and today we're making [DISH]. [Hook]. About 20 words.\",\n"
    "      \"videoPrompt\": \"40-60 word cinematic opening. Camera movement, lighting, textures, ambient audio.\"\n"
    "    },\n"
    "    {\n"
    "      \"scene\": 2,\n"
    "      \"voiceText\": \"One sentence about the main cooking step. About 20 words.\",\n"
    "      \"videoPrompt\": \"40-60 word mid-scene shot. Action, close-ups, sizzle sounds, steam, camera angle.\"\n"
    "    },\n"
    "    {\n"
    "      \"scene\": 3,\n"
    "      \"voiceText\": \"Final line ending with the word but or so. About 20 words.\",\n"
    "      \"videoPrompt\": \"40-60 word beauty shot. Warm golden light, full dish reveal, camera pull-back.\"\n"
    "    }\n"
    "  ]\n"
    "}\n\n"
    "Hard rules:\n"
    "- scene 1 voiceText MUST start with: Hi, I'm George, this is FitSweetTreat and today we're making\n"
    "- scene 3 voiceText MUST end with the word: but  OR  so\n"
    "- Each voiceText must be ~20 words (5-8 seconds spoken)\n"
    "- Each videoPrompt must be 40-60 words with camera movement + lighting + audio detail"
)


@dataclass
class ScheduledPost:
    """Represents a scheduled social media post"""
    video_id: int
    platform: str  # tiktok, instagram, youtube
    scheduled_time: str  # ISO format
    caption: str
    hashtags: str
    status: str = "pending"  # pending, posted, failed


class CredentialVault:
    def __init__(self, vault_path=CREDS_PATH):
        self.vault_path = vault_path
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)

    def _load_or_create_key(self):
        key_file = self.vault_path.parent / ".vault_key"
        if key_file.exists():
            return key_file.read_bytes()
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        return key

    def save_credentials(self, creds_dict):
        data = json.dumps(creds_dict).encode()
        self.vault_path.write_bytes(self.cipher.encrypt(data))

    def load_credentials(self):
        if not self.vault_path.exists():
            return {}
        try:
            return json.loads(self.cipher.decrypt(self.vault_path.read_bytes()).decode())
        except Exception:
            return {}


class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        
        # Video queue table
        conn.execute(
            "CREATE TABLE IF NOT EXISTS video_queue ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  recipe_name TEXT,"
            "  george_json TEXT,"
            "  final_video_path TEXT,"
            "  final_video_url TEXT,"
            "  status TEXT DEFAULT 'pending',"
            "  created_at TEXT DEFAULT (datetime('now')),"
            "  approved_at TEXT"
            ")"
        )
        
        # Scheduled posts table
        conn.execute(
            "CREATE TABLE IF NOT EXISTS scheduled_posts ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  video_id INTEGER NOT NULL,"
            "  platform TEXT NOT NULL,"
            "  scheduled_time TEXT NOT NULL,"
            "  caption TEXT,"
            "  hashtags TEXT,"
            "  status TEXT DEFAULT 'pending',"
            "  posted_at TEXT,"
            "  error_msg TEXT,"
            "  created_at TEXT DEFAULT (datetime('now')),"
            "  FOREIGN KEY (video_id) REFERENCES video_queue(id)"
            ")"
        )
        
        conn.commit()
        conn.close()

    def add_to_queue(self, recipe_name, george_json, final_video_path, final_video_url=None):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO video_queue (recipe_name, george_json, final_video_path, final_video_url) "
            "VALUES (?, ?, ?, ?)",
            (recipe_name, json.dumps(george_json), str(final_video_path), final_video_url),
        )
        vid_id = c.lastrowid
        conn.commit()
        conn.close()
        return vid_id

    def approve(self, vid_id):
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE video_queue SET status='approved', approved_at=datetime('now') WHERE id=?",
            (vid_id,),
        )
        conn.commit()
        conn.close()

    def delete(self, vid_id):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM video_queue WHERE id=?", (vid_id,))
        conn.execute("DELETE FROM scheduled_posts WHERE video_id=?", (vid_id,))
        conn.commit()
        conn.close()

    def get_pending(self):
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT id, recipe_name, final_video_path, created_at FROM video_queue "
            "WHERE status='pending' ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return rows

    def add_scheduled_post(self, video_id, platform, scheduled_time, caption, hashtags):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO scheduled_posts (video_id, platform, scheduled_time, caption, hashtags) "
            "VALUES (?, ?, ?, ?, ?)",
            (video_id, platform, scheduled_time, caption, hashtags),
        )
        post_id = c.lastrowid
        conn.commit()
        conn.close()
        return post_id

    def get_scheduled_posts_due(self):
        """Get posts that should be posted now"""
        conn = sqlite3.connect(DB_PATH)
        now = datetime.now().isoformat()
        rows = conn.execute(
            "SELECT id, video_id, platform, caption, hashtags "
            "FROM scheduled_posts "
            "WHERE status='pending' AND scheduled_time<=? "
            "ORDER BY scheduled_time ASC",
            (now,),
        ).fetchall()
        conn.close()
        return rows

    def update_post_status(self, post_id, status, error_msg=None):
        conn = sqlite3.connect(DB_PATH)
        if status == "posted":
            conn.execute(
                "UPDATE scheduled_posts SET status=?, posted_at=datetime('now') WHERE id=?",
                (status, post_id),
            )
        else:
            conn.execute(
                "UPDATE scheduled_posts SET status=?, error_msg=? WHERE id=?",
                (status, error_msg, post_id),
            )
        conn.commit()
        conn.close()

    def get_video_path(self, video_id):
        conn = sqlite3.connect(DB_PATH)
        path = conn.execute(
            "SELECT final_video_path FROM video_queue WHERE id=?", (video_id,)
        ).fetchone()
        conn.close()
        return path[0] if path else None


class GeminiGeorge:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=GEORGE_SYSTEM_PROMPT)

    def generate_scenes(self, user_prompt):
        response = self.model.generate_content(user_prompt)
        text = response.text.strip()
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())


class N8NOrchestrator:
    """Sends prompts to n8n workflow and handles callbacks"""
    
    def __init__(self, webhook_url=N8N_CHAT_WEBHOOK):
        self.webhook_url = webhook_url
        self.callbacks = {}  # session_id -> callback function

    def submit_recipe(self, recipe_prompt, session_id):
        """Submit recipe to n8n workflow"""
        try:
            payload = {
                "chatInput": recipe_prompt,
                "sessionId": session_id,
            }
            resp = requests.post(self.webhook_url, json=payload, timeout=30)
            resp.raise_for_status()
            return {"success": True, "session_id": session_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def register_callback(self, session_id, callback_fn):
        """Register a callback for when n8n completes"""
        self.callbacks[session_id] = callback_fn

    def handle_callback(self, session_id, final_video_url, george_json):
        """Called by n8n callback endpoint"""
        if session_id in self.callbacks:
            self.callbacks[session_id](final_video_url, george_json)
            del self.callbacks[session_id]


class SocialMediaPoster:
    """Handles posting to TikTok, Instagram, YouTube"""

    def __init__(self, credentials):
        self.tiktok_token = credentials.get("tiktok_api_key")
        self.instagram_token = credentials.get("instagram_api_token")
        self.youtube_key = credentials.get("youtube_api_key")

    def post_to_tiktok(self, video_path, caption, hashtags):
        """Post to TikTok via official API"""
        try:
            with open(video_path, "rb") as f:
                files = {"video": f}
                data = {
                    "description": f"{caption}\n\n{hashtags}",
                    "access_token": self.tiktok_token,
                }
                # TikTok Business API endpoint
                resp = requests.post(
                    "https://open.tiktok.com/v1/video/upload",
                    data=data,
                    files=files,
                    timeout=600,
                )
                resp.raise_for_status()
                result = resp.json()
                if result.get("data", {}).get("video_id"):
                    return {"success": True, "video_id": result["data"]["video_id"]}
                return {"success": False, "error": "No video_id returned"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_instagram(self, video_path, caption, hashtags):
        """Post to Instagram via Meta Graph API"""
        try:
            # Get Instagram Business Account ID first
            ig_user = requests.get(
                "https://graph.instagram.com/me",
                params={"access_token": self.instagram_token, "fields": "instagram_business_account"},
                timeout=30,
            ).json()
            
            ig_business_id = ig_user.get("instagram_business_account", {}).get("id")
            if not ig_business_id:
                return {"success": False, "error": "Could not find Instagram Business Account"}

            # Upload video as a container
            with open(video_path, "rb") as f:
                upload = requests.post(
                    f"https://graph.instagram.com/{ig_business_id}/media",
                    data={
                        "media_type": "VIDEO",
                        "video_url": f"file://{video_path}",  # or upload to temp storage first
                        "caption": f"{caption}\n\n{hashtags}",
                        "access_token": self.instagram_token,
                    },
                    timeout=600,
                ).json()

            if upload.get("id"):
                # Publish the container
                publish = requests.post(
                    f"https://graph.instagram.com/{ig_business_id}/media_publish",
                    data={
                        "creation_id": upload["id"],
                        "access_token": self.instagram_token,
                    },
                    timeout=30,
                ).json()
                if publish.get("id"):
                    return {"success": True, "post_id": publish["id"]}

            return {"success": False, "error": json.dumps(upload)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_to_youtube(self, video_path, caption, hashtags):
        """Post to YouTube via official API"""
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request

            # Build request body
            body = {
                "snippet": {
                    "title": caption[:100],
                    "description": f"{caption}\n\n{hashtags}",
                    "tags": hashtags.split(),
                    "categoryId": "26",  # Howto & Style
                },
                "status": {"privacyStatus": "public"},
            }

            # Insert video
            request = self.youtube_service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=MediaFileUpload(video_path, mimetype="video/mp4", resumable=True),
            )

            response = None
            while response is None:
                status, response = request.next_chunk()

            return {"success": True, "video_id": response["id"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_video(self, platform, video_path, caption, hashtags):
        """Route to appropriate platform"""
        if platform == "tiktok":
            return self.post_to_tiktok(video_path, caption, hashtags)
        elif platform == "instagram":
            return self.post_to_instagram(video_path, caption, hashtags)
        elif platform == "youtube":
            return self.post_to_youtube(video_path, caption, hashtags)
        else:
            return {"success": False, "error": f"Unknown platform: {platform}"}


def ensure_dirs():
    for d in (TEMP_DIR, OUTPUT_DIR, ASSETS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def download_bg_music(log_cb=None):
    bg_path = ASSETS_DIR / "bg_music.mp3"
    if bg_path.exists():
        return str(bg_path)
    if log_cb:
        log_cb("Downloading background music (one-time)...")
    try:
        r = requests.get(BG_MUSIC_URL, timeout=60, stream=True)
        r.raise_for_status()
        with open(bg_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return str(bg_path)
    except Exception as e:
        if log_cb:
            log_cb(f"BG music download failed: {e}")
        return None


class VideoProcessor:
    """Download video from n8n/Modal and process if needed"""
    
    @staticmethod
    def download_video(url, output_path, progress_cb=None):
        """Download video from n8n callback URL"""
        try:
            if progress_cb:
                progress_cb("Downloading video from n8n...")
            
            resp = requests.get(url, timeout=600, stream=True)
            resp.raise_for_status()
            
            with open(output_path, "wb") as f:
                total = int(resp.headers.get("content-length", 0))
                downloaded = 0
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb and total > 0:
                        pct = int(100 * downloaded / total)
                        progress_cb(f"Downloading... {pct}%")
            
            return str(output_path)
        except Exception as e:
            if progress_cb:
                progress_cb(f"Download error: {e}")
            raise


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FitSweetTreat Video Automation")
        self.root.geometry("1200x900")
        ensure_dirs()
        self.vault = CredentialVault()
        self.db = Database()
        self.credentials = self.vault.load_credentials()
        self.n8n = N8NOrchestrator()
        self.poster = SocialMediaPoster(self.credentials)
        self._pipeline_running = False
        self._posting_running = False
        
        # Start background posting thread
        self._start_posting_thread()
        
        self._build_ui()

    def _build_ui(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tab_gen = ttk.Frame(nb)
        self.tab_queue = ttk.Frame(nb)
        self.tab_schedule = ttk.Frame(nb)
        self.tab_settings = ttk.Frame(nb)
        self.tab_logs = ttk.Frame(nb)
        
        nb.add(self.tab_gen, text="Generate")
        nb.add(self.tab_queue, text="Queue")
        nb.add(self.tab_schedule, text="Schedule Posts")
        nb.add(self.tab_settings, text="Settings")
        nb.add(self.tab_logs, text="Logs")
        
        self._build_generate_tab()
        self._build_queue_tab()
        self._build_schedule_tab()
        self._build_settings_tab()
        self._build_logs_tab()

    def _build_generate_tab(self):
        f = ttk.Frame(self.tab_gen, padding=12)
        f.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(f, text="Recipe Prompt", font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(f, text="Describe the dish, ingredients, macros, and style.", foreground="#555").pack(anchor="w")
        self.prompt_input = tk.Text(f, height=7, width=140, wrap=tk.WORD)
        self.prompt_input.pack(fill=tk.X, pady=(5, 8))
        
        btn_row = ttk.Frame(f)
        btn_row.pack(fill=tk.X)
        self.gen_btn = ttk.Button(btn_row, text="Generate Video (via n8n) >>>", command=self._start_pipeline)
        self.gen_btn.pack(side=tk.LEFT, padx=5)
        self.status_lbl = ttk.Label(btn_row, text="Ready", foreground="#007700", font=("Arial", 11, "bold"))
        self.status_lbl.pack(side=tk.LEFT, padx=15)
        
        self.progress = ttk.Progressbar(f, mode="indeterminate", length=600)
        self.progress.pack(fill=tk.X, pady=6)
        
        ttk.Label(f, text="George's 3-Scene Plan (live):", font=("Arial", 11, "bold")).pack(anchor="w", pady=(8, 2))
        self.plan_text = scrolledtext.ScrolledText(f, height=20, width=140, state=tk.DISABLED, wrap=tk.WORD)
        self.plan_text.pack(fill=tk.BOTH, expand=True)

    def _build_queue_tab(self):
        f = ttk.Frame(self.tab_queue, padding=12)
        f.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(f, text="Pending Review", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 8))
        cols = ("ID", "Recipe", "Video Path", "Created")
        self.queue_tree = ttk.Treeview(f, columns=cols, show="headings", height=15)
        self.queue_tree.heading("ID", text="ID")
        self.queue_tree.heading("Recipe", text="Recipe")
        self.queue_tree.heading("Video Path", text="Video Path")
        self.queue_tree.heading("Created", text="Created")
        self.queue_tree.column("ID", width=40)
        self.queue_tree.column("Recipe", width=250)
        self.queue_tree.column("Video Path", width=550)
        self.queue_tree.column("Created", width=150)
        self.queue_tree.pack(fill=tk.BOTH, expand=True)
        
        bf = ttk.Frame(f)
        bf.pack(fill=tk.X, pady=8)
        ttk.Button(bf, text="Refresh", command=self._refresh_queue).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="Approve + Schedule", command=self._approve_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="Open File", command=self._open_video).pack(side=tk.LEFT, padx=4)
        
        self._refresh_queue()

    def _build_schedule_tab(self):
        f = ttk.Frame(self.tab_schedule, padding=12)
        f.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(f, text="Scheduled Posts", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 8))
        cols = ("ID", "Video ID", "Platform", "Scheduled", "Status")
        self.schedule_tree = ttk.Treeview(f, columns=cols, show="headings", height=12)
        self.schedule_tree.heading("ID", text="ID")
        self.schedule_tree.heading("Video ID", text="Video ID")
        self.schedule_tree.heading("Platform", text="Platform")
        self.schedule_tree.heading("Scheduled", text="Scheduled Time")
        self.schedule_tree.heading("Status", text="Status")
        
        for col in cols:
            self.schedule_tree.column(col, width=150)
        self.schedule_tree.pack(fill=tk.BOTH, expand=True)
        
        bf = ttk.Frame(f)
        bf.pack(fill=tk.X, pady=8)
        ttk.Button(bf, text="Refresh", command=self._refresh_schedule).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="Delete Scheduled", command=self._delete_scheduled).pack(side=tk.LEFT, padx=4)
        
        self._refresh_schedule()

    def _build_settings_tab(self):
        f = ttk.Frame(self.tab_settings, padding=12)
        f.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(f, text="API Credentials", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))
        self._cred_entries = {}
        for label, key in [
            ("Gemini API Key", "gemini_api_key"),
            ("TikTok API Key", "tiktok_api_key"),
            ("Instagram Token", "instagram_api_token"),
            ("YouTube API Key", "youtube_api_key"),
        ]:
            ttk.Label(f, text=label + ":").pack(anchor="w")
            e = ttk.Entry(f, width=80, show="*")
            e.pack(anchor="w", pady=(2, 8))
            e.insert(0, self.credentials.get(key, ""))
            self._cred_entries[key] = e
        
        ttk.Button(f, text="Save Credentials", command=self._save_credentials).pack(pady=8, anchor="w")
        ttk.Separator(f).pack(fill=tk.X, pady=10)
        
        ttk.Label(f, text="Service Endpoints", font=("Arial", 11, "bold")).pack(anchor="w", pady=(8, 5))
        ttk.Label(f, text=f"n8n Chat Webhook: {N8N_CHAT_WEBHOOK}").pack(anchor="w")
        ttk.Label(f, text=f"ComfyUI (fallback): {COMFYUI_URL}").pack(anchor="w")
        ttk.Label(f, text=f"KokoroTTS: {KOKORO_URL}").pack(anchor="w")
        ttk.Label(f, text=f"Gemini Model: {GEMINI_MODEL}").pack(anchor="w")

    def _build_logs_tab(self):
        f = ttk.Frame(self.tab_logs, padding=12)
        f.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(f, text="System Logs", font=("Arial", 12, "bold")).pack(anchor="w")
        self.logs_text = scrolledtext.ScrolledText(f, height=40, wrap=tk.WORD, font=("Courier", 9))
        self.logs_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.logs_text.config(state=tk.DISABLED)
        self._log("App started. Ready.")

    def _save_credentials(self):
        creds = {k: e.get() for k, e in self._cred_entries.items()}
        self.vault.save_credentials(creds)
        self.credentials = creds
        self.poster = SocialMediaPoster(creds)
        messagebox.showinfo("Saved", "Credentials saved securely.")
        self._log("Credentials updated.")

    def _start_pipeline(self):
        if self._pipeline_running:
            messagebox.showwarning("Busy", "Pipeline already running.")
            return
        
        prompt = self.prompt_input.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input", "Enter a recipe prompt first.")
            return
        
        api_key = self.credentials.get("gemini_api_key") or self._cred_entries["gemini_api_key"].get()
        if not api_key:
            messagebox.showerror("Error", "Set your Gemini API key in Settings first.")
            return
        
        self._pipeline_running = True
        self.gen_btn.config(state=tk.DISABLED)
        self.progress.start(12)
        threading.Thread(target=self._run_pipeline, args=(prompt, api_key), daemon=True).start()

    def _run_pipeline(self, prompt, api_key):
        try:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            self._status("Step 1/5  Generating script with Gemini (George)...")
            george = GeminiGeorge(api_key)
            plan = george.generate_scenes(prompt)
            self._show_plan(plan)
            recipe = plan.get("recipe_name", "Unknown Recipe")
            self._log(f"✓ George created plan: {recipe}")

            self._status("Step 2/5  Submitting to n8n workflow...")
            result = self.n8n.submit_recipe(prompt, session_id)
            if not result["success"]:
                raise Exception(f"n8n submission failed: {result.get('error')}")
            self._log(f"✓ n8n workflow triggered (session: {session_id})")

            self._status("Step 3/5  Waiting for n8n to generate video (5-15 min)...")
            
            # Create a callback
            video_received = threading.Event()
            received_data = {}
            
            def on_video_complete(final_video_url, george_json):
                received_data["url"] = final_video_url
                received_data["plan"] = george_json
                video_received.set()
            
            # Register callback (would be called by n8n webhook)
            self.n8n.register_callback(session_id, on_video_complete)
            
            # Wait for completion (with timeout)
            if not video_received.wait(timeout=1800):  # 30 min timeout
                raise TimeoutError("n8n did not complete within 30 minutes")
            
            final_video_url = received_data["url"]
            final_video_path = OUTPUT_DIR / f"final_{session_id}.mp4"
            
            self._status("Step 4/5  Downloading final video...")
            VideoProcessor.download_video(
                final_video_url, 
                final_video_path,
                progress_cb=self._status
            )
            self._log(f"✓ Video downloaded: {final_video_path}")

            self._status("Step 5/5  Adding to review queue...")
            vid_id = self.db.add_to_queue(recipe, plan, str(final_video_path), final_video_url)
            self._log(f"✓ Added to queue as #{vid_id}")

            self._status(f"Done! '{recipe}' ready for review and scheduling.")
            self.root.after(0, lambda: messagebox.showinfo(
                "Video Ready",
                f"Done! '{recipe}' is in the Queue tab.\n\nReview and approve to schedule posting."
            ))
            self.root.after(0, self._refresh_queue)

        except Exception as exc:
            import traceback
            self._log(f"❌ PIPELINE ERROR: {exc}")
            self._log(traceback.format_exc())
            self._status(f"Error: {exc}")
            self.root.after(0, lambda: messagebox.showerror("Pipeline Error", str(exc)))
        finally:
            self._pipeline_running = False
            self.root.after(0, lambda: self.gen_btn.config(state=tk.NORMAL))
            self.root.after(0, self.progress.stop)

    def _refresh_queue(self):
        for row in self.queue_tree.get_children():
            self.queue_tree.delete(row)
        for row in self.db.get_pending():
            self.queue_tree.insert("", tk.END, values=row)

    def _approve_selected(self):
        sel = self.queue_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a video first.")
            return
        
        vid_id = self.queue_tree.item(sel[0])["values"][0]
        
        # Open scheduling dialog
        self._open_schedule_dialog(vid_id)

    def _open_schedule_dialog(self, vid_id):
        """Open dialog to schedule posts for a video"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Schedule Posts - Video #{vid_id}")
        dialog.geometry("600x500")
        
        f = ttk.Frame(dialog, padding=15)
        f.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(f, text="Video Caption:", font=("Arial", 11, "bold")).pack(anchor="w")
        caption = tk.Text(f, height=3, width=70)
        caption.pack(anchor="w", pady=(2, 10))
        
        ttk.Label(f, text="Hashtags (space-separated):", font=("Arial", 11, "bold")).pack(anchor="w")
        hashtags_var = tk.StringVar(value="#FitSweetTreat #HealthyRecipe #FoodVideo #ShortForm")
        ttk.Entry(f, textvariable=hashtags_var, width=70).pack(anchor="w", pady=(2, 10))
        
        ttk.Label(f, text="Platforms to Post:", font=("Arial", 11, "bold")).pack(anchor="w")
        platforms_frame = ttk.Frame(f)
        platforms_frame.pack(anchor="w", pady=(2, 10))
        
        tiktok_var = tk.BooleanVar(value=True)
        instagram_var = tk.BooleanVar(value=True)
        youtube_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(platforms_frame, text="TikTok", variable=tiktok_var).pack(anchor="w")
        ttk.Checkbutton(platforms_frame, text="Instagram", variable=instagram_var).pack(anchor="w")
        ttk.Checkbutton(platforms_frame, text="YouTube", variable=youtube_var).pack(anchor="w")
        
        ttk.Label(f, text="Schedule Times (one per line, ISO format):", font=("Arial", 11, "bold")).pack(anchor="w")
        times = tk.Text(f, height=6, width=70)
        times.pack(anchor="w", pady=(2, 10))
        # Default: now + 1 hour for each platform
        default_time = (datetime.now() + timedelta(hours=1)).isoformat()
        times.insert("1.0", f"{default_time}\n{default_time}\n{default_time}")
        
        def schedule_posts():
            caption_text = caption.get("1.0", tk.END).strip()
            hashtags_text = hashtags_var.get()
            times_text = times.get("1.0", tk.END).strip().split("\n")
            
            platforms = []
            if tiktok_var.get():
                platforms.append("tiktok")
            if instagram_var.get():
                platforms.append("instagram")
            if youtube_var.get():
                platforms.append("youtube")
            
            # Approve video
            self.db.approve(vid_id)
            
            # Create scheduled posts
            for i, platform in enumerate(platforms):
                if i < len(times_text):
                    scheduled_time = times_text[i].strip()
                    self.db.add_scheduled_post(vid_id, platform, scheduled_time, caption_text, hashtags_text)
                    self._log(f"✓ Scheduled {platform} post for {scheduled_time}")
            
            self._log(f"✓ Video #{vid_id} approved and scheduled")
            self._refresh_queue()
            self._refresh_schedule()
            messagebox.showinfo("Scheduled", f"Video #{vid_id} approved and scheduled for posting.")
            dialog.destroy()
        
        ttk.Button(f, text="Schedule & Approve", command=schedule_posts).pack(pady=10)

    def _delete_selected(self):
        sel = self.queue_tree.selection()
        if not sel:
            return
        if messagebox.askokcancel("Delete", "Delete this video?"):
            vid_id = self.queue_tree.item(sel[0])["values"][0]
            self.db.delete(vid_id)
            self._refresh_queue()
            self._log(f"Video #{vid_id} deleted.")

    def _open_video(self):
        sel = self.queue_tree.selection()
        if not sel:
            return
        path = self.queue_tree.item(sel[0])["values"][2]
        if path and Path(str(path)).exists():
            os.startfile(path) if sys.platform == "win32" else os.system(f"open '{path}'")
        else:
            messagebox.showwarning("Not Found", f"File not found:\n{path}")

    def _refresh_schedule(self):
        """Refresh scheduled posts view (read-only)"""
        for row in self.schedule_tree.get_children():
            self.schedule_tree.delete(row)
        
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT id, video_id, platform, scheduled_time, status FROM scheduled_posts "
            "ORDER BY scheduled_time ASC"
        ).fetchall()
        conn.close()
        
        for row in rows:
            self.schedule_tree.insert("", tk.END, values=row)

    def _delete_scheduled(self):
        sel = self.schedule_tree.selection()
        if not sel:
            return
        if messagebox.askokcancel("Delete", "Delete this scheduled post?"):
            post_id = self.schedule_tree.item(sel[0])["values"][0]
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM scheduled_posts WHERE id=?", (post_id,))
            conn.commit()
            conn.close()
            self._refresh_schedule()
            self._log(f"Scheduled post #{post_id} deleted.")

    def _start_posting_thread(self):
        """Background thread to post videos at scheduled times"""
        def posting_loop():
            while True:
                try:
                    posts = self.db.get_scheduled_posts_due()
                    for post_id, video_id, platform, caption, hashtags in posts:
                        self._log(f"Posting to {platform} (scheduled post #{post_id})...")
                        
                        video_path = self.db.get_video_path(video_id)
                        if not video_path:
                            self._log(f"❌ Video file not found for post #{post_id}")
                            self.db.update_post_status(post_id, "failed", "Video file not found")
                            continue
                        
                        result = self.poster.post_video(platform, video_path, caption, hashtags)
                        if result["success"]:
                            self._log(f"✓ Posted to {platform} successfully")
                            self.db.update_post_status(post_id, "posted")
                        else:
                            error = result.get("error", "Unknown error")
                            self._log(f"❌ Failed to post to {platform}: {error}")
                            self.db.update_post_status(post_id, "failed", error)
                        
                        self.root.after(0, self._refresh_schedule)
                    
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self._log(f"❌ Posting thread error: {e}")
                    time.sleep(60)
        
        threading.Thread(target=posting_loop, daemon=True).start()

    def _status(self, msg):
        self.root.after(0, lambda: self.status_lbl.config(text=msg))
        self._log(msg)

    def _show_plan(self, plan):
        def _update():
            self.plan_text.config(state=tk.NORMAL)
            self.plan_text.delete("1.0", tk.END)
            self.plan_text.insert("1.0", json.dumps(plan, indent=2))
            self.plan_text.config(state=tk.DISABLED)
        self.root.after(0, _update)

    def _log(self, message):
        def _write():
            if not hasattr(self, "logs_text"):
                return
            self.logs_text.config(state=tk.NORMAL)
            ts = datetime.now().strftime("%H:%M:%S")
            self.logs_text.insert(tk.END, f"[{ts}] {message}\n")
            self.logs_text.see(tk.END)
            self.logs_text.config(state=tk.DISABLED)
        self.root.after(0, _write)


def main():
    root = tk.Tk()
    MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
