import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("LuxeStayAPI")

def send_booking_confirmation(booking: dict):
    """
    Sends a booking confirmation email to the guest.
    Reads SMTP configuration from environment variables.
    """
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    sender_email = os.environ.get("SENDER_EMAIL")

    if not all([smtp_server, smtp_username, smtp_password, sender_email]):
        logger.error("Email configuration is missing. Cannot send booking confirmation.")
        return

    guest_email = booking.get("guest_email")
    if not guest_email:
        logger.error("Guest email is missing from booking data.")
        return

    guest_name = booking.get("guest_name", "Guest")
    booking_id = booking.get("booking_id", "Unknown")
    room_name = booking.get("room_name", "Unknown Room")
    checkin = booking.get("checkin", "Unknown")
    checkout = booking.get("checkout", "Unknown")
    amount = booking.get("amount", 0)

    # Create the email message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Booking Confirmation - LuxeStay Hotels ({booking_id})"
    msg['From'] = f"LuxeStay Hotels <{sender_email}>"
    msg['To'] = guest_email

    # Plain text version
    text = f"""
    Dear {guest_name},

    Thank you for choosing LuxeStay Hotels. Your booking is confirmed!

    Booking Details:
    ----------------
    Booking ID: {booking_id}
    Room: {room_name}
    Check-in: {checkin}
    Check-out: {checkout}
    Total Amount: ${amount}

    We look forward to welcoming you.

    Best regards,
    The LuxeStay Team
    """

    # HTML version
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #E8A838; border-bottom: 2px solid #E8A838; padding-bottom: 10px;">LuxeStay Hotels</h2>
        <p>Dear <strong>{guest_name}</strong>,</p>
        <p>Thank you for choosing LuxeStay Hotels. We are thrilled to confirm your reservation!</p>
        
        <div style="background-color: #F8FAFC; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #0F172A;">Booking Details</h3>
            <p><strong>Booking ID:</strong> <span style="color: #0D9488;">{booking_id}</span></p>
            <p><strong>Room:</strong> {room_name}</p>
            <p><strong>Check-in Date:</strong> {checkin}</p>
            <p><strong>Check-out Date:</strong> {checkout}</p>
            <p style="font-size: 1.2em; border-top: 1px solid #ddd; padding-top: 10px;">
                <strong>Total Amount:</strong> <span style="color: #0D9488;">${amount}</span>
            </p>
        </div>

        <p>If you have any special requests or need to modify your booking, please don't hesitate to contact us.</p>
        <p>We look forward to welcoming you.</p>
        
        <p style="margin-top: 30px; font-size: 0.9em; color: #666;">
            Best regards,<br>
            <strong>The LuxeStay Team</strong>
        </p>
      </body>
    </html>
    """

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, guest_email, msg.as_string())
        server.quit()
        logger.info(f"Booking confirmation email sent to {guest_email} for booking {booking_id}")
    except Exception as e:
        logger.error(f"Failed to send email to {guest_email}: {str(e)}")
