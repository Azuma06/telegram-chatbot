from typing import Final

from googleapiclient.errors import HttpError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, \
    ConversationHandler
import calendar
import datetime
from datetime import timedelta
from firebase_config import add_appointment, is_time_slot_available, fetch_appointments, delete_appointment, credentials, firebase_admin, firestore, get_calendar_event_id
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os.path
from report_generator import generate_last_month_report
import re


db = firestore.client()

# google calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# firebase db
TOKEN: Final = '7445691165:AAF3zQgRCky9mu_b8noFB9Ym6fFSVOYClHc'

# telegram bot @
BOT_USERNAME: Final = '@secrrr_bot'

# telegram owner id
OWNER_USER_ID = 968615314  # Replace with the actual user ID of the business owner

# Employee emails
employee_emails = {
    'ana': 'ana@gmail.com',
    'beatriz': 'beatriz@gmail.com',
    'carlos': 'carlos@gmail.com',
    'diana': 'diana@gmail.com'
}

# Define services and their prices
SERVICES = {
    '1': ('Corte', 50),
    '2': ('Hidratacao', 40),
    '3': ('Manicure', 30),
    '4': ('Pedicure', 40),
    '5': ('Tintura', 70)
}

# Define employees
EMPLOYEES = {
    '1': 'Ana',
    '2': 'Beatriz',
    '3': 'Carlos',
    '4': 'Diana'
}

# Define conversation states
CHOOSING_SERVICE, CHOOSING_DATE, CHOOSING_TIME, CHOOSING_EMPLOYEE, ADDING_HOLIDAY, DELETING_HOLIDAY, TIME_SELECTION, EMAIL_INPUT, EMAIL_CHOICE, CONFIRMATION = range(10)


async def generate_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user has permission to generate reports
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("Desculpe, você não tem permissão para gerar relatórios.")
        return

    await update.message.reply_text("Gerando o relatório deste mês. Por favor, aguarde...")

    try:
        # Generate the report
        report_file = generate_last_month_report()

        # Send the report
        with open(report_file, 'rb') as file:
            await update.message.reply_document(document=file, filename=report_file)

        await update.message.reply_text("Relatório do mês atual gerado e enviado com sucesso!")
    except Exception as e:
        await update.message.reply_text(f"Ocorreu um erro ao gerar o relatório: {str(e)}")
        print(f"Erro em generate_report_command: {str(e)}")


def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service



# Appointment reminder function with debug logs
async def send_appointment_reminders(context: ContextTypes.DEFAULT_TYPE):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    print(f"Running send_appointment_reminders for {tomorrow_str}")  # Debug log

    appointments = fetch_appointments()
    for appointment in appointments:
        print(f"Checking appointment: {appointment}")  # Debug log
        if appointment['date'] == tomorrow_str:
            user_id = appointment['user_id']
            employee = appointment['employee']
            service = appointment['service']
            date = appointment['date']
            time = appointment['time']

            reminder_text = (
                f"Lembrete: Você tem um agendamento para {service} "
                f"amanhã, dia {date}, às {time} com a {employee}."
            )
            print(f"Sending reminder to {user_id}: {reminder_text}")  # Debug log
            await context.bot.send_message(chat_id=user_id, text=reminder_text)


# really not optimal, but im just a girl :P
# Define holidays
def load_holidays(file_path: str):
    holidays = []
    with open(file_path, 'r') as file:
        for line in file:
            date_str = line.strip()
            if date_str:
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                holidays.append(date)
    return holidays


def add_holiday(date_str: str) -> bool:
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        with open('holidays.txt', 'a') as file:
            file.write(f"{date_str}\n")
        return True
    except ValueError:
        return False


# Command to start adding a holiday
async def add_holiday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_USER_ID:
        await update.message.reply_text("Por favor, insira a data do feriado no formato AAAA-MM-DD:")
        return ADDING_HOLIDAY
    else:
        await update.message.reply_text("Desculpe, você não tem permissão para adicionar feriados.")
        return ConversationHandler.END


def delete_holiday(date_str: str) -> bool:
    try:
        holiday_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        if holiday_date in HOLIDAYS:
            with open('holidays.txt', 'r') as file:
                lines = file.readlines()
            with open('holidays.txt', 'w') as file:
                for line in lines:
                    if line.strip() != date_str:
                        file.write(line)
            HOLIDAYS.remove(holiday_date)
            return True
        else:
            return False
    except ValueError:
        return False


# Command to start deleting a holiday
async def delete_holiday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_USER_ID:
        await update.message.reply_text("Por favor, insira a data do feriado que deseja excluir no formato AAAA-MM-DD:")
        return DELETING_HOLIDAY
    else:
        await update.message.reply_text("Desculpe, você não tem permissão para excluir feriados.")
        return ConversationHandler.END


# Function to handle the holiday deletion
async def handle_holiday_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_USER_ID:
        date_str = update.message.text
        if delete_holiday(date_str):
            await update.message.reply_text(f"Feriado excluído com sucesso: {date_str}")
            return ConversationHandler.END
        else:
            await update.message.reply_text("O feriado não existe ou já foi excluído.")
            return DELETING_HOLIDAY
    else:
        await update.message.reply_text("Desculpe, você não tem permissão para excluir feriados.")
        return ConversationHandler.END


# Function to handle the holiday date input
async def handle_holiday_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_USER_ID:
        date_str = update.message.text
        if add_holiday(date_str):
            HOLIDAYS.append(datetime.datetime.strptime(date_str, '%Y-%m-%d').date())
            await update.message.reply_text(f"Feriado adicionado com sucesso: {date_str}")
            return ConversationHandler.END
        else:
            await update.message.reply_text("Formato de data inválido. Por favor, use AAAA-MM-DD.")
            return ADDING_HOLIDAY
    else:
        await update.message.reply_text("Desculpe, você não tem permissão para adicionar feriados.")
        return ConversationHandler.END


# Load holidays from the file
HOLIDAYS = load_holidays('holidays.txt')


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
    await query.answer()

    service_key = query.data
    if service_key in SERVICES:
        service_name, service_price = SERVICES[service_key]
        context.user_data['service'] = service_name
        context.user_data['price'] = service_price

        # Proceed to choosing employee
        keyboard = [
            [InlineKeyboardButton(name, callback_data=key)]
            for key, name in EMPLOYEES.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Escolha um funcionário:", reply_markup=reply_markup)
        return CHOOSING_EMPLOYEE
    else:
        await query.edit_message_text(text="Desculpe, essa opção não é válida.")
        return ConversationHandler.END


async def employee_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # to show "processing..." to the user

    employee_key = query.data
    if employee_key in EMPLOYEES:
        employee_name = EMPLOYEES[employee_key]
        context.user_data['employee'] = employee_name
        await send_calendar(update, context)  # Proceed to date selection
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
            await query.edit_message_text(
                text="Desculpe, não podemos agendar neste dia, pois não estaremos trabalhando. Por favor, escolha outra data.")
            return CHOOSING_DATE
        context.user_data['date'] = selected_date
        await show_time_slots(update.effective_chat.id, context)
        return CHOOSING_TIME


async def show_time_slots(chat_id, context: ContextTypes.DEFAULT_TYPE):
    date = context.user_data['date']
    today = datetime.date.today()

    if date == today:
        await context.bot.send_message(chat_id=chat_id,
                                       text="Desculpe, não é possível agendar para o dia de hoje. Por favor, escolha outra data.")
        await send_calendar(chat_id, context)  # Show the calendar again
        return

    if is_holiday(date):
        await context.bot.send_message(chat_id=chat_id,
                                       text="Desculpe, não podemos agendar neste dia, pois não estaremos trabalhando. Por favor, escolha outra data.")
        await send_calendar(chat_id, context)  # Show the calendar again
        return

    time_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "23:00"]
    keyboard = [[InlineKeyboardButton(slot, callback_data=f"time_{slot}") for slot in time_slots[i:i + 3]] for i in
                range(0, len(time_slots), 3)]
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
    employee = context.user_data['employee']
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name

    # Check if the time slot is available
    if is_time_slot_available(date, time_slot, employee):
        context.user_data['user_id'] = user_id
        context.user_data['first_name'] = first_name
        context.user_data['last_name'] = last_name

        # Check if user email exists in Firestore
        user_ref = db.collection('users').document(str(user_id))
        user_doc = user_ref.get()
        if user_doc.exists:
            user_email = user_doc.to_dict().get('email')
            context.user_data['email'] = user_email

            keyboard = [
                [
                    InlineKeyboardButton("Usar e-mail salvo", callback_data='use_saved_email'),
                    InlineKeyboardButton("Fornecer novo e-mail", callback_data='provide_new_email')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="Já temos um e-mail salvo para você. Deseja usar este e-mail ou fornecer um novo?",
                reply_markup=reply_markup
            )
            return EMAIL_INPUT
        else:
            await query.edit_message_text(text="Por favor, forneça seu endereço de e-mail para a confirmação do agendamento:")
            return EMAIL_INPUT
    else:
        response = f"Desculpe, o horário {time_slot} no dia {date} com {employee} já está ocupado. Por favor, escolha outro horário."
        await query.edit_message_text(text=response)
        return ConversationHandler.END


async def handle_email_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'use_saved_email':
        email = context.user_data['email']
        await query.edit_message_text(text=f"Confirmando agendamento com o email: {email}")
        return await finalize_appointment(update, context, email)
    else:
        await query.edit_message_text(text="Por favor, forneça seu endereço de e-mail para a confirmação do agendamento:")
        return EMAIL_INPUT

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

async def handle_email_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_email = update.message.text
    if is_valid_email(user_email):
        context.user_data['email'] = user_email
        await update.message.reply_text(f"Confirmando agendamento com o email: {user_email}")
        return await finalize_appointment(update, context, user_email)
    else:
        await update.message.reply_text("O email fornecido parece ser inválido. Por favor, forneça um endereço de email válido.")
        return EMAIL_INPUT


async def finalize_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE, email):
    service = context.user_data['service']
    price = context.user_data['price']
    date = context.user_data['date']
    time_slot = context.user_data['time']
    employee = context.user_data['employee']
    user_id = context.user_data['user_id']
    first_name = context.user_data['first_name']
    last_name = context.user_data['last_name']

    if isinstance(date, datetime.date):
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = date

    start_time = datetime.datetime.strptime(f"{date_str} {time_slot}", "%Y-%m-%d %H:%M")
    end_time = start_time + datetime.timedelta(hours=1)

    event = {
        'summary': f'{service} com {employee}',
        'location': 'Av. Pres. Lucena, 2439 - Brasília, Ivoti - RS, 93900-000',
        'description': f'Appointment for {service} com {employee}',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
        'attendees': [
            {'email': employee_emails.get(employee.lower())},
            {'email': email},
        ],
    }

    calendar_service = get_calendar_service()
    try:
        event = calendar_service.events().insert(calendarId='primary', body=event).execute()
        calendar_event_id = event['id']

        success = add_appointment(user_id, first_name, last_name, service, employee, date_str, time_slot, email, calendar_event_id)

        if success:
            response = f"Ótimo! Você agendou {service} por R${price} com {employee} no dia {date_str} às {time_slot}. Esperamos você! Um convite foi enviado para seu email {email}."
        else:
            response = f"Desculpe, ocorreu um erro ao agendar seu compromisso. Por favor, tente novamente mais tarde."
    except HttpError as e:
        if "Invalid attendee email" in str(e):
            response = f"Desculpe, o endereço de e-mail fornecido ({email}) parece ser inválido. Por favor, verifique o e-mail e tente novamente."
        else:
            response = f"Desculpe, ocorreu um erro ao agendar seu compromisso. Por favor, tente novamente mais tarde."
        print(f"Error adding event to Google Calendar: {e}")

    if isinstance(update, Update):
        if update.callback_query:
            await update.callback_query.edit_message_text(text=response)
        else:
            await update.message.reply_text(text=response)
    else:
        await context.bot.send_message(chat_id=user_id, text=response)

    return ConversationHandler.END


async def view_appointments_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_USER_ID:
        appointments = fetch_appointments()
        if appointments:
            response = "Aqui estão seus próximos horários:\n\n"
            for appointment in appointments:
                response += (
                    f"User: {appointment['first_name']} {appointment['last_name']} ({appointment['user_id']})\n"
                    f"Service: {appointment['service']}\n"
                    f"Date: {appointment['date']}\n"
                    f"Time: {appointment['time']}\n\n")
        else:
            response = "Nenhum horário encontrado."

        await update.message.reply_text(response)
    else:
        # Fetch only user's appointments
        user_appointments = fetch_appointments(user_id=user_id)
        if user_appointments:
            response = "Aqui estão seus próximos horários:\n\n"
            for appointment in user_appointments:
                response += (f"Service: {appointment['service']}\n"
                             f"Date: {appointment['date']}\n"
                             f"Time: {appointment['time']}\n\n")
        else:
            response = "Nenhum horário encontrado."

        await update.message.reply_text(response)


async def cancel_appointment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Fetch user's appointments
    appointments = fetch_appointments(user_id=user_id)
    if not appointments:
        await update.message.reply_text("Você não tem horários para cancelar")
        return

    # Display user's appointments with options to cancel
    keyboard = [
        [InlineKeyboardButton(f"{appointment['service']} on {appointment['date']} at {appointment['time']}",
                              callback_data=f"cancel_{appointment['id']}")]
        for appointment in appointments
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Selecione um horário para cancelar:', reply_markup=reply_markup)


async def handle_cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    appointment_id = query.data[7:]  # remove the "cancel_" prefix

    # Get the Google Calendar event ID before deleting the appointment
    calendar_event_id = get_calendar_event_id(appointment_id)

    if calendar_event_id:
        # Delete the event from Google Calendar
        calendar_service = get_calendar_service()
        try:
            calendar_service.events().delete(calendarId='primary', eventId=calendar_event_id).execute()
        except Exception as e:
            print(f"Error deleting Google Calendar event: {e}")

    # Delete the appointment from Firestore
    delete_appointment(appointment_id)

    await query.edit_message_text(text="Seu horário foi cancelado.")


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

    # Set up the job to send appointment reminders
    job_queue = app.job_queue
    print('Setting up the job queue...')
    job_queue.run_repeating(
        send_appointment_reminders,
        interval=timedelta(seconds=86400),  # Run the task every 24 hours
    )
    print('Job queue set up completed.')

    # Set up conversation handler for appointment scheduling
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('agendar', agendar_command)],
        states={
            CHOOSING_SERVICE: [CallbackQueryHandler(button_callback)],
            CHOOSING_EMPLOYEE: [CallbackQueryHandler(employee_callback)],
            CHOOSING_DATE: [CallbackQueryHandler(handle_calendar)],
            CHOOSING_TIME: [CallbackQueryHandler(handle_time_selection)],
            EMAIL_INPUT: [
                CallbackQueryHandler(handle_email_choice),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email_input)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )

    # Set up conversation handler for adding holidays
    holiday_handler = ConversationHandler(
        entry_points=[CommandHandler('add_holiday', add_holiday_command)],
        states={
            ADDING_HOLIDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_holiday_date)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )

    # Set up conversation handler for deleting holidays
    delete_holiday_handler = ConversationHandler(
        entry_points=[CommandHandler('delete_holiday', delete_holiday_command)],
        states={
            DELETING_HOLIDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_holiday_deletion)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )

    app.add_handler(conv_handler)
    app.add_handler(holiday_handler)
    app.add_handler(delete_holiday_handler)

    # Other handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('view_appointments', view_appointments_command))
    app.add_handler(CommandHandler('cancel_appointment', cancel_appointment_command))  # Add handler for cancel appointment
    app.add_handler(CallbackQueryHandler(handle_cancel_appointment, pattern='^cancel_'))  # Add handler for cancel appointment button
    app.add_handler(CommandHandler('generate_report', generate_report_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error)

    print('Pensando...')
    app.run_polling(poll_interval=0.1)
