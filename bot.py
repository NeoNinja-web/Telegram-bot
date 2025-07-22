import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler,
    CallbackQueryHandler
)
from telegram.error import Conflict, NetworkError
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# États de conversation
USERNAME_INPUT, PRICE_INPUT = range(2)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://telegram-bot-vic3.onrender.com')
PORT = int(os.getenv('PORT', 10000))

print(f"🔍 DEBUG: BOT_TOKEN configuré: {'✅' if BOT_TOKEN else '❌'}")
print(f"🔍 DEBUG: WEBAPP_URL: {WEBAPP_URL}")
print(f"🔍 DEBUG: PORT: {PORT}")

# Variables globales pour stocker les données
user_data = {}

# ===== SERVEUR DE SANTÉ =====
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK - Fragment Deal Bot is running')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Supprime les logs HTTP pour éviter le spam
        pass

def start_health_server():
    """Démarrage du serveur de santé - OBLIGATOIRE pour Render"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        print(f"🏥 Serveur de santé démarré sur port {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️  Erreur serveur de santé: {e}")
        # Si le port est occupé, essaye un port alternatif
        try:
            alt_port = PORT + 1
            server = HTTPServer(('0.0.0.0', alt_port), HealthHandler)
            print(f"🏥 Serveur de santé démarré sur port alternatif {alt_port}")
            server.serve_forever()
        except Exception as e2:
            print(f"❌ Impossible de démarrer le serveur de santé: {e2}")

# ===== GESTIONNAIRES TELEGRAM =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gestionnaire de commande /start - Demande directement le username"""
    user = update.effective_user
    
    await update.message.reply_text(
        f"Hello {user.first_name} 👋\n\n"
        "💎 **Fragment Username Deal**\n\n"
        "Please send me the **Fragment username** you want to sell.\n\n"
        "📝 **Format:** Just the name (without @ or .ton)\n"
        "📝 **Example:** `crypto` or `defi`\n\n"
        "❌ **Cancel:** /cancel",
        parse_mode='Markdown'
    )
    return USERNAME_INPUT

async def newdeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Démarrer un nouveau deal (fonction alternative)"""
    keyboard = [
        [InlineKeyboardButton("🚀 Start Deal", callback_data='start_deal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "💎 **Fragment Username Deal Bot**\n\n"
        "Ready to create a deal for a Fragment username?\n\n"
        "Click the button below to get started! 👇",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des boutons callback"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start_deal':
        await query.edit_message_text(
            "💎 **Fragment Username Deal**\n\n"
            "Please send me the **Fragment username** you want to sell.\n\n"
            "📝 **Format:** Just the name (without @ or .ton)\n"
            "📝 **Example:** `crypto` or `defi`\n\n"
            "❌ **Cancel:** /cancel",
            parse_mode='Markdown'
        )
        return USERNAME_INPUT
    
    return ConversationHandler.END

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Récupérer le nom d'utilisateur"""
    username = update.message.text.strip().lower()
    user_id = update.effective_user.id
    
    # Validation simple du nom d'utilisateur
    if len(username) < 2:
        await update.message.reply_text(
            "❌ **Invalid username**\n\n"
            "Username must be at least 2 characters long.\n"
            "Please try again:"
        )
        return USERNAME_INPUT
    
    if not username.replace('_', '').replace('-', '').isalnum():
        await update.message.reply_text(
            "❌ **Invalid username**\n\n"
            "Username can only contain letters, numbers, hyphens and underscores.\n"
            "Please try again:"
        )
        return USERNAME_INPUT
    
    # Stocker les données utilisateur
    user_data[user_id] = {'username': username}
    
    await update.message.reply_text(
        f"✅ **Username saved:** `{username}`\n\n"
        "💰 Now please enter the **price in TON**\n\n"
        "📝 **Examples:** `1000`, `500.5`, `250`\n"
        "💎 **Note:** Price should be the total amount in TON",
        parse_mode='Markdown'
    )
    
    return PRICE_INPUT

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Récupérer le prix et générer directement le message"""
    try:
        price = float(update.message.text.strip())
        user_id = update.effective_user.id
        
        if price <= 0:
            await update.message.reply_text(
                "❌ **Invalid price**\n\n"
                "Price must be greater than 0.\n"
                "Please enter a valid price in TON:"
            )
            return PRICE_INPUT
        
        if price > 1000000:  # Limite raisonnable
            await update.message.reply_text(
                "❌ **Price too high**\n\n"
                "Maximum price is 1,000,000 TON.\n"
                "Please enter a reasonable price:"
            )
            return PRICE_INPUT
        
        # Mise à jour des données utilisateur
        if user_id in user_data:
            user_data[user_id]['price'] = price
            username = user_data[user_id]['username']
        else:
            await update.message.reply_text(
                "❌ **Error:** Username not found.\n"
                "Please start over with /start"
            )
            return ConversationHandler.END
        
        # Calcul de la commission (5%)
        commission = price * 0.05
        
        # Message de simulation Fragment (DIRECTEMENT SANS CONFIRMATION)
        deal_message = f"""We have received a purchase request for your username @{username.upper()}_DEAL via Fragment.com. Below are the transaction details:

• Offer Amount: 💎{price:g}
• Commission: 💎{commission:g}

Please note that a 5% commission is charged to the seller prior to accepting the deal. This ensures a secure and efficient transaction process.

Additional Information:
• Device: Safari on macOS  
• IP Address: 103.56.72.245
• Wallet: [EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U](https://tonviewer.com/EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U)

Important:
• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible.
• If you choose not to proceed, simply ignore this message."""
        
        # Bouton vers la mini-app
        keyboard = [[InlineKeyboardButton("View details", url=f"https://myminiapp.onrender.com/?user={username}_deal&price={price:g}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            deal_message,
            reply_markup=reply_markup
        )
        
        # Nettoyage des données temporaires
        del user_data[user_id]
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Invalid price format**\n\n"
            "Please enter a valid number.\n"
            "📝 **Examples:** `1000`, `500.5`, `250`"
        )
        return PRICE_INPUT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Annuler la conversation"""
    user_id = update.effective_user.id
    
    # Nettoyage des données
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text(
        "❌ **Operation cancelled**\n\n"
        "Use /start to create a new deal anytime! 👋",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande d'aide"""
    help_text = """
🤖 **Fragment Deal Bot - Help**

**Available Commands:**
• `/start` - Create a new Fragment username deal
• `/help` - Show this help message
• `/cancel` - Cancel current operation

**How it works:**
1. 🚀 Use `/start` to begin
2. 📝 Enter Fragment username  
3. 💰 Set price in TON
4. 🔗 Get your deal message instantly

**Support:** This bot helps simulate Fragment.com username deals.

💎 **Ready to start?** Use `/start`
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ===== FONCTION PRINCIPALE =====

def main():
    """Fonction principale - Mode Polling uniquement"""
    try:
        # Serveur de santé simple pour Render
        health_thread = Thread(target=start_health_server, daemon=True)
        health_thread.start()
        
        # Création de l'application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Gestionnaire de conversation
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                CommandHandler('newdeal', newdeal),
                CallbackQueryHandler(button_callback, pattern='^start_deal$')
            ],
            states={
                USERNAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
                PRICE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Ajout des gestionnaires
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(conv_handler)
        
        print("🚀 Fragment Deal Bot démarré...")
        print("💎 Mode: TON uniquement")
        print("🏥 Serveur de santé: Activé")
        print("🔄 Mode: Polling (Compatible Render)")
        
        # MODE POLLING UNIQUEMENT - Fonctionne partout
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Conflict:
        print("⚠️  Autre instance détectée, redémarrage en cours...")
        time.sleep(5)
        main()  # Retry
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        raise

if __name__ == '__main__':
    main()
