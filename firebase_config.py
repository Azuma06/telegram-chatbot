import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('C:\\Users\\arthu\Documents\code-projects\\telegram-chatbot\\sabaodb-firebase-adminsdk-vcyys-bfb0fa9a02.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

#hello :)


# Add an appointment to Firestore
def add_appointment(user_id, first_name, last_name, service, date, time):
    appointments_ref = db.collection('appointments')
    appointments_ref.add({
        'user_id': user_id,
        'first_name': first_name,
        'last_name': last_name,
        'service': service,
        'date': date,
        'time': time
    })

# Check if a time slot is available
def is_time_slot_available(date, time):
    appointments_ref = db.collection('appointments')
    query = appointments_ref.where('date', '==', date).where('time', '==', time).stream()
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

