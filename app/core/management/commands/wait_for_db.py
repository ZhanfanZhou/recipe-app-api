"""
Django command to wait for the database to be established.
"""

import time
from psycopg2 import OperationalError as Psycopg2Error

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to handle waiting for the database established"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')

        db_available = False
        while not db_available:
            try:
                self.check(databases=['default'])
                db_available = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write('Database unavailable, retry for 1s...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available!'))
