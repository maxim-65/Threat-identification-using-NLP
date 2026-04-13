from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password, identify_hasher

from apps.Remote_User.models import ClientRegister_Model


class Command(BaseCommand):
    help = "Migrate plaintext passwords in ClientRegister_Model to secure Django hashes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many passwords would be migrated without saving changes.",
        )

    def _is_hashed(self, password_value):
        if not password_value:
            return False
        try:
            identify_hasher(password_value)
            return True
        except Exception:
            return False

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        total = 0
        migrated = 0

        users = ClientRegister_Model.objects.all()
        for user in users:
            total += 1
            if self._is_hashed(user.password):
                continue

            migrated += 1
            if not dry_run:
                user.password = make_password(user.password)
                user.save(update_fields=["password"])

        mode = "DRY-RUN" if dry_run else "EXECUTED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: scanned={total}, migrated={migrated}"))
