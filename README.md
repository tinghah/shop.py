# Telegram Shop Bot

A Telegram bot for selling courses and services with Myanmar/English language support.

## Quick Start

```bash
# Install dependencies
pip install python-telegram-bot

# Set environment variables (create .env file)
cp .env.example .env
# Edit .env with your values

# Run bot
python telegram_bot.py
```

## Environment Variables

Create a `.env` file:
```
BOT_TOKEN=your_telegram_bot_token
OWNER_ID=your_telegram_user_id
ACCOUNT_NUMBER=your_payment_number
ACCOUNT_NAME=Your Name
```

## Admin Commands

- `/admin` - Admin dashboard
- `/admin list` - List all items
- `/admin add_course` - Add new course
- `/admin add_service` - Add new service
- `/admin delete <id>` - Delete item
- `/pending` - View pending orders
- `/approve <order_id>` - Approve order

## Deploy to Render (Free)

1. Push code to GitHub (add your `.env` values in Render dashboard)
2. Create Web Service on Render
3. Set environment variables in Render
4. Start command: `python telegram_bot.py`

## Security Note

Never commit `.env`, `*.db`, or `shop.db` to GitHub! The `.gitignore` file prevents this.