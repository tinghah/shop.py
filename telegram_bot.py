#!/usr/bin/env python3
"""
Telegram Business Bot - Training Courses
Optimized Myanmar/English Language Support & Advanced Shop Logic
"""

import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# === CONFIGURATION ===
BOT_TOKEN = "8684412687:AAEp5ZRO6s1wSh0KmUP_GZa351HtNDmYJ4k"
OWNER_ID = int(os.environ.get("OWNER_ID", "1909898183"))

# Bank Details (All available options)
ACCOUNT_NUMBER = "09786579514"
ACCOUNT_NAME = "Htet Aung Hlaing"

# Products with descriptions
PRODUCTS = {
    "1": {
        "name": "OpenClaw for Beginners", 
        "name_mm": "OpenClaw အခြေခံသင်တန်း",
        "price": 49,
        "description": "Learn OpenClaw from scratch! This course covers:\n\n• Bot setup & configuration\n• Automation workflows\n• Integration with AI tools\n• Building your first agent\n\nDuration: 4 hours video + lifetime access",
        "description_mm": "OpenClaw ကို အခြေခံမှစတင်လေ့လာမည်။ သင်ယူမည့်အရာများ -\n\n• Bot အသုံးပြုနည်း\n• Automation လုပ်ငန်းစဉ်များ\n• AI tools များနှင့် ချိတ်ဆက်ခြင်း\n• ကိုယ်ပိုင် Agent ဖန်တီးခြင်း\n\nကြာချိန် - ၄ နာရီ + တစ်သက်တာဝင်ရောက်ကြည့်ရှုခွင့်"
    },
    "2": {
        "name": "NotebookLM Training", 
        "name_mm": "NotebookLM အသုံးပြုနည်း",
        "price": 39,
        "description": "Master Google's NotebookLM!\n\n• Upload & analyze documents\n• Generate podcasts from notes\n• Create study guides\n• AI-powered research\n\nDuration: 3 hours",
        "description_mm": "Google ၏ NotebookLM ကို ကျွမ်းကျင်စွာအသုံးပြုမည်။\n\n• စာရွက်စာတမ်းများထည့်သွင်းခြင်းနှင့် လေ့လာခြင်း\n• မှတ်စုများမှ Podcast ဖန်တီးခြင်း\n• Study guides များဖန်တီးခြင်း\n• AI အကူအညီဖြင့် သုတေသနပြုခြင်း\n\nကြာချိန် - ၃ နာရီ"
    },
    "3": {
        "name": "AI Tools Mastery", 
        "name_mm": "AI Tools ကျွမ်းကျင်မှု",
        "price": 79,
        "description": "Complete guide to AI tools:\n\n• ChatGPT, Claude, Gemini\n• Image generation (Midjourney, DALL-E)\n• Video & audio AI tools\n• Prompt engineering\n\nDuration: 8 hours",
        "description_mm": "AI Tools များကို လက်တွေ့အသုံးပြုနည်း လမ်းညွှန် -\n\n• ChatGPT, Claude, Gemini\n• ပုံဖန်တီးခြင်း (Midjourney, DALL-E)\n• Video နှင့် Audio AI tools များ\n• Prompt ရေးသားနည်း\n\nကြာချိန် - ၈ နာရီ"
    },
    "4": {
        "name": "Python for Automation", 
        "name_mm": "Python အော်တိုမေးရှင်း",
        "price": 59,
        "description": "Automate your work with Python:\n\n• Python basics\n• File automation\n• Web scraping\n• API integrations\n• Building bots\n\nDuration: 6 hours",
        "description_mm": "Python ဖြင့် လုပ်ငန်းများကို အလိုအလျောက်လုပ်ဆောင်မည် -\n\n• Python အခြေခံ\n• File များ စီမံခြင်း\n• Web scraping\n• API ချိတ်ဆက်ခြင်း\n• Bot များဖန်တီးခြင်း\n\nကြာချိန် - ၆ နာရီ"
    },
    "5": {
        "name": "Telegram Bot Building", 
        "name_mm": "Telegram Bot ရေးသားနည်း",
        "price": 69,
        "description": "Create powerful Telegram bots:\n\n• BotFather setup\n• Inline keyboards\n• Payments integration\n• User management\n• Deploy to server\n\nDuration: 5 hours",
        "description_mm": "အဆင့်မြင့် Telegram Bot များ ဖန်တီးမည် -\n\n• BotFather အသုံးပြုနည်း\n• Inline keyboards များ\n• ငွေပေးချေမှု ချိတ်ဆက်ခြင်း\n• User များကို စီမံခြင်း\n• Server ပေါ်တင်ခြင်း (Deploy)\n\nကြာချိန် - ၅ နာရီ"
    },
}

# Language texts
TEXTS = {
    "en": {
        "welcome": "👋 Welcome!\n\nI'm your training course assistant.\n\nUse the menu below to browse and purchase courses.",
        "main_menu": "📋 *Main Menu*\n\nChoose an option:",
        "products": "📦 *Product Catalog*\n\nSelect a course to see details:",
        "help": "📖 *Help*\n\n• /start - Show menu\n• Browse products and tap to see details\n• Tap 'Buy Now' to get payment info\n• Upload screenshot after payment\n• I'll notify the owner after payment",
        "my_cart": "🛒 *Your Cart*",
        "cart_empty": "🛒 Your cart is empty.",
        "total": "*Total: ${}*",
        "confirm_order": "✅ *Order Confirmed!*\n\n{}\n\n*Total: ${}*\n\nPlease proceed to Payment section.",
        "payment_details": "💳 *Payment Details*\n\nTransfer to any of these banks:\n\n🏦 *KBZ Pay* - အောက်ပါအကောင့်သို့\n💳 *Wave Pay* - အောက်ပါအကောင့်သို့\n🏦 *AYA Pay* - အောက်ပါအကောင့်သို့\n💳 *A+ Wallet* - အောက်ပါအကောင့်သို့\n\n━━━━━━━━━━━━━\n\n💳 Account: `{}`\n👤 Name: {}\n\nPlease transfer and upload payment proof.",
        "buy_now": "🛒 *Buy Now*",
        "added_to_cart": "✅ *Added to Cart!*\n\n📚 {}\n💰 Price: ${}\n\n━━━━━━━━━━━━━\n\n💳 *Payment Details*\n\n🏦 KBZ Pay | 💳 Wave Pay | 🏦 AYA Pay | 💳 A+ Wallet\n\nAccount: `{}`\nName: {}\n\nPlease transfer *${}* and upload your payment screenshot.",
        "upload_proof": "📤 *Upload Payment Proof*\n\nPlease send me a screenshot or photo of your payment transaction.",
        "payment_submitted": "✅ *Payment Proof Submitted!*\n\nOrder ID: `{}`\nProduct: {}\nAmount: ${}\n\nThank you! The owner will verify your payment and send course access details.",
        "no_pending": "❌ No pending order. Please buy a product first.",
        "no_image": "❌ No image received. Please upload your payment screenshot.",
        "order_confirmed": "✅ Order Confirmed!\n\nYour order has been submitted.",
        "cart_cleared": "🛒 Cart cleared.",
        "back": "🔙 Back",
        "confirm": "✅ Confirm & Pay",
        "clear": "❌ Clear Cart",
        "upload_btn": "📤 Upload Payment Proof",
        "help_btn": "❓ Help",
        "products_btn": "📦 Products",
        "myorder_btn": "🛒 My Orders",
        "payment_btn": "💳 Payment Info",
        "lang_btn": "🌐 မြန်မာစာ",
    },
    "mm": {
        "welcome": "👋 မင်္ဂလာပါ။\n\nသင်တန်းများနှင့်ပတ်သက်ပြီး ကူညီပေးမည့် Bot ဖြစ်ပါသည်။\n\nသင်တန်းများ ဝယ်ယူရန် အောက်ပါမီနူးကို အသုံးပြုပါ။",
        "main_menu": "📋 *ပင်မမီနူး*\n\nရွေးချယ်ပါ:",
        "products": "📦 *သင်တန်းများ*\n\nအသေးစိတ်သိရှိရန် သင်တန်းကို နှိပ်ပါ:",
        "help": "📖 *အကူအညီ*\n\n• /start - မီနူးပြရန်\n• သင်တန်းများကို လေ့လာပြီး အသေးစိတ်ကို ဖတ်ရန်\n• ၀ယ်ယူလိုပါက 'ဝယ်ယူမည်' ကိုနှိပ်ပြီး ငွေချေရန်အချက်အလက်များကို ကြည့်ပါ\n• ငွေပေးချေပြီးပါက Screenshot ဖြင့် ငွေလွှဲပြေစာ ပေးပို့ပါ\n• အက်ဒမင်မှ စစ်ဆေးပြီး အတည်ပြုပေးပါမည်",
        "my_cart": "🛒 *သင်၏ စျေးဝယ်ခြင်းတောင်း*",
        "cart_empty": "🛒 ခြင်းတောင်းထဲတွင် ဘာမှမရှိပါ။",
        "total": "*စုစုပေါင်း: ${}*",
        "confirm_order": "✅ *မှာယူမှု အတည်ပြုပြီးပါပြီ*\n\n{}\n\n*စုစုပေါင်း: ${}*\n\nငွေပေးချေရန် ဆက်လက်လုပ်ဆောင်ပါ။",
        "payment_details": "💳 *ငွေပေးချေရန် အချက်အလက်များ*\n\nအောက်ပါ ဘဏ်များသို့ ငွေလွှဲနိုင်ပါသည်။\n\n🏦 *KBZ Pay*\n💳 *Wave Pay*\n🏦 *AYA Pay*\n💳 *A+ Wallet*\n\n━━━━━━━━━━━━━\n\n💳 အကောင့်: `{}`\n👤 အမည်: {}\n\nငွေလွှဲပြီးပါက ပြေစာ (Screenshot) ကို ဤ Chat တွင် ပေးပို့ပါ။",
        "buy_now": "🛒 *ယခု ဝယ်မည်*",
        "added_to_cart": "✅ *ခြင်းတောင်းထဲသို့ ထည့်ပြီးပါပြီ*\n\n📚 {}\n💰 ဈေးနှုန်း: ${}\n\n━━━━━━━━━━━━━\n\n💳 *ငွေပေးချေရန် အချက်အလက်များ*\n\n🏦 KBZ Pay | 💳 Wave Pay | 🏦 AYA Pay | 💳 A+ Wallet\n\nအကောင့်: `{}`\nအမည်: {}\n\nကျေးဇူးပြု၍ *${}* ကိုလွှဲပေးပြီး ငွေလွှဲပြေစာ (Screenshot) ပေးပို့ပါ။",
        "upload_proof": "📤 *ငွေလွှဲပြေစာ ပေးပို့ရန်*\n\nသင်၏ ငွေလွှဲထားသော Screenshot (သို့) ဓာတ်ပုံကို ဤနေရာတွင် ပေးပို့ပါ။",
        "payment_submitted": "✅ *ပြေစာ လက်ခံရရှိပါပြီ*\n\nOrder ID: `{}`\nသင်တန်း: {}\nပမာဏ: ${}\n\nကျေးဇူးတင်ပါသည်။ အက်ဒမင်မှ ငွေလွှဲမှတ်တမ်းကို စစ်ဆေးပြီး သင်တန်းဝင်ခွင့် ပေးပို့ပါမည်။",
        "no_pending": "❌ ဝယ်ယူထားခြင်း မရှိသေးပါ။ ကျေးဇူးပြု၍ သင်တန်းအရင်ရွေးချယ်ပါ။",
        "no_image": "❌ ပုံမတွေ့ရပါ။ ငွေလွှဲပြေစာ Screenshot ကို Upload လုပ်ပေးပါ။",
        "order_confirmed": "✅ အော်ဒါ တင်ပြီးပါပြီ။",
        "cart_cleared": "🛒 ခြင်းတောင်း ရှင်းလင်းပြီးပါပြီ။",
        "back": "🔙 နောက်သို့",
        "confirm": "✅ အတည်ပြုပြီး ငွေချေမည်",
        "clear": "❌ ခြင်းတောင်း ရှင်းမည်",
        "upload_btn": "📤 ငွေလွှဲပြေစာ ပေးပို့ရန်",
        "help_btn": "❓ အကူအညီ",
        "products_btn": "📦 သင်တန်းများ",
        "myorder_btn": "🛒 ကျွန်ုပ်၏ အော်ဒါများ",
        "payment_btn": "💳 ငွေပေးချေရန်",
        "lang_btn": "🌐 English",
    }
}

# === DATA STORAGE ===
ORDERS_FILE = "orders.json"

def load_orders():
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)

def get_text(key, lang="en"):
    return TEXTS.get(lang, TEXTS["en"]).get(key, key)

# === KEYBOARDS ===
def main_menu_keyboard(lang="en"):
    keyboard = [
        [InlineKeyboardButton(get_text("products_btn", lang), callback_data="products")],
        [InlineKeyboardButton(get_text("myorder_btn", lang), callback_data="my_order")],
        [InlineKeyboardButton(get_text("payment_btn", lang), callback_data="payment")],
        [InlineKeyboardButton(get_text("help_btn", lang), callback_data="help")],
        [InlineKeyboardButton(get_text("lang_btn", lang), callback_data="switch_lang")],
    ]
    return InlineKeyboardMarkup(keyboard)

def products_keyboard(lang="en"):
    keyboard = []
    for pid, p in PRODUCTS.items():
        name = p.get(f"name_mm", p["name"]) if lang == "mm" else p["name"]
        keyboard.append([InlineKeyboardButton(f"📚 {name}", callback_data=f"product_{pid}")])
    keyboard.append([InlineKeyboardButton(get_text("back", lang), callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def product_detail_keyboard(product_id, lang="en"):
    keyboard = [
        [InlineKeyboardButton(get_text("buy_now", lang), callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton(get_text("back", lang), callback_data="products")],
    ]
    return InlineKeyboardMarkup(keyboard)

def cart_keyboard(lang="en"):
    keyboard = [
        [InlineKeyboardButton(get_text("confirm", lang), callback_data="confirm_order")],
        [InlineKeyboardButton(get_text("clear", lang), callback_data="clear_cart")],
        [InlineKeyboardButton(get_text("back", lang), callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

def payment_keyboard(lang="en"):
    keyboard = [
        [InlineKeyboardButton(get_text("upload_btn", lang), callback_data="upload_proof")],
        [InlineKeyboardButton(get_text("back", lang), callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

# === ADMIN COMMANDS ===
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    
    orders = load_orders()
    pending = {k: v for k, v in orders.items() if v.get("status") == "pending_verification"}
    
    msg = f"👨‍💻 *Admin Dashboard*\n\nTotal Orders: {len(orders)}\nPending Approvals: {len(pending)}\n\n"
    msg += "To approve an order, use: `/approve <order_id>`\n"
    msg += "To view pending orders, use: `/pending`\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    
    orders = load_orders()
    pending = {k: v for k, v in orders.items() if v.get("status") == "pending_verification"}
    
    if not pending:
        await update.message.reply_text("✅ No pending orders!")
        return
        
    msg = "⏳ *Pending Orders:*\n\n"
    for oid, o in pending.items():
        msg += f"ID: `{oid}`\nUser: {o.get('name')} (@{o.get('username')})\nItem: {o.get('product_name')}\nAmount: ${o.get('price')}\n---\n"
        
    await update.message.reply_text(msg, parse_mode="Markdown")

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
        
    if not context.args:
        await update.message.reply_text("Usage: `/approve <order_id>`", parse_mode="Markdown")
        return
        
    order_id = context.args[0]
    orders = load_orders()
    
    if order_id not in orders:
        await update.message.reply_text(f"❌ Order `{order_id}` not found.", parse_mode="Markdown")
        return
        
    if orders[order_id]["status"] == "paid":
        await update.message.reply_text(f"⚠️ Order `{order_id}` is already approved.", parse_mode="Markdown")
        return
        
    orders[order_id]["status"] = "paid"
    save_orders(orders)
    
    # Notify User
    try:
        buyer_id = orders[order_id]["user_id"]
        lang = context.bot_data.get("user_lang", {}).get(buyer_id, "mm")
        
        if lang == "mm":
            notify_msg = f"🎉 *ဂုဏ်ယူပါသည်! သင့်ငွေပေးချေမှုကို အတည်ပြုပြီးပါပြီ။*\n\nသင်တန်း: {orders[order_id]['product_name']}\nOrder ID: `{order_id}`\n\nသင်တန်းလင့်ခ်ကို မကြာမီ ပေးပို့ပါမည်။"
        else:
            notify_msg = f"🎉 *Payment Approved!*\n\nCourse: {orders[order_id]['product_name']}\nOrder ID: `{order_id}`\n\nYour course access details will be sent soon."
            
        await context.bot.send_message(chat_id=buyer_id, text=notify_msg, parse_mode="Markdown")
        await update.message.reply_text(f"✅ Order `{order_id}` approved and user notified.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"✅ Order approved, but couldn't notify user: {e}")

# === GENERAL HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    # Give priority to MM lang
    if "user_lang" not in context.bot_data:
        context.bot_data["user_lang"] = {}
    if user_id not in context.bot_data["user_lang"]:
         context.bot_data["user_lang"][user_id] = "mm"
         
    lang = context.bot_data["user_lang"][user_id]
    
    await update.message.reply_text(
        get_text("welcome", lang),
        reply_markup=main_menu_keyboard(lang)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    lang = context.bot_data.get("user_lang", {}).get(user_id, "mm")
    
    await update.message.reply_text(
        get_text("help", lang),
        reply_markup=main_menu_keyboard(lang)
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    lang = context.bot_data.get("user_lang", {}).get(user_id, "mm")
    
    await update.message.reply_text(
        get_text("main_menu", lang),
        reply_markup=main_menu_keyboard(lang)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    # Get user language
    if "user_lang" not in context.bot_data:
        context.bot_data["user_lang"] = {}
    lang = context.bot_data["user_lang"].get(user_id, "mm")
    
    # Initialize user cart
    if "carts" not in context.bot_data:
        context.bot_data["carts"] = {}
    if user_id not in context.bot_data["carts"]:
        context.bot_data["carts"][user_id] = []
    
    cart = context.bot_data["carts"][user_id]
    
    # Switch language
    if data == "switch_lang":
        new_lang = "en" if lang == "mm" else "mm"
        context.bot_data["user_lang"][user_id] = new_lang
        lang = new_lang
        await query.edit_message_text(
            get_text("main_menu", lang),
            reply_markup=main_menu_keyboard(lang)
        )
        return
    
    if data == "products":
        text = get_text("products", lang)
        await query.edit_message_text(text, reply_markup=products_keyboard(lang))
    
    elif data.startswith("product_"):
        pid = data.replace("product_", "")
        if pid in PRODUCTS:
            p = PRODUCTS[pid]
            name = p.get(f"name_{lang}", p["name"]) if lang == "mm" else p["name"]
            desc = p.get(f"description_{lang}", p["description"]) if lang == "mm" else p["description"]
            
            price_label = "စျေးနှုန်း" if lang == "mm" else "Price"
            text = f"📚 *{name}*\n\n{desc}\n\n💰 *{price_label}: ${p['price']}*"
            await query.edit_message_text(text, reply_markup=product_detail_keyboard(pid, lang), parse_mode="Markdown")
    
    elif data.startswith("buy_"):
        pid = data.replace("buy_", "")
        if pid in PRODUCTS:
            p = PRODUCTS[pid]
            # Clear previous cart and only keep current item for simplified checkout
            context.bot_data["carts"][user_id] = [pid]
            cart = context.bot_data["carts"][user_id]
            
            name = p.get(f"name_{lang}", p["name"]) if lang == "mm" else p["name"]
            
            text = get_text("added_to_cart", lang).format(
                name, p['price'], ACCOUNT_NUMBER, ACCOUNT_NAME, p['price']
            )
            
            if "pending_payment" not in context.bot_data:
                context.bot_data["pending_payment"] = {}
            context.bot_data["pending_payment"][user_id] = {"product_id": pid, "price": p['price'], "name": name}
            
            await query.edit_message_text(text, reply_markup=payment_keyboard(lang), parse_mode="Markdown")
    
    elif data == "my_order":
        orders = load_orders()
        user_orders = [o for o in orders.values() if o["user_id"] == user_id]
        
        if not user_orders:
            empty_msg = "📭 သင်ဝယ်ယူထားသည်များ မရှိသေးပါ။" if lang == "mm" else "📭 No orders yet."
            await query.edit_message_text(empty_msg, reply_markup=main_menu_keyboard(lang))
        else:
            title = "📋 *သင်၏ အော်ဒါမှတ်တမ်း:*\n\n" if lang == "mm" else "📋 *Your Orders:*\n\n"
            text = title
            for o in sorted(user_orders, key=lambda x: x["created"], reverse=True)[:5]:  # Show latest 5
                status_emoji = "⏳" if o["status"] == "pending_verification" else "✅" if o["status"] == "paid" else "📦"
                text += f"{status_emoji} Order `{o['created'][-6:]}` - {o['product_name']} - ${o['price']}\n"
            
            if len(user_orders) > 5:
                text += "\n*(Showing latest 5 orders)*"
                
            # Add back button
            markup = InlineKeyboardMarkup([[InlineKeyboardButton(get_text("back", lang), callback_data="back")]])
            await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    
    elif data == "payment":
        text = get_text("payment_details", lang).format(ACCOUNT_NUMBER, ACCOUNT_NAME)
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang), parse_mode="Markdown")
    
    elif data == "help":
        await query.edit_message_text(
            get_text("help", lang),
            reply_markup=main_menu_keyboard(lang)
        )
    
    elif data == "upload_proof":
        await query.answer()
        await context.bot.send_message(
            chat_id=user_id,
            text=get_text("upload_proof", lang),
            parse_mode="Markdown"
        )
    
    elif data == "back":
        await query.edit_message_text(
            get_text("main_menu", lang),
            reply_markup=main_menu_keyboard(lang)
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    lang = context.bot_data.get("user_lang", {}).get(user_id, "mm")
    
    photo = update.message.photo[-1] if update.message.photo else None
    
    if not photo:
        await update.message.reply_text(get_text("no_image", lang))
        return
    
    pending = context.bot_data.get("pending_payment", {}).get(user_id)
    
    if not pending:
        await update.message.reply_text(get_text("no_pending", lang))
        return
    
    # Create order
    orders = load_orders()
    
    # Generate cleaner short order ID
    order_id = datetime.now().strftime("%y%m%d%H%M") + str(update.message.from_user.id)[-3:]
    
    orders[order_id] = {
        "user_id": user_id,
        "username": update.message.from_user.username or "N/A",
        "name": update.message.from_user.first_name or "N/A",
        "product_id": pending["product_id"],
        "product_name": pending["name"],
        "price": pending["price"],
        "status": "pending_verification",
        "payment_proof": f"photo_file_id:{photo.file_id}",
        "created": datetime.now().isoformat()
    }
    save_orders(orders)
    
    # Send photo to owner
    caption = (f"🆕 *New Payment Received!*\n\n"
               f"Order ID: `{order_id}`\n"
               f"User: [{update.message.from_user.first_name}](tg://user?id={user_id}) (@{update.message.from_user.username or 'N/A'})\n"
               f"Product: {pending['name']}\n"
               f"Amount: ${pending['price']}\n\n"
               f"Status: ⏳ Waiting for verification\n\n"
               f"👉 Reply with `/approve {order_id}` to confirm payment.")
    
    try:
        await context.bot.send_photo(
            OWNER_ID,
            photo.file_id,
            caption=caption,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Failed to send to admin: {e}")
        try:
             await context.bot.send_message(
                 OWNER_ID,
                 text=f"⚠️ Payment arrived but photo failed to forward.\n\nUser ID: {user_id}\nOrder ID: {order_id}\nError: {e}"
             )
        except Exception:
             pass
    
    if "pending_payment" in context.bot_data:
        context.bot_data["pending_payment"].pop(user_id, None)
    
    if "carts" in context.bot_data:
        context.bot_data["carts"][user_id] = []
    
    await update.message.reply_text(
        get_text("payment_submitted", lang).format(order_id, pending["name"], pending["price"]),
        parse_mode="Markdown"
    )

# === MAIN ===
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # User Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Admin Commands
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("pending", admin_pending))
    app.add_handler(CommandHandler("approve", admin_approve))
    
    # Callbacks & Messages
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Superior Bot starting with full DB capabilities & Native Myanmar support...")
    app.run_polling()

if __name__ == "__main__":
    main()