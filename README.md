
# TODO list

- [x] selecionar funcionario

- [X] conectar com google calendar

- [ ] reports mensair (pdf?)

- [x] checar os horarios que marcou (user)

- [x] cancelar operaçao

- [x] cancelar horario marcado

- [x] save usename, not only user ID

- [x] add exceptions (non working hours, holidays, non working days...)

- [ ] work hours

- [x] alert about upcoming appointments

- [x] alert admin that an appointment was created by someone 

# Telegram Appointment Bot

This is a Telegram bot for scheduling appointments using Firebase as the backend database.

## Requirements

- Python 3.8+
- pip

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up Firebase:
    - Obtain your Firebase service account key JSON file.
    - Place the service account key JSON file in your project directory.

4. Update the Firebase configuration in `firebase_config.py`:
    ```python
    cred = credentials.Certificate('path/to/your/serviceAccountKey.json')
    ```

5. Update the Telegram bot token in `main.py`:
    ```python
    TOKEN: Final = 'YOUR_TELEGRAM_BOT_TOKEN'
    ```

6. Run the bot:
    ```bash
    python main.py
    ```

## Usage

- Use the `/start` command to start interacting with the bot.
- Use the `/help` command to get help.
- Use the `/agendar` command to schedule an appointment.
- The bot owner can use the keyword `vapp` to view all scheduled appointments.

## License
TODO
This project is licensed under the ... License.
