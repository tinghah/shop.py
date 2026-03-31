#!/usr/bin/env python3
"""
Telegram Business Bot - Training Courses & Services
SQLite Database + Admin Management
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# === CONFIGURATION ===
# Load from environment variables for security
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    # Fallback to empty - bot won't work without env var
    BOT_TOKEN = ""

OWNER_ID = int(os.environ.get("OWNER_ID", "1909898183"))
ACCOUNT_NUMBER = os.environ.get("ACCOUNT_NUMBER", "09786579514")
ACCOUNT_NAME = os.environ.get("ACCOUNT_NAME", "Htet Aung Hlaing")

# Webhook configuration
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", "8443"))

# === DATABASE SETUP ===
DB_FILE = "shop.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Items table (courses + services)
    c.execute('''CREATE TABLE IF NOT EXISTS items (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        name_mm TEXT,
        price TEXT NOT NULL,
        type TEXT NOT NULL,
        description TEXT,
        description_mm TEXT,
        is_active INTEGER DEFAULT 1
    )''')
    
    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        username TEXT,
        name TEXT,
        item_id TEXT,
        item_name TEXT,
        price TEXT,
        status TEXT DEFAULT 'pending',
        payment_proof TEXT,
        created TEXT
    )''')
    
    # User preferences table
    c.execute('''CREATE TABLE IF NOT EXISTS user_prefs (
        user_id TEXT PRIMARY KEY,
        lang TEXT DEFAULT 'mm'
    )''')
    
    conn.commit()
    
    # Insert default items if empty
    c.execute("SELECT COUNT(*) FROM items")
    if c.fetchone()[0] == 0:
        default_items = [
            ("1", "OpenClaw for Beginners", "OpenClaw အခြေခံသင်တန်း", "90,000", "course",
             "Learn OpenClaw from scratch!\n\n• Bot setup\n• Automation\n• AI tools\n• Building agents\n\nDuration: 4 hours + lifetime access",
             "OpenClaw ကို အခြေခံမှစတင်လေ့လာမည်။\n\nကြာချိန် - ၄ နာရီ + တစ်သက်တာဝင်ရောက်ကြည့်ရှုခွင့်"),
            ("2", "NotebookLM Training", "NotebookLM အသုံးပြုနည်း", "75,000", "course",
             "Master Google's NotebookLM!\n\n• Upload & analyze\n• Generate podcasts\n• Study guides\n\nDuration: 3 hours",
             "Google ၏ NotebookLM ကို ကျွမ်းကျင်စွာအသုံးပြုမည်။\n\nကြာချိန် - ၃ နာရီ"),
            ("s1", "Custom Telegram Bot Development", "Telegram Bot ရေးသားပေးခြင်း ဝန်ဆောင်မှု", "150,000", "service",
             "Get a custom Telegram bot:\n\n• Auto-replies\n• Payment integration\n• User management\n• 1 month free hosting",
             "သင့်လုပ်ငန်းအတွက် Telegram Bot ရေးသားပေးမည်။\n\n• အလိုအလျောက်စာပြန်စနစ်\n• ငွေပေးချေမှု\n• User စီမံခြင်း\n• ၁ လ အခမဲ့ Server"),
            ("s2", "AI Workflow Setup", "AI လုပ်ငန်းစဉ်များ ချိတ်ဆက်ပေးခြင်း", "200,000", "service",
             "Automate with AI:\n\n• Customer support AI\n• Document summarization\n• Content generation\n• OpenClaw setup",
             "AI ဖြင့် လုပ်ငန်းကို အော်တိုမေးရှင်း ပြုလုပ်ပေးမည်။\n\n• Customer စာပြန်ပေးမည့် AI\n• စာရွက်အကျဉ်းချုပ်\n• Content ရေးသားပေးခြင်း"),
        ]
        c.executemany("INSERT INTO items VALUES (?,?,?,?,?,?,?,1)", default_items)
        conn.commit()
    
    conn.close()

def get_items(item_type=None, active_only=True):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if item_type:
        if active_only:
            c.execute("SELECT * FROM items WHERE type=? AND is_active=1", (item_type,))
        else:
            c.execute("SELECT * FROM items WHERE type=?", (item_type,))
    else:
        if active_only:
            c.execute("SELECT * FROM items WHERE is_active=1")
        else:
            c.execute("SELECT * FROM items")
    items = {row[0]: {"id": row[0], "name": row[1], "name_mm": row[2], "price": row[3], 
                      "type": row[4], "description": row[5], "description_mm": row[6], "is_active": row[7]} 
                     for row in c.fetchall()}
    conn.close()
    return items

def add_item(item_id, name, name_mm, price, item_type, description, description_mm):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO items VALUES (?,?,?,?,?,?,?,1)",
               (item_id, name, name_mm, price, item_type, description, description_mm))
    conn.commit()
    conn.close()

def delete_item(item_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE items SET is_active=0 WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def get_all_items():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM items ORDER BY type, id")
    items = {}
    for row in c.fetchall():
        items[row[0]] = {"id": row[0], "name": row[1], "name_mm": row[2], "price": row[3], 
                        "type": row[4], "description": row[5], "description_mm": row[6], "is_active": row[7]}
    conn.close()
    return items

# === ORDER FUNCTIONS ===
def load_orders():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM orders")
    orders = {row[0]: dict(zip(["id", "user_id", "username", "name", "item_id", "item_name", "price", "status", "payment_proof", "created"], row)) 
             for row in c.fetchall()}
    conn.close()
    return orders

def save_order(order):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?,?,?,?,?)",
               (order["id"], order["user_id"], order["username"], order["name"], order["item_id"],
                order["item_name"], order["price"], order["status"], order.get("payment_proof", ""), order["created"]))
    conn.commit()
    conn.close()

def update_order_status(order_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()

def get_user_lang(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT lang FROM user_prefs WHERE user_id=?", (str(user_id),))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "mm"

def set_user_lang(user_id, lang):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO user_prefs (user_id, lang) VALUES (?, ?)",
              (str(user_id), lang))
    conn.commit()
    conn.close()

# === LANGUAGE TEXTS ===
TEXTS = {
    "en": {
        "welcome": "👋 Welcome!\n\nI'm your assistant.\n\nUse the menu below to browse courses and services.",
        "main_menu": "📋 *Main Menu*\n\nChoose an option:",
        "products": "📦 *Courses*\n\nSelect a course to see details:",
        "services": "🛠 *Services*\n\nSelect a service to see details:",
        "help": "📖 *Help*\n\n• /start - Menu\n• Browse courses/services\n• Buy Now → Payment\n• Upload screenshot after payment",
        "payment_details": "💳 *Payment Details*\n\nTransfer to:\n\n🏦 KBZ Pay\n💳 Wave Pay\n🏦 AYA Pay\n💳 A+ Wallet\n\n━━━━━━━━━━━━━\n\n💳 Account: `{}`\n👤 Name: {}\n\nTransfer and upload proof.",
        "buy_now": "🛒 *Buy Now*",
        "added_to_cart": "✅ *Selected!*\n\n📚 {}\n💰 Price: {} MMK\n\n💳 Account: `{}`\n👤 Name: {}\n\nTransfer *{} MMK* and upload screenshot.",
        "upload_proof": "📤 Upload Payment Proof\n\nSend your payment screenshot.",
        "payment_submitted": "✅ *Payment Submitted!*\n\nOrder ID: `{}`\nItem: {}\nAmount: {} MMK\n\nOwner will verify soon.",
        "no_pending": "❌ No pending order. Please select an item first.",
        "no_image": "❌ No image. Please upload screenshot.",
        "back": "🔙 Back",
        "upload_btn": "📤 Upload Proof",
        "help_btn": "❓ Help",
        "products_btn": "📦 Courses",
        "services_btn": "🛠 Services",
        "myorder_btn": "🛒 My Orders",
        "payment_btn": "💳 Payment",
        "lang_btn": "🌐 မြန်မာ",
    },
    "mm": {
        "welcome": "👋 မင်္ဂလာပါ။\n\nသင်တန်းများနှင့် ဝန်ဆောင်မှုများအတွက် ကူညီပေးမည့် Bot ဖြစ်ပါသည်။",
        "main_menu": "📋 *ပင်မမီနူး*",
        "products": "📦 *သင်တန်းများ*",
        "services": "🛠 *ဝန်ဆောင်မှုများ*",
        "help": "📖 *အကူအညီ*\n\n• /start - မီနူး\n• သင်တန်း/ဝန်ဆောင်မှု ရွေးချယ်ပါ\n• ဝယ်ယူ → ငွေချေ\n• Screenshot ပါးလိုက်ပါ",
        "payment_details": "💳 *ငွေပေးချေရန်*\n\n🏦 KBZ Pay\n💳 Wave Pay\n🏦 AYA Pay\n💳 A+ Wallet\n\n━━━━━━━━━━━━━\n\n💳 အကောင့်: `{}`\n👤 အမည်: {}\n\nငွေလွှဲပြီး Screenshot ပါးလိုက်ပါ။",
        "buy_now": "🛒 *ဝယ်မည်*",
        "added_to_cart": "✅ *ရွေးပြီးပါပြီ*\n\n📚 {}\n💰 ဈေး: {} MMK\n\n💳 အကောင့်: `{}`\n👤 အမည်: {}\n\n{} MMK လွှဲပြီး Screenshot ပါးလိုက်ပါ။",
        "upload_proof": "📤 ငွေလွှဲပြေစာ ပါးလိုက်ရန်",
        "payment_submitted": "✅ *ပြေစာ လက်ခံရရှိပါပြီ*\n\nOrder ID: `{}`\nဝယ်ယူမှု: {}\nပမာဏ: {} MMK\n\nအက်ဒမင်မှ စစ်ဆေးပါမည်။",
        "no_pending": "❌ ဝယ်ယူထားခြင်း မရှိသေးပါ။",
        "no_image": "❌ ပုံမတွေ့ပါ။ Screenshot ပါးလိုက်ပါ။",
        "back": "🔙 နောက်သို့",
        "upload_btn": "📤 ပြေစာ",
        "help_btn": "❓ အကူအညီ",
        "products_btn": "📦 သင်တန်းများ",
        "services_btn": "🛠 ဝန်ဆောင်မှုများ",
        "myorder_btn": "🛒 ကျွန်ုပ်၏ အော်ဒါ",
        "payment_btn": "💳 ငွေပေးချေ",
        "lang_btn": "🌐 English",
    }
}

def get_text(key, lang="en"):
    return TEXTS.get(lang, TEXTS["en"]).get(key, key)

# === KEYBOARDS ===
def main_menu_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("products_btn", lang), callback_data="products"),
         InlineKeyboardButton(get_text("services_btn", lang), callback_data="services")],
        [InlineKeyboardButton(get_text("myorder_btn", lang), callback_data="my_order"),
         InlineKeyboardButton(get_text("payment_btn", lang), callback_data="payment")],
        [InlineKeyboardButton(get_text("help_btn", lang), callback_data="help"),
         InlineKeyboardButton(get_text("lang_btn", lang), callback_data="switch_lang")]
    ])

def items_keyboard(items_dict, prefix, lang="en"):
    keyboard = []
    for iid, item in items_dict.items():
        name = item.get("name_mm", item["name"]) if lang == "mm" else item["name"]
        icon = "📚" if item["type"] == "course" else "🛠"
        keyboard.append([InlineKeyboardButton(f"{icon} {name}", callback_data=f"{prefix}{iid}")])
    keyboard.append([InlineKeyboardButton(get_text("back", lang), callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def item_detail_keyboard(item_id, back_target, lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("buy_now", lang), callback_data=f"buy_{item_id}")],
        [InlineKeyboardButton(get_text("back", lang), callback_data=back_target)]
    ])

def payment_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("upload_btn", lang), callback_data="upload_proof")],
        [InlineKeyboardButton(get_text("back", lang), callback_data="back")]
    ])

# === ADMIN HANDLERS ===
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    items = get_all_items()
    courses = {k:v for k,v in items.items() if v["type"] == "course" and v["is_active"]}
    services = {k:v for k,v in items.items() if v["type"] == "service" and v["is_active"]}
    orders = load_orders()
    pending = len([o for o in orders.values() if o["status"] == "pending"])
    
    msg = f"👨‍💻 *Admin Panel*\n\n"
    msg += f"📦 Courses: {len(courses)}\n"
    msg += f"🛠 Services: {len(services)}\n"
    msg += f"📋 Pending Orders: {pending}\n\n"
    msg += "*Commands:*\n"
    msg += "/admin add_course - Add new course\n"
    msg += "/admin add_service - Add new service\n"
    msg += "/admin list - List all items\n"
    msg += "/admin delete <id> - Delete item\n"
    msg += "/pending - View pending orders\n"
    msg += "/approve <order_id> - Approve order"
    
    await update.message.reply_text(msg, parse_mode=None)

async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    items = all_items = get_all_items()
    msg = "📋 *All Items:*\n\n"
    
    msg += "📦 *Courses:*\n"
    for iid, item in all_items.items():
        if item["type"] == "course":
            status = "✅" if item["is_active"] else "❌"
            msg += f"{status} `{iid}` - {item['name']} ({item['price']} MMK)\n"
    
    msg += "\n🛠 *Services:*\n"
    for iid, item in all_items.items():
        if item["type"] == "service":
            status = "✅" if item["is_active"] else "❌"
            msg += f"{status} `{iid}` - {item['name']} ({item['price']} MMK)\n"
    
    await update.message.reply_text(msg, parse_mode=None)

async def admin_add_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    context.bot_data.setdefault("awaiting_admin_input", {})[str(update.effective_user.id)] = "course"
    await update.message.reply_text(
        "📦 *Add New Course*\n\n"
        "Send in this format:\n"
        "`id|name|name_mm|price|description|description_mm`\n\n"
        "Example:\n"
        "`3|New Course|သင်တန်းအသစ်|50,000|Course desc|သင်တန်းအသစ်အောက်မှာ`",
        parse_mode=None
    )

async def admin_add_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    context.bot_data.setdefault("awaiting_admin_input", {})[str(update.effective_user.id)] = "service"
    await update.message.reply_text(
        "🛠 *Add New Service*\n\n"
        "Send in this format:\n"
        "`id|name|name_mm|price|description|description_mm`\n\n"
        "Example:\n"
        "`s3|Web Dev|ဝက်ဘ်ဖန်တီးခြင်း|100,000|We build websites|ဝက်ဘ်ဆိုဒ်များဖန်တီးပါးစပါး`",
        parse_mode=None
    )

async def admin_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: `/admin delete <id>`", parse_mode=None)
        return
    
    item_id = context.args[0]
    delete_item(item_id)
    await update.message.reply_text(f"✅ Item `{item_id}` deleted!", parse_mode=None)

async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    orders = load_orders()
    pending = {k:v for k,v in orders.items() if v["status"] == "pending"}
    
    if not pending:
        await update.message.reply_text("✅ No pending orders!")
        return
    
    msg = "⏳ *Pending Orders:*\n\n"
    for oid, o in pending.items():
        msg += f"ID: `{oid}`\nUser: {o['name']} (@{o['username']})\nItem: {o['item_name']}\nAmount: {o['price']} MMK\n---\n"
    
    await update.message.reply_text(msg, parse_mode=None)

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: `/approve <order_id>`", parse_mode=None)
        return
    
    order_id = context.args[0]
    orders = load_orders()
    
    if order_id not in orders:
        await update.message.reply_text(f"❌ Order `{order_id}` not found.", parse_mode=None)
        return
    
    update_order_status(order_id, "paid")
    
    try:
        buyer_id = orders[order_id]["user_id"]
        lang = get_user_lang(buyer_id)
        
        notify_msg = "🎉 *အတည်ပြုပါပြီ!*\n\nသင့်ငွေလွှဲကို ရရှိပြီး အတည်ပြုပါပြီ။" if lang == "mm" else "🎉 *Payment Approved!*\n\nYour order is confirmed."
        
        await context.bot.send_message(chat_id=buyer_id, text=notify_msg, parse_mode=None)
        await update.message.reply_text(f"✅ Order `{order_id}` approved!", parse_mode=None)
    except Exception as e:
        await update.message.reply_text(f"✅ Approved but couldn't notify: {e}")

# === MESSAGE HANDLER FOR ADDING ITEMS ===
async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    awaiting = context.bot_data.get("awaiting_admin_input", {})
    item_type = awaiting.get(user_id)
    
    if not item_type:
        return
    
    if update.effective_user.id != OWNER_ID:
        return
    
    text = update.message.text.strip()
    parts = text.split("|")
    
    if len(parts) < 6:
        await update.message.reply_text(
            "❌ Invalid format. Need 6 parts separated by `|`:\n"
            "`id|name|name_mm|price|description|description_mm`",
            parse_mode=None
        )
        return
    
    item_id = parts[0].strip()
    name = parts[1].strip()
    name_mm = parts[2].strip()
    price = parts[3].strip()
    description = parts[4].strip()
    description_mm = parts[5].strip()
    
    add_item(item_id, name, name_mm, price, item_type, description, description_mm)
    
    del context.bot_data["awaiting_admin_input"][user_id]
    
    type_label = "Course" if item_type == "course" else "Service"
    await update.message.reply_text(
        f"✅ {type_label} added!\n\n"
        f"ID: `{item_id}`\n"
        f"Name: {name}\n"
        f"Price: {price} MMK",
        parse_mode=None
    )

# === GENERAL HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    lang = get_user_lang(user_id)
    await update.message.reply_text(get_text("welcome", lang), reply_markup=main_menu_keyboard(lang))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    lang = get_user_lang(user_id)
    
    photo = update.message.photo[-1] if update.message.photo else None
    if not photo:
        await update.message.reply_text(get_text("no_image", lang))
        return
    
    pending = context.bot_data.get("pending_payment", {}).get(user_id)
    if not pending:
        await update.message.reply_text(get_text("no_pending", lang))
        return
    
    order_id = datetime.now().strftime("%y%m%d%H%M") + str(update.message.from_user.id)[-3:]
    
    order = {
        "id": order_id, "user_id": user_id,
        "username": update.message.from_user.username or "N/A",
        "name": update.message.from_user.first_name or "N/A",
        "item_id": pending["item_id"], "item_name": pending["name"],
        "price": pending["price"], "status": "pending",
        "payment_proof": f"photo:{photo.file_id}", "created": datetime.now().isoformat()
    }
    save_order(order)
    
    caption = f"🆕 *New Payment!*\n\nOrder: `{order_id}`\nUser: {update.message.from_user.first_name}\nItem: {pending['name']}\nAmount: {pending['price']} MMK\n\n/approve {order_id}"
    
    try:
        await context.bot.send_photo(OWNER_ID, photo.file_id, caption=caption, parse_mode=None)
    except:
        await context.bot.send_message(OWNER_ID, caption, parse_mode=None)
    
    context.bot_data.get("pending_payment", {}).pop(user_id, None)
    await update.message.reply_text(get_text("payment_submitted", lang).format(order_id, pending["name"], pending["price"]), parse_mode=None)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    lang = get_user_lang(user_id)
    
    if data == "switch_lang":
        lang = "en" if lang == "mm" else "mm"
        set_user_lang(user_id, lang)
        await query.edit_message_text(get_text("main_menu", lang), reply_markup=main_menu_keyboard(lang))
        return
    
    PRODUCTS = get_items("course")
    SERVICES = get_items("service")
    
    if data == "products":
        await query.edit_message_text(get_text("products", lang), reply_markup=items_keyboard(PRODUCTS, "p_", lang))
    elif data == "services":
        await query.edit_message_text(get_text("services", lang), reply_markup=items_keyboard(SERVICES, "s_", lang))
    
    elif data.startswith("p_") or data.startswith("s_"):
        is_service = data.startswith("s_")
        iid = data[2:]
        collection = SERVICES if is_service else PRODUCTS
        back = "services" if is_service else "products"
        
        if iid in collection:
            item = collection[iid]
            name = item.get("name_mm", item["name"]) if lang == "mm" else item["name"]
            desc = item.get("description_mm", item["description"]) if lang == "mm" else item["description"]
            icon = "🛠" if is_service else "📚"
            price_label = "စျေးနှုန်း" if lang == "mm" else "Price"
            text = f"{icon} *{name}*\n\n{desc}\n\n💰 *{price_label}: {item['price']} MMK*"
            await query.edit_message_text(text, reply_markup=item_detail_keyboard(data, back, lang), parse_mode=None)
    
    elif data.startswith("buy_"):
        raw_id = data[4:]
        iid = raw_id[2:]
        is_service = raw_id.startswith("s")
        collection = SERVICES if is_service else PRODUCTS
        
        if iid in collection:
            item = collection[iid]
            name = item.get("name_mm", item["name"]) if lang == "mm" else item["name"]
            text = get_text("added_to_cart", lang).format(name, item['price'], ACCOUNT_NUMBER, ACCOUNT_NAME, item['price'])
            context.bot_data.setdefault("pending_payment", {})[user_id] = {"item_id": raw_id, "price": item['price'], "name": name}
            await query.edit_message_text(text, reply_markup=payment_keyboard(lang), parse_mode=None)
    
    elif data == "my_order":
        orders = load_orders()
        user_orders = [o for o in orders.values() if o["user_id"] == user_id]
        
        if not user_orders:
            msg = "📭 သင်ဝယ်ယူထားသည်များ မရှိသေးပါ။" if lang == "mm" else "📭 No orders yet."
        else:
            msg = "📋 *Your Orders:*\n\n"
            for o in sorted(user_orders, key=lambda x: x["created"], reverse=True)[:5]:
                status = "⏳" if o["status"] == "pending" else "✅"
                msg += f"{status} `{o['id'][-6:]}` - {o['item_name']} - {o['price']} MMK\n"
        
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(get_text("back", lang), callback_data="back")]])
        await query.edit_message_text(msg, reply_markup=markup, parse_mode=None)
    
    elif data == "payment":
        text = get_text("payment_details", lang).format(ACCOUNT_NUMBER, ACCOUNT_NAME)
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang), parse_mode=None)
    
    elif data == "help":
        await query.edit_message_text(get_text("help", lang), reply_markup=main_menu_keyboard(lang))
    
    elif data == "upload_proof":
        await query.answer()
        await context.bot.send_message(chat_id=user_id, text=get_text("upload_proof", lang), parse_mode=None)
    
    elif data == "back":
        await query.edit_message_text(get_text("main_menu", lang), reply_markup=main_menu_keyboard(lang))

# === HEALTH CHECK ===
async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})

# === MAIN ===
def main():
    init_db()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("admin_list", admin_list))
    app.add_handler(CommandHandler("admin_add_course", admin_add_course))
    app.add_handler(CommandHandler("admin_add_service", admin_add_service))
    app.add_handler(CommandHandler("admin_delete", admin_delete))
    app.add_handler(CommandHandler("pending", admin_pending))
    app.add_handler(CommandHandler("approve", admin_approve))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_input))
    
    if WEBHOOK_URL:
        webhook_path = f"/{BOT_TOKEN}"
        web_app = web.Application()
        web_app.router.add_get("/health", health_handler)
        
        print(f"🤖 Bot starting in WEBHOOK mode on port {PORT}...")
        print(f"   Webhook URL: {WEBHOOK_URL}{webhook_path}")
        print(f"   Health check: {WEBHOOK_URL}/health")
        
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=webhook_path,
            webhook_url=f"{WEBHOOK_URL}{webhook_path}",
            web_app=web_app,
        )
    else:
        print("🤖 Bot starting in POLLING mode...")
        app.run_polling()

if __name__ == "__main__":
    main()