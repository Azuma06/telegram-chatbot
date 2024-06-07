from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
import calendar
import datetime
from firebase_config import add_appointment, is_time_slot_available, fetch_appointments, delete_appointment

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

# Define conversation states
CHOOSING_SERVICE, CHOOSING_DATE, CHOOSING_TIME = range(3)

#only 2024, hardcoded
#really not optimal, but im just a girl :P
# Define holidays
HOLIDAYS = [ 
    datetime.date(2024, 1, 1),   # New Year's Day
    datetime.date(2024, 2, 12),  # Carnival
    datetime.date(2024, 3, 29),  # Good Friday
    datetime.date(2024, 3, 31),  # Easter Sunday
    datetime.date(2024, 4, 21),  # Tiradentes' Day
    datetime.date(2024, 5, 1),   # Labour Day
    datetime.date(2024, 5, 30),  # Corpus Christi
    datetime.date(2024, 9, 7),   # Independence Day
    datetime.date(2024, 10, 12), # Our Lady of Aparecida
    datetime.date(2024, 11, 2),  # All Souls' Day
    datetime.date(2024, 11, 15), # Proclamation of the Republic
    datetime.date(2024, 12, 25), # Christmas
    
    #sundays
    datetime.date(2024, 1, 7), datetime.date(2024, 1, 14), datetime.date(2024, 1, 21), datetime.date(2024, 1, 28),
    datetime.date(2024, 2, 4), datetime.date(2024, 2, 11), datetime.date(2024, 2, 18), datetime.date(2024, 2, 25),
    datetime.date(2024, 3, 3), datetime.date(2024, 3, 10), datetime.date(2024, 3, 17), datetime.date(2024, 3, 24), datetime.date(2024, 3, 31),
    datetime.date(2024, 4, 7), datetime.date(2024, 4, 14), datetime.date(2024, 4, 21), datetime.date(2024, 4, 28),
    datetime.date(2024, 5, 5), datetime.date(2024, 5, 12), datetime.date(2024, 5, 19), datetime.date(2024, 5, 26),
    datetime.date(2024, 6, 2), datetime.date(2024, 6, 9), datetime.date(2024, 6, 16), datetime.date(2024, 6, 23), datetime.date(2024, 6, 30),
    datetime.date(2024, 7, 7), datetime.date(2024, 7, 14), datetime.date(2024, 7, 21), datetime.date(2024, 7, 28),
    datetime.date(2024, 8, 4), datetime.date(2024, 8, 11), datetime.date(2024, 8, 18), datetime.date(2024, 8, 25),
    datetime.date(2024, 9, 1), datetime.date(2024, 9, 8), datetime.date(2024, 9, 15), datetime.date(2024, 9, 22), datetime.date(2024, 9, 29),
    datetime.date(2024, 10, 6), datetime.date(2024, 10, 13), datetime.date(2024, 10, 20), datetime.date(2024, 10, 27),
    datetime.date(2024, 11, 3), datetime.date(2024, 11, 10), datetime.date(2024, 11, 17), datetime.date(2024, 11, 24),
    datetime.date(2024, 12, 1), datetime.date(2024, 12, 8), datetime.date(2024, 12, 15), datetime.date(2024, 12, 22), datetime.date(2024, 12, 29),

]

# Function to check if a date is a holiday
def is_holiday(date):
    return date in HOLIDAYS

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
    return CHOOSING_SERVICE

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Operação cancelada.')
    return ConversationHandler.END

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # to show "processing..." to the user

    service_key = query.data
    if service_key in SERVICES:
        service_name, service_price = SERVICES[service_key]
        context.user_data['service'] = service_name
        context.user_data['price'] = service_price
        await send_calendar(update, context)
        return CHOOSING_DATE
    else:
        await query.edit_message_text(text="Desculpe, essa opção não é válida.")
        return ConversationHandler.END

async def send_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now()
    
    # Set default month and year if not in user data
    year = context.user_data.get('year', now.year)
    month = context.user_data.get('month', now.month)

    # Update the year and month in the context
    context.user_data['year'] = year
    context.user_data['month'] = month

    # Create the calendar for the specified month and year
    cal = calendar.Calendar(firstweekday=6)  # Start the week with Sunday
    month_days = cal.monthdayscalendar(year, month)

    # Create navigation buttons
    keyboard = [
        [InlineKeyboardButton("◀️", callback_data="prev_month"), 
         InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="ignore"),
         InlineKeyboardButton("▶️", callback_data="next_month")]
    ]
    
    # Create day names row
    day_names = ['S', 'M', 'T', 'W', 'T', 'F', 'S']
    day_names_row = [InlineKeyboardButton(day, callback_data="ignore") for day in day_names]
    keyboard.append(day_names_row)
    
    # Create the calendar days buttons
    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                if year == now.year and month == now.month and day < now.day:
                    row.append(InlineKeyboardButton(str(day), callback_data="ignore"))
                else:
                    row.append(InlineKeyboardButton(str(day), callback_data=f"day_{day}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "Para qual dia você deseja agendar o serviço?"
    if isinstance(update, Update):
        await update.callback_query.edit_message_text(text=message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=message, reply_markup=reply_markup)


async def handle_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    now = datetime.datetime.now()
    year = context.user_data.get('year', now.year)
    month = context.user_data.get('month', now.month)
    
    if data == "ignore":
        return
    elif data == "prev_month":
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
        context.user_data['year'] = year
        context.user_data['month'] = month
        await send_calendar(update, context)
    elif data == "next_month":
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        context.user_data['year'] = year
        context.user_data['month'] = month
        await send_calendar(update, context)
    elif data.startswith("day_"):
        day = int(data[4:])
        selected_date = datetime.date(year, month, day)
        if is_holiday(selected_date):
            await query.edit_message_text(text="Desculpe, não podemos agendar neste dia porque é um feriado. Por favor, escolha outra data.")
            return CHOOSING_DATE
        context.user_data['date'] = selected_date
        await show_time_slots(update.effective_chat.id, context)
        return CHOOSING_TIME

async def show_time_slots(chat_id, context: ContextTypes.DEFAULT_TYPE):
    date = context.user_data['date']
    if is_holiday(date):
        await context.bot.send_message(chat_id=chat_id, text="Desculpe, não podemos agendar neste dia porque é um feriado. Por favor, escolha outra data.")
        await send_calendar(chat_id, context)  # Show the calendar again
        return

    time_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    keyboard = [[InlineKeyboardButton(slot, callback_data=f"time_{slot}") for slot in time_slots[i:i+3]] for i in range(0, len(time_slots), 3)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "Escolha um horário disponível:"
    await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    time_slot = query.data[5:]  # remove the "time_" prefix
    context.user_data['time'] = time_slot

    service = context.user_data['service']
    price = context.user_data['price']
    date = context.user_data['date'].strftime("%Y-%m-%d")
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name

    # Check if the time slot is available
    if is_time_slot_available(date, time_slot):
        add_appointment(user_id, first_name, last_name, service, date, time_slot)
        response = f"Ótimo! Você agendou {service} por R${price} no dia {date} às {time_slot}. Esperamos você!"
    else:
        response = f"Desculpe, o horário {time_slot} no dia {date} já está ocupado. Por favor, escolha outro horário."

    await query.edit_message_text(text=response)
    return ConversationHandler.END

async def view_appointments_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    OWNER_USER_ID = 968615314  # Replace with the actual user ID of the business owner

    if user_id == OWNER_USER_ID:
        appointments = fetch_appointments()
        if appointments:
            response = "Here are the upcoming appointments:\n\n"
            for appointment in appointments:
                response += (f"User: {appointment['first_name']} {appointment['last_name']} ({appointment['user_id']})\n"
                             f"Service: {appointment['service']}\n"
                             f"Date: {appointment['date']}\n"
                             f"Time: {appointment['time']}\n\n")
        else:
            response = "No appointments found."
        
        await update.message.reply_text(response)
    else:
        # Fetch only user's appointments
        user_appointments = fetch_appointments(user_id=user_id)
        if user_appointments:
            response = "Here are your upcoming appointments:\n\n"
            for appointment in user_appointments:
                response += (f"Service: {appointment['service']}\n"
                             f"Date: {appointment['date']}\n"
                             f"Time: {appointment['time']}\n\n")
        else:
            response = "You have no appointments."
        
        await update.message.reply_text(response)


async def cancel_appointment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Fetch user's appointments
    appointments = fetch_appointments(user_id=user_id)
    if not appointments:
        await update.message.reply_text("You have no appointments to cancel.")
        return

    # Display user's appointments with options to cancel
    keyboard = [
        [InlineKeyboardButton(f"{appointment['service']} on {appointment['date']} at {appointment['time']}", callback_data=f"cancel_{appointment['id']}")]
        for appointment in appointments
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Select an appointment to cancel:', reply_markup=reply_markup)

async def handle_cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    appointment_id = query.data[7:]  # remove the "cancel_" prefix
    delete_appointment(appointment_id)
    await query.edit_message_text(text="Your appointment has been canceled.")

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

    if 'vapp' in text.lower():
        await view_appointments_command(update, context)
        return

    response: str = handle_response(text)

    print('Bot:', response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == "__main__":
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Set up conversation handler for appointment scheduling
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('agendar', agendar_command)],
        states={
            CHOOSING_SERVICE: [CallbackQueryHandler(button_callback)],
            CHOOSING_DATE: [CallbackQueryHandler(handle_calendar)],
            CHOOSING_TIME: [CallbackQueryHandler(handle_time_selection)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]  # Add cancel command as fallback
    )

    app.add_handler(conv_handler)

    # Other handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('view_appointments', view_appointments_command)) 
    app.add_handler(CommandHandler('cancel_appointment', cancel_appointment_command))  # Add handler for cancel appointment
    app.add_handler(CallbackQueryHandler(handle_cancel_appointment, pattern='^cancel_'))  # Add handler for cancel appointment button
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error)

    # polls the bot
    print('Pensando...')
    app.run_polling(poll_interval=3)
