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
PORT = int(os.getenv('PORT', 8080))

print(f"🔍 DEBUG: BOT_TOKEN configuré: {'✅' if BOT_TOKEN else '❌'}")
print(f"🔍 DEBUG: WEBAPP_URL: {WEBAPP_URL}")

# Variables globales pour stocker les données
user_data = {}

def format_ton_amount(amount):
    """Formate un montant en TON avec le symbole 💎"""
    try:
        num_amount = float(amount)
        if num_amount.is_integer():
            return f"💎{int(num_amount)}"
        else:
            return f"💎{num_amount:.2f}"
    except:
        return f"💎{amount}"

def extract_amount_from_text(text):
    """Extrait le montant numérique d'un texte"""
    import re
    
    # Supprime les symboles et espaces
    clean_text = re.sub(r'[💎\$\s,]', '', text)
    
    # Extrait le nombre
    match = re.search(r'[\d.]+', clean_text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

def calculate_commission(price, rate=0.05):
    """Calcule la commission (défaut: 5%)"""
    return price * rate

# Gestionnaires de commandes
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    welcome_text = (
        "🔥 **Fragment Deal Bot**\n\n"
        "Créez facilement vos messages de deals Fragment.com !\n\n"
        "💎 **Montants affichés en TON uniquement**\n"
        "⚡ **Commission calculée automatiquement (5%)**\n"
        "🎯 **Interface simple et intuitive**\n\n"
        "**Commandes disponibles :**\n"
        "• `/newdeal` - Créer un nouveau deal\n"
        "• `/help` - Aide et instructions\n\n"
        "✨ Commencez par créer votre premier deal !"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Créer un deal", callback_data="start_deal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /help"""
    help_text = (
        "📖 **Guide d'utilisation**\n\n"
        "**1️⃣ Créer un deal :**\n"
        "• Tapez `/newdeal`\n"
        "• Entrez le nom d'utilisateur\n"
        "• Entrez le prix (exemple: `1500` ou `1500.50`)\n"
        "• Confirmez et publiez !\n\n"
        "**💡 Formats de prix supportés :**\n"
        "• `1500` → 💎1500\n"
        "• `1500.50` → 💎1500.50\n"
        "• `💎2000` → 💎2000\n\n"
        "**⚙️ Fonctionnalités :**\n"
        "• Commission automatique (5%)\n"
        "• Formatage TON automatique\n"
        "• Bouton d'action personnalisable\n\n"
        "Besoin d'aide ? Contactez le support !"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des boutons inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_deal":
        return await start_new_deal_process(query, context)

async def start_new_deal_process(update, context: ContextTypes.DEFAULT_TYPE):
    """Démarre le processus de création de deal"""
    user_id = update.from_user.id if hasattr(update, 'from_user') else update.effective_user.id
    
    user_data[user_id] = {}
    
    text = (
        "🎯 **Création d'un nouveau deal**\n\n"
        "Entrez le **nom d'utilisateur** du compte Fragment :\n\n"
        "📝 Exemple : `@username` ou `username`\n"
        "💡 Tapez /cancel pour annuler"
    )
    
    if hasattr(update, 'edit_message_text'):
        await update.edit_message_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, parse_mode='Markdown')
    
    return USERNAME_INPUT

async def newdeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /newdeal"""
    return await start_new_deal_process(update, context)

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Récupère le nom d'utilisateur"""
    user_id = update.effective_user.id
    username = update.message.text.strip()
    
    # Formatage du nom d'utilisateur
    if not username.startswith('@'):
        username = f"@{username}"
    
    user_data[user_id]['username'] = username
    
    text = (
        f"✅ **Nom d'utilisateur :** {username}\n\n"
        "💰 Maintenant, entrez le **prix du deal** :\n\n"
        "📝 **Exemples :**\n"
        "• `1500`\n"
        "• `2000.50`\n"
        "• `💎3000`\n\n"
        "💡 Tapez /cancel pour annuler"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')
    return PRICE_INPUT

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Récupère le prix"""
    user_id = update.effective_user.id
    price_text = update.message.text.strip()
    
    # Extraction du montant numérique
    price_amount = extract_amount_from_text(price_text)
    
    if price_amount is None or price_amount <= 0:
        await update.message.reply_text(
            "❌ **Prix invalide !**\n\n"
            "Veuillez entrer un nombre valide :\n"
            "• `1500`\n"
            "• `2000.50`\n"
            "• `💎3000`"
        )
        return PRICE_INPUT
    
    # Calcul de la commission
    commission = calculate_commission(price_amount)
    
    # Formatage des montants
    formatted_price = format_ton_amount(price_amount)
    formatted_commission = format_ton_amount(commission)
    
    # Stockage des données
    user_data[user_id]['price'] = price_amount
    user_data[user_id]['formatted_price'] = formatted_price
    user_data[user_id]['commission'] = commission
    user_data[user_id]['formatted_commission'] = formatted_commission
    
    # Aperçu du message final
    username = user_data[user_id]['username']
    preview_text = (
        "👀 **Aperçu du message :**\n\n"
        "─────────────────────\n"
        f"🔥 **FRAGMENT DEAL** 🔥\n\n"
        f"👤 **Username:** {username}\n"
        f"💎 **Offer Amount:** {formatted_price}\n"
        f"💰 **Commission:** {formatted_commission}\n\n"
        f"📅 **Date:** {datetime.now().strftime('%d/%m/%Y')}\n"
        f"⏰ **Time:** {datetime.now().strftime('%H:%M')}\n\n"
        f"🚀 **Status:** Available\n"
        "─────────────────────\n\n"
        "✅ **Confirmer et publier ?**"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Publier", callback_data="confirm_deal"),
            InlineKeyboardButton("❌ Annuler", callback_data="cancel_deal")
        ],
        [InlineKeyboardButton("✏️ Modifier", callback_data="edit_deal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(preview_text, reply_markup=reply_markup)
    return CONFIRMATION

async def confirm_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirme et publie le deal"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "confirm_deal":
        # Récupération des données
        data = user_data.get(user_id, {})
        username = data.get('username', '@username')
        formatted_price = data.get('formatted_price', '💎0')
        formatted_commission = data.get('formatted_commission', '💎0')
        
        # Message final
        final_message = (
            f"🔥 **FRAGMENT DEAL** 🔥\n\n"
            f"👤 **Username:** {username}\n"
            f"💎 **Offer Amount:** {formatted_price}\n"
            f"💰 **Commission:** {formatted_commission}\n\n"
            f"📅 **Date:** {datetime.now().strftime('%d/%m/%Y')}\n"
            f"⏰ **Time:** {datetime.now().strftime('%H:%M')}\n\n"
            f"🚀 **Status:** Available"
        )
        
        # Bouton d'action
        keyboard = [[InlineKeyboardButton("💎 Finaliser le deal", url=WEBAPP_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Publication du message
        await query.edit_message_text(final_message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Message de confirmation
        await context.bot.send_message(
            user_id,
            "✅ **Deal publié avec succès !**\n\n"
            "Créer un autre deal ? Tapez `/newdeal`"
        )
        
        # Nettoyage
        if user_id in user_data:
            del user_data[user_id]
        
        return ConversationHandler.END
    
    elif query.data == "cancel_deal":
        await query.edit_message_text("❌ Deal annulé. Tapez `/newdeal` pour recommencer.")
        if user_id in user_data:
            del user_data[user_id]
        return ConversationHandler.END
    
    elif query.data == "edit_deal":
        await query.edit_message_text(
            "✏️ **Modification du deal**\n\n"
            "Tapez `/newdeal` pour recommencer la création."
        )
        if user_id in user_data:
            del user_data[user_id]
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule la conversation"""
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text(
        "❌ **Création annulée.**\n\n"
        "Tapez `/newdeal` pour créer un nouveau deal."
    )
    return ConversationHandler.END

def main():
    """Fonction principale"""
    try:
        # Création de l'application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Gestionnaire de conversation pour les deals
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
            fallbacks=[CommandHandler('cancel', cancel)]
        )
        
        # Ajout des gestionnaires
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(conv_handler)
        
        print("🚀 Fragment Deal Bot démarré...")
        print("💎 Mode: TON uniquement")
        
        # Démarrage du bot
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        raise

if __name__ == '__main__':
    main()
