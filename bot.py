import os
import re
import json
import time
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

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = 8361587941
STORAGE_CHANNEL_ID = -1003934729128

DB_PREFIX = "CODEDB:"
codes = {}          # {"482913": [12, 13], ...}
db_msg_id = None    # Channel-এর pinned database মেসেজ
fails = {}          # {user_id: (count, first_time)}
MAX_FAILS = 5
LOCK_SECONDS = 600


# ---------- Database (Channel-এর pinned মেসেজে) ----------
async def load_db(app: Application):
    global db_msg_id, codes
    try:
        chat = await app.bot.get_chat(STORAGE_CHANNEL_ID)
        pm = chat.pinned_message
        if pm and pm.text and pm.text.startswith(DB_PREFIX):
            db_msg_id = pm.message_id
            codes = json.loads(pm.text[len(DB_PREFIX):] or "{}")
            log.info("Loaded %d codes", len(codes))
        else:
            m = await app.bot.send_message(STORAGE_CHANNEL_ID, DB_PREFIX + "{}")
            await app.bot.pin_chat_message(
                STORAGE_CHANNEL_ID, m.message_id, disable_notification=True
            )
            db_msg_id = m.message_id
            log.info("Created new code database")
    except Exception as e:
        log.error("Database load failed: %s", e)


async def save_db(bot) -> bool:
    if db_msg_id is None:
        return False
    try:
        await bot.edit_message_text(
            DB_PREFIX + json.dumps(codes),
            chat_id=STORAGE_CHANNEL_ID,
            message_id=db_msg_id,
        )
        return True
    except TelegramError as e:
        if "not modified" in str(e).lower():
            return True
        log.error("Save failed: %s", e)
        return False


# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    payload = context.args[0] if context.args else None

    if not payload:
        text = "👋 স্বাগতম! আপনার কাছে থাকা কোড (পাসওয়ার্ড) এখানে লিখে পাঠান, আমি ফাইল দিয়ে দেব।"
        if update.effective_user.id == ADMIN_ID:
            text += (
                "\n\n🔧 Admin:\n"
                "• ফাইল পাঠান -> লিংক পাবেন\n"
                "• লিংক মেসেজে Reply করে /setcode 482913 লিখুন\n"
                "• /codes — সব কোড দেখুন\n"
                "• /delcode 482913 — কোড মুছুন"
            )
        await msg.reply_text(text)
        return

    if not payload.startswith("f") or not payload[1:].isdigit():
        await msg.reply_text("❌ লিংকটি সঠিক নয়।")
        return

    try:
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=int(payload[1:]),
        )
    except TelegramError as e:
        log.warning("copy failed: %s", e)
        await msg.reply_text("❌ ফাইলটি পাওয়া যায়নি।")


# ---------- Admin: ফাইল আপলোড ----------
async def admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    try:
        copied = await context.bot.copy_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=update.effective_chat.id,
            message_id=msg.message_id,
        )
    except TelegramError as e:
        await msg.reply_text(f"❌ Channel-এ সেভ হয়নি: {e}")
        return

    link = f"https://t.me/{context.bot.username}?start=f{copied.message_id}"
    await msg.reply_text(
        f"✅ সেভ হয়েছে!\n\n🔗 লিংক:\n{link}\n\n"
        "🔑 কোড সেট করতে এই মেসেজে Reply করে লিখুন:\n/setcode 482913"
    )


async def non_admin_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("⛔ শুধু Admin আপলোড করতে পারে।")


# ---------- Admin: কোড কমান্ড ----------
async def setcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("ব্যবহার: লিংকের মেসেজে Reply করে /setcode 482913")
        return
    if not msg.reply_to_message or not msg.reply_to_message.text:
        await msg.reply_text("⚠️ ফাইলের লিংক-মেসেজে Reply করে কমান্ডটি দিন।")
        return

    m = re.search(r"start=f(\d+)", msg.reply_to_message.text)
    if not m:
        await msg.reply_text("⚠️ ওই মেসেজে ফাইলের লিংক পাওয়া যায়নি।")
        return

    code = context.args[0].strip()
    file_id = int(m.group(1))
    codes.setdefault(code, [])
    if file_id not in codes[code]:
        codes[code].append(file_id)

    if await save_db(context.bot):
        await msg.reply_text(
            f"✅ কোড `{code}` সেট হয়েছে ({len(codes[code])}টি ফাইল)।\n"
            "একই কোডে আরও ফাইল যোগ করতে একইভাবে আবার /setcode দিন।",
            parse_mode="Markdown",
        )
    else:
        await msg.reply_text(
            "❌ কোড সেভ হয়নি। বটকে Channel-এ Pin Messages ও Edit Messages অনুমতি দিয়েছেন কিনা দেখুন।"
        )


async def delcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("ব্যবহার: /delcode 482913")
        return
    code = context.args[0].strip()
    if code in codes:
        del codes[code]
        await save_db(context.bot)
        await msg.reply_text(f"🗑️ কোড {code} মুছে ফেলা হয়েছে।")
    else:
        await msg.reply_text("❌ এই কোড নেই।")


async def list_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not codes:
        await update.effective_message.reply_text("কোনো কোড নেই।")
        return
    lines = [f"{c} -> {len(f)}টি ফাইল" for c, f in codes.items()]
    await update.effective_message.reply_text("🔑 কোড তালিকা:\n" + "\n".join(lines))


# ---------- User: কোড লিখলে ফাইল ----------
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    uid = update.effective_user.id
    text = (msg.text or "").strip()
    now = time.time()

    count, first = fails.get(uid, (0, now))
    if now - first > LOCK_SECONDS:
        count, first = 0, now
    if count >= MAX_FAILS:
        await msg.reply_text("⏳ অনেকবার ভুল কোড দিয়েছেন। ১০ মিনিট পর আবার চেষ্টা করুন।")
        return

    if text in codes:
        fails.pop(uid, None)
        sent = 0
        for fid in codes[text]:
            try:
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=fid,
                )
                sent += 1
            except TelegramError as e:
                log.warning("copy failed %s: %s", fid, e)
        if sent == 0:
            await msg.reply_text("❌ ফাইল পাওয়া যায়নি।")
    else:
        fails[uid] = (count + 1, first)
        await msg.reply_text("❌ ভুল কোড। আবার চেষ্টা করুন।")


# ---------- Render health server ----------
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass


def start_health_server():
    port = os.environ.get("PORT")
    if port:
        server = HTTPServer(("0.0.0.0", int(port)), Health)
        threading.Thread(target=server.serve_forever, daemon=True).start()


def main():
    start_health_server()
    app = Application.builder().token(BOT_TOKEN).post_init(load_db).build()

    files = (
        filters.Document.ALL
        | filters.VIDEO
        | filters.AUDIO
        | filters.PHOTO
        | filters.ANIMATION
        | filters.VOICE
    )
    admin = filters.User(ADMIN_ID)
    private = filters.ChatType.PRIVATE

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setcode", setcode, filters=admin))
    app.add_handler(CommandHandler("delcode", delcode, filters=admin))
    app.add_handler(CommandHandler("codes", list_codes, filters=admin))
    app.add_handler(MessageHandler(files & admin & private, admin_upload))
    app.add_handler(MessageHandler(files & private, non_admin_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & private, on_text))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
