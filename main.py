from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN: Final = '7445691165:AAF3zQgRCky9mu_b8noFB9Ym6fFSVOYClHc'
BOT_USERNAME: Final = '@secrrr_bot'

# Define services and their prices
SERVICES = {
    '1': ('Corte', 50),
    '2': ('Hidratacao', 40),
    '3': ('Manicure', 30),
    '4': ('Pedicure', 40),
    '5': ('Tintura', 70)
}

# commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Olá, seja bem vinda ao chat bot do S. Beleza!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Eu sou um robô, digite algo que vou lhe ajudar!')

async def agendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"{value[0]} - R${value[1]}", callback_data=key)]
        for key, value in SERVICES.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Escolha um dos serviços abaixo:', reply_markup=reply_markup)

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('TODO: custom command.')

# Handle button callbacks
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # to show "processing..." to the user

    service_key = query.data
    if service_key in SERVICES:
        service_name, service_price = SERVICES[service_key]
        response = f"Você escolheu {service_name} por R${service_price}. Por favor, confirme seu agendamento."
    else:
        response = "Desculpe, essa opção não é válida."

    await query.edit_message_text(text=response)

# responses
def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'ola' in processed or 'oi' in processed:
        return 'Oi!'

    if 'tudo bem' in processed:
        return 'eu estou bem!'

    return 'Eu nao entendi o que voce digitou...'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    chat_type: str = update.message.chat.type

    print(f'User ({update.message.chat.id}) in {chat_type}: "{text}"')

    response: str = handle_response(text)

    print('Bot:', response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == "__main__":
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # commands - these should come BEFORE the text message handler
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('agendar', agendar_command))
    app.add_handler(CommandHandler('custom', custom_command))

    # Handle button presses
    app.add_handler(CallbackQueryHandler(button_callback))

    # messages - this comes AFTER all the command handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # errors
    app.add_error_handler(error)

    # polls the bot
    print('Pensando...')
    app.run_polling(poll_interval=3)