import os
import logging
import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.error import TelegramError

# Configuration
TELEGRAM_TOKEN = "8779521734:AAFkwMlX_ifJR1rDeEV84nQlNQxK3ZKaJKU"
MEXC_API_KEY = "mx0vglDutscn4CC6xG"
MEXC_SECRET_KEY = "63fb44cd77e94684b3980ddf7285b7ca"

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variable to store active chat IDs
active_chats = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_chats.add(chat_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text="Trading Scanner စတင်ပါပြီ။ BTC, ETH, SOL နဲ့ Top 3 Gainers တွေကို ၅ မိနစ်တစ်ခါ Scan ဖတ်ပေးသွားပါမယ်။"
    )

def get_mexc_ticker():
    url = "https://api.mexc.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching MEXC ticker: {e}")
        return []

async def scan_market(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Scanning market...")
    tickers = get_mexc_ticker()
    if not tickers:
        return

    # Focus pairs
    focus_pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    # Get Top 3 Gainers
    usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
    sorted_gainers = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)
    top_3_gainers = [t['symbol'] for t in sorted_gainers[:3]]
    
    all_to_scan = list(set(focus_pairs + top_3_gainers))
    
    message = "🔍 **Market Scan Report**\n\n"
    for symbol in all_to_scan:
        ticker = next((t for t in tickers if t['symbol'] == symbol), None)
        if ticker:
            price = ticker['lastPrice']
            change = ticker['priceChangePercent']
            message += f"🔸 **{symbol}**\nPrice: {price}\n24h Change: {change}%\n\n"
    
    message += "💡 _CRT + TBS Model 1 အရ Setup တွေ့ပါက အကြောင်းကြားပေးပါမည်။_"

    for chat_id in active_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        except TelegramError as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    
    job_queue = application.job_queue
    # Run every 5 minutes (300 seconds)
    job_queue.run_repeating(scan_market, interval=300, first=10)
    
    logger.info("Bot is running...")
    application.run_polling()
