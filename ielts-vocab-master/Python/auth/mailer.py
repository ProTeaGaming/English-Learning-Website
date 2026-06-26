import importlib.util
import logging
import os
import smtplib
from email.mime.text import MIMEText


def get_mail_config() -> dict | None:
    path = os.path.join(os.path.dirname(__file__), 'config.local.py')
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location('config_local', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, 'CONFIG', None)


def smtp_send_mail(to: str, subject: str, body_text: str) -> bool:
    config = get_mail_config()
    if not config:
        logging.error('Mailer: auth/config.local.py is missing, cannot send email.')
        return False

    msg = MIMEText(body_text, 'plain', 'utf-8')
    msg['From'] = f"{config['from_name']} <{config['from_email']}>"
    msg['To'] = to
    msg['Subject'] = subject

    try:
        with smtplib.SMTP(config['smtp_host'], config['smtp_port'], timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(config['smtp_user'], config['smtp_pass'])
            smtp.sendmail(config['from_email'], [to], msg.as_string())
        return True
    except Exception as exc:
        logging.error('Mailer: %s', exc)
        return False
