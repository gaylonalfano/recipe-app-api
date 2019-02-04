# management/commands/wait_for_db.py
# Import time module to make application sleep between db checks
import time

# Import connections module to check if db connection available
from django.db import connections
# Import OperationalError that Dj throws if db unavailable
from django.db.utils import OperationalError
# Import BaseCommand class so we can build our custom Command class
from django.core.management.base import BaseCommand


# Convention is to create new Command class inheriting from BaseCommand
class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    # Add handle() that is ran when we run this management command
    # Can pass custom args and options to management command
    def handle(self, *args, **options):
        # print screen to user
        self.stdout.write("Waiting for database...")
        db_conn = None
        while not db_conn:
            try:
                db_conn = connections['default']
            except OperationalError:
                self.stdout.write("Database unavailable. Waiting 1 second...")
                time.sleep(1)

        # Print a success message once database is available. SUCCESS is green
        self.stdout.write(self.style.SUCCESS('Database available!'))
