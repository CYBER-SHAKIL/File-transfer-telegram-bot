# Telegram File Transfer Bot

## কীভাবে কাজ করে
1. Admin বটে ফাইল পাঠায় -> বট ফাইলটি private Storage Channel-এ রাখে -> আলাদা লিংক দেয়।
2. কেউ লিংকে ক্লিক করে Start চাপলে বট সরাসরি ওই ফাইল পাঠায়।

## Setup
1. @BotFather থেকে নতুন টোকেন নিন (পুরনোটা Revoke করুন)।
2. একটি **Private Channel** বানান -> বটকে **Admin** করুন (Post messages অনুমতিসহ)।
3. Channel ID বের করুন (@userinfobot / @getidsbot-এ channel-এর একটি মেসেজ forward করুন)। ID `-100...` দিয়ে শুরু হয়।
4. Hosting-এ Environment Variables দিন:
   - BOT_TOKEN
   - ADMIN_ID = 8361587941
   - STORAGE_CHANNEL_ID

## Deploy
**Render:** New -> Web Service -> GitHub repo
- Build: `pip install -r requirements.txt`
- Start: `python bot.py`
- Free plan ১৫ মিনিট idle থাকলে ঘুমায়: UptimeRobot দিয়ে আপনার Render URL প্রতি ৫ মিনিটে ping করুন।

**Railway:** New Project -> Deploy from GitHub
- Start Command: `python bot.py`
- Variables ট্যাবে উপরের ৩টি variable দিন।

দুই জায়গায় একই টোকেনে একসাথে চালাবেন না (Conflict error হবে)। একটাই চালু রাখুন।
