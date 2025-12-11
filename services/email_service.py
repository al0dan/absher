from flask_mail import Mail, Message
from flask import current_app
import logging

logger = logging.getLogger(__name__)
mail = Mail()

def send_contract_email(recipient, subject, body):
    try:
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        # msg.html = render_template(...) # optimized later
        mail.send(msg)
        logger.info(f"Email sent to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
