import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate(
    'C:\\Users\\arthu\\PycharmProjects\\telegram-chatbot\\sabaodb-firebase-adminsdk-vcyys-bfb0fa9a02.json')
firebase_admin.initialize_app(cred)

db = firestore.client()


# hello :)


# Add an appointment to Firestore
def add_appointment(user_id, first_name, last_name, service, employee, date, time, email):
    appointments_ref = db.collection('appointments')
    appointments_ref.add({
        'user_id': user_id,
        'first_name': first_name,
        'last_name': last_name,
        'service': service,
        'employee': employee,
        'date': date,
        'time': time,
        'email': email
    })

    # Save the email to a separate collection if not already present
    user_ref = db.collection('users').document(str(user_id))
    user_ref.set({
        'first_name': first_name,
        'last_name': last_name,
        'email': email
    }, merge=True)


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
