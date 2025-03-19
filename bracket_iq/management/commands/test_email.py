from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = "Test email configuration by sending a test email"

    def add_arguments(self, parser):
        parser.add_argument(
            "to_email", type=str, help="Email address to send test email to"
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write("Attempting to send test email...")

            # Print configuration for verification
            self.stdout.write(f"Using email configuration:")
            self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
            self.stdout.write(f"EMAIL_PORT: {settings.EMAIL_PORT}")
            self.stdout.write(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
            self.stdout.write(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
            self.stdout.write(f"FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

            # Send test email
            send_mail(
                subject="Test Email from BracketIQ",
                message="This is a test email to verify the email configuration is working correctly.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[options["to_email"]],
                fail_silently=False,
            )

            self.stdout.write(self.style.SUCCESS("Successfully sent test email!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {str(e)}"))
