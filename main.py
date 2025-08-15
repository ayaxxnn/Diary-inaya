import os
from flask import Flask
import telebot
from datetime import datetime

TOKEN = "8209067688:AAG89WS4BzGhVznDeO5ClWtGEQsyiEbTVCs"  # Telegram BotFather se liya hua token
ADMIN_ID = 6788809365  # Apna Telegram user id daalo

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Initial Products
products = [
    {"name": "Gold Amul Milk", "price": 37},
    {"name": "Amul Taza", "price": 29},
    {"name": "Toast Big", "price": 75},
    {"name": "Tuar Dal 1kg", "price": 115}
]

# Purchase Record: user_id -> list of purchases
purchases = {}

# 🛒 /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use /products to see items.")

# 📦 /products command
@bot.message_handler(commands=['products'])
def list_products(message):
    text = "Available Products:\n"
    for i, p in enumerate(products, start=1):
        text += f"{i}. {p['name']} - ₹{p['price']}\n"
    text += "\nReply with item number to buy."
    bot.send_message(message.chat.id, text)

# 🆕 /add command (Admin only)
@bot.message_handler(commands=['add'])
def add_product_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Only admin can add products.")
        return
    bot.send_message(message.chat.id, "Send product name on first line, price on second line.")
    bot.register_next_step_handler(message, process_add_product)

def process_add_product(message):
    try:
        lines = message.text.strip().split("\n")
        if len(lines) != 2:
            bot.send_message(message.chat.id, "Format wrong. First line=Name, Second line=Price.")
            return
        name = lines[0]
        price = float(lines)
        products.append({"name": name, "price": price})
        bot.send_message(message.chat.id, f"✅ Added: {name} - ₹{price}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

# 📦 Buy by number
@bot.message_handler(func=lambda m: m.text.isdigit())
def buy_product(message):
    idx = int(message.text) - 1
    if 0 <= idx < len(products):
        product = products[idx]
        user_id = message.from_user.id
        if user_id not in purchases:
            purchases[user_id] = []
        purchases[user_id].append({
            "name": product['name'],
            "price": product['price'],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        bot.send_message(message.chat.id, f"✅ Purchased {product['name']} for ₹{product['price']}")
    else:
        bot.send_message(message.chat.id, "❌ Invalid product number.")

# 💰 /total command
@bot.message_handler(commands=['total'])
def total_purchase(message):
    user_id = message.from_user.id
    if user_id not in purchases or len(purchases[user_id]) == 0:
        bot.send_message(message.chat.id, "You have not purchased anything yet.")
        return
    total_amount = sum(p['price'] for p in purchases[user_id])
    history = "\n".join([f"{p['name']} - ₹{p['price']} on {p['date']}" for p in purchases[user_id]])
    bot.send_message(message.chat.id, f"🛒 Purchase History:\n{history}\n\n💰 Total Spent: ₹{total_amount}")

# Flask route for Render health check
@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    # Telegram polling (webhook not used)
    import threading
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
