import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

def send_email_with_pdf(pdf_bytes, recipient_email, start_email, app_password, subject_address):
    """
    Sends an email with the PDF report attached.
    
    Args:
        pdf_bytes (bytes): The PDF content.
        recipient_email (str): The recipient's email address.
        start_email (str): The sender's email address (Gmail).
        app_password (str): The sender's App Password (Gmail).
        subject_address (str): The address of the property analyzed.
        
    Returns:
        bool: True if successful, False otherwise.
        str: Error message if failed, None if successful.
    """
    if not recipient_email or not start_email or not app_password:
        return False, "Missing email credentials or recipient."

    msg = MIMEMultipart()
    msg['Subject'] = f"ARV Report for {subject_address}"
    msg['From'] = start_email
    msg['To'] = recipient_email

    body = f"""
    Hello,
    
    Attached is the ARV Analysis Report for {subject_address}.
    
    Best regards,
    Real Estate Comps Bot
    """
    msg.attach(MIMEText(body, 'plain'))

    # Attach PDF
    part = MIMEApplication(pdf_bytes, Name=f"ARV_Report_{subject_address}.pdf")
    part['Content-Disposition'] = f'attachment; filename="ARV_Report_{subject_address}.pdf"'
    msg.attach(part)

    try:
        # Connect to Gmail SMTP (standard port 587 for TLS)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(start_email, app_password)
            server.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)
