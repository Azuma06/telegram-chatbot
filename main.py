from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN: Final = '7445691165:AAF3zQgRCky9mu_b8noFB9Ym6fFSVOYClHc'
BOT_USERNAME: Final = '@secrrr_bot'

# commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Olá, seja bem vinda ao chat bot do S. Beleza!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Eu sou um robô, digite algo que vou lhe ajudar!')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('TODO: custom command.')

# responses
def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'ola' in processed:
        return 'Oi!'

    if 'tudo bem' in processed:
        return 'eu estou bem!'

    return 'Eu nao entendi o que voce digitou...'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message_type = update.effective_chat.type
        text: str = update.message.text.lower()

        print(f'User ({update.effective_user.id}) in {message_type}: "{text}"')

        response: str = handle_response(text)

        print('Bot:', response)
        await update.message.reply_text(response)
    except AttributeError as e:
        print(f"Error in handle_message: {e}")
        await update.effective_chat.send_message("I encountered an error processing your message.")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    if update.effective_chat:
        print(f"Chat type: {update.effective_chat.type}")
    else:
        print("No chat information available")

def main():
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))

    # messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # errors
    app.add_error_handler(error)

    # polls the bot
    print('Pensando...')
    app.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()
