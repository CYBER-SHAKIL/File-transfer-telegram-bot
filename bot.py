import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
)
log = logging.getLogger("filebot")

# ---- Config (Environment Variables) ----
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("BOT_TOKEN পাওয়া যায়নি। কাছাকাছি নামের Variable:",
          [repr(k) for k in os.environ if "BOT" in k.upper() or "TOKEN" in k.upper()])
    raise SystemExit(1)
ADMIN_ID = int(os.environ["8361587941"])
STORAGE_CHANNEL_ID = int(os.environ["-1003934729128"])  # e.g. -1001234567890


# ---- /start ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    payload = context.args[0] if context.args else None

    # Link ছাড়া সাধারণ /start
    if not payload:
        text = "👋 স্বাগতম! ফাইল পেতে চ্যানেল/পোস্টের লিংকে ক্লিক করুন।"
        if update.effective_user.id == ADMIN_ID:
            text += (
                "\n\n🔧 Admin: আমাকে যেকোনো ফাইল (APK, Video, PDF, ZIP...) পাঠান, "
                "আমি তার জন্য আলাদা লিংক তৈরি করে দেব।"
            )
        await msg.reply_text(text)
        return

    # Link দিয়ে এলে সরাসরি ফাইল পাঠাও
    if not payload.startswith("f") or not payload[1:].isdigit():
        await msg.reply_text("❌ লিংকটি সঠিক নয়।")
        return

    file_msg_id = int(payload[1:])
    try:
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=file_msg_id,
        )
    except TelegramError as e:
        log.warning("copy failed for %s: %s", file_msg_id, e)
        await msg.reply_text("❌ ফাইলটি পাওয়া যায়নি বা মুছে ফেলা হয়েছে।")


# ---- Admin: ফাইল আপলোড -> লিংক তৈরি ----
async def admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    try:
        copied = await context.bot.copy_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=update.effective_chat.id,
            message_id=msg.message_id,
        )
    except TelegramError as e:
        await msg.reply_text(
            f"❌ Storage channel-এ সেভ হয়নি: {e}\n"
            "বটকে channel-এর Admin বানিয়েছেন কিনা এবং STORAGE_CHANNEL_ID ঠিক আছে কিনা দেখুন।"
        )
        return

    link = f"https://t.me/{context.bot.username}?start=f{copied.message_id}"
    await msg.reply_text(
        f"✅ ফাইল সেভ হয়েছে!\n\n🔗 লিংক:\n{link}",
        disable_web_page_preview=True,
    )


async def non_admin_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("⛔ শুধু Admin ফাইল আপলোড করতে পারে।")


# ---- Render-এর জন্য ছোট health server ----
class _Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass


def start_health_server():
    port = os.environ.get("PORT")
    if not port:
        return
    server = HTTPServer(("0.0.0.0", int(port)), _Health)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info("Health server running on port %s", port)


def main():
    start_health_server()

    app = Application.builder().token(BOT_TOKEN).build()

    file_filter = (
        filters.Document.ALL
        | filters.VIDEO
        | filters.AUDIO
        | filters.PHOTO
        | filters.ANIMATION
        | filters.VOICE
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            file_filter & filters.User(ADMIN_ID) & filters.ChatType.PRIVATE,
            admin_upload,
        )
    )
    app.add_handler(
        MessageHandler(file_filter & filters.ChatType.PRIVATE, non_admin_file)
    )

    log.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
