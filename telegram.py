#!/usr/bin/env python3
"""
Telegram Business Bot - Training Courses
Myanmar/English Language Support
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
        "name_mm": "OpenClaw အစပါးစပါး",
        "price": 49,
        "description": "Learn OpenClaw from scratch! This course covers:\n\n• Bot setup & configuration\n• Automation workflows\n• Integration with AI tools\n• Building your first agent\n\nDuration: 4 hours video + lifetime access",
        "description_mm": "OpenClaw ကို အစပါးစပါးကနေ သင်ပါန်းမှာ...\n\n• Bot စပါးစပါးနဲ့ ပါပါယ်ပါ\n• Automation workflows\n• AI tools တွေနဲ့ ပါပါယ်ပါ\n• သင့်ရဲ့ ပါစတစ် Agent တစ်ခုဆောက်ပါ\n\nအချိန်: ၄ နာရီဗီဒီယား + သက်တောင့်သက်သာ ဝင်ခွင့်"
    },
    "2": {
        "name": "NotebookLM Training", 
        "name_mm": "NotebookLM သင်တန်း",
        "price": 39,
        "description": "Master Google's NotebookLM!\n\n• Upload & analyze documents\n• Generate podcasts from notes\n• Create study guides\n• AI-powered research\n\nDuration: 3 hours",
        "description_mm": "Google ရဲ့ NotebookLM ကို အသည်းအသန်း သင်ပါန်းမှာ...\n\n• ဖိုင်တွေအပါးလိုက် အပါစပါး\n• မှတ်စုတွေကနေ Podcast ဖန်တီးပါ\n• သင်ပါးစပါးလမ်းညွှန်ဖန်တီးပါ\n• AI ကူညီပါသေးစီးပါ\n\nအချိန်: ၃ နာရီ"
    },
    "3": {
        "name": "AI Tools Mastery", 
        "name_mm": "AI Tools အသည်းအသန်း",
        "price": 79,
        "description": "Complete guide to AI tools:\n\n• ChatGPT, Claude, Gemini\n• Image generation (Midjourney, DALL-E)\n• Video & audio AI tools\n• Prompt engineering\n\nDuration: 8 hours",
        "description_mm": "AI Tools တွေရဲ့ ပါပါယ်ပါ လမ်းညွှန်...\n\n• ChatGPT, Claude, Gemini\n• ပါစတစ်ပုံဖန်တီးပါ (Midjourney, DALL-E)\n• ဗီဒီယားနဲ့ အာဒီယား AI tools တွေ\n• Prompt engineering\n\nအချိန်: ၈ နာရီ"
    },
    "4": {
        "name": "Python for Automation", 
        "name_mm": "Python အလိုအပါးလိုက်",
        "price": 59,
        "description": "Automate your work with Python:\n\n• Python basics\n• File automation\n• Web scraping\n• API integrations\n• Building bots\n\nDuration: 6 hours",
        "description_mm": "Python နဲ့ သင့်အလုပ်တွေကို အလိုအပါးလိုက် လုပ်ပါ...\n\n• Python အခြေခံ\n• ဖိုင်အလိုအပါးလိုက်\n• Web scraping\n• API ပါပါယ်ပါ\n• Bot တွေဖန်တီးပါ\n\nအချိန်: ၆ နာရီ"
    },
    "5": {
        "name": "Telegram Bot Building", 
        "name_mm": "Telegram Bot ဖန်တီးပါးစပါး",
        "price": 69,
        "description": "Create powerful Telegram bots:\n\n• BotFather setup\n• Inline keyboards\n• Payments integration\n• User management\n• Deploy to server\n\nDuration: 5 hours",
        "description_mm": "အင်အားကောင်းတဲ့ Telegram Bots တွေဖန်တီးပါ...\n\n• BotFather စပါးစပါး\n• Inline keyboards\n• ငွေချေလွှားပါပါယ်ပါ\n• အသုံးပါသူစီမံခန့်ခွဲပါ\n• Server ပေါ်တင်ပါ\n\nအချိန်: ၅ နာရီ"
    },
}

# Language texts
TEXTS = {
    "en": {
        "welcome": "👋 Welcome!\n\nI'm your training course assistant.\n\nUse the menu below to browse and purchase courses.",
        "main_menu": "📋 *Main Menu*\n\nChoose an option:",
        "products": "📦 *Product Catalog*\n\nSelect a course to see details:",
        "help": "📖 *Help*\n\n• /start - Show menu\n• /menu - Show menu\n• Browse products and tap to see details\n• Tap 'Buy Now' to get payment info\n• Upload screenshot after payment\n• I'll notify the owner after payment",
        "my_cart": "🛒 *Your Cart*",
        "cart_empty": "🛒 Your cart is empty.",
        "total": "*Total: ${}*",
        "confirm_order": "✅ *Order Confirmed!*\n\n{}*\n\n*Total: ${}*\n\nPlease proceed to Payment section.",
        "payment_details": "💳 *Payment Details*\n\nTransfer to any of these banks:\n\n🏦 *KBZ Pay* - အောက်မှာဖူး\n💳 *Wave Pay* - အောက်မှာဖူး\n🏦 *AYA Pay* - အောက်မှာဖူး\n💳 *A+ Wallet* - အောက်မှာဖူး\n\n━━━━━━━━━━━━━\n\n💳 Account: ||{}||\n👤 Name: {}\n\nPlease transfer and upload payment proof.",
        "buy_now": "🛒 *Buy Now*",
        "added_to_cart": "✅ *Added to Cart!*\n\n📚 {}\n💰 Price: ${}\n\n━━ ACCESS DENIED ━━\n\n💳 *Payment Details*\n\n🏦 KBZ Pay\n💳 Wave Pay\n🏦 AYA Pay\n💳 A+ Wallet\n\nAccount: ||{}||\nName: {}\n\nPlease transfer *${}* and upload your payment screenshot.",
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
        "myorder_btn": "🛒 My Order",
        "payment_btn": "💳 Payment Info",
        "lang_btn": "🌐 English",
    },
    "mm": {
        "welcome": "👋 မင်္ဂလာပါ!\n\nသင့်အတွက် သင်တန်းအောက်မှာ ဝန်ဆောင်ပါတယ်။\n\nသင်ပါးစပါးမှာရှိတဲ့ သင်တန်းတွေကို ဝယ်ယူပါန်းမှာ။",
        "main_menu": "📋 *ပါးစပါးမှာ မန်နူး*\n\nသင်လိုချင်တာကို ရွေးပါ:",
        "products": "📦 *သင်တန်းမှတ်တမ်း*\n\nသင်တန်းအသေးစိတ်ကို မှန်းလိုက်ပါ:",
        "help": "📖 *အကူညီ*\n\n• /start - မန်နူးပါ\n• /menu - မန်နူးပါ\n• သင်တန်းတွေကို ကြည့်ပါ\n• ဝယ်ယူဖို့ Buy Now နှိပ်ပါ\n• ငွေပါးစပါးပြောင်းပါန်းမှာ screenshot အပါးလိုက်ပါ\n• သင့်အမှားစီကို ပါစတစ်ပါသူမှာ သတင်းပါးပါးပါ",
        "my_cart": "🛒 *သင့်မှား*",
        "cart_empty": "🛒 သင့်မှားသည်း ဗလာပါ။",
        "total": "*စုစုပါး: ${}*",
        "confirm_order": "✅ *မှားပါးပါ အတည်ပါးပါ*\n\n{}*\n\n*စုစုပါး: ${}*\n\nငွေပါးစပါးပြောင်းဖို့ သွားပါ။",
        "payment_details": "💳 *ငွေပါးစပါး အသေးစိတ်*\n\nဤဘဏ်တွေမှာ လွှဲပါးစပါးပါ။\n\n🏦 *KBZ Pay*\n💳 *Wave Pay*\n🏦 *AYA Pay*\n💳 *A+ Wallet*\n\n━━━━━━━━━━━━━\n\n💳 အကောင့်: ||{}||\n👤 အမည်: {}\n\nငွေပါးစပါးပြောင်းပါးစပါးပါ။",
        "buy_now": "🛒 ဝယ်ယူပါ",
        "added_to_cart": "✅ *မှားထဲထည့်ပါးပါ*\n\n📚 {}\n💰 အခေါင်း: ${}\n\n━━ ACCESS DENIED ━━\n\n💳 *ငွေပါးစပါး အသေးစိတ်*\n\n🏦 KBZ Pay\n💳 Wave Pay\n🏦 AYA Pay\n💳 A+ Wallet\n\nအကောင့်: ||{}||\nအမည်: {}\n\nငွေ ${} လွှဲပါးစပါးပါ။ ပါးစပါးပြောင်းပါးစပါးပါ။",
        "upload_proof": "📤 *ငွေပါးစပါးပြောင်းပါးစပါး ပါးပါးစပါး*\n\nသင့်ငွေပါးစပါးပြောင်းပါးစပါးရဲ့ screenshot ကို ပါးလိုက်ပါ။",
        "payment_submitted": "✅ *ငွေပါးစပါး ပြောင်းပါးစပါး ပါးပါးပါ*\n\nမှားနံပါတ်: `{}`\nသင်တန်း: {}\nပါးစပါး: ${}\n\nကျေးဇူးပါါးမှာ။ ပါစတစ်ပါသူက သင့်ငွေပါးစပါးကို စစ်ပါြောင်းလိမ့်မယ်။ သင်တန်းဝင်ခွင့်ကို ပါးပါးပါ။",
        "no_pending": "❌ မှားမရှိပါ။ သင်တန်းဝယ်ယူပါ။",
        "no_image": "❌ ပုံမရပါ။ screenshot ပါးလိုက်ပါ။",
        "order_confirmed": "✅ မှားပါးပါ အတည်ပါးပါ!",
        "cart_cleared": "🛒 မှားသည်း ရှင်းပါ။",
        "back": "🔙 ပါးစပါး",
        "confirm": "✅ အတည်ပါးပါ နဲ့ ငွေပါးစပါး",
        "clear": "❌ မှားရှင်းပါ",
        "upload_btn": "📤 ငွေပါးစပါး ပါးပါးစပါး",
        "help_btn": "❓ အကူညီ",
        "products_btn": "📦 သင်တန်းမှတ်တမ်း",
        "myorder_btn": "🛒 မှားမန်နူး",
        "payment_btn": "💳 ငွေပါးစပါး",
        "lang_btn": "🌐 မြန်မာစာ",
    }
}

# === DATA STORAGE ===
ORDERS_FILE = "orders.json"

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)

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

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    lang = context.bot_data.get("user_lang", {}).get(user_id, "mm")  # Default to Myanmar
    
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
            name = p.get(f"name_mm", p["name"]) if lang == "mm" else p["name"]
            desc = p.get(f"description_mm", p["description"]) if lang == "mm" else p["description"]
            text = f"📚 *{name}*\n\n{desc}\n\n💰 *အခေါင်း: ${p['price']}*" if lang == "mm" else f"📚 *{name}*\n\n{desc}\n\n💰 *Price: ${p['price']}*"
            await query.edit_message_text(text, reply_markup=product_detail_keyboard(pid, lang), parse_mode="Markdown")
    
    elif data.startswith("buy_"):
        pid = data.replace("buy_", "")
        if pid in PRODUCTS:
            p = PRODUCTS[pid]
            cart.append(pid)
            
            name = p.get(f"name_mm", p["name"]) if lang == "mm" else p["name"]
            
            if lang == "mm":
                text = (f"✅ *မှားထဲထည့်ပါးပါ*\n\n"
                        f"📚 {name}\n"
                        f"💰 အခေါင်း: ${p['price']}\n\n"
                        f"━━ ACCESS DENIED ━━\n\n"
                        f"💳 *ငွေပါးစပါး အသေးစိတ်*\n\n"
                        f"🏦 KBZ Pay\n"
                        f"💳 Wave Pay\n"
                        f"🏦 AYA Pay\n"
                        f"💳 A+ Wallet\n\n"
                        f"အကောင့်: ||{ACCOUNT_NUMBER}||\n"
                        f"အမည်: {ACCOUNT_NAME}\n\n"
                        f"ငွေ ${p['price']} လွှဲပါးစပါးပါ။ ပါးစပါးပြောင်းပါးစပါးပါ။")
            else:
                text = (f"✅ *Added to Cart!*\n\n"
                        f"📚 {name}\n"
                        f"💰 Price: ${p['price']}\n\n"
                        f"━━ ACCESS DENIED ━━\n\n"
                        f"💳 *Payment Details*\n\n"
                        f"🏦 KBZ Pay\n"
                        f"💳 Wave Pay\n"
                        f"🏦 AYA Pay\n"
                        f"💳 A+ Wallet\n\n"
                        f"Account: ||{ACCOUNT_NUMBER}||\n"
                        f"Name: {ACCOUNT_NAME}\n\n"
                        f"Please transfer *${p['price']}* and upload your payment screenshot.")
            
            if "pending_payment" not in context.bot_data:
                context.bot_data["pending_payment"] = {}
            context.bot_data["pending_payment"][user_id] = {"product_id": pid, "price": p['price'], "name": name}
            
            await query.edit_message_text(text, reply_markup=payment_keyboard(lang), parse_mode="Markdown")
    
    elif data == "my_order":
        if not cart:
            await query.edit_message_text(get_text("cart_empty", lang), reply_markup=main_menu_keyboard(lang))
        else:
            total = sum(PRODUCTS[pid]["price"] for pid in cart)
            items = "\n".join(f"• {PRODUCTS[pid].get('name_mm', PRODUCTS[pid]['name'])} - ${PRODUCTS[pid]['price']}" for pid in cart) if lang == "mm" else "\n".join(f"• {PRODUCTS[pid]['name']} - ${PRODUCTS[pid]['price']}" for pid in cart)
            total_text = f"စုစုပါး: ${total}" if lang == "mm" else f"Total: ${total}"
            text = f"{get_text('my_cart', lang)}\n\n{items}\n\n*{total_text}*"
            await query.edit_message_text(text, reply_markup=cart_keyboard(lang))
    
    elif data == "payment":
        if lang == "mm":
            text = (f"💳 *ငွေပါးစပါး အသေးစိတ်*\n\n"
                    f"ဤဘဏ်တွေမှာ လွှဲပါးစပါးပါ။\n\n"
                    f"🏦 *KBZ Pay*\n"
                    f"💳 *Wave Pay*\n"
                    f"🏦 *AYA Pay*\n"
                    f"💳 *A+ Wallet*\n\n"
                    f"━━━━━━━━━━━━━\n\n"
                    f"💳 အကောင့်: ||{ACCOUNT_NUMBER}||\n"
                    f"👤 အမည်: {ACCOUNT_NAME}\n\n"
                    f"ငွေပါးစပါးပြောင်းပါးစပါးပါ။")
        else:
            text = (f"💳 *Payment Details*\n\n"
                    f"Transfer to any of these banks:\n\n"
                    f"🏦 *KBZ Pay*\n"
                    f"💳 *Wave Pay*\n"
                    f"🏦 *AYA Pay*\n"
                    f"💳 *A+ Wallet*\n\n"
                    f"━━━━━━━━━━━━━\n\n"
                    f"💳 Account: ||{ACCOUNT_NUMBER}||\n"
                    f"👤 Name: {ACCOUNT_NAME}\n\n"
                    f"Please transfer and upload payment proof.")
        
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang), parse_mode="Markdown")
    
    elif data == "help":
        await query.edit_message_text(
            get_text("help", lang),
            reply_markup=main_menu_keyboard(lang)
        )
    
    elif data == "clear_cart":
        cart.clear()
        await query.answer("Cart cleared!" if lang == "en" else "မှားသည်း ရှင်းပါ။")
        await query.edit_message_text(get_text("cart_cleared", lang), reply_markup=main_menu_keyboard(lang))
    
    elif data == "confirm_order":
        if not cart:
            await query.edit_message_text(get_text("cart_empty", lang), reply_markup=main_menu_keyboard(lang))
        else:
            total = sum(PRODUCTS[pid]["price"] for pid in cart)
            items = "\n".join(f"• {PRODUCTS[pid].get('name_mm', PRODUCTS[pid]['name'])}" for pid in cart) if lang == "mm" else "\n".join(f"• {PRODUCTS[pid]['name']}" for pid in cart)
            text = get_text("confirm_order", lang).format(items, total)
            await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang))
    
    elif data == "upload_proof":
        await query.answer(get_text("upload_proof", lang))
        await query.message.reply_text(
            get_text("upload_proof", lang),
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
    order_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    orders[order_id] = {
        "user_id": user_id,
        "username": update.message.from_user.username or "N/A",
        "name": update.message.from_user.name or "N/A",
        "product_id": pending["product_id"],
        "product_name": pending["name"],
        "price": pending["price"],
        "status": "pending_verification",
        "payment_proof": f"photo_file_id:{photo.file_id}",
        "created": datetime.now().isoformat()
    }
    save_orders(orders)
    
    # Send photo to owner
    caption = (f"🆕 *New Payment!*\n\n"
               f"Order ID: `{order_id}`\n"
               f"User: @{update.message.from_user.username or 'N/A'}\n"
               f"Product: {pending['name']}\n"
               f"Amount: ${pending['price']}\n\n"
               f"Status: ⏳ Waiting for verification")
    
    try:
        await context.bot.send_photo(
            OWNER_ID,
            photo.file_id,
            caption=caption,
            parse_mode="Markdown"
        )
    except Exception as e:
        await context.bot.send_message(
            OWNER_ID,
            caption + f"\n\n⚠️ Failed to forward photo: {e}",
            parse_mode="Markdown"
        )
    
    if "pending_payment" in context.bot_data:
        context.bot_data["pending_payment"].pop(user_id, None)
    
    if "carts" in context.bot_data:
        context.bot_data["carts"][user_id] = []
    
    await update.message.reply_text(
        get_text("payment_submitted", lang).format(order_id, pending["name"], pending["price"]),
        parse_mode="Markdown"
    )

async def myorders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    lang = context.bot_data.get("user_lang", {}).get(user_id, "mm")
    orders = load_orders()
    
    user_orders = [o for o in orders.values() if o["user_id"] == user_id]
    
    if not user_orders:
        await update.message.reply_text("📭 No orders yet." if lang == "en" else "📭 မှားမရှိပါ။")
    else:
        text = "📋 *Your Orders:*\n\n" if lang == "en" else "📋 *သင့်မှားမှတ်တမ်း:*\n\n"
        for o in sorted(user_orders, key=lambda x: x["created"], reverse=True):
            status_emoji = "⏳" if o["status"] == "pending_verification" else "✅" if o["status"] == "paid" else "📦"
            text += f"{status_emoji} Order {o['created'][-6:]} - {o['product_name']} - ${o['price']}\n"
        await update.message.reply_text(text, parse_mode="Markdown")

# === MAIN ===
def main():
    logging.basicConfig(level=logging.INFO)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myorders", myorders_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()