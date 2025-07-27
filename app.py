import datetime
import time
import smtplib
import ssl
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template, send_from_directory
from threading import Thread
import os
import pytz # Import the pytz library

app = Flask(__name__)

# --- Configuration for Email Sending ---
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your_email@example.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your_email_app_password")

# SMTP server details (for Gmail)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 # For SSL

# Define the timezone for the alarm system
ALARM_TIMEZONE = pytz.timezone('Asia/Kolkata')

def send_email(receiver_email, subject, body):
    """
    Sends an email to the specified receiver.
    """
    if SENDER_EMAIL == "your_email@example.com" or SENDER_PASSWORD == "your_email_app_password":
        print("ERROR: Email credentials are still default placeholders. Please set SENDER_EMAIL and SENDER_PASSWORD environment variables.")
        return False

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Email successfully sent to {receiver_email}!")
        return True
    except Exception as e:
        print(f"Failed to send email to {receiver_email}. Error: {e}")
        return False

def schedule_and_send_email(alarm_datetime_str, receiver_email, message):
    """
    Calculates the time to wait and sends the email, adjusted for ALARM_TIMEZONE.
    This function should ideally run in a separate thread or background task.
    """
    try:
        # Parse the alarm datetime string as a naive datetime object
        naive_alarm_datetime = datetime.datetime.fromisoformat(alarm_datetime_str)

        # Localize the naive alarm datetime to the specified timezone
        # This assumes the frontend sends the date/time in the desired timezone's local format
        timezone_aware_alarm_datetime = ALARM_TIMEZONE.localize(naive_alarm_datetime)

        # Get the current time, localized to the specified timezone
        current_timezone_aware_datetime = datetime.datetime.now(ALARM_TIMEZONE)

        # Calculate time difference in seconds
        time_difference = (timezone_aware_alarm_datetime - current_timezone_aware_datetime).total_seconds()

        if time_difference <= 0:
            print(f"Alarm for {receiver_email} is in the past or current (Timezone: {ALARM_TIMEZONE.tzname(datetime.datetime.now())}). Not scheduling.")
            return

        print(f"Scheduling email for {receiver_email} in {time_difference:.2f} seconds (Timezone: {ALARM_TIMEZONE.tzname(datetime.datetime.now())})...")
        time.sleep(time_difference)

        subject = "Your Scheduled Reminder!"
        body = f"Hello,\n\nThis is your reminder:\n\n{message}\n\nBest regards,\nYour Alarm System"

        send_email(receiver_email, subject, body)

    except Exception as e:
        print(f"Error during scheduling or sending email: {e}")

@app.route('/')
def index():
    """
    Serves the main HTML page.
    """
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """
    Serves the favicon.
    You can place a favicon.ico file in your 'static' folder.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/set-alarm', methods=['POST'])
def set_alarm():
    """
    API endpoint to receive alarm details from the frontend.
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    alarm_date = data.get('date')
    alarm_time = data.get('time')
    receiver_email = data.get('email')
    message = data.get('message')

    if not all([alarm_date, alarm_time, receiver_email, message]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    # Combine date and time into a single ISO format string for consistency
    # Frontend sends naive datetime, which we will localize in the backend
    alarm_datetime_str = f"{alarm_date}T{alarm_time}"

    try:
        thread = Thread(target=schedule_and_send_email, args=(alarm_datetime_str, receiver_email, message))
        thread.daemon = True
        thread.start()

        print(f"Alarm request received and scheduled for {receiver_email} at {alarm_datetime_str} (Timezone: {ALARM_TIMEZONE.tzname(datetime.datetime.now())})")
        return jsonify({"success": True, "message": "Alarm set successfully!"}), 200
    except Exception as e:
        print(f"Error processing alarm request: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

if __name__ == '__main__':
    # To run this Flask app:
    # 1. Save it as a Python file (e.g., app.py).
    # 2. Install Flask: pip install Flask
    # 3. Install pytz: pip install pytz
    # 4. Create a folder named 'templates' in the same directory as app.py.
    # 5. Place your 'index.html' file inside the 'templates' folder.
    # 6. Optionally, create a folder named 'static' and place 'favicon.ico' inside it.
    # 7. Set the SENDER_EMAIL and SENDER_PASSWORD environment variables.
    # 8. Run from your terminal: python app.py
    # The server will typically run on http://127.0.0.1:5000/
    print("Starting Flask server...")
    app.run(debug=True)
