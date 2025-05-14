import os
import sys
import django
import shutil

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms_project.settings')

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize Django
django.setup()

def reset_database():
    """Reset the database by removing the db.sqlite3 file and all migrations except __init__.py"""
    print("Resetting database...")

    # Remove the database file
    if os.path.exists('db.sqlite3'):
        os.remove('db.sqlite3')
        print("  ✓ Removed db.sqlite3")

    # Remove migration files except __init__.py
    apps = ['core', 'guests', 'weddings', 'tasks', 'gallery']

    for app in apps:
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            for filename in os.listdir(migrations_dir):
                if filename != '__init__.py' and filename.endswith('.py'):
                    file_path = os.path.join(migrations_dir, filename)
                    os.remove(file_path)
                    print(f"  ✓ Removed migration: {file_path}")

    # Remove __pycache__ directories in migrations folders
    for app in apps:
        pycache_dir = os.path.join(app, 'migrations', '__pycache__')
        if os.path.exists(pycache_dir):
            shutil.rmtree(pycache_dir)
            print(f"  ✓ Removed __pycache__: {pycache_dir}")

    print("Database reset complete.")

def run_migrations():
    """Run makemigrations and migrate commands"""
    print("Running migrations...")

    # Make migrations
    os.system('python manage.py makemigrations')

    # Apply migrations
    os.system('python manage.py migrate')

    print("Migrations complete.")

def seed_data(preserve_users=False):
    """Run the comprehensive seed script

    Args:
        preserve_users (bool): If True, preserve existing users when seeding
    """
    print("Seeding database...")

    # Run the new comprehensive seed script with appropriate options
    print("Running seed.py...")
    if preserve_users:
        os.system('python seed.py --preserve-users')
    else:
        os.system('python seed.py --reset-users')

    print("Database seeding complete.")

if __name__ == "__main__":
    import argparse
    import os

    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Reset and seed the database.')
    parser.add_argument('--preserve-users', action='store_true',
                        help='Preserve existing users when seeding (default: False)')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompt')

    args = parser.parse_args()

    # Check if running on Railway
    on_railway = os.environ.get('RAILWAY', False)

    if args.yes or on_railway:
        confirm = 'y'
    else:
        # Confirm with the user
        confirm = input("This will delete the database and all migrations. Are you sure? (y/n): ")

    if confirm.lower() == 'y':
        # On Railway, we don't want to reset the database, just seed it if it's empty
        if on_railway:
            # Check if database is empty (no users)
            from django.contrib.auth.models import User
            if User.objects.count() == 0:
                print("Running on Railway with empty database. Seeding data...")
                seed_data(preserve_users=False)
                print("Database has been seeded successfully.")
            else:
                print("Database already contains data. Skipping seeding.")
        else:
            # Local development - full reset and seed
            reset_database()
            run_migrations()
            seed_data(preserve_users=args.preserve_users)
            print("Database has been reset and reseeded successfully.")
            if args.preserve_users:
                print("Existing users have been preserved.")
    else:
        print("Operation cancelled.")
