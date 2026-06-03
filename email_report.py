import os
import smtplib
import sys
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_report_email(report_path):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL", sender_email)
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    if not sender_email or not sender_password:
        print("Skipping email: credentials not set.")
        return

    with open(report_path, "r") as f:
        report_content = f.read()

    msg = MIMEMultipart("alternative")
    today = datetime.now().strftime("%b %d, %Y")
    msg["Subject"] = "Sustainability Stock Report - " + today
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(report_content, "plain"))

    html = report_content
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = html.replace("\n\n", "</p><p>")
    html = html.replace("\n", "<br>")
    style = "font-family:Arial,sans-serif;max-width:700px;margin:0 auto;padding:20px;line-height:1.7;"
    html = "<html><body style='" + style + "'><p>" + html + "</p></body></html>"
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print("Email sent to " + recipient_email)
    except Exception as e:
        print("Email failed: " + str(e))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python email_report.py report.md")
        sys.exit(1)
    send_report_email(sys.argv[1])
