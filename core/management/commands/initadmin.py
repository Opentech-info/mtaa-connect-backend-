import os

from django.core.management.base import BaseCommand

from core.models import User


class Command(BaseCommand):
    help = "Create an admin user if it does not exist (uses env vars)."

    def handle(self, *args, **options):
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        full_name = os.getenv("DJANGO_SUPERUSER_FULL_NAME", "Admin User")

        if not email or not password:
            self.stdout.write("Skipping admin creation (missing env vars).")
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write("Admin already exists.")
            return

        User.objects.create_superuser(email=email, password=password, full_name=full_name)
        self.stdout.write(self.style.SUCCESS("Admin user created."))
