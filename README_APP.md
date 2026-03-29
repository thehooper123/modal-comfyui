# 🎬 FitSweetTreat Video Automation System

**Complete end-to-end automation for creating, scheduling, and posting AI-generated food videos to TikTok, Instagram, and YouTube.**

> **Status**: ✅ Complete & Production-Ready

---

## 🎯 What This Does

1. **Takes a recipe prompt** → "Make a healthy protein bowl video"
2. **Generates a 3-scene video script** → Using Gemini AI (with character voices)
3. **Creates AI-generated video clips** → Using LTX-2.3 or Krea video models
4. **Adds voice-over narration** → Using KokoroTTS (local)
5. **Stitches everything together** → With background music
6. **Queues for review** → In your local app
7. **Automatically posts to social media** → At scheduled times
8. **Posts to all platforms** → TikTok, Instagram, YouTube simultaneously

**Total time per video**: ~15 minutes (generation) + instant posting at scheduled times

---

## 📦 Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **app.py** | Main UI application (Tkinter) | ✅ Complete |
| **callback_server.py** | Receives videos from n8n | ✅ Complete |
| **n8n_workflow_with_callback.json** | Video generation orchestration | ✅ Complete |
| **.env** | Your API credentials | ⚠️ Need to fill |
| **SETUP_GUIDE.md** | Detailed documentation | ✅ Complete |
| **requirements.txt** | Python dependencies | ✅ Complete |
| **start.sh / start.bat** | One-click launcher | ✅ Complete |

---

## ⚡ Quick Start (2 Minutes)

### Linux/Mac
```bash
cd /workspaces/modal-comfyui
chmod +x start.sh
./start.sh
```

### Windows
```bash
cd C:\path\to\modal-comfyui
start.bat
```

### Manual (if scripts don't work)
```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Start callback server (Terminal 1)
python callback_server.py

# Start main app (Terminal 2)
python app.py
```

---

## 🎨 User Interface (5 Tabs)

### 1️⃣ **Generate** Tab
- Enter recipe prompt
- Click "Generate Video (via n8n) ✓"
- Watch real-time progress
- See George's 3-scene script live
- Video automatically added to Queue

### 2️⃣ **Queue** Tab
- Review pending videos
- Open video file to preview
- Click "Approve + Schedule"
- Choose platforms & times
- Delete unwanted videos

### 3️⃣ **Schedule Posts** Tab
- View all scheduled posts
- See posting times & status
- Monitor success/failures
- Delete scheduled posts if needed

### 4️⃣ **Settings** Tab
- Store API credentials (encrypted)
- View service endpoints
- Credentials auto-saved securely

### 5️⃣ **Logs** Tab
- Real-time system activity
- Error tracking
- Debugging information

---

## 🔑 Required API Keys (Setup in `.env`)

```bash
# Essential
GEMINI_API_KEY=xxx              # Get from https://aistudio.google.com
N8N_CHAT_WEBHOOK=http://...    # Your n8n webhook URL
N8N_CALLBACK_WEBHOOK=http://... # Callback URL (usually localhost:5000)

# Social Media (for posting)
TIKTOK_API_KEY=xxx              # TikTok Business API
INSTAGRAM_API_TOKEN=xxx         # Meta Graph API token
YOUTUBE_API_KEY=xxx             # YouTube Data API key

# Services (if not localhost)
KOKORO_URL=http://localhost:8000
COMFYUI_URL=https://...          # Fallback video generation
```

### Getting API Keys (5 min per platform)

**🤖 Gemini API** (FREE)
> https://aistudio.google.com → "Get API Key" → Copy paste

**🎵 TikTok API**
> https://developers.tiktok.com → Create app → Business API → Get credentials

**📸 Instagram API**
> https://developers.facebook.com → Apps → Instagram Graph API → Generate token

**▶️ YouTube API**
> https://console.cloud.google.com → APIs → YouTube Data v3 → Create credentials

---

## 🔄 Data Flow Diagram

```
User Input (Recipe)
       ↓
    [app.py] ← User clicks "Generate"
       ↓
    n8n POST /webhook/chat-trigger
       ↓
─────────────────────────────────────
│ n8n Workflow (n8n_workflow.json) │
│ ────────────────────────────── │
│ 1. Gemini: Generate 3 scenes   │
│ 2. KokoroTTS: Bella intro      │
│ 3. KokoroTTS: George scenes    │
│ 4. Krea API: Generate videos   │
│ 5. Modal Stitcher: Combine    │
│ 6. Callback: Send to Python    │
─────────────────────────────────────
       ↓
    callback_server.py (Port 5000)
       ↓
    [app.py receives video]
       ↓
    SQLite Database
       ├─ video_queue (for review)
       └─ scheduled_posts (for posting)
       ↓
    Background posting thread
       ├─ TikTok API POST
       ├─ Instagram API POST
       └─ YouTube API POST
```

---

## 🗂️ File Structure

```
modal-comfyui/
├── app.py                          # Main app (run this!)
├── callback_server.py              # Video delivery server
├── n8n_workflow_with_callback.json # Import into n8n
├── requirements.txt                # Python dependencies
├── .env.example                    # Copy & edit this
├── .env                            # Your credentials (git ignored)
├── start.sh                        # Linux/Mac launcher
├── start.bat                       # Windows launcher
├── SETUP_GUIDE.md                  # Detailed setup
├── README.md                       # This file
├── app_database.db                 # SQLite (auto-created)
├── credentials.vault               # Encrypted creds (auto-created)
├── .vault_key                      # Encryption key (git ignored)
├── temp/                           # Working files (deleted after)
├── output/                         # Final MP4s (keep forever)
└── assets/                         # BG music etc
```

---

## 🚀 Workflow Examples

### Example 1: Simple Recipe
```
Input: "Make a chocolate chip cookie recipe for TikTok"
      ↓
George: Writes 3-scene script with introduction, baking step, beauty shot
      ↓
n8n: Generates 3 videos + narration + background music (12 min)
      ↓
Output: 60-second vertical video ready for posting
```

### Example 2: Healthy Bowl
```
Input: "Healthy quinoa Buddha bowl - vegan, green goddess dressing"
      ↓
George: Creates script focusing on fresh ingredients, prep, final presentation
      ↓
n8n: Generates cinematic food video with ASMR sounds
      ↓
Queue: Video ready for approval
      ↓
Schedule: Post to TikTok (2PM), Instagram (4PM), YouTube (6PM)
      ↓
Auto-post: At scheduled times (user receives notification)
```

---

## 🔌 Integration Points

### n8n → Python App
```
n8n sends POST to: http://localhost:5000/n8n-callback
Payload:
{
  "sessionId": "20240101_120000",
  "finalVideoUrl": "https://..../video.mp4",
  "georgeJson": {...}
}
```

### Python App → Social Media
```
TikTok:   POST /v1/video/upload (business API)
Instagram: POST /graph/api/v18.0/{id}/media (Meta)
YouTube:  POST /v1/videos?part=snippet (Google)
```

---

## 🔐 Security

### Credentials Are Encrypted
- All API keys stored encrypted with Fernet (AES)
- Encryption key generated once: `.vault_key`
- Never logged or transmitted
- Only decrypted in memory when needed

### Vault Structure
```
credentials.vault  ← Encrypted blob of {
                      "gemini_api_key": "...",
                      "tiktok_api_key": "...",
                      ...
                    }
.vault_key         ← Symmetric encryption key (keep private!)
app_database.db    ← SQLite with video/post records
```

---

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Port 5000 already in use | Another app using it | `lsof -i :5000` and kill, or change port in code |
| n8n connection refused | n8n not running | Start n8n: `docker run -it -p 5678:5678 n8nio/n8n` |
| KokoroTTS errors | TTS server down | Restart: `docker restart kokoro-tts` |
| Video timeout | Generation too slow | Increase timeout: edit `wait_and_download(..., timeout=3600)` |
| API key invalid | Wrong credentials | Paste into .env, save, restart app |
| Social media posting fails | Rate limited | Wait 1 hour, retry from Schedule tab |
| Database locked | Concurrent access | Kill other Python processes, restart |

---

## 📊 Database Schema

### video_queue Table
```sql
id              INTEGER PRIMARY KEY
recipe_name     TEXT              — Recipe name from George
george_json     TEXT              — Full script data (JSON)
final_video_path TEXT             — Local MP4 path
final_video_url TEXT              — URL from n8n
status          TEXT DEFAULT pending  — pending, approved
created_at      DATETIME          — Auto timestamped
approved_at     DATETIME          — When approved
```

### scheduled_posts Table
```sql
id              INTEGER PRIMARY KEY
video_id        INTEGER FOREIGN KEY  — Reference to video_queue
platform        TEXT                 — tiktok, instagram, youtube
scheduled_time  DATETIME             — ISO format (e.g., 2024-01-15T14:30:00)
caption         TEXT                 — "Chocolate chip cookies are life"
hashtags        TEXT                 — "#FitSweetTreat #Baking #Cookies"
status          TEXT DEFAULT pending  — pending, posted, failed
posted_at       DATETIME             — When actually posted
error_msg       TEXT                 — Error if failed
created_at      DATETIME             — Auto timestamped
```

---

## 🎓 Advanced Configuration

### Using Different Video Models
Edit in `app.py`:
```python
# Default: Krea AI via n8n
# Change n8n workflow to use Modal/LTX instead

# Or use Modal ComfyUI directly (change ComfyUIBridge)
COMFYUI_URL = "https://your-modal-url.modal.run"
```

### Custom TTS Voices
Edit in n8n workflow:
```
Bella's Voice Generation: voice="af_bella"  ← Change to: af_default, bm_default, etc
George's Voice Takeover: voice="bm_george" ← Change to your favorite male voice
```

### Batch Processing
```python
# Queue multiple recipes at once in app.py
# Implement loop in _start_pipeline()
recipes = ["recipe1", "recipe2", "recipe3"]
for recipe in recipes:
    self._run_pipeline(recipe, api_key)
```

---

## 📈 Performance Tips

### Faster Generation
- Use 512p instead of 768p resolution
- Use 2 scenes instead of 3
- Use 10 steps instead of 20
- Force GPU: Check Modal dashboard

### Lower Cost
- TikTok: FREE ✓
- Instagram: FREE ✓
- YouTube: FREE ✓
- Gemini: ~$0.075/1M tokens ✓
- KokoroTTS: Free (local) ✓
- Krea AI: ~$0.50-2.00 per video
- Modal/LTX: $4.73/hr for A100 (use scheduled)

### Concurrent Posting
- Background thread handles all platforms in parallel
- Automatic retry on failure
- Rate-limit aware

---

## 🤝 Contributing

This system is complete and production-ready. To extend it:

1. **Add new social platforms**: Extend `SocialMediaPoster` class
2. **Custom video generators**: Modify `N8NOrchestrator` or `ComfyUIBridge`
3. **New TTS providers**: Add to `KokoroTTS` class
4. **Analytics**: Add to `Database` class

---

## 📝 Checklist Before First Use

- [ ] Python 3.9+ installed
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file created and filled with API keys
- [ ] n8n running on http://localhost:5678
- [ ] KokoroTTS running on http://localhost:8000
- [ ] n8n workflow imported from `n8n_workflow_with_callback.json`
- [ ] Callback server ready to start: `python callback_server.py`
- [ ] Main app ready to start: `python app.py`
- [ ] Tested with 1 recipe prompt
- [ ] Social media credentials working

---

## 🎬 Next Features (Future)

- [ ] Pinterest integration
- [ ] Discord/Telegram notifications
- [ ] Analytics dashboard
- [ ] A/B testing (different captions)
- [ ] Batch processing (CSV upload)
- [ ] Cloud storage (AWS S3)
- [ ] Video thumbnails + custom branding
- [ ] Multi-language support

---

## 📞 Support

- **Bug Reports**: Check logs tab for error messages
- **Setup Issues**: See SETUP_GUIDE.md detailed troubleshooting
- **API Issues**: Check respective platform documentation
- **Performance**: Monitor Modal/Krea dashboards

---

## 📜 License

This project is configured for FitSweetTreat video automation. Use responsibly.

---

## 🙏 Acknowledgments

Built with:
- **n8n** - Open-source workflow automation
- **Gemini** - Google's LLM for script generation
- **LTX-2.3** - Lightricks video generation (Modal)
- **KokoroTTS** - Open-source text-to-speech
- **Meta/Google/TikTok** - Social media APIs

---

**Ready to automate your food video empire? Let's go! 🚀**

Questions? Check `SETUP_GUIDE.md` for detailed explanations.

Last Updated: 2024 | Version: 1.0.0 | Status: ✅ Production Ready
