import os
import sys
# Ensure project root is in sys.path when running from scripts/
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from utils import send_email


def main():
    app = create_app()
    with app.app_context():
        cfg = app.config
        admin_list_raw = cfg.get('ADMIN_NOTIFY_EMAILS', '') or ''
        if admin_list_raw:
            recipients = [e.strip() for e in admin_list_raw.split(',') if e.strip()]
        else:
            # Fallback to MAIL_USERNAME
            sender = cfg.get('MAIL_USERNAME', '')
            recipients = [sender] if sender else []

        subject = 'Email thử: cấu hình SMTP'
        body = 'Xin chào, đây là email kiểm tra cấu hình SMTP của hệ thống.'

        ok = send_email(subject, recipients, body_text=body)
        print('SEND_OK=' + str(ok))
        print('RECIPIENTS=' + ','.join(recipients))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('ERROR=' + str(e))
        sys.exit(1)