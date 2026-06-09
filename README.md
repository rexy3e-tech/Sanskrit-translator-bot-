# 🕉️ Sanskrit Translation Bot

A Discord bot that translates **Sanskrit** text and images into **Urdu**, **English**, and **Hindi** — powered by [OpenRouter AI](https://openrouter.ai).

---

## ✨ Features

- 📝 Translate Sanskrit text typed directly in Discord
- 🖼️ OCR support — attach a scanned Sanskrit manuscript/book image and the bot extracts + translates it
- 🖋️ Supports **Urdu**, **✒️ English**, and **🏵️ Hindi** as output languages
- 🔒 Optional role-based access control and server whitelisting
- ⚡ Uses multiple free vision AI models as fallback for reliable OCR

---

## 📋 Commands

### Text Translation

| Command | What it does |
|---|---|
| `!su <sanskrit text>` | Translate Sanskrit → **Urdu** |
| `!se <sanskrit text>` | Translate Sanskrit → **English** |
| `!sh <sanskrit text>` | Translate Sanskrit → **Hindi** |
| `!translate <sanskrit text>` | Translate Sanskrit → **All three** |

### Image OCR + Translation

Attach a Sanskrit image and use any translation command:

| Command | What it does |
|---|---|
| Attach image + `!su` | Extract Sanskrit from image → **Urdu** |
| Attach image + `!se` | Extract Sanskrit from image → **English** |
| Attach image + `!sh` | Extract Sanskrit from image → **Hindi** |
| Attach image + `!translate` | Extract Sanskrit from image → **All three** |

### Utility

| Command | Access | What it does |
|---|---|---|
| `!guide` or `!h` | Everyone | Show full command guide |
| `!ping` | Everyone | Check bot latency |
| `!servers` | Bot owner only | List all servers the bot is in |
| `!stats` | Bot owner only | Show server count, members, latency |

---

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/sanskrit-translation-bot.git
cd sanskrit-translation-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
DISCORD_TOKEN=your_discord_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 4. Run the bot

```bash
python bot.py
```

Or use the build script:

```bash
bash build.sh
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✅ Yes | Your Discord bot token |
| `OPENROUTER_API_KEY` | ✅ Yes | Your OpenRouter API key |
| `ALLOWED_SERVERS` | ❌ No | Comma-separated Discord server IDs to whitelist. Leave empty to allow all servers. |
| `PROXY_URL` | ❌ No | HTTP proxy URL (only if running behind a proxy) |
| `COUNCIL_ROLE_ID` | ❌ No | Role ID with full bot access. Set to `0` to disable role restrictions. |
| `LIBRARY_ROLE_ID` | ❌ No | Role ID with restricted access (forum channel only). Set to `0` to disable. |
| `FORUM_CHANNEL_ID` | ❌ No | Channel ID where Library Pass role is allowed. Set to `0` to disable. |

---

## 🔐 Access Control

The bot supports two layers of access control:

**Server Whitelist** — Set `ALLOWED_SERVERS` to restrict the bot to specific Discord servers. The bot will auto-leave any server not on the list.

**Role-based Access** — Configure `COUNCIL_ROLE_ID` and `LIBRARY_ROLE_ID`:
- **Council role**: full access in all channels
- **Library Pass role**: access only inside the designated forum channel and its threads

> Leave all role/channel IDs as `0` to allow all members to use the bot freely.

---

## 🧠 AI Models Used

| Purpose | Models |
|---|---|
| **Sanskrit OCR** (image reading) | Qwen 2.5 VL 72B, Qwen 2.5 VL 32B, Llama 4 Maverick, Llama 4 Scout, Nemotron Nano VL, Kimi VL, Mistral Small 3.1 — tried in sequence as fallback |
| **Translation** | `openrouter/auto` (OpenRouter picks the best available model) |

All models used are **free-tier** on OpenRouter.

---

## 📦 Dependencies

- [discord.py](https://discordpy.readthedocs.io/) — Discord bot framework
- [aiohttp](https://docs.aiohttp.org/) — Async HTTP client for API calls
- [python-dotenv](https://pypi.org/project/python-dotenv/) — Load environment variables from `.env`

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
