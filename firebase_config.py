import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('/workspaces/telegram-chatbot/sabaodb-firebase-adminsdk-vcyys-bfb0fa9a02.json')
firebase_admin.initialize_app(cred)



db = firestore.client()

# Add an appointment to Firestore
def add_appointment(user_id, service, date, time):
    appointments_ref = db.collection('appointments')
    appointments_ref.add({
        'user_id': user_id,
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
