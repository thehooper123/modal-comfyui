# FitSweetTreat Video Automation - Complete Setup Guide

**End-to-End Pipeline**: Recipe Prompt → Gemini AI → TTS → Video Generation → Social Media Posting

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    FitSweetTreat App (UI)                       │
│  - Recipe input, video queue, scheduling, social media posting  │
└─────────────┬────────────────────────────────────┬──────────────┘
              │                                    │
              ▼                                    ▼
        ┌──────────────┐                    ┌─────────────┐
        │  n8n Core    │                    │  Callback   │
        │  Workflow    │◄──────────────────►│  Server     │
        │ (Gemini AI,  │                    │  (Flask)    │
        │  TTS, Video) │                    └─────────────┘
        └──────────────┘
              │
              ▼
      ┌──────────────────────┐
      │  3 Media Endpoints   │
      ├──────────────────────┤
      │ • KokoroTTS (local)  │
      │ • Krea AI (video)    │
      │ • Modal/LTX (video)  │
      └──────────────────────┘
              │
              ▼
      ┌──────────────────────┐
      │  Output Database     │
      ├──────────────────────┤
      │ • Video Queue        │
      │ • Scheduled Posts    │
      │ • Social Media Logs  │
      └──────────────────────┘
```

## 📋 Prerequisites

### Required Services
- **n8n**: Self-hosted workflow orchestration (http://localhost:5678)
- **KokoroTTS**: Local TTS server (http://localhost:8000)
- **Gemini API**: Google's LLM (free tier available)
- **Social Media API Keys**:
  - TikTok Business API
  - Instagram Graph API
  - YouTube Data API v3

### Python Requirements
- Python 3.9+
- pip or uv package manager

---

## 🚀 Quick Start (5 Steps)

### 1. **Clone & Setup**
```bash
# Navigate to workspace
cd /workspaces/modal-comfyui

# Install dependencies
pip install -r requirements.txt
# OR with uv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. **Configure Environment**
```bash
# Copy example env
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

**Required credentials in `.env`:**
```
GEMINI_API_KEY=your_api_key
TIKTOK_API_KEY=your_tiktok_business_key
INSTAGRAM_API_TOKEN=your_ig_token
YOUTUBE_API_KEY=your_youtube_key
N8N_CHAT_WEBHOOK=http://localhost:5678/webhook/chat-trigger
```

### 3. **Start KokoroTTS**
```bash
# In separate terminal
docker run -p 8000:8000 kokoro-tts:latest
# OR if installed locally
kokoro-server --port 8000
```

### 4. **Start Callback Server**
```bash
# In separate terminal
python callback_server.py
# Runs on http://localhost:5000
```

### 5. **Launch Main App**
```bash
# In main terminal
python app.py
```

The Tkinter UI will open with these tabs:
- **Generate**: Create videos from recipe prompts
- **Queue**: Review pending videos before approval
- **Schedule Posts**: Set posting times for TikTok, Instagram, YouTube
- **Settings**: Store API credentials (encrypted)
- **Logs**: Real-time system activity

---

## 📱 Social Media Setup Details

### TikTok Business API
1. Go to [TikTok Creator Center](https://creators.tiktok.com)
2. Register as Business Account
3. Create OAuth App in [TikTok Developer Portal](https://developers.tiktok.com)
4. Get `Client Key` and `Client Secret`
5. Paste `TIKTOK_API_KEY` in app settings

### Instagram Graph API
1. Go to [Meta Developers](https://developers.facebook.com)
2. Create app and register `Instagram Graph API`
3. Connect Instagram Business Account
4. Generate long-lived access token
5. Paste as `INSTAGRAM_API_TOKEN`

### YouTube Data API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable `YouTube Data API v3`
3. Create OAuth 2.0 credentials (type: Desktop App)
4. Download JSON key file
5. Paste `YOUTUBE_API_KEY` in settings

---

## 🎬 Usage Workflow

### Creating a Video
1. Open app → **Generate** tab
2. Enter recipe prompt (e.g., "Healthy protein bowl with quinoa, grilled chicken, roasted vegetables, tahini dressing")
3. Click **"Generate Video (via n8n) ✓"**
4. App will:
   - Call Gemini to create 3-scene script
   - Submit to n8n workflow
   - Wait for video generation (5-15 min)
   - Download final MP4
   - Display in Queue

### Approving & Scheduling Posts
1. **Queue** tab → Select video → Click **"Approve + Schedule"**
2. Write caption and hashtags
3. Select platforms (TikTok, Instagram, YouTube)
4. Set posting times (default: now + 1 hour)
5. Click **"Schedule & Approve"**
6. Video queued for auto-posting at specified times

### Background Posting
- Posting thread checks every 60 seconds for due posts
- Automatically uploads to selected platforms
- Logs success/failures in **Logs** tab
- View status in **Schedule Posts** tab

---

## 🔌 n8n Workflow Configuration

### Importing the Workflow
1. Open n8n (http://localhost:5678)
2. Click **"Import"** → Select `n8n_workflow_with_callback.json`
3. Configure connections:
   - **Google Gemini**: Add your API key
   - **KokoroTTS**: Ensure running on localhost:8000
   - **Krea/Modal**: Update video generation endpoints

### Critical Nodes
| Node | Purpose | Config |
|------|---------|--------|
| When chat message received | Entry point | Webhook URL |
| AI Agent | Creates script | Connected to Gemini model |
| Bella's Voice Generation | TTS | KokoroTTS endpoint |
| George's Voice Takeover | TTS | KokoroTTS endpoint |
| Krea Video Generation | Video gen | Krea API or Modal |
| Video Stitcher | Combines clips | Modal stitcher endpoint |
| Callback to Python App | Webhook response | http://localhost:5000/n8n-callback |

---

## 🗄️ Database Schema

### video_queue table
```sql
id (PRIMARY KEY)
recipe_name (TEXT)
george_json (JSON) -- Full script data
final_video_path (TEXT) -- Local file path
final_video_url (TEXT) -- n8n callback URL
status (TEXT) -- pending, approved
created_at (DATETIME)
approved_at (DATETIME)
```

### scheduled_posts table
```sql
id (PRIMARY KEY)
video_id (FOREIGN KEY)
platform (TEXT) -- tiktok, instagram, youtube
scheduled_time (DATETIME) -- ISO format
caption (TEXT)
hashtags (TEXT)
status (TEXT) -- pending, posted, failed
posted_at (DATETIME)
error_msg (TEXT)
created_at (DATETIME)
```

---

## 🔐 Security Features

### Credential Encryption
- All API keys stored encrypted with Fernet
- Encryption key generated once and stored in `.vault_key`
- Credentials never logged or sent to external services (except platforms)

### Vault File Structure
```
credentials.vault  (encrypted blob)
.vault_key        (symmetric key - keep safe!)
app_database.db   (SQLite with credentials schema)
```

---

## 🐛 Troubleshooting

### n8n Not Responding
```bash
# Check if running
lsof -i :5678

# Restart
docker restart n8n  # if using Docker
```

### KokoroTTS Errors
```bash
# Verify TTS server
curl http://localhost:8000/health

# Restart if needed
docker restart kokoro-tts
```

### Video Generation Timeout
- Increase timeout in code: `wait_and_download(..., timeout=3600)`
- Check Modal/Krea dashboard for queue status
- Verify GPU allocation

### Social Media Posting Fails
- Verify API keys are non-expired
- Check platform's rate limits
- Review error message in Logs tab
- Retry from Schedule Posts tab

### Database Locked
```bash
# Check for lingering processes
ps aux | grep python

# Remove database if corrupted
rm app_database.db
# App will recreate on next run
```

---

## 📊 Performance Tuning

### For Faster Video Generation
1. Reduce resolution in n8n workflow (512p instead of 768p)
2. Use 2 scenes instead of 3
3. Reduce sample steps (10 instead of 20)
4. Use GPU in "fast" mode if available

### For Concurrent Processing
1. Run multiple callback server instances
2. Use Redis instead of in-memory callbacks
3. Configure n8n for parallel execution

### Cost Optimization
- TikTok: FREE (direct API)
- Instagram: FREE (Meta platform)
- YouTube: FREE (Google platform)
- Gemini: ~$0.075/1M tokens (free tier: 60 req/min)
- KokoroTTS: FREE (local)
- Krea AI: Pay-per-video (~$0.50-2.00)
- Modal LTX: A100 $4.73/hr (use scheduled execution)

---

## 📚 API Reference

### Callback Server Endpoints

#### Health Check
```bash
GET http://localhost:5000/health
# Response: {"status": "healthy"}
```

#### Receive Video
```bash
POST http://localhost:5000/n8n-callback
# Payload:
{
  "sessionId": "20240101_120000",
  "finalVideoUrl": "https://.../video.mp4",
  "georgeJson": {...}
}
```

#### Register Callback
```bash
POST http://localhost:5000/register-callback
# Payload:
{
  "sessionId": "20240101_120000",
  "callbackUrl": "http://app:5001/video-ready"
}
```

#### Check Status
```bash
GET http://localhost:5000/callback-status/20240101_120000
# Response: {"status": "completed", "final_video_url": "..."}
```

---

## 📝 Example Workflow

**Input**: "Make a healthy açai bowl recipe video - purple base, granola, berries, coconut"

### n8n Flow
1. **Gemini**: Generates 3-scene script focused on açai bowl
2. **Bella TTS**: "Sure, I'll have George prep that for you" (af_bella voice)
3. **Scene 1 TTS**: "Hi, I'm George, this is FitSweetTreat..." (bm_george voice)
4. **Scene 1 Video**: Generates cinematic açai bowl preparation
5. **Scene 2 TTS**: "Diced fresh berries..." (bm_george)
6. **Scene 2 Video**: Close-ups of toppings
7. **Scene 3 TTS**: "...but wait, there's more!" (bm_george, ends with "but")
8. **Scene 3 Video**: Final beauty shot
9. **Stitch**: Combines audio + video + BG music
10. **Callback**: Returns URL to Python app

### Python App
1. Video downloaded to `output/final_20240101_120000.mp4`
2. Added to Queue for manual review
3. User clicks "Approve + Schedule"
4. Prompt for caption: "Açai bowl perfection 🥣"
5. Hashtags: "#FitSweetTreat #HealthyBowl #AcaiBowl #Breakfast"
6. Select: TikTok, Instagram, YouTube
7. Times: Today 2PM, 4PM, 6PM
8. Background thread posts automatically at each time

---

## 🎯 Next Steps

1. ✅ Install dependencies
2. ✅ Configure `.env` with API keys
3. ✅ Start all services (KokoroTTS, n8n, callback_server)
4. ✅ Import n8n workflow from `n8n_workflow_with_callback.json`
5. ✅ Launch Python app: `python app.py`
6. ✅ Test with sample recipe prompt
7. ✅ Approve video and schedule posts
8. ✅ Monitor posting in Logs tab

**That's it!** Your video automation pipeline is live and posting.

---

## 📞 Support

- **n8n Issues**: Check n8n Discord/Docs
- **KokoroTTS Issues**: Check Kokoro repo
- **API Errors**: Review platform's API documentation
- **Python Errors**: Check `app_database.db` permissions and Python version

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready
