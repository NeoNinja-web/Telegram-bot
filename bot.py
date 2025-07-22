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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de commande /start"""
    user = update.effective_user
    
    # Bouton pour accéder à la webapp
    keyboard = [
        [InlineKeyboardButton("🌐 Ouvrir Fragment Deals", url=WEBAPP_URL)],
        [InlineKeyboardButton("💎 Créer un nouveau deal", callback_data='start_deal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = f"""
🔥 **Fragment Deal Bot** 🔥

Salut {user.mention_html()} !

Je t'aide à créer et partager tes deals Fragment de manière anonyme et sécurisée.

**Fonctionnalités :**
• 💎 Création de deals TON
• 🔒 Anonymat garanti  
• ⚡ Partage instantané
• 🛡️ Transactions sécurisées

**Comment ça marche :**
1. Clique sur "Créer un nouveau deal"
2. Renseigne le username et le prix
3. Partage ton lien sécurisé !

Prêt à commencer ? 🚀
    """
    
    await update.message.reply_html(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire de commande /help"""
    help_text = """
📚 **Aide - Fragment Deal Bot**

**Commandes disponibles :**
• `/start` - Menu principal
• `/newdeal` - Créer un nouveau deal
• `/cancel` - Annuler l'opération en cours
• `/help` - Afficher cette aide

**Comment créer un deal :**
1. Utilise `/newdeal` ou le bouton du menu
2. Entre le username Fragment (sans @)
3. Entre le prix en TON
4. Confirme et partage ton lien !

**Sécurité :**
✅ Aucune donnée personnelle stockée
✅ Liens temporaires et sécurisés
✅ Anonymat total garanti

**Support :** Contacte @FragmentDeals pour toute question.
    """
    await update.message.reply_html(help_text)

# ===== GESTIONNAIRES DE BOUTONS =====
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gestionnaire des boutons inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start_deal':
        await query.edit_message_text(
            "💎 **Nouveau Deal Fragment**\n\n"
            "Pour commencer, envoie-moi le **username Fragment** que tu veux vendre.\n\n"
            "📝 **Format :** Juste le nom (sans @ ni .ton)\n"
            "📝 **Exemple :** `crypto` ou `defi`\n\n"
            "❌ **Annuler :** /cancel",
            parse_mode='Markdown'
        )
        return USERNAME_INPUT
    
    return ConversationHandler.END

# ===== CRÉATION DE DEALS =====
async def newdeal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Commande pour créer un nouveau deal"""
    await update.message.reply_text(
        "💎 **Nouveau Deal Fragment**\n\n"
        "Pour commencer, envoie-moi le **username Fragment** que tu veux vendre.\n\n"
        "📝 **Format :** Juste le nom (sans @ ni .ton)\n"
        "📝 **Exemple :** `crypto` ou `defi`\n\n"
        "❌ **Annuler :** /cancel",
        parse_mode='Markdown'
    )
    return USERNAME_INPUT

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Récupère le username"""
    username = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Validation basique du username
    if len(username) < 1 or len(username) > 50:
        await update.message.reply_text(
            "❌ **Username invalide**\n\n"
            "Le username doit contenir entre 1 et 50 caractères.\n"
            "Réessaie ou utilise /cancel pour annuler."
        )
        return USERNAME_INPUT
    
    # Nettoyage du username
    username_clean = username.replace('@', '').replace('.ton', '').lower()
    
    # Stockage temporaire
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['username'] = username_clean
    
    await update.message.reply_text(
        f"✅ **Username enregistré :** `{username_clean}`\n\n"
        "💰 Maintenant, envoie-moi le **prix en TON**.\n\n"
        "📝 **Format :** Nombre avec ou sans décimales\n"
        "📝 **Exemples :** `100`, `150.5`, `99.99`\n\n"
        "❌ **Annuler :** /cancel",
        parse_mode='Markdown'
    )
    return PRICE_INPUT

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Récupère le prix"""
    price_text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Validation du prix
    try:
        price = float(price_text)
        if price <= 0 or price > 1000000:
            raise ValueError("Prix hors limites")
    except ValueError:
        await update.message.reply_text(
            "❌ **Prix invalide**\n\n"
            "Veuillez entrer un nombre valide entre 0 et 1,000,000 TON.\n"
            "📝 **Exemples :** `100`, `150.5`, `99.99`\n\n"
            "Réessaie ou utilise /cancel pour annuler."
        )
        return PRICE_INPUT
    
    # Stockage du prix
    user_data[user_id]['price'] = price
    
    # Génération de l'aperçu
    username = user_data[user_id]['username']
    deal_url = f"{WEBAPP_URL}/deal/{username}_{price}"
    
    # Boutons de confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmer", callback_data='confirm_yes'),
            InlineKeyboardButton("❌ Annuler", callback_data='confirm_no')
        ],
        [InlineKeyboardButton("🔄 Recommencer", callback_data='start_deal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    preview_message = f"""
🎯 **Aperçu de ton deal**

**Username :** `{username}.ton`
**Prix :** `{price:g} TON`
**Lien :** `{deal_url}`

💡 **Ce lien permettra aux acheteurs de :**
• Voir les détails du username
• Te contacter de manière anonyme
• Négocier en sécurité

**Confirmer ce deal ?**
    """
    
    await update.message.reply_text(
        preview_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return CONFIRMATION

async def confirm_deal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirmation finale du deal"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == 'confirm_yes':
        if user_id in user_data:
            username = user_data[user_id]['username']
            price = user_data[user_id]['price']
            deal_url = f"{WEBAPP_URL}/deal/{username}_{price}"
            
            success_message = f"""
🎉 **Deal créé avec succès !**

**Ton lien de deal :**
`{deal_url}`

**Partage ce lien pour :**
✅ Recevoir des offres d'achat
✅ Négocier en toute sécurité  
✅ Finaliser la vente

**Conseils :**
💡 Partage sur les groupes Fragment
💡 Ajoute des screenshots du username
💡 Reste disponible pour les questions

**Bonne vente !** 🚀
            """
            
            # Bouton pour créer un autre deal
            keyboard = [[InlineKeyboardButton("🔄 Créer un autre deal", callback_data='start_deal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                success_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Nettoyage des données temporaires
            del user_data[user_id]
        else:
            await query.edit_message_text(
                "❌ **Erreur :** Données de deal introuvables.\n"
                "Utilise /newdeal pour recommencer."
            )
    
    elif query.data == 'confirm_no':
        await query.edit_message_text(
            "❌ **Deal annulé**\n\n"
            "Aucun deal n'a été créé.\n"
            "Utilise /newdeal pour recommencer quand tu veux !"
        )
        
        # Nettoyage des données temporaires
        if user_id in user_data:
            del user_data[user_id]
    
    elif query.data == 'start_deal':
        await query.edit_message_text(
            "💎 **Nouveau Deal Fragment**\n\n"
            "Pour commencer, envoie-moi le **username Fragment** que tu veux vendre.\n\n"
            "📝 **Format :** Juste le nom (sans @ ni .ton)\n"
            "📝 **Exemple :** `crypto` ou `defi`\n\n"
            "❌ **Annuler :** /cancel",
            parse_mode='Markdown'
        )
        return USERNAME_INPUT
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Annulation de la création de deal"""
    user_id = update.effective_user.id
    
    # Nettoyage des données temporaires
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text(
        "❌ **Opération annulée**\n\n"
        "Aucun deal n'a été créé.\n"
        "Utilise /start ou /newdeal quand tu veux recommencer !"
    )
    return ConversationHandler.END

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
