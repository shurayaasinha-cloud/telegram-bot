import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = os.environ.get("MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")

# OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation history per user
user_histories = {}

SYSTEM_PROMPT = """You are a helpful AI assistant. You are knowledgeable about anime, donghua, Chinese web novels especially Reverend Insanity, and general topics. 
Respond in the same language the user writes in — Hindi, Hinglish, or English."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Main tera AI assistant hoon 🤖\n"
        "Kuch bhi pucho — anime, donghua, web novels, ya kuch bhi!\n\n"
        "Commands:\n"
        "/start - Bot start karo\n"
        "/clear - Chat history clear karo"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("Chat history clear ho gayi! ✅")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Initialize history
    if user_id not in user_histories:
        user_histories[user_id] = []

    # Add user message
    user_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Keep last 10 messages only
    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]

    # Typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + user_histories[user_id],
            max_tokens=1000,
        )

        reply = response.choices[0].message.content

        # Add assistant response to history
        user_histories[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "Kuch error aa gaya! Thodi der baad try karo. 😅"
        )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
