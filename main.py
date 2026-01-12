import os
import logging
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from collections import defaultdict

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render ENV
ADMIN_IDS = {8541949664}  # <-- apna Telegram numeric ID yahan daalo

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ================= LOGGING =================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ================= STORAGE =================
users = set()
total_downloads = 0

# ================= YT-DLP =================
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
}

# ================= HELPERS =================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def search_and_download(song: str):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{song}", download=True)
        video = info["entries"][0]

        for ext in ["mp3", "m4a", "webm", "opus"]:
            file_path = f"{DOWNLOAD_DIR}/{video['id']}.{ext}"
            if os.path.exists(file_path):
                return file_path, video["title"], video.get("duration", 0)

        raise Exception("Audio file not found")

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)
    await update.message.reply_text(
        "🎵 *Music Downloader Bot*\n\n"
        "Commands:\n"
        "/music <song name> – Download music\n"
        "/help – Help\n\n"
        "Example:\n"
        "`/music Kesariya`",
        parse_mode="Markdown",
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *Available Commands*\n\n"
        "/music <song> – Download audio\n\n"
        "👑 *Admin Commands*\n"
        "/broadcast <msg>\n"
        "/status\n"
        "/users",
        parse_mode="Markdown",
    )

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_downloads
    users.add(update.effective_user.id)

    if not context.args:
        return await update.message.reply_text("❌ Song name likho.\nExample: `/music Senorita`", parse_mode="Markdown")

    song = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 Searching: *{song}*", parse_mode="Markdown")

    try:
        file_path, title, duration = await asyncio.get_event_loop().run_in_executor(
            None, search_and_download, song
        )

        await update.message.reply_audio(
            audio=open(file_path, "rb"),
            title=title,
            duration=int(duration) if duration else None,
            caption=f"🎵 {title}",
        )

        total_downloads += 1
        os.remove(file_path)
        await msg.delete()

    except Exception as e:
        logger.error(e)
        await msg.edit_text("❌ Download failed. Dusra song try karo.")

# ================= ADMIN COMMANDS =================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        return await update.message.reply_text("Usage: /broadcast <message>")

    text = " ".join(context.args)
    sent = 0

    for uid in users:
        try:
            await context.bot.send_message(uid, f"📢 *Broadcast:*\n{text}", parse_mode="Markdown")
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        f"📊 *Bot Status*\n\n"
        f"👥 Users: {len(users)}\n"
        f"⬇️ Downloads: {total_downloads}",
        parse_mode="Markdown",
    )

async def user_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(f"👥 Total users: {len(users)}")

# ================= MAIN =================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("music", music))

    # admin
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("users", user_count))

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
