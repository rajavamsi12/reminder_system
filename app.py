import datetime
import time
import smtplib
import ssl
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template, send_from_directory
from threading import Thread
import os # Import os module for accessing environment variables

app = Flask(__name__)

# --- Configuration for Email Sending ---
# IMPORTANT: It is highly recommended to store sensitive information like
# email credentials in environment variables rather than hardcoding them.
# For Gmail, you'll need to generate an "App password" if you have 2FA enabled.
# Do NOT use your regular email password directly.

# Read sender email and password from environment variables
# How to set environment variables (example for Windows, Linux/macOS):
# Windows (Command Prompt): set SENDER_EMAIL="your_email@example.com"
# Windows (PowerShell): $env:SENDER_EMAIL="your_email@example.com"
# Linux/macOS: export SENDER_EMAIL="your_email@example.com"
# Make sure to set both SENDER_EMAIL and SENDER_PASSWORD before running the app.
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your_email@example.com") # Default if not set
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your_email_app_password") # Default if not set

# SMTP server details (for Gmail)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 # For SSL

def send_email(receiver_email, subject, body):
    """
    Sends an email to the specified receiver.
    """
    # Check if credentials are still default placeholders
    if SENDER_EMAIL == "your_email@example.com" or SENDER_PASSWORD == "your_email_app_password":
        print("ERROR: Email credentials are still default placeholders. Please set SENDER_EMAIL and SENDER_PASSWORD environment variables.")
        return False

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email

        # Create a secure SSL context
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
    Calculates the time to wait and sends the email.
    This function should ideally run in a separate thread or background task.
    """
    try:
        # Parse the alarm datetime string
        alarm_datetime = datetime.datetime.fromisoformat(alarm_datetime_str)
        current_datetime = datetime.datetime.now()

        # Calculate time difference in seconds
        time_difference = (alarm_datetime - current_datetime).total_seconds()

        if time_difference <= 0:
            print(f"Alarm for {receiver_email} is in the past or current. Not scheduling.")
            return

        print(f"Scheduling email for {receiver_email} in {time_difference:.2f} seconds...")
        time.sleep(time_difference) # This will block the thread until the time is up

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
    alarm_datetime_str = f"{alarm_date}T{alarm_time}"

    try:
        # Start a new thread to handle the scheduling and email sending.
        # This prevents the web server from being blocked while waiting for the alarm time.
        # For a production system, consider using a proper task queue like Celery or APScheduler.
        thread = Thread(target=schedule_and_send_email, args=(alarm_datetime_str, receiver_email, message))
        thread.daemon = True # Allow the main program to exit even if threads are running
        thread.start()

        print(f"Alarm request received and scheduled for {receiver_email} at {alarm_datetime_str}")
        return jsonify({"success": True, "message": "Alarm set successfully!"}), 200
    except Exception as e:
        print(f"Error processing alarm request: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

if __name__ == '__main__':
    # To run this Flask app:
    # 1. Save it as a Python file (e.g., app.py).
    # 2. Install Flask: pip install Flask
    # 3. Create a folder named 'templates' in the same directory as app.py.
    # 4. Place your 'index.html' file inside the 'templates' folder.
    # 5. Optionally, create a folder named 'static' and place 'favicon.ico' inside it.
    # 6. Set the SENDER_EMAIL and SENDER_PASSWORD environment variables.
    #    Example (replace with your actual email and app password):
    #    Windows (Command Prompt):
    #        set SENDER_EMAIL="your_email@example.com"
    #        set SENDER_PASSWORD="your_app_password"
    #    Windows (PowerShell):
    #        $env:SENDER_EMAIL="your_email@example.com"
    #        $env:SENDER_PASSWORD="your_app_password"
    #    Linux/macOS:
    #        export SENDER_EMAIL="your_email@example.com"
    #        export SENDER_PASSWORD="your_app_password"
    # 7. Run from your terminal: python app.py
    # The server will typically run on http://127.0.0.1:5000/
    print("Starting Flask server...")
    app.run(debug=True) # debug=True allows for auto-reloading and better error messages
