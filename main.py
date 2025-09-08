import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# Get API keys from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check if the keys are loaded
if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("API keys not found. Please check your .env file.")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])


# --- TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user_name = update.effective_user.first_name
    await update.message.reply_html(
        f"👋 Hi {user_name}!\n\n"
        f"I'm an AI assistant powered by Google Gemini.\n"
        f"Just send me a message, and I'll do my best to respond!\n\n"
        f"💬 I have conversation memory, so I'll remember our chat context."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming text messages and gets a response from Gemini."""
    message_text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Received message from user {user_id}: {message_text}")

    try:
        # Show a "typing..." status in Telegram
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='typing'
        )

        # Send the user's message to Gemini
        response = chat.send_message(message_text)

        # Send Gemini's response back to the user with markdown formatting
        try:
            # Use parse_mode='Markdown' for better compatibility
            await update.message.reply_text(response.text, parse_mode='Markdown')
        except Exception as format_error:
            # If formatting fails, send as plain text
            logger.warning(f"Markdown formatting failed, sending as plain text: {format_error}")
            await update.message.reply_text(response.text)
        logger.info(f"Sent Gemini response to user {user_id}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await update.message.reply_text("Sorry, I encountered an error while processing your request.")


def main() -> None:
    """Start the bot with polling."""
    logger.info("Starting bot with polling...")

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Register handlers ---
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non-command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot is polling for updates...")
    application.run_polling()


if __name__ == '__main__':
    main()