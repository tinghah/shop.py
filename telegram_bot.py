#!/usr/bin/env python3
"""
Telegram Business Bot - Training Courses & Services
SQLite Database + Admin Management
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
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
        is_active INTEGER DEFAULT 1,
        stock INTEGER DEFAULT -1
    )''')

    # Migration: add stock column if missing
    c.execute("PRAGMA table_info(items)")
    columns = [col[1] for col in c.fetchall()]
    if "stock" not in columns:
        c.execute("ALTER TABLE items ADD COLUMN stock INTEGER DEFAULT -1")
    
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
        created TEXT,
        coupon_id TEXT,
        original_price TEXT
    )''')

    # Coupons table
    c.execute('''CREATE TABLE IF NOT EXISTS coupons (
        id TEXT PRIMARY KEY,
        code TEXT UNIQUE,
        discount_type TEXT CHECK(discount_type IN ('percent', 'fixed')),
        discount_value REAL NOT NULL,
        max_uses INTEGER,
        uses INTEGER DEFAULT 0,
        expires_at TEXT,
        is_active INTEGER DEFAULT 1
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
        c.executemany("INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?)",
                       [(i[0], i[1], i[2], i[3], i[4], i[5], i[6], 1, -1) for i in default_items])
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
                      "type": row[4], "description": row[5], "description_mm": row[6], "is_active": row[7],
                      "stock": row[8] if len(row) > 8 else -1}
                     for row in c.fetchall()}
    conn.close()
    return items

def add_item(item_id, name, name_mm, price, item_type, description, description_mm, stock=-1):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO items VALUES (?,?,?,?,?,?,?,?,?)",
               (item_id, name, name_mm, price, item_type, description, description_mm, 1, stock))
    conn.commit()
    conn.close()

def delete_item(item_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE items SET is_active=0 WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def set_stock(item_id, quantity):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE items SET stock=? WHERE id=?", (quantity, item_id))
    if quantity > 0:
        c.execute("UPDATE items SET is_active=1 WHERE id=? AND is_active=0", (item_id,))
    elif quantity == 0:
        c.execute("UPDATE items SET is_active=0 WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def decrement_stock(item_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT stock FROM items WHERE id=?", (item_id,))
    row = c.fetchone()
    if row and row[0] is not None and row[0] > 0:
        new_stock = row[0] - 1
        c.execute("UPDATE items SET stock=? WHERE id=?", (new_stock, item_id))
        if new_stock == 0:
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
                        "type": row[4], "description": row[5], "description_mm": row[6], "is_active": row[7],
                        "stock": row[8] if len(row) > 8 else -1}
    conn.close()
    return items

# === ORDER FUNCTIONS ===
def load_orders():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM orders")
    orders = {row[0]: dict(zip(["id", "user_id", "username", "name", "item_id", "item_name", "price", "status", "payment_proof", "created", "coupon_id", "original_price"], row)) 
             for row in c.fetchall()}
    conn.close()
    return orders

def save_order(order):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
               (order["id"], order["user_id"], order["username"], order["name"], order["item_id"],
                order["item_name"], order["price"], order["status"], order.get("payment_proof", ""), order["created"],
                order.get("coupon_id"), order.get("original_price")))
    conn.commit()
    conn.close()

def update_order_status(order_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()

# === COUPON FUNCTIONS ===
def add_coupon(code, discount_type, discount_value, max_uses):
    import uuid
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    coupon_id = uuid.uuid4().hex[:8]
    c.execute("INSERT OR REPLACE INTO coupons (id, code, discount_type, discount_value, max_uses) VALUES (?,?,?,?,?)",
              (coupon_id, code.upper(), discount_type, discount_value, max_uses))
    conn.commit()
    conn.close()
    return coupon_id

def get_coupon_by_code(code):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM coupons WHERE code=?", (code.upper(),))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "code": row[1], "discount_type": row[2], "discount_value": row[3],
                "max_uses": row[4], "uses": row[5], "expires_at": row[6], "is_active": row[7]}
    return None

def list_coupons(active_only=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if active_only:
        c.execute("SELECT * FROM coupons WHERE is_active=1")
    else:
        c.execute("SELECT * FROM coupons")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "code": r[1], "discount_type": r[2], "discount_value": r[3],
             "max_uses": r[4], "uses": r[5], "expires_at": r[6], "is_active": r[7]} for r in rows]

def deactivate_coupon(code):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE coupons SET is_active=0 WHERE code=?", (code.upper(),))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def validate_coupon(code):
    coupon = get_coupon_by_code(code)
    if not coupon:
        return None, "not_found"
    if not coupon["is_active"]:
        return None, "inactive"
    if coupon["max_uses"] is not None and coupon["uses"] >= coupon["max_uses"]:
        return None, "max_uses"
    if coupon["expires_at"]:
        try:
            exp = datetime.fromisoformat(coupon["expires_at"])
            if datetime.now() > exp:
                return None, "expired"
        except ValueError:
            pass
    return coupon, "ok"

def apply_discount(price_str, coupon):
    price = parse_price(price_str)
    if coupon["discount_type"] == "percent":
        discount = int(price * coupon["discount_value"] / 100)
    else:
        discount = int(coupon["discount_value"])
    discounted = max(0, price - discount)
    return discounted, discount

def increment_coupon_usage(coupon_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE coupons SET uses = uses + 1 WHERE id=?", (coupon_id,))
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
        "coupon_btn": "🎟 Have a coupon?",
        "coupon_prompt": "🎟 Enter your coupon code:",
        "coupon_applied": "✅ *Coupon Applied!*\n\nCode: `{}`\nDiscount: {}\n\n💰 Original: {} MMK\n🏷 Discount: -{} MMK\n*Total: {} MMK*",
        "coupon_invalid": "❌ Invalid coupon code.",
        "coupon_expired": "❌ This coupon has expired.",
        "coupon_max_uses": "❌ This coupon has reached its usage limit.",
        "coupon_inactive": "❌ This coupon is no longer active.",
        "coupon_skipped": "❌ No coupon applied. Use 'Have a coupon?' to enter a code.",
        "lang_btn": "🌐 မြန်မာ",
        "out_of_stock": "❌ *Out of Stock*",
        "low_stock": "⚠️ Only {} left!",
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
        "coupon_btn": "🎟 ကူပွန်ရှိပါသလား?",
        "coupon_prompt": "🎟 ကူပွန်ကုဒ်ထည့်ပါ:",
        "coupon_applied": "✅ *ကူပွန် အသုံးပြုပြီးပါပြီ!*\n\nCode: `{}`\nလျှော့ဈေး: {}\n\n💰 မူလဈေး: {} MMK\n🏷 လျှော့ဈေး: -{} MMK\n*စုစုပေါင်း: {} MMK*",
        "coupon_invalid": "❌ ကူပွန်ကုဒ် မမှန်ပါ။",
        "coupon_expired": "❌ ဤကူပွန်သည် သက်တမ်းကုန်ဆုံးသွားပါပြီ။",
        "coupon_max_uses": "❌ ဤကူပွန်သည် အသုံးပြုခွင့် ပြည့်သွားပါပြီ။",
        "coupon_inactive": "❌ ဤကူပွန်သည် အသုံးပြု၍ မရတော့ပါ။",
        "coupon_skipped": "❌ ကူပွန်မသုံးပါ။ 'ကူပွန်ရှိပါသလား?' ကိုနှိပ်ပြီး ကုဒ်ထည့်ပါ။",
        "lang_btn": "🌐 English",
        "out_of_stock": "❌ *ကုန်သွားပါပြီ*",
        "low_stock": "⚠️ {} ခုသာကျန်တော့သည်!",
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
        stock = item.get("stock", -1)
        if stock == 0:
            label = f"{icon} {name} ❌"
        elif 0 < stock < 3:
            label = f"{icon} {name} ⚠️"
        else:
            label = f"{icon} {name}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"{prefix}{iid}")])
    keyboard.append([InlineKeyboardButton(get_text("back", lang), callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def item_detail_keyboard(item_id, back_target, lang="en", stock=-1):
    buttons = []
    if stock == 0:
        buttons.append([InlineKeyboardButton(get_text("out_of_stock", lang), callback_data="noop")])
    else:
        buttons.append([InlineKeyboardButton(get_text("buy_now", lang), callback_data=f"buy_{item_id}")])
    buttons.append([InlineKeyboardButton(get_text("back", lang), callback_data=back_target)])
    return InlineKeyboardMarkup(buttons)

def payment_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("coupon_btn", lang), callback_data="apply_coupon")],
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
    msg += "/admin_stock <id> <qty> - Set stock (-1=unlimited)\n"
    msg += "/pending - View pending orders\n"
    msg += "/approve <order_id> - Approve order\n"
    msg += "/admin_stats - Analytics overview\n"
    msg += "/admin_revenue - Revenue report\n"
    msg += "/admin_export - Export orders (30d)\n"
    msg += "/coupon_add CODE percent|fixed VALUE MAX_USES\n"
    msg += "/coupon_list - List all coupons\n"
    msg += "/coupon_delete CODE - Deactivate coupon"
    
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
            stock = item.get("stock", -1)
            stock_label = "∞" if stock == -1 else str(stock)
            msg += f"{status} `{iid}` - {item['name']} ({item['price']} MMK) [Stock: {stock_label}]\n"
    
    msg += "\n🛠 *Services:*\n"
    for iid, item in all_items.items():
        if item["type"] == "service":
            status = "✅" if item["is_active"] else "❌"
            stock = item.get("stock", -1)
            stock_label = "∞" if stock == -1 else str(stock)
            msg += f"{status} `{iid}` - {item['name']} ({item['price']} MMK) [Stock: {stock_label}]\n"
    
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

async def admin_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/admin_stock <item_id> <quantity>`\nUse -1 for unlimited.", parse_mode=None)
        return
    
    item_id = context.args[0]
    try:
        quantity = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Quantity must be a number. Use -1 for unlimited.", parse_mode=None)
        return
    
    items = get_all_items()
    if item_id not in items:
        await update.message.reply_text(f"❌ Item `{item_id}` not found.", parse_mode=None)
        return
    
    set_stock(item_id, quantity)
    
    if quantity == -1:
        stock_label = "unlimited (∞)"
    elif quantity == 0:
        stock_label = "0 (out of stock, item deactivated)"
    else:
        stock_label = str(quantity)
        if quantity > 0:
            stock_label += " (item reactivated)" if not items[item_id]["is_active"] else ""
    
    await update.message.reply_text(f"✅ Stock for `{item_id}` set to {stock_label}!", parse_mode=None)

async def admin_coupon_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    args = context.args
    if len(args) < 4:
        await update.message.reply_text(
            "Usage: `/coupon_add CODE percent|fixed VALUE MAX_USES`\n\n"
            "Examples:\n"
            "`/coupon_add SALE10 percent 10 50` (10% off, max 50 uses)\n"
            "`/coupon_add FLAT5K fixed 5000 20` (5000 MMK off, max 20 uses)",
            parse_mode=None
        )
        return

    code = args[0].upper()
    discount_type = args[1].lower()
    if discount_type not in ("percent", "fixed"):
        await update.message.reply_text("❌ Discount type must be `percent` or `fixed`.", parse_mode=None)
        return

    try:
        discount_value = float(args[2])
        max_uses = int(args[3])
    except ValueError:
        await update.message.reply_text("❌ Invalid value or max uses. Must be numbers.", parse_mode=None)
        return

    if get_coupon_by_code(code):
        await update.message.reply_text(f"❌ Coupon `{code}` already exists.", parse_mode=None)
        return

    coupon_id = add_coupon(code, discount_type, discount_value, max_uses)

    desc = f"{discount_value}%" if discount_type == "percent" else f"{fmt_number(int(discount_value))} MMK"
    await update.message.reply_text(
        f"✅ *Coupon Created!*\n\n"
        f"ID: `{coupon_id}`\n"
        f"Code: `{code}`\n"
        f"Discount: {desc}\n"
        f"Max Uses: {max_uses}",
        parse_mode=None
    )

async def admin_coupon_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    coupons = list_coupons()
    if not coupons:
        await update.message.reply_text("📋 No coupons found.", parse_mode=None)
        return

    msg = "📋 *All Coupons:*\n\n"
    for c in coupons:
        status = "✅" if c["is_active"] else "❌"
        if c["discount_type"] == "percent":
            desc = f"{c['discount_value']}%"
        else:
            desc = f"{fmt_number(int(c['discount_value']))} MMK"
        expires = c["expires_at"][:10] if c["expires_at"] else "Never"
        uses_str = f"{c['uses']}/{c['max_uses']}" if c["max_uses"] is not None else f"{c['uses']}/∞"
        msg += f"{status} `{c['code']}` - {desc} off | Uses: {uses_str} | Expires: {expires}\n"

    await update.message.reply_text(msg, parse_mode=None)

async def admin_coupon_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: `/coupon_delete CODE`", parse_mode=None)
        return

    code = context.args[0]
    if deactivate_coupon(code):
        await update.message.reply_text(f"✅ Coupon `{code.upper()}` deactivated!", parse_mode=None)
    else:
        await update.message.reply_text(f"❌ Coupon `{code.upper()}` not found.", parse_mode=None)

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

    order = orders[order_id]
    if order.get("coupon_id"):
        increment_coupon_usage(order["coupon_id"])
    
    item_id = orders[order_id]["item_id"]
    items = get_all_items()
    
    stock_msg = ""
    if item_id in items:
        stock_before = items[item_id].get("stock", -1)
        if stock_before > 0:
            decrement_stock(item_id)
            if stock_before - 1 == 0:
                stock_msg = "\n⚠️ Stock is now 0 - item auto-deactivated."
            elif stock_before - 1 < 3:
                stock_msg = f"\n⚠️ Only {stock_before - 1} left in stock."
    
    try:
        buyer_id = orders[order_id]["user_id"]
        lang = get_user_lang(buyer_id)
        
        notify_msg = "🎉 *အတည်ပြုပါပြီ!*\n\nသင့်ငွေလွှဲကို ရရှိပြီး အတည်ပြုပါပြီ။" if lang == "mm" else "🎉 *Payment Approved!*\n\nYour order is confirmed."
        
        await context.bot.send_message(chat_id=buyer_id, text=notify_msg, parse_mode=None)
        await update.message.reply_text(f"✅ Order `{order_id}` approved!{stock_msg}", parse_mode=None)
    except Exception as e:
        await update.message.reply_text(f"✅ Approved but couldn't notify: {e}{stock_msg}")

# === ANALYTICS HANDLERS ===

def parse_price(price_str):
    return int(str(price_str).replace(",", "").replace(" ", ""))

def fmt_number(n):
    return f"{n:,}"

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    now = datetime.now()
    d7 = (now - timedelta(days=7)).isoformat()
    d30 = (now - timedelta(days=30)).isoformat()
    month_start = now.strftime("%Y-%m-01")

    c.execute("SELECT COUNT(*) FROM orders")
    total_all = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM orders WHERE created >= ?", (d7,))
    total_7d = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM orders WHERE created >= ?", (d30,))
    total_30d = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
    pending = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(CAST(REPLACE(price, ',', '') AS INTEGER)), 0) FROM orders WHERE status = 'paid'")
    rev_all = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(CAST(REPLACE(price, ',', '') AS INTEGER)), 0) FROM orders WHERE status = 'paid' AND created >= ?", (d7,))
    rev_7d = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(CAST(REPLACE(price, ',', '') AS INTEGER)), 0) FROM orders WHERE status = 'paid' AND created >= ?", (d30,))
    rev_30d = c.fetchone()[0]

    c.execute("SELECT item_name, COUNT(*) as cnt FROM orders WHERE status = 'paid' GROUP BY item_name ORDER BY cnt DESC LIMIT 5")
    top_items = c.fetchall()

    c.execute("SELECT COUNT(DISTINCT user_id) FROM orders WHERE created >= ?", (month_start,))
    new_customers = c.fetchone()[0]

    conn.close()

    msg = "📊 *Admin Statistics*\n\n"
    msg += "📋 *Orders:*\n"
    msg += f"  All time: {fmt_number(total_all)}\n"
    msg += f"  Last 7 days: {fmt_number(total_7d)}\n"
    msg += f"  Last 30 days: {fmt_number(total_30d)}\n"
    msg += f"  Pending: {fmt_number(pending)}\n\n"
    msg += "💰 *Revenue (paid):*\n"
    msg += f"  All time: {fmt_number(rev_all)} MMK\n"
    msg += f"  Last 7 days: {fmt_number(rev_7d)} MMK\n"
    msg += f"  Last 30 days: {fmt_number(rev_30d)} MMK\n\n"
    msg += "🏆 *Top 5 Best Sellers:*\n"
    for i, (name, cnt) in enumerate(top_items, 1):
        msg += f"  {i}. {name} - {cnt} orders\n"
    if not top_items:
        msg += "  No paid orders yet\n"
    msg += f"\n👥 New customers this month: {fmt_number(new_customers)}"

    await update.message.reply_text(msg, parse_mode=None)

async def admin_revenue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    now = datetime.now()

    msg = "💰 *Revenue Report*\n\n"

    msg += "📅 *Daily Revenue (Last 7 Days):*\n"
    msg += "```\n"
    msg += f"{'Date':<12} {'Revenue':>12}\n"
    msg += "-" * 25 + "\n"
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_label = day.strftime("%b %d")
        next_day = (day + timedelta(days=1)).strftime("%Y-%m-%d")
        c.execute("SELECT COALESCE(SUM(CAST(REPLACE(price, ',', '') AS INTEGER)), 0) FROM orders WHERE status = 'paid' AND created >= ? AND created < ?", (day_str, next_day))
        rev = c.fetchone()[0]
        msg += f"{day_label:<12} {fmt_number(rev):>12}\n"
    msg += "```\n\n"

    msg += "📆 *Monthly Revenue (Last 6 Months):*\n"
    msg += "```\n"
    msg += f"{'Month':<12} {'Revenue':>12}\n"
    msg += "-" * 25 + "\n"
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30 * i)
        month_str = month_date.strftime("%Y-%m")
        month_label = month_date.strftime("%b %Y")
        c.execute("SELECT COALESCE(SUM(CAST(REPLACE(price, ',', '') AS INTEGER)), 0) FROM orders WHERE status = 'paid' AND created LIKE ?", (f"{month_str}%",))
        rev = c.fetchone()[0]
        msg += f"{month_label:<12} {fmt_number(rev):>12}\n"
    msg += "```\n\n"

    items = get_all_items()
    item_types = set(i["type"] for i in items.values())

    msg += "📊 *Revenue by Type:*\n"
    for itype in sorted(item_types):
        c.execute("SELECT COALESCE(SUM(CAST(REPLACE(o.price, ',', '') AS INTEGER)), 0) FROM orders o JOIN items i ON o.item_id = i.id WHERE o.status = 'paid' AND i.type = ?", (itype,))
        rev = c.fetchone()[0]
        icon = "📚" if itype == "course" else "🛠"
        msg += f"  {icon} {itype.title()}: {fmt_number(rev)} MMK\n"

    conn.close()

    await update.message.reply_text(msg, parse_mode=None)

async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    d30 = (datetime.now() - timedelta(days=30)).isoformat()
    c.execute("SELECT * FROM orders WHERE created >= ? ORDER BY created DESC", (d30,))
    rows = c.fetchall()

    cols = ["id", "user_id", "username", "name", "item_id", "item_name", "price", "status", "payment_proof", "created"]
    orders = [dict(zip(cols, row)) for row in rows]

    total = len(orders)
    paid = len([o for o in orders if o["status"] == "paid"])
    pending = len([o for o in orders if o["status"] == "pending"])
    total_rev = sum(parse_price(o["price"]) for o in orders if o["status"] == "paid")

    conn.close()

    msg = "📋 *Orders Export (Last 30 Days)*\n"
    msg += "=" * 35 + "\n\n"
    msg += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    msg += f"Total orders: {total}\n"
    msg += f"Paid: {paid} | Pending: {pending}\n"
    msg += f"Total revenue: {fmt_number(total_rev)} MMK\n\n"
    msg += "-" * 35 + "\n\n"

    for o in orders:
        status_icon = "✅" if o["status"] == "paid" else "⏳"
        created = o["created"][:10] if o["created"] else "N/A"
        msg += f"{status_icon} Order {o['id']}\n"
        msg += f"  Customer: {o['name']} (@{o['username']})\n"
        msg += f"  Item: {o['item_name']}\n"
        msg += f"  Amount: {o['price']} MMK\n"
        msg += f"  Status: {o['status']}\n"
        msg += f"  Date: {created}\n\n"

    if not orders:
        msg += "No orders in the last 30 days.\n"

    await update.message.reply_text(msg, parse_mode=None)

# === MESSAGE HANDLER FOR ADDING ITEMS AND COUPON INPUT ===
async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Handle coupon code input
    if context.bot_data.get("awaiting_coupon", {}).get(user_id):
        del context.bot_data["awaiting_coupon"][user_id]
        lang = get_user_lang(user_id)
        pending = context.bot_data.get("pending_payment", {}).get(user_id)

        if not pending:
            await update.message.reply_text(get_text("no_pending", lang), parse_mode=None)
            return

        code = update.message.text.strip()
        coupon, status = validate_coupon(code)

        if status == "not_found":
            await update.message.reply_text(get_text("coupon_invalid", lang), parse_mode=None)
            return
        if status == "expired":
            await update.message.reply_text(get_text("coupon_expired", lang), parse_mode=None)
            return
        if status == "max_uses":
            await update.message.reply_text(get_text("coupon_max_uses", lang), parse_mode=None)
            return
        if status == "inactive":
            await update.message.reply_text(get_text("coupon_inactive", lang), parse_mode=None)
            return

        original_price = pending.get("original_price", pending["price"])
        discounted, discount_amount = apply_discount(original_price, coupon)

        if coupon["discount_type"] == "percent":
            discount_desc = f"{coupon['discount_value']}%"
        else:
            discount_desc = f"{fmt_number(int(coupon['discount_value']))} MMK"

        pending["price"] = fmt_number(discounted)
        pending["coupon_id"] = coupon["id"]
        pending["coupon_code"] = coupon["code"]

        text = get_text("coupon_applied", lang).format(
            coupon["code"], discount_desc,
            fmt_number(parse_price(original_price)),
            fmt_number(discount_amount),
            fmt_number(discounted)
        )
        markup = payment_keyboard(lang)
        await update.message.reply_text(text, reply_markup=markup, parse_mode=None)
        return

    # Handle admin item input
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
        "payment_proof": f"photo:{photo.file_id}", "created": datetime.now().isoformat(),
        "coupon_id": pending.get("coupon_id"),
        "original_price": pending.get("original_price")
    }
    save_order(order)
    
    coupon_info = ""
    if pending.get("coupon_code"):
        coupon_info = f"\n🏷 Coupon: `{pending['coupon_code']}`\nOriginal: {pending.get('original_price', pending['price'])} MMK"
    caption = f"🆕 *New Payment!*\n\nOrder: `{order_id}`\nUser: {update.message.from_user.first_name}\nItem: {pending['name']}\nAmount: {pending['price']} MMK{coupon_info}\n\n/approve {order_id}"
    
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
            price_label = "ဈေးနှုန်း" if lang == "mm" else "Price"
            text = f"{icon} *{name}*\n\n{desc}\n\n💰 *{price_label}: {item['price']} MMK*"
            stock = item.get("stock", -1)
            if stock == 0:
                text += f"\n\n{get_text('out_of_stock', lang)}"
            elif 0 < stock < 3:
                text += f"\n\n{get_text('low_stock', lang).format(stock)}"
            await query.edit_message_text(text, reply_markup=item_detail_keyboard(data, back, lang, stock=stock), parse_mode=None)
    
    elif data.startswith("buy_"):
        raw_id = data[4:]
        iid = raw_id[2:]
        is_service = raw_id.startswith("s")
        collection = SERVICES if is_service else PRODUCTS
        
        if iid in collection:
            item = collection[iid]
            stock = item.get("stock", -1)
            if stock == 0:
                await query.answer(get_text("out_of_stock", lang), show_alert=True)
                return
            name = item.get("name_mm", item["name"]) if lang == "mm" else item["name"]
            text = get_text("added_to_cart", lang).format(name, item['price'], ACCOUNT_NUMBER, ACCOUNT_NAME, item['price'])
            context.bot_data.setdefault("pending_payment", {})[user_id] = {"item_id": raw_id, "price": item['price'], "original_price": item['price'], "name": name}
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

    elif data == "apply_coupon":
        pending = context.bot_data.get("pending_payment", {}).get(user_id)
        if not pending:
            await query.answer(get_text("no_pending", lang), show_alert=True)
            return
        context.bot_data.setdefault("awaiting_coupon", {})[user_id] = True
        await query.answer()
        await context.bot.send_message(chat_id=user_id, text=get_text("coupon_prompt", lang), parse_mode=None)

    elif data == "back":
        await query.edit_message_text(get_text("main_menu", lang), reply_markup=main_menu_keyboard(lang))
    
    elif data == "noop":
        pass

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
    app.add_handler(CommandHandler("admin_stock", admin_stock))
    app.add_handler(CommandHandler("coupon_add", admin_coupon_add))
    app.add_handler(CommandHandler("coupon_list", admin_coupon_list))
    app.add_handler(CommandHandler("coupon_delete", admin_coupon_delete))
    app.add_handler(CommandHandler("admin_stats", admin_stats))
    app.add_handler(CommandHandler("admin_revenue", admin_revenue))
    app.add_handler(CommandHandler("admin_export", admin_export))
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