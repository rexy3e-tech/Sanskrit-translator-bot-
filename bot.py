# Sanskrit Translation Bot v1.0
# Translates Sanskrit text/images → Urdu, English, Hindi
# Commands: !su (Urdu), !se (English), !sh (Hindi)

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiohttp
import re
import base64
import asyncio
import time

load_dotenv()

TOKEN             = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PROXY_URL         = os.getenv("PROXY_URL")
OPENROUTER_URL    = "https://openrouter.ai/api/v1/chat/completions"

# ── Allowed Servers Whitelist ─────────────────────────────────────────────────
# Add comma-separated server IDs in ALLOWED_SERVERS env variable.
# Leave empty to allow ALL servers.
ALLOWED_SERVERS_ENV = os.getenv("ALLOWED_SERVERS", "")
ALLOWED_SERVERS = [int(x.strip()) for x in ALLOWED_SERVERS_ENV.split(",") if x.strip().isdigit()]

# ── Role & Channel Config (set via env or hardcode) ───────────────────────────
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID", "0"))
COUNCIL_ROLE_ID  = int(os.getenv("COUNCIL_ROLE_ID",  "0"))
LIBRARY_ROLE_ID  = int(os.getenv("LIBRARY_ROLE_ID",  "0"))

# ── Vision models for Sanskrit OCR (Devanagari) ───────────────────────────────
VISION_MODELS = [
    "qwen/qwen2.5-vl-72b-instruct:free",
    "qwen/qwen2.5-vl-32b-instruct:free",
    "meta-llama/llama-4-maverick:free",
    "meta-llama/llama-4-scout:free",
    "nvidia/llama-3.2-nemotron-nano-vl-8b-v1:free",
    "moonshotai/kimi-vl-a3b-thinking:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "openrouter/healer-alpha",
]

# Translation model (OpenRouter auto-selects best available)
TRANSLATION_MODEL = "openrouter/auto"

# ── Bot setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    proxy=PROXY_URL
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def contains_sanskrit(text: str) -> bool:
    """Check for Devanagari script (used by Sanskrit, Hindi, etc.)"""
    return bool(re.search(r'[\u0900-\u097F]', text))


async def call_openrouter(messages: list, model: str, retries: int = 2):
    """Generic OpenRouter API call with retry logic."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://discord-sanskrit-bot.com",
        "X-Title": "Sanskrit Translation Bot",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 4000,
    }

    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENROUTER_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    data = await resp.json()
                    if "error" in data:
                        err = data["error"].get("message", "Unknown error")
                        print(f"OpenRouter error [{model}] (attempt {attempt+1}): {err}")
                        if "rate" in err.lower():
                            await asyncio.sleep(10)
                        continue
                    content = data["choices"][0]["message"]["content"]
                    if content and content.strip():
                        return content.strip()
                    return None
        except Exception as e:
            print(f"Exception [{model}] (attempt {attempt+1}): {e}")
            await asyncio.sleep(3)
    return None


async def extract_sanskrit_from_image(image_bytes: bytes, mime_type: str) -> str:
    """Try multiple free vision models for Sanskrit / Devanagari OCR."""
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                },
                {
                    "type": "text",
                    "text": (
                        "This image contains Sanskrit text written in Devanagari script, "
                        "possibly from a scanned manuscript, book, or document.\n\n"
                        "Your task:\n"
                        "- Extract ALL Sanskrit / Devanagari text visible in the image\n"
                        "- Include any highlighted or bold text\n"
                        "- Preserve the original Devanagari text exactly as written\n"
                        "- Do NOT translate anything\n"
                        "- Return ONLY the Sanskrit/Devanagari text, nothing else\n"
                        "- If you cannot find any Devanagari text, return: NONE"
                    ),
                },
            ],
        }
    ]

    for model in VISION_MODELS:
        print(f"Trying vision model: {model}")
        result = await call_openrouter(messages, model)
        if result:
            cleaned = result.strip()
            if cleaned and cleaned.upper() != "NONE" and contains_sanskrit(cleaned):
                print(f"✅ OCR succeeded with: {model}")
                return cleaned
            print(f"❌ Model {model} returned: {cleaned[:50] if cleaned else 'empty'}")
        else:
            print(f"❌ Model {model} failed completely")

    print("❌ All vision models failed")
    return ""


async def translate_text(sanskrit_text: str, language: str = "all") -> dict:
    """
    Translate Sanskrit text.
    language: "urdu" | "english" | "hindi" | "all"
    """
    if language == "urdu":
        prompt = (
            "Translate the COMPLETE Sanskrit text below to Urdu.\n"
            "Do not skip or truncate any part. Return ONLY the Urdu translation.\n\n"
            f"Sanskrit text:\n{sanskrit_text}"
        )
    elif language == "english":
        prompt = (
            "Translate the COMPLETE Sanskrit text below to English.\n"
            "Do not skip or truncate any part. Return ONLY the English translation.\n\n"
            f"Sanskrit text:\n{sanskrit_text}"
        )
    elif language == "hindi":
        prompt = (
            "Translate the COMPLETE Sanskrit text below to Hindi.\n"
            "Do not skip or truncate any part. Return ONLY the Hindi translation.\n\n"
            f"Sanskrit text:\n{sanskrit_text}"
        )
    else:  # "all" — Urdu + English + Hindi
        prompt = (
            "Translate the COMPLETE Sanskrit text below to Urdu, English, and Hindi.\n"
            "Do not skip or truncate any part.\n\n"
            f"Sanskrit text:\n{sanskrit_text}\n\n"
            "Respond in EXACTLY this format:\n"
            "URDU: [complete urdu translation]\n"
            "ENGLISH: [complete english translation]\n"
            "HINDI: [complete hindi translation]"
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional Sanskrit scholar and translator. "
                "Translate Sanskrit text accurately and completely into the requested language(s)."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    response = await call_openrouter(messages, TRANSLATION_MODEL)
    if not response:
        return {"urdu": "Translation failed", "english": "Translation failed", "hindi": "Translation failed"}

    if language == "urdu":
        return {"urdu": response, "english": "", "hindi": ""}
    elif language == "english":
        return {"urdu": "", "english": response, "hindi": ""}
    elif language == "hindi":
        return {"urdu": "", "english": "", "hindi": response}
    else:
        return parse_all(response)


def parse_all(text: str) -> dict:
    """Parse URDU / ENGLISH / HINDI blocks from a combined translation response."""
    result = {"urdu": "", "english": "", "hindi": ""}
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.upper().startswith("URDU:"):
            result["urdu"] = line[5:].strip()
        elif line.upper().startswith("ENGLISH:"):
            result["english"] = line[8:].strip()
        elif line.upper().startswith("HINDI:"):
            result["hindi"] = line[6:].strip()

    # Fallback if parsing fails
    if not any(result.values()):
        result["english"] = text[:500]
        result["urdu"] = "Could not parse"
        result["hindi"] = "Could not parse"
    return result


def add_long_field(embed: discord.Embed, name: str, value: str):
    """Add a field to embed, splitting into chunks if > 1024 chars."""
    if not value or not value.strip():
        return
    chunks = [value[i:i+1024] for i in range(0, len(value), 1024)]
    for i, chunk in enumerate(chunks):
        embed.add_field(
            name=name if i == 0 else f"{name} (cont.)",
            value=chunk,
            inline=False,
        )


async def get_image_sanskrit(ctx) -> str | None:
    """Download attached image, run OCR, return extracted Sanskrit text."""
    attachment = ctx.message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith("image/"):
        await ctx.reply("⚠️ Please attach a valid image file.")
        return None

    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as resp:
            image_bytes = await resp.read()

    await ctx.reply("🔍 Extracting Sanskrit text from image, please wait...")
    extracted = await extract_sanskrit_from_image(image_bytes, attachment.content_type)

    if not extracted:
        await ctx.reply(
            "🖼️ Could not extract Sanskrit text from this image. "
            "Try a clearer or higher-resolution image."
        )
        return None
    return extracted


# ── Events ───────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"OpenRouter: {'✅' if OPENROUTER_API_KEY else '❌ MISSING'}")
    print(f"Vision models: {len(VISION_MODELS)} models available")
    if ALLOWED_SERVERS:
        print(f"🔒 Restricted to servers: {ALLOWED_SERVERS}")
    else:
        print("🌐 No whitelist — all servers allowed")

    # Auto-leave unauthorized servers on startup
    for guild in bot.guilds:
        if ALLOWED_SERVERS and guild.id not in ALLOWED_SERVERS:
            print(f"⛔ Leaving unauthorized server: {guild.name} ({guild.id})")
            await guild.leave()


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Auto-leave if the server is not whitelisted."""
    if ALLOWED_SERVERS and guild.id not in ALLOWED_SERVERS:
        print(f"⛔ Leaving unauthorized server: {guild.name} ({guild.id})")
        try:
            await guild.system_channel.send(
                "⛔ This bot is restricted to specific servers only. Leaving now."
            )
        except Exception:
            pass
        await guild.leave()


# ── Global Check: Role + Channel Restrictions ─────────────────────────────────

@bot.check
async def global_server_check(ctx):
    """Block DMs; enforce role + channel restrictions."""
    # Ignore DMs
    if not ctx.guild:
        return False

    # If role IDs are not configured, allow everyone
    if COUNCIL_ROLE_ID == 0 and LIBRARY_ROLE_ID == 0:
        return True

    member = ctx.author
    has_council = any(role.id == COUNCIL_ROLE_ID for role in member.roles)
    has_library = any(role.id == LIBRARY_ROLE_ID for role in member.roles)

    # Council role → full access everywhere
    if has_council:
        return True

    # Library Pass → only inside the designated forum channel / threads
    if has_library and (
        ctx.channel.id == FORUM_CHANNEL_ID
        or getattr(ctx.channel, "parent_id", None) == FORUM_CHANNEL_ID
    ):
        return True

    await ctx.reply("❌ You do not have permission to use this bot.")
    return False


# ── Commands ─────────────────────────────────────────────────────────────────

@bot.command(name="su", aliases=["sanskritudru", "surdu"])
async def translate_urdu(ctx, *, text: str = None):
    """Translate Sanskrit → Urdu only.  Usage: !su <sanskrit> or attach image + !su"""
    if ctx.message.attachments:
        sanskrit = await get_image_sanskrit(ctx)
        if not sanskrit:
            return
        async with ctx.typing():
            translations = await translate_text(sanskrit, "urdu")
        embed = discord.Embed(title="🖋️ Sanskrit → Urdu", color=0xFF6B35)
        add_long_field(embed, "📜 Original Sanskrit", sanskrit)
        add_long_field(embed, "🖋️ Urdu", translations["urdu"])
        embed.set_footer(text="Powered by OpenRouter 🦙")
        await ctx.reply(embed=embed)
        return

    if not text:
        await ctx.reply("**Usage:** `!su <sanskrit text>` or attach image + `!su`")
        return
    if not contains_sanskrit(text):
        await ctx.reply("⚠️ Please provide Sanskrit text written in Devanagari script.")
        return

    async with ctx.typing():
        translations = await translate_text(text, "urdu")
    embed = discord.Embed(title="🖋️ Sanskrit → Urdu", color=0xFF6B35)
    add_long_field(embed, "📜 Original Sanskrit", text)
    add_long_field(embed, "🖋️ Urdu", translations["urdu"])
    embed.set_footer(text="Powered by OpenRouter 🦙")
    await ctx.reply(embed=embed)


@bot.command(name="se", aliases=["sanskritenglish", "senglish"])
async def translate_english(ctx, *, text: str = None):
    """Translate Sanskrit → English only.  Usage: !se <sanskrit> or attach image + !se"""
    if ctx.message.attachments:
        sanskrit = await get_image_sanskrit(ctx)
        if not sanskrit:
            return
        async with ctx.typing():
            translations = await translate_text(sanskrit, "english")
        embed = discord.Embed(title="✒️ Sanskrit → English", color=0x00B4D8)
        add_long_field(embed, "📜 Original Sanskrit", sanskrit)
        add_long_field(embed, "✒️ English", translations["english"])
        embed.set_footer(text="Powered by OpenRouter 🦙")
        await ctx.reply(embed=embed)
        return

    if not text:
        await ctx.reply("**Usage:** `!se <sanskrit text>` or attach image + `!se`")
        return
    if not contains_sanskrit(text):
        await ctx.reply("⚠️ Please provide Sanskrit text written in Devanagari script.")
        return

    async with ctx.typing():
        translations = await translate_text(text, "english")
    embed = discord.Embed(title="✒️ Sanskrit → English", color=0x00B4D8)
    add_long_field(embed, "📜 Original Sanskrit", text)
    add_long_field(embed, "✒️ English", translations["english"])
    embed.set_footer(text="Powered by OpenRouter 🦙")
    await ctx.reply(embed=embed)


@bot.command(name="sh", aliases=["sanskrithindi", "shindi"])
async def translate_hindi(ctx, *, text: str = None):
    """Translate Sanskrit → Hindi only.  Usage: !sh <sanskrit> or attach image + !sh"""
    if ctx.message.attachments:
        sanskrit = await get_image_sanskrit(ctx)
        if not sanskrit:
            return
        async with ctx.typing():
            translations = await translate_text(sanskrit, "hindi")
        embed = discord.Embed(title="🏵️ Sanskrit → Hindi", color=0xFF9933)
        add_long_field(embed, "📜 Original Sanskrit", sanskrit)
        add_long_field(embed, "🏵️ Hindi", translations["hindi"])
        embed.set_footer(text="Powered by OpenRouter 🦙")
        await ctx.reply(embed=embed)
        return

    if not text:
        await ctx.reply("**Usage:** `!sh <sanskrit text>` or attach image + `!sh`")
        return
    if not contains_sanskrit(text):
        await ctx.reply("⚠️ Please provide Sanskrit text written in Devanagari script.")
        return

    async with ctx.typing():
        translations = await translate_text(text, "hindi")
    embed = discord.Embed(title="🏵️ Sanskrit → Hindi", color=0xFF9933)
    add_long_field(embed, "📜 Original Sanskrit", text)
    add_long_field(embed, "🏵️ Hindi", translations["hindi"])
    embed.set_footer(text="Powered by OpenRouter 🦙")
    await ctx.reply(embed=embed)


@bot.command(name="translate", aliases=["t", "tr", "all", "sa"])
async def translate_all(ctx, *, text: str = None):
    """Translate Sanskrit → Urdu + English + Hindi.  Usage: !translate <sanskrit> or attach image"""
    if ctx.message.attachments:
        sanskrit = await get_image_sanskrit(ctx)
        if not sanskrit:
            return
        async with ctx.typing():
            translations = await translate_text(sanskrit, "all")
        embed = discord.Embed(title="🌐 Sanskrit Translation", color=0x7B2D8B)
        add_long_field(embed, "📜 Original Sanskrit", sanskrit)
        add_long_field(embed, "🖋️ Urdu",    translations["urdu"])
        add_long_field(embed, "✒️ English",  translations["english"])
        add_long_field(embed, "🏵️ Hindi",   translations["hindi"])
        embed.set_footer(text="Powered by OpenRouter 🦙")
        await ctx.reply(embed=embed)
        return

    if not text:
        await ctx.reply(
            "**📖 Quick Guide:**\n\n"
            "`!su <sanskrit>` — Urdu only\n"
            "`!se <sanskrit>` — English only\n"
            "`!sh <sanskrit>` — Hindi only\n"
            "`!translate <sanskrit>` — All three\n"
            "Attach image + any command for image OCR translation\n\n"
            "Type `!guide` for the full guide."
        )
        return
    if not contains_sanskrit(text):
        await ctx.reply("⚠️ Please provide Sanskrit text written in Devanagari script.")
        return

    async with ctx.typing():
        translations = await translate_text(text, "all")
    embed = discord.Embed(title="🌐 Sanskrit Translation", color=0x7B2D8B)
    add_long_field(embed, "📜 Original Sanskrit", text)
    add_long_field(embed, "🖋️ Urdu",    translations["urdu"])
    add_long_field(embed, "✒️ English",  translations["english"])
    add_long_field(embed, "🏵️ Hindi",   translations["hindi"])
    embed.set_footer(text="Powered by OpenRouter 🦙")
    await ctx.reply(embed=embed)


@bot.command(name="guide", aliases=["h", "help", "commands"])
async def guide(ctx):
    """Show the full command guide."""
    embed = discord.Embed(
        title="📖 Sanskrit Translation Bot — Full Guide",
        description="Translates Sanskrit text and images → Urdu, English, and/or Hindi.",
        color=0x7B2D8B,
    )
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="**📝 TEXT TRANSLATION**", inline=False)
    embed.add_field(name="🖋️ Urdu only",              value="`!su <sanskrit text>`",        inline=False)
    embed.add_field(name="✒️ English only",            value="`!se <sanskrit text>`",        inline=False)
    embed.add_field(name="🏵️ Hindi only",             value="`!sh <sanskrit text>`",        inline=False)
    embed.add_field(name="🌐 All three",               value="`!translate <sanskrit text>`", inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="**🖼️ IMAGE OCR + TRANSLATION**", inline=False)
    embed.add_field(name="🖋️ Image → Urdu",           value="Attach image + `!su`",         inline=False)
    embed.add_field(name="✒️ Image → English",         value="Attach image + `!se`",         inline=False)
    embed.add_field(name="🏵️ Image → Hindi",          value="Attach image + `!sh`",         inline=False)
    embed.add_field(name="🌐 Image → All three",       value="Attach image + `!translate`",  inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="**⚙️ OTHER**", inline=False)
    embed.add_field(name="🏓 Ping",   value="`!ping`",  inline=False)
    embed.add_field(name="📖 Guide",  value="`!guide`", inline=False)
    embed.set_footer(text="Powered by OpenRouter 🦙")
    await ctx.reply(embed=embed)


@bot.command(name="ping")
async def ping(ctx):
    """Check bot latency."""
    await ctx.reply(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")


# ── Owner-only Commands ───────────────────────────────────────────────────────

@bot.command(name="servers")
@commands.is_owner()
async def servers(ctx):
    """Show all servers the bot is in (owner only)."""
    guilds = bot.guilds
    if not guilds:
        await ctx.reply("Bot is not in any servers!")
        return
    embed = discord.Embed(title=f"🌐 Servers ({len(guilds)} total)", color=0x00f3ff)
    for guild in guilds:
        embed.add_field(
            name=guild.name,
            value=f"👥 Members: {guild.member_count}\n🆔 ID: {guild.id}",
            inline=False,
        )
    embed.set_footer(text="Only visible to bot owner")
    await ctx.reply(embed=embed)

@servers.error
async def servers_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        await ctx.reply("⛔ This command is only for the bot owner!")


@bot.command(name="stats")
@commands.is_owner()
async def stats(ctx):
    """Show bot statistics (owner only)."""
    total_members = sum(g.member_count for g in bot.guilds)
    embed = discord.Embed(title="📊 Bot Statistics", color=0x00f3ff)
    embed.add_field(name="🌐 Servers",       value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="👥 Total Members", value=str(total_members),   inline=True)
    embed.add_field(name="🏓 Latency",       value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.set_footer(text="Sanskrit Translation Bot")
    await ctx.reply(embed=embed)

@stats.error
async def stats_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        await ctx.reply("⛔ This command is only for the bot owner!")


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("⏳ Waiting 5 seconds before connecting...")
    time.sleep(5)
    bot.run(TOKEN, reconnect=True, log_handler=None)
