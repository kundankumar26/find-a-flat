# 🏠 House Search Agent — HSR Layout, Bangalore

Automatically scrapes NoBroker every 4 hours for rentals in HSR Layout under ₹30,000 and sends Telegram alerts for new listings.

---

## 📦 What's Inside

```
house-agent/
├── main.py              # Orchestrator — runs the full pipeline
├── scraper.py           # Playwright scraper for NoBroker
├── parser_ai.py         # OpenAI GPT-4o-mini parses & ranks listings
├── database.py          # SQLite deduplication (no repeat alerts)
├── notifier.py          # Telegram bot notifications
├── requirements.txt     # Python dependencies
└── .github/
    └── workflows/
        └── scheduler.yml  # GitHub Actions cron (every 4 hours)
```

---

## 🚀 Setup Guide (One-Time, ~45 minutes)

### Step 1: Create a Telegram Bot (5 mins)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy your **Bot Token** (looks like `123456:ABCdef...`)
4. Start a chat with your new bot (send any message)
5. Get your **Chat ID**:
   - Open this URL in browser (replace YOUR_TOKEN):
   - `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
   - Find `"chat":{"id":XXXXXXXXX}` — that number is your Chat ID

---

### Step 2: Get OpenAI API Key (5 mins)

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up / log in → API Keys → Create new key
3. Copy the key (starts with `sk-...`)
4. Add credits ($5 minimum — will last months for this use case)

---

### Step 3: Upload Code to GitHub (10 mins)

1. Create a new **private** GitHub repository (e.g. `house-search-agent`)
2. Upload all files from this folder to the repo
   - Easiest: drag and drop files in GitHub web UI
   - Or use git CLI:
     ```bash
     git init
     git add .
     git commit -m "Initial setup"
     git remote add origin https://github.com/YOUR_USERNAME/house-search-agent.git
     git push -u origin main
     ```

---

### Step 4: Add Secrets to GitHub (5 mins)

In your GitHub repo:
1. Go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret** and add these 3 secrets:

| Secret Name | Value |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI key (`sk-...`) |
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID number |

---

### Step 5: Enable GitHub Actions (2 mins)

1. Go to the **Actions** tab in your repo
2. Click **"I understand my workflows, go ahead and enable them"**
3. The workflow will now run automatically every 4 hours!

---

### Step 6: Test It Manually (2 mins)

1. Go to **Actions → House Search Agent**
2. Click **"Run workflow"** → **"Run workflow"**
3. Watch the logs — you should get a Telegram message!

---

## 📲 Example Telegram Message

```
🏠 2BHK Apartment
📍 HSR Layout Sector 2

💰 Rent: ₹27,000/mo
🔑 Deposit: ₹54,000
📐 Area: 1050 sq ft
🛋️ Semi Furnished
✨ Amenities: Parking, Gym, 24hr Security, Power Backup

🟢 Score: 8/10
_Spacious 2BHK with good amenities at below-market price_

🔗 View Listing
```

---

## 💰 Cost Summary

| Component | Cost |
|---|---|
| GitHub Actions | **Free** |
| Playwright scraping | **Free** |
| OpenAI gpt-4o-mini | **~₹40-80/month** |
| Telegram bot | **Free** |
| **Total** | **~₹50/month** |

---

## 🔧 Customization

Edit `scraper.py` to change:
- `MAX_BUDGET = 30000` → your budget
- `LOCATION = "HSR Layout"` → any Bangalore area
- `MAX_PAGES = 3` → how many pages to scrape

Edit `parser_ai.py` to change ranking criteria in the prompt.

---

## ❓ Troubleshooting

**No listings found:**
- NoBroker may have changed its HTML structure
- Try running manually and check the logs in GitHub Actions

**Telegram not receiving messages:**
- Make sure you sent at least one message to your bot first
- Double-check the Chat ID (it's a number, not your username)

**OpenAI errors:**
- Check your API key is valid and has credits
- gpt-4o-mini is very cheap — $5 credit lasts months

---

## 📌 Notes

- The agent only alerts for **new listings** — no duplicate notifications
- Database persists across GitHub Actions runs via cache
- The scraper mimics human browsing to reduce blocking risk
