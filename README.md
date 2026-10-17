# Telegram File Transfer Bot

## কীভাবে কাজ করে
1. Admin বটে ফাইল পাঠায় (APK, Video, PDF, ZIP ইত্যাদি) -> বট ফাইলটি private Storage Channel-এ রাখে -> প্রতিটি ফাইলের জন্য আলাদা লিংক দেয়।
2. কেউ লিংকে ক্লিক করে Start চাপলে বট সরাসরি ওই ফাইল পাঠায়।

## ফাইল স্ট্রাকচার
- `bot.py` : বটের মূল কোড
- `requirements.txt` : দরকারি লাইব্রেরি

## Setup
1. @BotFather থেকে বট বানিয়ে টোকেন নিন।
2. একটি **Private Channel** বানান -> বটকে **Admin** করুন (Post Messages অনুমতিসহ)।
3. `bot.py`-তে এই দুটি লাইন নিজের ID দিয়ে ঠিক করুন (সরাসরি সংখ্যা, `os.environ` ছাড়া):

   ADMIN_ID = আপনার_টেলিগ্রাম_ইউজার_আইডি
   STORAGE_CHANNEL_ID = -100xxxxxxxxxx

4. Hosting-এ শুধু **একটি** Environment Variable দিন:
   - Key: `BOT_TOKEN`
   - Value: BotFather-এর টোকেন

⚠️ টোকেন কখনো কোডে, README-তে বা চ্যাটে লিখবেন না। GitHub repo Private রাখুন।

## Deploy

**Render:** New -> Web Service -> GitHub repo
- Build Command: `pip install -r requirements.txt`
- Start Command: `python bot.py`
- Environment পেজে Key `BOT_TOKEN` দিয়ে টোকেন বসান, তারপর **Save, rebuild, and deploy** চাপুন।
- Free plan ১৫ মিনিট idle থাকলে ঘুমায়: UptimeRobot দিয়ে Render URL প্রতি ৫ মিনিটে ping করুন।

**Railway:** New Project -> Deploy from GitHub
- Start Command: `python bot.py`
- Variables ট্যাবে `BOT_TOKEN` দিন।

দুই জায়গায় একই টোকেনে একসাথে চালাবেন না (Conflict error হবে)। একটাই চালু রাখুন।

## ব্যবহার
1. বটকে `/start` দিন।
2. Admin অ্যাকাউন্ট থেকে বটে ফাইল পাঠান -> লিংক ফেরত পাবেন।
3. লিংকটি অন্য অ্যাকাউন্ট থেকে খুলে Start চাপলে ফাইল আসবে।

## সাধারণ সমস্যা
- **KeyError: 'BOT_TOKEN'** : Render-এর Environment পেজে Key-এর নাম হুবহু `BOT_TOKEN` কিনা দেখুন (Key-তে নাম, Value-তে টোকেন)।
- **KeyError: '123456...' (সংখ্যা)** : `bot.py`-তে `os.environ["..."]`-এর ভেতরে সংখ্যা বসিয়েছেন। ADMIN_ID আর STORAGE_CHANNEL_ID সরাসরি `=` চিহ্নের পরে লিখুন।
- **Channel-এ সেভ হয়নি** : বট Channel-এর Admin কিনা এবং Channel ID ঠিক কিনা দেখুন।
- **Conflict error** : একই টোকেনে একাধিক জায়গায় বট চলছে, একটা বন্ধ করুন।
