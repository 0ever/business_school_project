import requests
import json
import os
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import nest_asyncio

# === SETTINGS ===
TELEGRAM_TOKEN = '7555388402:AAECv7Mii5rS6BRClE000TZ_4nNDBu8gT98'
YOUR_CHAT_ID = 1249180037
DATA_FILE = "tracked_items.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

# === tracked items ===
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        tracked_items = json.load(f)
else:
    tracked_items = []

def save_tracked_items():
    with open(DATA_FILE, "w") as f:
        json.dump(tracked_items, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to your Price Tracker Bot!\n\n"
        "Commands:\n"
        "`add <url> <target_price>` – Start tracking\n"
        "`show all` – List all tracked items\n"
        "`remove <number>` – Remove item from list\n",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()

    if message.lower().startswith("add"):
        parts = message.split()
        if len(parts) == 3:
            url = parts[1]
            try:
                target_price = float(parts[2])
                if any(item["url"] == url for item in tracked_items):
                    await update.message.reply_text("⚠️ This product is already being tracked.")
                else:
                    tracked_items.append({"url": url, "target_price": target_price})
                    save_tracked_items()
                    await update.message.reply_text(f"✅ Tracking:\n{url}\nTarget price: €{target_price}")
            except ValueError:
                await update.message.reply_text("❗ Invalid price format. Example: `add https://asos.com/... 95`")
        else:
            await update.message.reply_text("❗ Wrong format. Example: `add https://asos.com/... 95`")

    elif message.lower() == "show all":
        if not tracked_items:
            await update.message.reply_text("📂 No items are currently being tracked.")
        else:
            text = "🛒 Currently tracking:\n\n"
            for i, item in enumerate(tracked_items, 1):
                text += f"{i}. [{item['url']}] – €{item['target_price']}\n"
            await update.message.reply_text(text, disable_web_page_preview=True)

    elif message.lower().startswith("remove"):
        parts = message.split()
        if len(parts) == 2 and parts[1].isdigit():
            index = int(parts[1]) - 1
            if 0 <= index < len(tracked_items):
                removed = tracked_items.pop(index)
                save_tracked_items()
                await update.message.reply_text(f"🗑️ Removed:\n{removed['url']}")
            else:
                await update.message.reply_text("❗ Invalid index. Use `show all` to see item numbers.")
        else:
            await update.message.reply_text("❗ Format: `remove <number>`. Example: `remove 1`")

    else:
        await update.message.reply_text(
            "❓ Unknown command.\nTry:\n"
            "`add <url> <price>`\n"
            "`show all`\n"
            "`remove <number>`",
            parse_mode="Markdown"
        )

async def check_prices(app):
    while True:
        for item in tracked_items:
            try:
                response = requests.get(item["url"], headers=HEADERS)
                soup = BeautifulSoup(response.content, "html.parser")
                price_tag = soup.find("span", class_="product-price-amount")
                if price_tag:
                    price_text = price_tag.get_text().strip().replace("€", "").replace(",", "").strip()
                    current_price = float(price_text)
                    print(f"[{item['url']}] Current price: €{current_price}")

                    if current_price <= item["target_price"]:
                        message = (
                            f"🔥 Price dropped!\n{item['url']}\n"
                            f"Now: €{current_price} (Target: €{item['target_price']})"
                        )
                        await app.bot.send_message(chat_id=YOUR_CHAT_ID, text=message, disable_web_page_preview=True)
                else:
                    print(f"[{item['url']}] ❌ Price not found.")
            except Exception as e:
                print(f"Error checking {item['url']}: {e}")
        await asyncio.sleep(10800)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.create_task(check_prices(app))
    print("✅ Bot started!")
    await app.run_polling()

# === running inside existing event loop ===
nest_asyncio.apply()
loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()