"""Email notification service for user registration and admin alerts"""
import os
import logging
from html import escape as html_escape
from flask_mail import Mail, Message
from flask import current_app

logger = logging.getLogger(__name__)

# Initialize Flask-Mail
mail = Mail()


class NotificationService:
    """Service for sending email notifications"""

    def __init__(self, app=None):
        """Initialize notification service"""
        self.enabled = False
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app"""
        mail.init_app(app)
        # Check if email is properly configured
        self.enabled = bool(
            app.config.get('MAIL_SERVER') and
            app.config.get('MAIL_USERNAME')
        )
        if self.enabled:
            logger.info("Email notification service is enabled")
        else:
            logger.warning(
                "Email notification service is disabled - "
                "MAIL_SERVER or MAIL_USERNAME not configured"
            )

    def _get_admin_emails(self):
        """Get list of admin email addresses from environment"""
        admin_emails_str = os.getenv('ADMIN_EMAILS', '')
        if not admin_emails_str:
            return []
        return [email.strip() for email in admin_emails_str.split(',') if email.strip()]

    def send_registration_confirmation(self, user):
        """
        Send registration confirmation email to user

        Args:
            user: User object with email, first_name, last_name attributes

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(
                f"Email notifications disabled - skipping registration "
                f"confirmation for user id={user.id}"
            )
            return False

        try:
            sender = current_app.config.get(
                'MAIL_DEFAULT_SENDER',
                os.getenv('MAIL_DEFAULT_SENDER', 'noreply@twendetours.com')
            )

            msg = Message(
                subject='Welcome to Twende Tours!',
                sender=sender,
                recipients=[user.email]
            )

            msg.body = f"""Hello {user.first_name},

Welcome to Twende Tours! Your account has been successfully created.

Account Details:
- Email: {user.email}
- Name: {user.first_name} {user.last_name}

You can now:
- Browse our exciting tour packages
- Make bookings for your dream adventures
- Pay securely using M-Pesa

If you have any questions, feel free to contact our support team.

Best regards,
The Twende Tours Team
"""

            # Escape user data for HTML to prevent XSS
            safe_first_name = html_escape(user.first_name)
            safe_last_name = html_escape(user.last_name)
            safe_email = html_escape(user.email)

            msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Twende Tours!</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{safe_first_name}</strong>,</p>
            <p>Your account has been successfully created!</p>

            <div class="details">
                <h3>Account Details:</h3>
                <p><strong>Email:</strong> {safe_email}</p>
                <p><strong>Name:</strong> {safe_first_name} {safe_last_name}</p>
            </div>

            <p>You can now:</p>
            <ul>
                <li>Browse our exciting tour packages</li>
                <li>Make bookings for your dream adventures</li>
                <li>Pay securely using M-Pesa</li>
            </ul>

            <p>If you have any questions, feel free to contact our support team.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>The Twende Tours Team</p>
        </div>
    </div>
</body>
</html>
"""

            mail.send(msg)
            logger.info(
                f"Registration confirmation email sent to user id={user.id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to send registration confirmation email to "
                f"user id={user.id}: {type(e).__name__}: {str(e)}"
            )
            return False

    def notify_admin_new_registration(self, user):
        """
        Notify admins about new user registration

        Args:
            user: User object with email, first_name, last_name, phone_number attributes

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(
                f"Email notifications disabled - skipping admin notification "
                f"for new user id={user.id}"
            )
            return False

        admin_emails = self._get_admin_emails()
        if not admin_emails:
            logger.info(
                f"No admin emails configured - skipping admin notification "
                f"for new user id={user.id}"
            )
            return False

        try:
            sender = current_app.config.get(
                'MAIL_DEFAULT_SENDER',
                os.getenv('MAIL_DEFAULT_SENDER', 'noreply@twendetours.com')
            )

            msg = Message(
                subject=f'[Twende Tours] New User Registration: {user.email}',
                sender=sender,
                recipients=admin_emails
            )

            phone_info = user.phone_number if user.phone_number else 'Not provided'
            created_at_str = (
                user.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                if user.created_at else 'Unknown'
            )

            msg.body = f"""New User Registration Alert

A new user has registered on Twende Tours.

User Details:
- ID: {user.id}
- Email: {user.email}
- Name: {user.first_name} {user.last_name}
- Phone: {phone_info}
- Registered: {created_at_str}

Please review the new registration in the admin dashboard.

---
This is an automated notification from Twende Tours.
"""

            # Escape user data for HTML to prevent XSS
            safe_first_name = html_escape(user.first_name)
            safe_last_name = html_escape(user.last_name)
            safe_email = html_escape(user.email)
            safe_phone_info = html_escape(phone_info)

            msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .details table {{ width: 100%; border-collapse: collapse; }}
        .details td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        .details td:first-child {{ font-weight: bold; width: 30%; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>New User Registration</h2>
        </div>
        <div class="content">
            <p>A new user has registered on Twende Tours.</p>

            <div class="details">
                <h3>User Details:</h3>
                <table>
                    <tr><td>ID</td><td>{user.id}</td></tr>
                    <tr><td>Email</td><td>{safe_email}</td></tr>
                    <tr><td>Name</td><td>{safe_first_name} {safe_last_name}</td></tr>
                    <tr><td>Phone</td><td>{safe_phone_info}</td></tr>
                    <tr><td>Registered</td><td>{created_at_str}</td></tr>
                </table>
            </div>

            <p>Please review the new registration in the admin dashboard.</p>
        </div>
        <div class="footer">
            <p>This is an automated notification from Twende Tours.</p>
        </div>
    </div>
</body>
</html>
"""

            mail.send(msg)
            logger.info(
                f"Admin notification sent for new user id={user.id} to "
                f"{len(admin_emails)} admin(s)"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to send admin notification for new user id={user.id}: "
                f"{type(e).__name__}: {str(e)}"
            )
            return False

    def send_trip_reminder_email(self, user, trip_schedule, reminder):
        """
        Send trip reminder email to user

        Args:
            user: User object with email, first_name, last_name attributes
            trip_schedule: TripSchedule object with title, location, departure_date
            reminder: Reminder object with message

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(
                f"Email notifications disabled - skipping trip reminder "
                f"for user id={user.id}"
            )
            return False

        try:
            sender = current_app.config.get(
                'MAIL_DEFAULT_SENDER',
                os.getenv('MAIL_DEFAULT_SENDER', 'noreply@twendetours.com')
            )

            msg = Message(
                subject=f'Trip Reminder: {trip_schedule.title}',
                sender=sender,
                recipients=[user.email]
            )

            # Format departure date
            departure_str = (
                trip_schedule.departure_date.strftime('%B %d, %Y at %H:%M')
                if trip_schedule.departure_date else 'Not specified'
            )

            # Custom message or default
            custom_message = reminder.message if reminder.message else ''

            msg.body = f"""Hello {user.first_name},

This is a reminder about your upcoming trip!

Trip Details:
- Trip: {trip_schedule.title}
- Location: {trip_schedule.location}
- Departure: {departure_str}

{custom_message}

Please make sure you're prepared for your adventure!

Best regards,
The Twende Tours Team
"""

            # Escape user data for HTML to prevent XSS
            safe_first_name = html_escape(user.first_name)
            safe_title = html_escape(trip_schedule.title)
            safe_location = html_escape(trip_schedule.location)
            safe_custom_message = html_escape(custom_message) if custom_message else ''

            msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .custom-message {{ background-color: #fff3e0; padding: 15px; border-left: 4px solid #FF9800; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Trip Reminder</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{safe_first_name}</strong>,</p>
            <p>This is a reminder about your upcoming trip!</p>

            <div class="details">
                <h3>Trip Details:</h3>
                <p><strong>Trip:</strong> {safe_title}</p>
                <p><strong>Location:</strong> {safe_location}</p>
                <p><strong>Departure:</strong> {departure_str}</p>
            </div>

            {f'<div class="custom-message"><p>{safe_custom_message}</p></div>' if safe_custom_message else ''}

            <p>Please make sure you're prepared for your adventure!</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>The Twende Tours Team</p>
        </div>
    </div>
</body>
</html>
"""

            mail.send(msg)
            logger.info(
                f"Trip reminder email sent to user id={user.id} for trip {trip_schedule.id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to send trip reminder email to "
                f"user id={user.id}: {type(e).__name__}: {str(e)}"
            )
            return False


# Create singleton instance
notification_service = NotificationService()
