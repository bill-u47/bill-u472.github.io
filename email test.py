from flask import Flask, request, jsonify
from flask_cors import CORS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import smtplib
import os
from typing import Optional
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)
load_dotenv()

scheduler = BackgroundScheduler()
scheduler.start()

def send_email(
    sender_email: str,
    receiver_email: str,
    subject: str,
    message: str,
    password: Optional[str] = None
):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        
        if password is None:
            password = os.environ.get("GMAIL_APP_PASSWORD")
            if not password:
                raise ValueError("No password provided and GMAIL_APP_PASSWORD not found in environment variables")
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        
        server.login(sender_email, password)
        server.send_message(msg)
        return True
        
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False
    finally:
        try:
            server.quit()
        except:
            pass

@app.route('/set_reminder', methods=['POST'])
def set_reminder():
    try:
        data = request.json
        reminder_name = data.get('reminderName')
        receiver_email = data.get('email')
        reminder_date = data.get('reminderDate')
        reminder_time = data.get('reminderTime')
        
        if not all([reminder_name, receiver_email, reminder_date, reminder_time]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        sender_email = os.environ.get("SENDER_EMAIL")
        if not sender_email:
            return jsonify({
                'status': 'error',
                'message': 'Sender email not configured'
            }), 500

        # Schedule the reminder
        datetime_str = f"{reminder_date} {reminder_time}"
        reminder_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        
        message = f"""
        What's poppin

        This is to remind you about {reminder_name}
        This was scheduled for {reminder_date} at {reminder_time}

        This was a message from Andrew's Bot
        """

        scheduler.add_job(
            send_email,
            'date',
            run_date=reminder_datetime,
            args=[sender_email, receiver_email, f"Reminder: {reminder_name}", message]
        )

        return jsonify({
            'status': 'success',
            'message': 'Reminder scheduled successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)