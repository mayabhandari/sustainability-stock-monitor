#!/usr/bin/env python3
"""
Optional: Email the daily report to yourself.
Uses SMTP (works with Gmail, Outlook, etc.)

Setup for Gmail:
  1. Enable 2FA on your Google account
  2. Generate an App Password: https://myaccount.google.com/apppasswords
  3. Set environment variables (see below)
"""

import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_report_email(report_path: str):
    """Send the markdown report as an HTML email."""

    # ── Config (set these as environment variables) ──
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")  # App password for Gmail
    recipient_email = os.environ.get("RECIPIENT_EMAIL", sender_email)

    if not all([sender_email, sender_password]):
        print("❌ Set SENDER_EMAIL and SENDER_PASSWORD environment variables.")
        print("   For Gmail, use an App Password (not your account password).")
        sys.exit(1)

    # Read the report
    with open(report_path, "r") as f:
        report_content = f.read()

    # Convert markdown to basic HTML (simple approach)
    html_body = markdown_to_html(report_content)

    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🌿 Sustainability Stock Report — {datetime.now().strftime('%b %d, %Y')}"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    # Attach both plain text and HTML versions
    msg.attach(MIMEText(report_content, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    # Send
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"📧 Report emailed to {recipient_email}")
    except Exception as e:
        print(f"❌ Email failed: {e}")


def markdown_to_html(md: str) -> str:
    """Minimal markdown-to-HTML for the email body."""
    import re

    html = md
    # Headers
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    # Italic
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    # Line breaks
    html = html.replace("\n\n", "</p><p>")
    html = html.replace("\n", "<br>")
    # Wrap
    html = f"""
    <html><body style="font-family: -apple-system, sans-serif; 
    max-width: 700px; margin: 0 auto; padding: 20px; 
    color: #1a1a1a; line-height: 1.6;">
    <p>{html}</p>
    </body></html>
    """
    return html


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python email_report.py <path_to_report.md>")
        sys.exit(1)
    send_report_email(sys.argv[1])
