"""
Email notification service using Mailgun SMTP
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings
from app.utils.logger import logger


class EmailService:
    def __init__(self):
        self.smtp_host = settings.MAILGUN_SMTP_HOST
        self.smtp_port = settings.MAILGUN_SMTP_PORT
        self.smtp_user = settings.MAILGUN_SMTP_USER
        self.smtp_password = settings.MAILGUN_SMTP_PASSWORD
        self.from_email = settings.ALERT_EMAIL_FROM
        self.to_email = settings.ALERT_EMAIL_TO

    async def send_storage_alert(self, provider: str, total_size_gb: float, limit_gb: float = 5.0):
        """Send email alert when storage limit is reached"""
        try:
            if not all([self.smtp_user, self.smtp_password, self.from_email, self.to_email]):
                logger.warning("Email configuration incomplete, skipping alert")
                return

            subject = f"Storage Alert: {provider} has reached {total_size_gb:.2f}GB"

            # Create HTML email body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #e74c3c;">Storage Limit Alert</h2>
                    <p>The <strong>{provider}</strong> storage provider has reached its limit.</p>
                    <table style="border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 10px; background-color: #f8f9fa;"><strong>Provider:</strong></td>
                            <td style="padding: 10px;">{provider}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background-color: #f8f9fa;"><strong>Current Usage:</strong></td>
                            <td style="padding: 10px;">{total_size_gb:.2f} GB</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; background-color: #f8f9fa;"><strong>Limit:</strong></td>
                            <td style="padding: 10px;">{limit_gb:.2f} GB</td>
                        </tr>
                    </table>
                    <p style="color: #666;">
                        No new files will be uploaded to this provider until space is freed up.
                        The system will automatically use other available storage providers.
                    </p>
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="font-size: 12px; color: #999;">
                        This is an automated message from YouTube Shorts Downloader.
                    </p>
                </body>
            </html>
            """

            # Create plain text alternative
            text_body = f"""
            Storage Limit Alert

            The {provider} storage provider has reached its limit.

            Provider: {provider}
            Current Usage: {total_size_gb:.2f} GB
            Limit: {limit_gb:.2f} GB

            No new files will be uploaded to this provider until space is freed up.
            The system will automatically use other available storage providers.

            ---
            This is an automated message from YouTube Shorts Downloader.
            """

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = self.to_email

            # Attach both plain text and HTML versions
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            message.attach(text_part)
            message.attach(html_part)

            # Send email via Mailgun SMTP
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Storage alert email sent for {provider} ({total_size_gb:.2f}GB)")

        except Exception as e:
            logger.error(f"Failed to send storage alert email: {e}")


email_service = EmailService()
