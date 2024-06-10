# import schedule
# import time
# from main import send_appointment_reminders
#
#
# def job(t):
#     print('working', t)
#     send_appointment_reminders()
#     return
#
#
# def start_scheduler():
#     schedule.every().day.at('13:01').do(job, 'its 9:00')
#
#     while True:
#         schedule.run_pending()
#         time.sleep(60)
#
#
# if __name__ == "__main__":
#     start_scheduler()
#