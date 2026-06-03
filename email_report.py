import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re

def send_report_email(report_path):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL", sender_email)
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    if not sender_email or not sender_password:
        print("Skipping email: SENDER_EMAIL and SENDER_PASSWORD not set.")
        return

    with open(report_path, "r") as f:
        report_content = f.read()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Sustainability Stock Report - {datetime.now().strftime('%b %d, %Y')}"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg.attach(MIMEText(report_content, "plain"))

    html = report_content
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = html.replace("\n\n", "</p><p>")
    html = html.replace("\n", "<br>")
    html = f"""<html><body style="font-family: -apple-system, Helvetica, Arial, sans-serif;
    max-width: 700px; margin: 0 auto; padding: 20px;
    color: #1a1a1a; line-height: 1.7; font-size: 15px;">
    <p>{html}</p></body></html>"""

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"Email sent to {recipient_email}")
    except Exception as e:
        print(f"Email failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python email_rep
