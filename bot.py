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

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# États de conversation
USERNAME_INPUT, PRICE_INPUT, CONFIRMATION = range(3)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://telegram-bot-vic3.onrender.com')
PORT = int(os.getenv('PORT', 10000))

print(f"🔍 DEBUG: BOT_TOKEN configuré: {'✅' if BOT_TOKEN else '❌'}")
print(f"🔍 DEBUG: WEBAPP_URL: {WEBAPP_URL}")
print(f"🔍 DEBUG: PORT: {PORT}")

# Variables globales pour stocker les données
user_data = {}

# ===== SERVEUR DE SANTÉ (PORT DIFFÉRENT) =====
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
    """Démarrage du serveur de santé sur un port différent"""
    # 🔧 CORRECTION : Port différent pour le serveur de santé
    health_port = PORT + 1 if PORT != 10000 else 8080
    try:
        server = HTTPServer(('0.0.0.0', health_port), HealthHandler)
        print(f"🏥 Serveur de santé démarré sur port {health_port}")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Erreur serveur de santé: {e}")

# ===== GESTIONNAIRES TELEGRAM =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire de la commande /start"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    # Interface avec bouton pour lancer un deal
    keyboard = [[InlineKeyboardButton("🚀 Créer un nouveau deal", callback_data='start_deal')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = f"""
🔥 **Fragment Deal Bot**

Salut {first_name} ! 👋

Je t'aide à finaliser des deals sur Fragment de manière sécurisée.

✅ **Fonctionnalités :**
• Création de deals TON
• Interface sécurisée  
• Confirmations automatiques

💎 **Prêt à commencer ?**
"""
    
    await update.message.reply_text(
        welcome_message, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des boutons inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start_deal':
        await start_new_deal(update, context)

async def start_new_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Démarre la création d'un nouveau deal"""
    user_id = update.effective_user.id
    
    # Interface avec Web App
    keyboard = [[
        InlineKeyboardButton(
            "💎 Ouvrir l'interface", 
            web_app={'url': WEBAPP_URL}
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = """
🚀 **Nouveau Deal TON**

Clique sur le bouton ci-dessous pour ouvrir l'interface sécurisée de création de deal.

✅ **Sécurité maximale**
✅ **Process simplifié**  
✅ **Validation automatique**
"""
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def newdeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /newdeal"""
    await start_new_deal(update, context)
    return USERNAME_INPUT

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Récupère le nom d'utilisateur"""
    username = update.message.text
    user_id = update.effective_user.id
    
    if username not in user_data:
        user_data[username] = {}
    
    user_data[username]['telegram_id'] = user_id
    context.user_data['target_username'] = username
    
    await update.message.reply_text(f"✅ Username: @{username}\n\n💰 Quel est le montant du deal en TON?")
    return PRICE_INPUT

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Récupère le prix"""
    try:
        price = float(update.message.text)
        context.user_data['price'] = price
        username = context.user_data.get('target_username')
        
        # Bouton de confirmation
        keyboard = [[InlineKeyboardButton("✅ Confirmer le deal", callback_data='confirm')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        confirmation_message = f"""
🔥 **Récapitulatif du Deal**

👤 **Vendeur:** @{username}
💰 **Prix:** {price} TON
⏰ **Date:** {datetime.now().strftime('%d/%m/%Y à %H:%M')}

🚀 **Prêt à finaliser ?**
"""
        
        await update.message.reply_text(
            confirmation_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CONFIRMATION
        
    except ValueError:
        await update.message.reply_text("❌ Veuillez entrer un montant valide en TON:")
        return PRICE_INPUT

async def confirm_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirme le deal"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'confirm':
        username = context.user_data.get('target_username')
        price = context.user_data.get('price')
        
        # Interface finale avec Web App pour le paiement
        keyboard = [[
            InlineKeyboardButton(
                "💳 Finaliser le paiement", 
                web_app={'url': f"{WEBAPP_URL}?username={username}&price={price}"}
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        final_message = f"""
✅ **Deal confirmé !**

🎯 **Prochaine étape:** Finaliser le paiement

👤 @{username}
💰 {price} TON

🔐 **Paiement sécurisé via notre interface**
"""
        
        await query.edit_message_text(
            final_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule la conversation"""
    await update.message.reply_text('❌ Deal annulé.')
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande d'aide"""
    help_text = """
🔥 **Fragment Deal Bot - Aide**

**Commandes disponibles :**
/start - Démarrer le bot
/newdeal - Créer un nouveau deal
/help - Afficher cette aide
/cancel - Annuler l'opération en cours

**Comment ça marche :**
1. Utilise /newdeal
2. Saisis le username Fragment
3. Indique le prix en TON
4. Confirme le deal
5. Finalise via notre interface sécurisée

💎 **Support:** Contact @support_bot
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Fonction principale"""
    try:
        # 🔧 CORRECTION : Démarrage conditionnel du serveur de santé
        is_render = 'RENDER' in os.environ
        
        if is_render:
            # Sur Render, on démarre le serveur de santé sur un port différent
            health_thread = Thread(target=start_health_server, daemon=True)
            health_thread.start()
        
        # Création de l'application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Gestionnaire de conversation corrigé
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('newdeal', newdeal),
                CallbackQueryHandler(button_callback, pattern='^start_deal$')
            ],
            states={
                USERNAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
                PRICE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
                CONFIRMATION: [CallbackQueryHandler(confirm_deal)]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Ajout des gestionnaires
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(conv_handler)
        
        print("🚀 Fragment Deal Bot démarré...")
        print("💎 Mode: TON uniquement")
        print(f"🏥 Serveur de santé: {'Activé' if is_render else 'Désactivé'}")
        
        if is_render:
            # Mode webhook sur Render
            print("🌍 Mode: Webhook (Render détecté)")
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=f"{WEBAPP_URL}/webhook",
                url_path="/webhook",
                drop_pending_updates=True
            )
        else:
            # Mode polling en local
            print("🔄 Mode: Polling (Local)")
            application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        raise

if __name__ == '__main__':
    main()
