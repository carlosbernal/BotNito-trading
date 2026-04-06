import os
import sys
import pytz
from smtplib import SMTP_SSL as SMTP
from datetime import datetime
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def sendEmail(Msg):
    SMTPserver = os.getenv("EMAIL_SMTP_SERVER", "smtp.dreamhost.com")
    sender = os.getenv("EMAIL_SENDER")
    destination = [os.getenv("EMAIL_RECIPIENT")]
    USERNAME = os.getenv("EMAIL_USERNAME")
    PASSWORD = os.getenv("EMAIL_PASSWORD")

    text_subtype = 'plain'
    utc_now = datetime.now(pytz.utc)
    content = Msg
    subject = utc_now.strftime("%m/%d/%Y, %H:%M:%S") + " Nito dice Hola!"

    try:
        msg = MIMEText(content, text_subtype)
        msg['Subject'] = subject
        msg['From'] = sender

        conn = SMTP(SMTPserver)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(sender, destination, msg.as_string())
        finally:
            conn.quit()

    except Exception:
        sys.exit("mail failed; CUSTOM_ERROR")
