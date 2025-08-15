import os, json
from flask import Flask
import telebot
from datetime import datetime
import threading

TOKEN = "8209067688:AAG89WS4BzGhVznDeO5ClWtGEQsyiEbTVCs"
ADMIN_ID = 6788809365  # Apna Telegram ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

PRODUCTS_FILE = "products.json"
PURCHASES_FILE = "purchases.json"

def load_data(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return [] if file == PRODUCTS_FILE else {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

products = load_data(PRODUCTS_FILE)
purchases = load_data(PURCHASES_FILE)

# ---------- Helper Price Parser ----------
def parse_price(price_text):
    clean = price_text.lower().replace("₹", "").replace("rs", "").replace("rupees", "").strip()
    return float(clean)

# ---------- Commands ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! 🛒 Use /products to see items, /total for your purchase summary.")

@bot.message_handler(commands=['products'])
def list_products(message):
    text = "📦 Available Products:\n"
    for i, p in enumerate(products, start=1):
        text += f"{i}. {p['name']} - ₹{p['price']}\n"
    text += "\nSend product number to buy."
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['add'])
def add_product_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Only admin can add products.")
        return
    bot.send_message(message.chat.id, "Send product name and price in one line: Example:\nAmul Cheese 150")
    bot.register_next_step_handler(message, process_add_product)

def process_add_product(message):
    try:
        parts = message.text.rsplit(" ", 1)  # Name and last word as price
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Format: ProductName Price\nExample: Amul Cheese 150")
            return
        name = parts[0].strip()
        price = parse_price(parts)
        products.append({"name": name, "price": price})
        save_data(PRODUCTS_FILE, products)
        bot.send_message(message.chat.id, f"✅ Added: {name} - ₹{price}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

@bot.message_handler(func=lambda m: m.text.isdigit())
def buy_product(message):
    idx = int(message.text) - 1
    if 0 <= idx < len(products):
        product = products[idx]
        user_id = str(message.from_user.id)
        if user_id not in purchases:
            purchases[user_id] = []
        purchases[user_id].append({
            "name": product['name'],
            "price": product['price'],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_data(PURCHASES_FILE, purchases)
        bot.send_message(message.chat.id, f"✅ Purchased {product['name']} for ₹{product['price']}")
    else:
        bot.send_message(message.chat.id, "❌ Invalid product number.")

@bot.message_handler(commands=['total'])
def total_purchase(message):
    user_id = str(message.from_user.id)
    if user_id not in purchases or len(purchases[user_id]) == 0:
        bot.send_message(message.chat.id, "You have not purchased anything yet.")
        return
    total_amount = sum(p['price'] for p in purchases[user_id])
    history = "\n".join([f"{i+1}. {p['name']} - ₹{p['price']} on {p['date']}" for i, p in enumerate(purchases[user_id])])
    bot.send_message(message.chat.id, f"🛒 Purchase History:\n{history}\n\n💰 Total Spent: ₹{total_amount}")

@bot.message_handler(commands=['delete'])
def delete_purchase(message):
    user_id = str(message.from_user.id)
    if user_id not in purchases or len(purchases[user_id]) == 0:
        bot.send_message(message.chat.id, "No purchases to delete.")
        return
    history = "\n".join([f"{i+1}. {p['name']} - ₹{p['price']} on {p['date']}" for i, p in enumerate(purchases[user_id])])
    bot.send_message(message.chat.id, f"Your purchases:\n{history}\n\nSend number to delete item.")
    bot.register_next_step_handler(message, process_delete)

def process_delete(message):
    try:
        user_id = str(message.from_user.id)
        idx = int(message.text) - 1
        if 0 <= idx < len(purchases[user_id]):
            removed = purchases[user_id].pop(idx)
            save_data(PURCHASES_FILE, purchases)
            bot.send_message(message.chat.id, f"🗑 Deleted: {removed['name']} - ₹{removed['price']}")
        else:
            bot.send_message(message.chat.id, "❌ Invalid number.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
