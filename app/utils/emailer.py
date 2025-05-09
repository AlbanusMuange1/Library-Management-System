#!/usr/bin/env python3
import os
from flask_mail import Message
from app.extensions import mail
from flask import current_app
from threading import Thread

def send_email_with_attachment(recipient, subject, body, attachment_path):
    app = current_app._get_current_object()
    try:
        if not os.path.exists(attachment_path):
            current_app.logger.error(f"Attachment not fount: {attachment_path}")
            return False
        msg = Message(subject, recipients=[recipient], body=body)
        with open(attachment_path, 'rb') as f:
            msg.attach(filename=os.path.basename(attachment_path), content_type='application/pdf', data=f.read()
            )

        Thread(target=send_async_email, args=(app, msg)).start()
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email: {recipient}: {str(e)}")

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f"Email sent to {msg.recipients}")
        except Exception as e:
            current_app.logger.error(f"Error sending email: {str(e)}")