import os
from django.conf import settings
from django.core.management import BaseCommand
from db.management.commands.populate_childes_db_derived import process_childes_db_derived_dirs

#The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = "Populate Peekbank MySQL Database"

    def add_arguments(self, parser):
        parser.add_argument('--data_root', help='Root directory to add to database')
        
        parser.add_argument('--validate_only', help="Only validate and don't upload to the database", action='store_true')

    # A command must define handle()
    def handle(self, *args, **options):
        print('Called populate_db with data_root '+options.get('data_root'))
        
        process_childes_db_derived_dirs(options.get('data_root'), options.get('validate_only'))
