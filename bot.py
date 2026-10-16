
import os
import re
import sqlite3
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
DB_FILE = os.environ.get("DB_FILE", "files.db")

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)


def init_db():
    with sqlite3.connect(DB_FILE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_key TEXT PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL
            )
        """)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if context.args:
        key = context.args[0]

        if not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", key):
            await message.reply_text("লিংকটি সঠিক নয়।")
            return

        with sqlite3.connect(DB_FILE) as db:
            row = db.execute(
                "SELECT chat_id, message_id FROM files "
                "WHERE file_key = ?",
                (key,)
            ).fetchone()

        if row:
            try:
                await context.bot.copy_message(
                    chat_id=user.id,
                    from_chat_id=row[0],
                    message_id=row[1],
                )
            except Exception:
                logging.exception("File delivery failed")
                await message.reply_text(
                    "ফাইল পাঠানো যায়নি। পরে আবার চেষ্টা করো।"
                )
        else:
            await message.reply_text(
                "এই ফাইলটি পাওয়া যায়নি। লিংকটি পরীক্ষা করো।"
            )
    else:
        await message.reply_text(
            "👋 স্বাগতম!\n"
            "Channel-এর নির্দিষ্ট Download Link দিয়ে এখানে এসো।"
        )


async def save_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user or user.id != ADMIN_ID:
        return

    key = (message.caption or "").strip()

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", key):
        await message.reply_text(
            "ফাইলের Caption-এ একটি ID দাও, যেমন: file_001"
        )
        return

    with sqlite3.connect(DB_FILE) as db:
        db.execute(
            "INSERT OR REPLACE INTO files "
            "(file_key, chat_id, message_id) VALUES (?, ?, ?)",
            (key, message.chat_id, message.message_id),
        )

    await message.reply_text(
        f"✅ ফাইল সংরক্ষিত হয়েছে!\n"
        f"ID: {key}\n\n"
        f"Download link-এর জন্য এই ID ব্যবহার করো।"
    )


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    
app.add_handler(MessageHandler(
    filters.ChatType.PRIVATE
    & filters.CAPTION
    & (
        filters.Document.ALL
        | filters.VIDEO
        | filters.PHOTO
        | filters.AUDIO
        | filters.ANIMATION
    ),
    save_file,
))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
          
