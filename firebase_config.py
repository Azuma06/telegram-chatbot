import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate(
    'C:\\Users\\arthu\\PycharmProjects\\telegram-chatbot\\sabaodb-firebase-adminsdk-vcyys-bfb0fa9a02.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# Add an appointment to Firestore
def add_appointment(user_id, first_name, last_name, service, employee, date, time, email, calendar_event_id):
    appointments_ref = db.collection('appointments')

    # Check if the appointment already exists
    existing_appointments = appointments_ref.where('user_id', '==', user_id) \
        .where('date', '==', date) \
        .where('time', '==', time) \
        .where('employee', '==', employee) \
        .get()

    if len(existing_appointments) > 0:
        print(f"Appointment already exists for user {user_id} on {date} at {time} with {employee}")
        return False

    # If no existing appointment, add the new one
    try:
        appointments_ref.add({
            'user_id': user_id,
            'first_name': first_name,
            'last_name': last_name,
            'service': service,
            'employee': employee,
            'date': date,  # This should now be a string
            'time': time,
            'email': email,
            'calendar_event_id': calendar_event_id
        })

        # Save the email to a separate collection if not already present
        user_ref = db.collection('users').document(str(user_id))
        user_ref.set({
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        }, merge=True)

        return True
    except Exception as e:
        print(f"Error adding appointment: {e}")
        return False

# Check if a time slot is available
def is_time_slot_available(date, time, employee):
    appointments_ref = db.collection('appointments')
    query = appointments_ref.where('date', '==', date).where('time', '==', time).where('employee', '==', employee).stream()
    for appointment in query:
        return False
    return True

# Fetch appointments from Firestore
def fetch_appointments(user_id=None):
    appointments_ref = db.collection('appointments')
    if user_id:
        appointments = appointments_ref.where('user_id', '==', user_id).stream()
    else:
        appointments = appointments_ref.stream()

    appointment_list = []
    for appointment in appointments:
        appointment_data = appointment.to_dict()
        appointment_data['id'] = appointment.id
        appointment_list.append(appointment_data)

    return appointment_list

# Delete an appointment from Firestore
def delete_appointment(appointment_id):
    appointments_ref = db.collection('appointments')
    appointment_ref = appointments_ref.document(appointment_id)
    appointment_ref.delete()

# New function to get the Google Calendar event ID for an appointment
def get_calendar_event_id(appointment_id):
    appointment_ref = db.collection('appointments').document(appointment_id)
    appointment = appointment_ref.get()
    if appointment.exists:
        return appointment.to_dict().get('calendar_event_id')
    return None