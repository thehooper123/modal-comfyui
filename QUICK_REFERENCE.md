# 🎯 QUICK REFERENCE CARD

## 🚀 One-Liner Startup

**Linux/Mac:**
```bash
cd /workspaces/modal-comfyui && chmod +x start.sh && ./start.sh
```

**Windows:**
```bash
cd C:\path\to\modal-comfyui && start.bat
```

---

## 📋 5-Step First Run

1. **Edit `.env`** with your API keys (Gemini, TikTok, Instagram, YouTube)
2. **Start n8n** on localhost:5678
3. **Start KokoroTTS** on localhost:8000
4. **Import n8n workflow** `n8n_workflow_with_callback.json` into n8n
5. **Run app** → Enter recipe → Approve → Schedule posts

---

## 🎬 Complete Workflow

```
Recipe Prompt
    ↓ (You type)
[Generate] Tab
    ↓
Gemini creates script
    ↓
n8n generates video (15 min)
    ↓
[Queue] Tab (Review)
    ↓
[Approve + Schedule]
    ↓
[Schedule Posts] Tab (Set times)
    ↓
Auto-posts at scheduled times
    ↓
[Logs] Tab (Monitor success)
```

---

## 🔑 Essential Commands

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run Parts Individually
```bash
# Terminal 1: Callback server
python callback_server.py

# Terminal 2: Main app
python app.py

# Terminal 3: Optional - run n8n
docker run -p 5678:5678 n8nio/n8n

# Terminal 4: Optional - run KokoroTTS
docker run -p 8000:8000 kokoro-tts
```

### Debug
```bash
# Check if port is in use
lsof -i :5000   # callback server
lsof -i :5678   # n8n
lsof -i :8000   # kokorotts

# Kill process
kill -9 <PID>

# Check Python env
python --version
pip list
```

---

## 🎬 Usage Tips

### Quick Test
1. Open app → Generate tab
2. Paste: "Make a healthy smoothie bowl recipe"
3. Click "Generate Video (via n8n) ✓"
4. Wait for video (watch progress in logs)
5. Approve and schedule to TikTok

### Best Captions for Social
- **TikTok**: Trendy + hashtags + call-to-action
  - "POV: You're making this healthy bowl today 🥣 #FitSweetTreat"
- **Instagram**: Longer + emoji + question
  - "Would you try this? Fresh, colorful, packed with nutrition 💚 What's your favorite bowl? Comment below!"
- **YouTube**: SEO-optimized + details
  - "Healthy Quinoa Buddha Bowl Recipe - Vegan & Delicious"

### Hashtag Strategy
- Core: `#FitSweetTreat #HealthyRecipe #FoodVideo #Shorts`
- Trend: `#FoodTok #RecipeOfTheDay #CoddieCheck`
- Domain: `#HealthyEating #FitnessFood #MealPrep`

---

## 🔐 Security Reminders

- **Never commit `.env`** (already in .gitignore)
- **Keep `.vault_key` private** (your encryption key)
- **Don't share API keys** (store only in `.env`)
- **Delete old credentials** if API key is compromised

```bash
# If compromised:
rm credentials.vault .vault_key app_database.db
# App will recreate on restart
```

---

## 📊 Platform-Specific Info

### TikTok
- **Video Length**: 3-60 sec (our: 60 sec optimal)
- **Format**: Vertical (9:16)
- **Best Time**: 6-10 PM (evening)
- **Rate Limit**: 50 posts/day

### Instagram Reels
- **Video Length**: 3-90 sec (our: 60 sec perfect)
- **Format**: Vertical (9:16)
- **Best Time**: 11 AM, 2 PM, 7-9 PM
- **Rate Limit**: 1 reel per minute, 25/day

### YouTube Shorts
- **Video Length**: <60 sec (our: 60 sec perfect)
- **Format**: Vertical (9:16)
- **Best Time**: 5-11 PM
- **Rate Limit**: Unlimited (but monitor CPU)

---

## 🐛 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Port already in use | `lsof -i :5000` → `kill -9 <PID>` |
| n8n won't start | Check Docker: `docker ps` |
| API key invalid | Regenerate in platform dashboard |
| Video too slow | Add more timeouts in code |
| DB locked | Kill Python: `ps aux \| grep python` |
| TTS errors | Restart KokoroTTS container |
| No more Gemini free requests | Upgrade to paid plan |

---

## 📁 Key Files

| File | Purpose | Edit? |
|------|---------|-------|
| `app.py` | Main application | No (unless extending) |
| `callback_server.py` | Video delivery | No |
| `n8n_workflow_with_callback.json` | n8n setup | Maybe (endpoints) |
| **`.env`** | **YOUR CREDENTIALS** | **YES - REQUIRED!** |
| `requirements.txt` | Dependencies | Only if adding packages |
| `app_database.db` | Video records | Auto-managed |
| `credentials.vault` | Encrypted creds | Auto-managed |

---

## ⏱️ Timing Guide

| Step | Time | Notes |
|------|------|-------|
| Gemini script generation | <10 sec | Sub-second usually |
| KokoroTTS (3 voices) | ~30 sec | Parallel processing |
| Krea video generation | 5-10 min | Depends on queue |
| Video stitching | 1-2 min | Local processing |
| **Total** | **~10-15 min** | Per video |
| Social media posting | <5 sec | Per platform |

---

## 💰 Cost Breakdown (Monthly)

| Service | Price | Notes |
|---------|-------|-------|
| Gemini API | ~$5-10 | 1M tokens per video |
| TikTok API | FREE | Direct business API |
| Instagram API | FREE | Meta platform |
| YouTube API | FREE | Google platform |
| KokoroTTS | FREE | Self-hosted |
| Krea AI | ~$100-200 | 50-100 videos |
| Modal (optional) | ~$0-100 | Scales with usage |
| **Total** | **~$100-200** | Depends on volume |

---

## 🎓 Learning Resources

- **n8n Docs**: https://docs.n8n.io
- **Gemini API**: https://aistudio.google.com
- **TikTok API**: https://developers.tiktok.com
- **Instagram Graph API**: https://developers.facebook.com
- **YouTube API**: https://developers.google.com/youtube
- **KokoroTTS**: https://github.com/remsky/Kokoro-FastAPI

---

## 📞 Quick Support

**App won't start?**
```bash
# Check Python version
python --version  # Need 3.9+

# Check dependencies
pip list | grep -E "flask|requests|cryptography|google-generativeai"

# Try fresh install
pip install --upgrade -r requirements.txt
```

**Videos not generating?**
```bash
# Check n8n workflow is imported
# Visit http://localhost:5678 → check workflow exists

# Check callback server is running
# Should see "Callback Server running on 0.0.0.0:5000"

# Check logs
# Go to Logs tab in app and search for "error"
```

**Posts not uploading?**
```bash
# Verify API keys in Settings tab
# Test one platform's credentials
# Check rate limits on platform dashboard
# Review error message in Logs → Schedule Posts tab
```

---

## 🎯 Pro Tips

1. **Schedule posts early** - Create 7 videos, schedule for week, auto-post
2. **Use trending sounds** - Edit n8n workflow to add Trending TTS
3. **A/B test captions** - Schedule same video with different captions
4. **Monitor comments** - Check social media directly for engagement
5. **Update hashtags weekly** - Trends change, keep them fresh
6. **Batch create** - Run 10 recipes, approve all, schedule week
7. **Use templates** - Save successful recipes, reuse captions

---

## 🚀 Launch!

```bash
# That's it!
./start.sh    # or start.bat on Windows

# Then:
# 1. Open .env and add API keys
# 2. Make sure n8n and KokoroTTS are running
# 3. Import n8n workflow
# 4. Enter recipe in app
# 5. Watch the magic happen
```

---

**Questions?** Check `SETUP_GUIDE.md` or `README_APP.md` for complete docs.

**Version**: 1.0.0 | **Status**: ✅ Ready to Use
