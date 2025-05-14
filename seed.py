import os
import sys
import django
import random
import time
import base64
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
from faker import Faker
import shutil

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms_project.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

# Import models after Django setup
from django.contrib.auth.models import User
from core.models import UserProfile
from weddings.models import Wedding, WeddingTeam, WeddingEvent, WeddingTheme
from guests.models import Guest, GuestCredential, Invitation
from tasks.models import Task, TaskComment, Checklist, ChecklistItem, Reminder
from gallery.models import MediaCategory, Media, MediaComment, MediaLike

# Initialize Faker
fake = Faker()

def generate_simple_password():
    """Generate a simple password for demo purposes"""
    return f"{fake.word()}{random.randint(100, 999)}"

def generate_qr_code(url):
    """Generate a QR code for the given URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer

def reset_database(preserve_users=True):
    """Reset the database by removing all data but keeping the structure

    Args:
        preserve_users (bool): If True, User and UserProfile data will be preserved
    """
    print("Resetting database...")

    # Clear all data from models in reverse order of dependencies
    with transaction.atomic():
        print("  Clearing MediaLike data...")
        MediaLike.objects.all().delete()

        print("  Clearing MediaComment data...")
        MediaComment.objects.all().delete()

        print("  Clearing Media data...")
        Media.objects.all().delete()

        print("  Clearing MediaCategory data...")
        MediaCategory.objects.all().delete()

        print("  Clearing Reminder data...")
        Reminder.objects.all().delete()

        print("  Clearing ChecklistItem data...")
        ChecklistItem.objects.all().delete()

        print("  Clearing Checklist data...")
        Checklist.objects.all().delete()

        print("  Clearing TaskComment data...")
        TaskComment.objects.all().delete()

        print("  Clearing Task data...")
        Task.objects.all().delete()

        print("  Clearing Invitation data...")
        Invitation.objects.all().delete()

        print("  Clearing GuestCredential data...")
        GuestCredential.objects.all().delete()

        print("  Clearing Guest data...")
        Guest.objects.all().delete()

        print("  Clearing WeddingTheme data...")
        WeddingTheme.objects.all().delete()

        print("  Clearing WeddingEvent data...")
        WeddingEvent.objects.all().delete()

        print("  Clearing WeddingTeam data...")
        WeddingTeam.objects.all().delete()

        print("  Clearing Wedding data...")
        Wedding.objects.all().delete()

        # Only clear User and UserProfile data if preserve_users is False
        if not preserve_users:
            print("  Clearing UserProfile data...")
            UserProfile.objects.all().delete()

            print("  Clearing non-superuser User data...")
            User.objects.filter(is_superuser=False).delete()
        else:
            print("  Preserving User and UserProfile data as requested...")

    # Clear media files
    media_dirs = ['media/wedding_media/', 'media/qr_codes/']
    for directory in media_dirs:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

    print("Database reset complete.")

def create_users():
    """Create admin, team members, and guest users"""
    print("Creating users...")

    # Create admin users (3) with Bangladeshi names
    admin_users = []
    admin_data = [
        {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'admin123',
            'first_name': 'Ashraf',
            'last_name': 'Rahman',
            'phone': '123-456-7890',
            'address': '123 Admin St, Dhaka, Bangladesh'
        },
        {
            'username': 'farhana',
            'email': 'farhana@weddingplanner.com',
            'password': 'admin123',
            'first_name': 'Farhana',
            'last_name': 'Akter',
            'phone': '123-456-7891',
            'address': '456 Planner Ave, Chittagong, Bangladesh'
        },
        {
            'username': 'mahbub',
            'email': 'mahbub@weddingplanner.com',
            'password': 'admin123',
            'first_name': 'Mahbub',
            'last_name': 'Hossain',
            'phone': '123-456-7892',
            'address': '789 Event Blvd, Sylhet, Bangladesh'
        }
    ]

    print("Creating admin users...")
    with transaction.atomic():
        for data in admin_data:
            try:
                # Check if user already exists
                user, created = User.objects.get_or_create(
                    username=data['username'],
                    defaults={
                        'email': data['email'],
                        'first_name': data['first_name'],
                        'last_name': data['last_name'],
                        'is_staff': True
                    }
                )

                if created:
                    user.set_password(data['password'])
                    user.save()
                    print(f"  ✓ Created admin user: {data['username']}")
                else:
                    print(f"  ⚠ Admin user {data['username']} already exists")

                # Create or update profile
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'admin',
                        'phone': data['phone'],
                        'address': data['address']
                    }
                )

                # Update profile data if it already exists
                if not profile_created:
                    profile.role = 'admin'
                    profile.phone = data['phone']
                    profile.address = data['address']
                    profile.save()
                    print(f"  ✓ Updated profile for {data['username']}")
                else:
                    print(f"  ✓ Created profile for {data['username']}")

                admin_users.append(user)
            except Exception as e:
                print(f"  ✗ Error creating admin user {data['username']}: {str(e)}")

    # Create team members (10)
    team_members = []
    print("Creating team members...")
    total_team_members = 10

    with transaction.atomic():
        for i in range(1, total_team_members + 1):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f'team{i}'
            email = f'{first_name.lower()}.{last_name.lower()}@weddingteam.com'
            password = 'team123'

            try:
                # Check if user already exists
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name
                    }
                )

                if created:
                    user.set_password(password)
                    user.save()
                    print(f"  ✓ Created team member: {username}")
                else:
                    print(f"  ⚠ Team member {username} already exists")

                # Create or update profile
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'team_member',
                        'phone': fake.phone_number(),
                        'address': fake.address().replace('\n', ', ')
                    }
                )

                # Update profile data if it already exists
                if not profile_created:
                    profile.role = 'team_member'
                    # Only update phone and address if they're empty
                    if not profile.phone:
                        profile.phone = fake.phone_number()
                    if not profile.address:
                        profile.address = fake.address().replace('\n', ', ')
                    profile.save()
                    print(f"  ✓ Updated profile for {username}")
                else:
                    print(f"  ✓ Created profile for {username}")

                team_members.append(user)
            except Exception as e:
                print(f"  ✗ Error creating team member {username}: {str(e)}")

    # Create guest users (20)
    guest_users = []
    print("Creating guest users...")
    total_guests = 20

    with transaction.atomic():
        for i in range(1, total_guests + 1):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f'guest{i}'
            email = f'{first_name.lower()}.{last_name.lower()}@example.com'
            password = 'guest123'

            try:
                # Check if user already exists
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name
                    }
                )

                if created:
                    user.set_password(password)
                    user.save()
                    print(f"  ✓ Created guest user: {username}")
                else:
                    print(f"  ⚠ Guest user {username} already exists")

                # Create or update profile
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'guest',
                        'phone': fake.phone_number(),
                        'address': fake.address().replace('\n', ', ')
                    }
                )

                # Update profile data if it already exists
                if not profile_created:
                    profile.role = 'guest'
                    # Only update phone and address if they're empty
                    if not profile.phone:
                        profile.phone = fake.phone_number()
                    if not profile.address:
                        profile.address = fake.address().replace('\n', ', ')
                    profile.save()
                    print(f"  ✓ Updated profile for {username}")
                else:
                    print(f"  ✓ Created profile for {username}")

                guest_users.append(user)
            except Exception as e:
                print(f"  ✗ Error creating guest user {username}: {str(e)}")

    print(f"Created {len(admin_users)} admin users")
    print(f"Created {len(team_members)} team members")
    print(f"Created {len(guest_users)} guest users")

    return {
        'admins': admin_users,
        'team_members': team_members,
        'guests': guest_users
    }

def create_weddings(users):
    """Create weddings with related data"""
    print("Creating weddings...")

    # Create 10 weddings with different statuses using Bangladeshi names
    weddings = []
    wedding_data = [
        {
            'title': 'Tasnim & Farhan\'s Wedding',
            'description': 'A beautiful garden wedding with close family and friends',
            'bride_name': 'Tasnim Rahman',
            'groom_name': 'Farhan Ahmed',
            'date': timezone.now().date() + timedelta(days=30),
            'time': datetime.strptime('16:00', '%H:%M').time(),
            'location': 'Botanical Gardens',
            'address': '123 Garden Way, Dhaka, Bangladesh',
            'status': 'upcoming',
            'admin': users['admins'][0]
        },
        {
            'title': 'Nusrat & Tanvir\'s Wedding',
            'description': 'An elegant beachside ceremony',
            'bride_name': 'Nusrat Jahan',
            'groom_name': 'Tanvir Hossain',
            'date': timezone.now().date() + timedelta(days=60),
            'time': datetime.strptime('17:30', '%H:%M').time(),
            'location': 'Cox\'s Bazar Beach Resort',
            'address': '456 Shoreline Drive, Cox\'s Bazar, Bangladesh',
            'status': 'planning',
            'admin': users['admins'][1]
        },
        {
            'title': 'Sabrina & Rafiq\'s Wedding',
            'description': 'A traditional ceremony with modern touches',
            'bride_name': 'Sabrina Akter',
            'groom_name': 'Rafiq Islam',
            'date': timezone.now().date() - timedelta(days=15),
            'time': datetime.strptime('15:00', '%H:%M').time(),
            'location': 'Grand Ballroom',
            'address': '789 Elegant Avenue, Chittagong, Bangladesh',
            'status': 'completed',
            'admin': users['admins'][2]
        },
        {
            'title': 'Fariha & Imran\'s Wedding',
            'description': 'A rustic countryside celebration',
            'bride_name': 'Fariha Karim',
            'groom_name': 'Imran Mahmud',
            'date': timezone.now().date() + timedelta(days=7),
            'time': datetime.strptime('14:00', '%H:%M').time(),
            'location': 'Rustic Barn Venue',
            'address': '101 Countryside Lane, Sylhet, Bangladesh',
            'status': 'in_progress',
            'admin': users['admins'][0]
        },
        {
            'title': 'Lamia & Samin\'s Wedding',
            'description': 'An intimate mountain retreat ceremony',
            'bride_name': 'Lamia Begum',
            'groom_name': 'Samin Khan',
            'date': timezone.now().date() + timedelta(days=90),
            'time': datetime.strptime('16:30', '%H:%M').time(),
            'location': 'Mountain View Lodge',
            'address': '202 Summit Road, Bandarban, Bangladesh',
            'status': 'planning',
            'admin': users['admins'][1]
        },
        {
            'title': 'Tasneem & Naveed\'s Wedding',
            'description': 'A luxurious vineyard wedding with traditional food',
            'bride_name': 'Tasneem Chowdhury',
            'groom_name': 'Naveed Rahman',
            'date': timezone.now().date() + timedelta(days=45),
            'time': datetime.strptime('15:30', '%H:%M').time(),
            'location': 'Sunset Estate',
            'address': '300 Garden Lane, Rajshahi, Bangladesh',
            'status': 'upcoming',
            'admin': users['admins'][2]
        },
        {
            'title': 'Ishrat & Zahid\'s Wedding',
            'description': 'A glamorous city rooftop celebration',
            'bride_name': 'Ishrat Zaman',
            'groom_name': 'Zahid Hasan',
            'date': timezone.now().date() + timedelta(days=120),
            'time': datetime.strptime('18:00', '%H:%M').time(),
            'location': 'Skyline Rooftop Venue',
            'address': '500 Downtown Avenue, Dhaka, Bangladesh',
            'status': 'planning',
            'admin': users['admins'][0]
        },
        {
            'title': 'Samira & Adnan\'s Wedding',
            'description': 'A charming historic library wedding',
            'bride_name': 'Samira Islam',
            'groom_name': 'Adnan Siddique',
            'date': timezone.now().date() - timedelta(days=30),
            'time': datetime.strptime('14:30', '%H:%M').time(),
            'location': 'Heritage Library',
            'address': '700 Book Street, Khulna, Bangladesh',
            'status': 'completed',
            'admin': users['admins'][1]
        },
        {
            'title': 'Raisa & Fahim\'s Wedding',
            'description': 'A bohemian forest wedding with fairy lights',
            'bride_name': 'Raisa Khanam',
            'groom_name': 'Fahim Ahmed',
            'date': timezone.now().date() + timedelta(days=15),
            'time': datetime.strptime('16:00', '%H:%M').time(),
            'location': 'Enchanted Forest Retreat',
            'address': '900 Woodland Path, Rangamati, Bangladesh',
            'status': 'in_progress',
            'admin': users['admins'][2]
        },
        {
            'title': 'Nazia & Rahim\'s Wedding',
            'description': 'A destination beach wedding in paradise',
            'bride_name': 'Nazia Sultana',
            'groom_name': 'Rahim Uddin',
            'date': timezone.now().date() + timedelta(days=75),
            'time': datetime.strptime('17:00', '%H:%M').time(),
            'location': 'Paradise Beach Resort',
            'address': '1100 Ocean Drive, Cox\'s Bazar, Bangladesh',
            'status': 'upcoming',
            'admin': users['admins'][0]
        }
    ]

    print("Creating wedding records...")
    with transaction.atomic():
        for data in wedding_data:
            try:
                wedding = Wedding.objects.create(
                    title=data['title'],
                    description=data['description'],
                    bride_name=data['bride_name'],
                    groom_name=data['groom_name'],
                    date=data['date'],
                    time=data['time'],
                    location=data['location'],
                    address=data['address'],
                    status=data['status'],
                    admin=data['admin']
                )
                weddings.append(wedding)
                print(f"  ✓ Created wedding: {wedding.title}")
            except Exception as e:
                print(f"  ✗ Error creating wedding {data['title']}: {str(e)}")

    print(f"Created {len(weddings)} weddings")
    return weddings

def create_wedding_teams(weddings, users):
    """Create wedding teams for each wedding"""
    print("Creating wedding teams...")

    wedding_teams = []
    team_roles = [
        'Wedding Coordinator', 'Lead Photographer', 'Videographer', 'Floral Designer',
        'Catering Manager', 'Music Director', 'Decor Specialist', 'Makeup Artist',
        'Hair Stylist', 'Event Assistant', 'Lighting Technician', 'Transportation Coordinator',
        'Sweet Maker', 'Imam/Officiant', 'Venue Manager', 'Mehendi Artist', 'Jewelry Coordinator'
    ]

    with transaction.atomic():
        for wedding in weddings:
            # Assign 3-5 team members to each wedding
            num_team_members = random.randint(3, min(5, len(users['team_members'])))
            selected_team_members = random.sample(users['team_members'], num_team_members)

            for i, member in enumerate(selected_team_members):
                role = team_roles[i % len(team_roles)]  # Cycle through roles

                try:
                    team = WeddingTeam.objects.create(
                        wedding=wedding,
                        member=member,
                        role=role
                    )
                    wedding_teams.append(team)
                    print(f"  ✓ Added {member.username} as {role} to {wedding.title}")
                except Exception as e:
                    print(f"  ✗ Error adding team member to {wedding.title}: {str(e)}")

    print(f"Created {len(wedding_teams)} wedding team assignments")
    return wedding_teams

def create_wedding_events(weddings):
    """Create events for each wedding"""
    print("Creating wedding events...")

    wedding_events = []
    event_types = [
        {'name': 'Engagement Party', 'days_before': 90, 'duration': 3},
        {'name': 'Bridal Shower', 'days_before': 30, 'duration': 2},
        {'name': 'Bachelor Party', 'days_before': 14, 'duration': 4},
        {'name': 'Bachelorette Party', 'days_before': 14, 'duration': 4},
        {'name': 'Rehearsal Dinner', 'days_before': 1, 'duration': 2},
        {'name': 'Wedding Ceremony', 'days_before': 0, 'duration': 1},
        {'name': 'Reception', 'days_before': 0, 'duration': 4},
        {'name': 'Post-Wedding Brunch', 'days_before': -1, 'duration': 2}
    ]

    with transaction.atomic():
        for wedding in weddings:
            # Create 3-6 events for each wedding
            num_events = random.randint(3, 6)
            selected_events = random.sample(event_types, num_events)

            for event in selected_events:
                event_date = wedding.date - timedelta(days=event['days_before'])
                start_time = (datetime.combine(datetime.today(), wedding.time) -
                             timedelta(hours=random.randint(0, 2))).time()
                end_time = (datetime.combine(datetime.today(), start_time) +
                           timedelta(hours=event['duration'])).time()

                try:
                    wedding_event = WeddingEvent.objects.create(
                        wedding=wedding,
                        name=event['name'],
                        description=f"{event['name']} for {wedding.bride_name} and {wedding.groom_name}",
                        date=event_date,
                        start_time=start_time,
                        end_time=end_time,
                        location=wedding.location if event['days_before'] == 0 else fake.company(),
                        address=wedding.address if event['days_before'] == 0 else fake.address().replace('\n', ', ')
                    )
                    wedding_events.append(wedding_event)
                    print(f"  ✓ Created event: {event['name']} for {wedding.title}")
                except Exception as e:
                    print(f"  ✗ Error creating event for {wedding.title}: {str(e)}")

    print(f"Created {len(wedding_events)} wedding events")
    return wedding_events

def create_wedding_themes(weddings):
    """Create themes for each wedding"""
    print("Creating wedding themes...")

    wedding_themes = []
    theme_data = [
        {
            'name': 'Rustic Elegance',
            'description': 'A perfect blend of rustic charm and elegant details',
            'color_scheme': 'Burgundy, Navy, and Gold',
            'decoration_notes': 'Wooden elements, fairy lights, and floral arrangements',
            'attire_notes': 'Semi-formal attire with rustic touches'
        },
        {
            'name': 'Beach Paradise',
            'description': 'A relaxed beachside celebration with tropical elements',
            'color_scheme': 'Turquoise, Coral, and White',
            'decoration_notes': 'Seashells, driftwood, and tropical flowers',
            'attire_notes': 'Beach formal attire, light fabrics'
        },
        {
            'name': 'Classic Romance',
            'description': 'Timeless elegance with romantic touches',
            'color_scheme': 'Blush, Ivory, and Silver',
            'decoration_notes': 'Roses, candles, and crystal accents',
            'attire_notes': 'Formal black tie attire'
        },
        {
            'name': 'Garden Whimsy',
            'description': 'A whimsical garden-inspired celebration',
            'color_scheme': 'Lavender, Sage, and Peach',
            'decoration_notes': 'Wildflowers, lanterns, and garden furniture',
            'attire_notes': 'Garden party attire, floral patterns encouraged'
        },
        {
            'name': 'Modern Minimalist',
            'description': 'Clean lines and contemporary style',
            'color_scheme': 'Black, White, and Gold',
            'decoration_notes': 'Geometric shapes, metallic accents, and minimal florals',
            'attire_notes': 'Modern formal attire, sleek silhouettes'
        }
    ]

    with transaction.atomic():
        for i, wedding in enumerate(weddings):
            theme = theme_data[i % len(theme_data)]

            try:
                wedding_theme = WeddingTheme.objects.create(
                    wedding=wedding,
                    name=theme['name'],
                    description=theme['description'],
                    color_scheme=theme['color_scheme'],
                    decoration_notes=theme['decoration_notes'],
                    attire_notes=theme['attire_notes']
                )
                wedding_themes.append(wedding_theme)
                print(f"  ✓ Created theme: {theme['name']} for {wedding.title}")
            except Exception as e:
                print(f"  ✗ Error creating theme for {wedding.title}: {str(e)}")

    print(f"Created {len(wedding_themes)} wedding themes")
    return wedding_themes

def create_guests(weddings, users):
    """Create guests for each wedding with credentials and invitations"""
    print("Creating guests...")

    all_guests = []
    all_credentials = []
    all_invitations = []

    # Create 10-20 guests per wedding
    with transaction.atomic():
        for wedding in weddings:
            print(f"Creating guests for {wedding.title}...")

            # Use some existing users as guests (5 per wedding)
            num_existing_users = min(5, len(users['guests']))
            existing_user_guests = random.sample(users['guests'], num_existing_users)

            # Create additional guests without user accounts
            num_additional_guests = random.randint(5, 15)

            # Process existing users first
            for user in existing_user_guests:
                try:
                    # Create guest record
                    guest = Guest.objects.create(
                        wedding=wedding,
                        user=user,
                        name=f"{user.first_name} {user.last_name}",
                        email=user.email,
                        phone=user.profile.phone if hasattr(user, 'profile') and user.profile.phone else fake.phone_number(),
                        address=user.profile.address if hasattr(user, 'profile') and user.profile.address else fake.address().replace('\n', ', '),
                        status=random.choice(['invited', 'confirmed', 'attended']),
                        invitation_sent=True,
                        invitation_sent_date=timezone.now() - timedelta(days=random.randint(10, 30)),
                        rsvp_date=timezone.now() - timedelta(days=random.randint(1, 9)) if random.random() > 0.3 else None,
                        plus_ones=random.randint(0, 2)
                    )
                    all_guests.append(guest)

                    # Create guest credential
                    expiry_date = wedding.date + timedelta(days=7)  # Expires 7 days after wedding
                    password = generate_simple_password()

                    credential = GuestCredential.objects.create(
                        guest=guest,
                        username=f"guest_{guest.id}",
                        password=password,  # Plain password for email
                        expiry_date=expiry_date
                    )
                    all_credentials.append(credential)

                    # Create invitation
                    invitation = Invitation.objects.create(
                        wedding=wedding,
                        guest=guest,
                        message=f"Dear {guest.name},\n\nYou are cordially invited to the wedding of {wedding.bride_name} and {wedding.groom_name} on {wedding.date.strftime('%B %d, %Y')} at {wedding.time.strftime('%I:%M %p')}.\n\nVenue: {wedding.location}, {wedding.address}\n\nPlease RSVP by {(wedding.date - timedelta(days=14)).strftime('%B %d, %Y')}.\n\nYour login credentials are:\nUsername: {credential.username}\nPassword: {password}\n\nWe look forward to celebrating with you!\n\nWarm regards,\n{wedding.bride_name} & {wedding.groom_name}",
                        viewed=random.random() > 0.3,
                        viewed_date=timezone.now() - timedelta(days=random.randint(1, 5)) if random.random() > 0.3 else None
                    )
                    all_invitations.append(invitation)

                    print(f"  ✓ Created guest from existing user: {guest.name}")
                except Exception as e:
                    print(f"  ✗ Error creating guest from user {user.username}: {str(e)}")

            # Create additional guests with realistic Bangladeshi names
            # List of realistic Bangladeshi guest names
            realistic_guest_names = [
                ('Abul', 'Kalam'), ('Fatima', 'Begum'), ('Mohammad', 'Rahman'), ('Nasreen', 'Akter'),
                ('Kamal', 'Hossain'), ('Taslima', 'Khatun'), ('Rafiqul', 'Islam'), ('Farzana', 'Yasmin'),
                ('Anwar', 'Hussain'), ('Nargis', 'Sultana'), ('Jahangir', 'Alam'), ('Shahnaz', 'Parvin'),
                ('Masud', 'Khan'), ('Salma', 'Jahan'), ('Nurul', 'Haque'), ('Rabeya', 'Khanam'),
                ('Shahid', 'Ahmed'), ('Nasima', 'Chowdhury'), ('Jamal', 'Uddin'), ('Amina', 'Begum'),
                ('Farid', 'Miah'), ('Roksana', 'Akhter'), ('Shafiqul', 'Islam'), ('Monowara', 'Khatun'),
                ('Rahim', 'Molla'), ('Farida', 'Yasmin'), ('Azad', 'Hossain'), ('Rahima', 'Begum'),
                ('Mofiz', 'Uddin'), ('Shamsun', 'Nahar'), ('Habib', 'Rahman'), ('Nazma', 'Akter'),
                ('Abdur', 'Rahim'), ('Hosne', 'Ara'), ('Mominul', 'Haque'), ('Sharmin', 'Sultana'),
                ('Zakir', 'Hussain'), ('Mahmuda', 'Khatun'), ('Aminul', 'Islam'), ('Nasrin', 'Jahan'),
                ('Shamsul', 'Huda'), ('Sabina', 'Yasmin'), ('Mostafa', 'Kamal'), ('Parvin', 'Akter'),
                ('Siraj', 'Miah'), ('Runa', 'Laila'), ('Saiful', 'Islam'), ('Shahana', 'Begum'),
                ('Jalal', 'Uddin'), ('Rokeya', 'Khanam'), ('Liton', 'Ahmed'), ('Sanjida', 'Hossain'),
                ('Rubel', 'Miah'), ('Shirin', 'Akter'), ('Shahin', 'Alam'), ('Razia', 'Sultana'),
                ('Monir', 'Hossain'), ('Ferdousi', 'Begum'), ('Jahirul', 'Islam'), ('Sumaiya', 'Khatun'),
                ('Sohel', 'Rana'), ('Tania', 'Ahmed'), ('Mamun', 'Khan'), ('Sadia', 'Jahan'),
                ('Imran', 'Hossain'), ('Munni', 'Akter'), ('Arif', 'Rahman'), ('Shila', 'Khanam'),
                ('Mizan', 'Miah'), ('Ruma', 'Begum'), ('Shahadat', 'Hossain'), ('Mitu', 'Akter'),
                ('Ripon', 'Ahmed'), ('Poly', 'Khatun'), ('Masum', 'Billah'), ('Ratna', 'Begum'),
                ('Shamim', 'Reza'), ('Lovely', 'Akter'), ('Mahbub', 'Alam'), ('Roksana', 'Parvin'),
                ('Selim', 'Reza'), ('Mina', 'Khatun'), ('Jashim', 'Uddin'), ('Mukta', 'Begum'),
                ('Rashed', 'Khan'), ('Shumi', 'Akter'), ('Helal', 'Uddin'), ('Reshma', 'Khatun'),
                ('Jewel', 'Rana'), ('Marzina', 'Begum'), ('Sohag', 'Hossain'), ('Lipi', 'Akter'),
                ('Rasel', 'Miah'), ('Moni', 'Begum'), ('Sumon', 'Ahmed'), ('Ripa', 'Khatun'),
                ('Sajib', 'Hossain'), ('Sumi', 'Akter'), ('Rony', 'Khan'), ('Mita', 'Begum'),
                ('Babu', 'Miah'), ('Shilpi', 'Akter'), ('Saidul', 'Islam'), ('Runa', 'Begum')
            ]

            # Shuffle the list to get random names
            random.shuffle(realistic_guest_names)

            for i in range(num_additional_guests):
                try:
                    # Get a name from the list or generate one if we run out
                    if i < len(realistic_guest_names):
                        first_name, last_name = realistic_guest_names[i]
                    else:
                        first_name = fake.first_name()
                        last_name = fake.last_name()

                    email = f"{first_name.lower()}.{last_name.lower()}@example.com"

                    # Create guest record
                    guest = Guest.objects.create(
                        wedding=wedding,
                        user=None,  # No user account
                        name=f"{first_name} {last_name}",
                        email=email,
                        phone=fake.phone_number(),
                        address=fake.address().replace('\n', ', '),
                        status=random.choice(['invited', 'confirmed', 'declined', 'attended', 'no_show']),
                        invitation_sent=True,
                        invitation_sent_date=timezone.now() - timedelta(days=random.randint(10, 30)),
                        rsvp_date=timezone.now() - timedelta(days=random.randint(1, 9)) if random.random() > 0.3 else None,
                        plus_ones=random.randint(0, 2)
                    )
                    all_guests.append(guest)

                    # Create guest credential
                    expiry_date = wedding.date + timedelta(days=7)  # Expires 7 days after wedding
                    password = generate_simple_password()

                    credential = GuestCredential.objects.create(
                        guest=guest,
                        username=f"guest_{guest.id}",
                        password=password,  # Plain password for email
                        expiry_date=expiry_date
                    )
                    all_credentials.append(credential)

                    # Create invitation
                    invitation = Invitation.objects.create(
                        wedding=wedding,
                        guest=guest,
                        message=f"Dear {guest.name},\n\nYou are cordially invited to the wedding of {wedding.bride_name} and {wedding.groom_name} on {wedding.date.strftime('%B %d, %Y')} at {wedding.time.strftime('%I:%M %p')}.\n\nVenue: {wedding.location}, {wedding.address}\n\nPlease RSVP by {(wedding.date - timedelta(days=14)).strftime('%B %d, %Y')}.\n\nYour login credentials are:\nUsername: {credential.username}\nPassword: {password}\n\nWe look forward to celebrating with you!\n\nWarm regards,\n{wedding.bride_name} & {wedding.groom_name}",
                        viewed=random.random() > 0.3,
                        viewed_date=timezone.now() - timedelta(days=random.randint(1, 5)) if random.random() > 0.3 else None
                    )
                    all_invitations.append(invitation)

                    print(f"  ✓ Created guest: {guest.name}")
                except Exception as e:
                    print(f"  ✗ Error creating guest {first_name} {last_name}: {str(e)}")

    print(f"Created {len(all_guests)} guests")
    print(f"Created {len(all_credentials)} guest credentials")
    print(f"Created {len(all_invitations)} invitations")

    return {
        'guests': all_guests,
        'credentials': all_credentials,
        'invitations': all_invitations
    }

def create_tasks(weddings, users):
    """Create tasks, task comments, checklists, and reminders"""
    print("Creating tasks and related items...")

    all_tasks = []
    all_task_comments = []
    all_checklists = []
    all_checklist_items = []
    all_reminders = []

    # Task templates for each wedding
    task_templates = [
        {'title': 'Book Venue', 'priority': 'high', 'days_before': 180},
        {'title': 'Hire Photographer', 'priority': 'high', 'days_before': 150},
        {'title': 'Hire Videographer', 'priority': 'medium', 'days_before': 150},
        {'title': 'Book Caterer', 'priority': 'high', 'days_before': 120},
        {'title': 'Order Wedding Cake', 'priority': 'medium', 'days_before': 90},
        {'title': 'Book Florist', 'priority': 'medium', 'days_before': 90},
        {'title': 'Hire DJ/Band', 'priority': 'medium', 'days_before': 90},
        {'title': 'Order Invitations', 'priority': 'high', 'days_before': 90},
        {'title': 'Shop for Wedding Dress', 'priority': 'high', 'days_before': 180},
        {'title': 'Shop for Groom\'s Attire', 'priority': 'high', 'days_before': 120},
        {'title': 'Choose Bridesmaids Dresses', 'priority': 'medium', 'days_before': 120},
        {'title': 'Choose Groomsmen Attire', 'priority': 'medium', 'days_before': 120},
        {'title': 'Book Honeymoon', 'priority': 'high', 'days_before': 180},
        {'title': 'Send Save-the-Dates', 'priority': 'high', 'days_before': 180},
        {'title': 'Send Invitations', 'priority': 'high', 'days_before': 60},
        {'title': 'Create Wedding Website', 'priority': 'low', 'days_before': 180},
        {'title': 'Finalize Menu', 'priority': 'medium', 'days_before': 60},
        {'title': 'Create Seating Chart', 'priority': 'medium', 'days_before': 30},
        {'title': 'Write Vows', 'priority': 'high', 'days_before': 30},
        {'title': 'Pick Up Wedding Rings', 'priority': 'high', 'days_before': 14},
        {'title': 'Final Dress Fitting', 'priority': 'high', 'days_before': 14},
        {'title': 'Confirm All Vendors', 'priority': 'high', 'days_before': 7},
        {'title': 'Pack for Honeymoon', 'priority': 'medium', 'days_before': 3},
        {'title': 'Prepare Wedding Day Emergency Kit', 'priority': 'low', 'days_before': 7}
    ]

    # Checklist templates
    checklist_templates = [
        {
            'title': 'Venue Checklist',
            'items': [
                'Confirm date and time',
                'Pay deposit',
                'Review contract',
                'Discuss layout and setup',
                'Confirm parking arrangements',
                'Check lighting and sound options',
                'Discuss decoration restrictions'
            ]
        },
        {
            'title': 'Photography Checklist',
            'items': [
                'Create shot list',
                'Discuss must-have photos',
                'Schedule engagement photos',
                'Confirm timeline for wedding day',
                'Discuss backup plans for bad weather',
                'Review photo album options',
                'Discuss post-processing preferences'
            ]
        },
        {
            'title': 'Catering Checklist',
            'items': [
                'Schedule tasting',
                'Select menu options',
                'Discuss dietary restrictions',
                'Confirm staff count',
                'Discuss bar service options',
                'Confirm cake cutting service',
                'Discuss leftover food policy'
            ]
        },
        {
            'title': 'Wedding Day Checklist',
            'items': [
                'Prepare emergency kit',
                'Pack wedding attire and accessories',
                'Confirm transportation',
                'Distribute timeline to wedding party',
                'Assign someone to collect gifts',
                'Confirm payment for vendors',
                'Pack honeymoon luggage'
            ]
        }
    ]

    with transaction.atomic():
        for wedding in weddings:
            print(f"Creating tasks for {wedding.title}...")

            # Get team members for this wedding
            team_members = [team.member for team in WeddingTeam.objects.filter(wedding=wedding)]
            if not team_members:
                team_members = [wedding.admin]  # Fallback to admin if no team members

            # Create 10-15 tasks per wedding
            num_tasks = random.randint(10, min(15, len(task_templates)))
            selected_tasks = random.sample(task_templates, num_tasks)

            for task_template in selected_tasks:
                try:
                    # Calculate due date based on wedding date
                    due_date = wedding.date - timedelta(days=task_template['days_before'])

                    # Determine status based on due date
                    if due_date < timezone.now().date() - timedelta(days=7):
                        status = 'completed'
                        completion_date = due_date + timedelta(days=random.randint(1, 5))
                    elif due_date < timezone.now().date():
                        status = random.choice(['completed', 'in_progress'])
                        completion_date = timezone.now() if status == 'completed' else None
                    else:
                        status = random.choice(['pending', 'in_progress'])
                        completion_date = None

                    # Assign to random team member
                    assigned_to = random.choice(team_members)

                    task = Task.objects.create(
                        wedding=wedding,
                        title=task_template['title'],
                        description=f"Task: {task_template['title']} for {wedding.bride_name} and {wedding.groom_name}'s wedding",
                        assigned_to=assigned_to,
                        created_by=wedding.admin,
                        due_date=due_date,
                        priority=task_template['priority'],
                        status=status,
                        completion_date=completion_date
                    )
                    all_tasks.append(task)

                    # Add 1-3 comments per task
                    num_comments = random.randint(1, 3)
                    for _ in range(num_comments):
                        comment_user = random.choice(team_members + [wedding.admin])
                        comment = TaskComment.objects.create(
                            task=task,
                            user=comment_user,
                            comment=fake.paragraph()
                        )
                        all_task_comments.append(comment)

                    # Create reminder for task
                    if random.random() > 0.3:  # 70% chance of having a reminder
                        reminder_date = due_date - timedelta(days=random.randint(1, 7))
                        reminder = Reminder.objects.create(
                            wedding=wedding,
                            title=f"Reminder: {task.title}",
                            description=f"Don't forget to complete the task: {task.title}",
                            reminder_type='task',
                            reminder_date=datetime.combine(reminder_date, datetime.strptime('09:00', '%H:%M').time()),
                            task=task,
                            is_sent=reminder_date < timezone.now().date(),
                            sent_date=timezone.now() if reminder_date < timezone.now().date() else None
                        )
                        all_reminders.append(reminder)

                    print(f"  ✓ Created task: {task.title}")
                except Exception as e:
                    print(f"  ✗ Error creating task {task_template['title']}: {str(e)}")

            # Create 2-4 checklists per wedding
            num_checklists = random.randint(2, min(4, len(checklist_templates)))
            selected_checklists = random.sample(checklist_templates, num_checklists)

            for checklist_template in selected_checklists:
                try:
                    checklist = Checklist.objects.create(
                        title=f"{checklist_template['title']} for {wedding.bride_name} & {wedding.groom_name}",
                        description=f"Checklist for {wedding.title}",
                        is_template=False,
                        wedding=wedding,
                        created_by=wedding.admin
                    )
                    all_checklists.append(checklist)

                    # Add items to checklist
                    for item_title in checklist_template['items']:
                        due_date = wedding.date - timedelta(days=random.randint(7, 60))
                        is_completed = random.random() > 0.5 and due_date < timezone.now().date()
                        completed_by = random.choice(team_members) if is_completed else None
                        completed_date = timezone.now() if is_completed else None

                        item = ChecklistItem.objects.create(
                            checklist=checklist,
                            title=item_title,
                            description=f"Checklist item: {item_title}",
                            due_date=due_date,
                            is_completed=is_completed,
                            completed_date=completed_date,
                            completed_by=completed_by
                        )
                        all_checklist_items.append(item)

                        # Create reminder for checklist item
                        if random.random() > 0.5:  # 50% chance of having a reminder
                            reminder_date = due_date - timedelta(days=random.randint(1, 5))
                            reminder = Reminder.objects.create(
                                wedding=wedding,
                                title=f"Reminder: {item.title}",
                                description=f"Don't forget to complete the checklist item: {item.title}",
                                reminder_type='checklist',
                                reminder_date=datetime.combine(reminder_date, datetime.strptime('10:00', '%H:%M').time()),
                                checklist_item=item,
                                is_sent=reminder_date < timezone.now().date(),
                                sent_date=timezone.now() if reminder_date < timezone.now().date() else None
                            )
                            all_reminders.append(reminder)

                    print(f"  ✓ Created checklist: {checklist.title} with {len(checklist_template['items'])} items")
                except Exception as e:
                    print(f"  ✗ Error creating checklist {checklist_template['title']}: {str(e)}")

    print(f"Created {len(all_tasks)} tasks")
    print(f"Created {len(all_task_comments)} task comments")
    print(f"Created {len(all_checklists)} checklists")
    print(f"Created {len(all_checklist_items)} checklist items")
    print(f"Created {len(all_reminders)} reminders")

    return {
        'tasks': all_tasks,
        'comments': all_task_comments,
        'checklists': all_checklists,
        'checklist_items': all_checklist_items,
        'reminders': all_reminders
    }

def create_media(weddings, users):
    """Create media categories and items"""
    print("Creating media categories and items...")

    # Import PIL for image generation
    from PIL import Image, ImageDraw, ImageFont
    import os
    from django.conf import settings
    from django.core.files.base import ContentFile
    from io import BytesIO

    all_categories = []
    all_media = []
    all_comments = []
    all_likes = []

    # Ensure media directories exist
    media_dir = os.path.join(settings.MEDIA_ROOT, 'wedding_media')
    thumbnails_dir = os.path.join(settings.MEDIA_ROOT, 'wedding_media', 'thumbnails')

    os.makedirs(media_dir, exist_ok=True)
    os.makedirs(thumbnails_dir, exist_ok=True)

    # Wedding-themed colors for placeholder images
    wedding_colors = [
        (255, 192, 203),  # Pink
        (255, 218, 185),  # Peach
        (230, 230, 250),  # Lavender
        (240, 248, 255),  # Alice Blue
        (255, 250, 205),  # Lemon Chiffon
        (255, 228, 225),  # Misty Rose
        (245, 255, 250),  # Mint Cream
        (255, 240, 245),  # Lavender Blush
        (250, 235, 215),  # Antique White
        (255, 222, 173),  # Navajo White
    ]

    # Media category templates
    category_templates = [
        {'name': 'Engagement Photos', 'description': 'Photos from the engagement session'},
        {'name': 'Pre-Wedding', 'description': 'Photos taken before the wedding day'},
        {'name': 'Ceremony', 'description': 'Photos from the wedding ceremony'},
        {'name': 'Reception', 'description': 'Photos from the wedding reception'},
        {'name': 'Family Portraits', 'description': 'Formal family portraits'},
        {'name': 'Couple Portraits', 'description': 'Romantic portraits of the couple'},
        {'name': 'Wedding Party', 'description': 'Photos with bridesmaids and groomsmen'},
        {'name': 'Details', 'description': 'Close-ups of wedding details and decorations'},
        {'name': 'Guests', 'description': 'Candid photos of wedding guests'}
    ]

    # Function to create a plain placeholder image
    def create_placeholder_image(width, height, category_name, image_number, wedding_title, color):
        # Create a new image with the given color
        image = Image.new('RGB', (width, height), color)
        draw = ImageDraw.Draw(image)

        # Create fonts with larger sizes
        try:
            # Try to use a system font
            title_font = ImageFont.truetype("arial.ttf", 48)
            subtitle_font = ImageFont.truetype("arial.ttf", 36)
        except IOError:
            try:
                # Linux: Fallback to DejaVuSans
                fallback_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                title_font = ImageFont.truetype(fallback_path, 48)
                subtitle_font = ImageFont.truetype(fallback_path, 36)
                print(f"Using fallback font: {fallback_path}")
            except IOError:
                # Fallback to default font if system font not available
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()

        # Add text
        text_color = (50, 50, 50)  # Darker gray text for better contrast

        # Draw category name at the top
        draw.text((width//2, height//4), category_name, fill=text_color, font=title_font, anchor="mm")

        # Draw image number in the middle
        draw.text((width//2, height//2), f"Image {image_number}", fill=text_color, font=subtitle_font, anchor="mm")

        # Draw wedding title at the bottom
        draw.text((width//2, 3*height//4), wedding_title, fill=text_color, font=subtitle_font, anchor="mm")

        return image

    with transaction.atomic():
        for wedding in weddings:
            print(f"Creating media for {wedding.title}...")

            # Create 3-5 categories per wedding
            num_categories = random.randint(3, min(5, len(category_templates)))
            selected_categories = random.sample(category_templates, num_categories)

            for category_template in selected_categories:
                try:
                    category = MediaCategory.objects.create(
                        wedding=wedding,
                        name=category_template['name'],
                        description=category_template['description']
                    )
                    all_categories.append(category)

                    # Create 5-10 media items per category
                    num_media_items = random.randint(5, 10)

                    for i in range(num_media_items):
                        # Determine uploader (admin, team member, or guest)
                        uploader_type = random.choice(['admin', 'team', 'guest'])
                        if uploader_type == 'admin':
                            uploader = wedding.admin
                        elif uploader_type == 'team':
                            team_members = [team.member for team in WeddingTeam.objects.filter(wedding=wedding)]
                            uploader = random.choice(team_members) if team_members else wedding.admin
                        else:
                            guests_with_users = Guest.objects.filter(wedding=wedding, user__isnull=False)
                            if guests_with_users.exists():
                                guest = random.choice(guests_with_users)
                                uploader = guest.user
                            else:
                                uploader = wedding.admin

                        # Generate a unique filename
                        filename = f"wedding_{wedding.id}_category_{category.id}_image_{i+1}.jpg"

                        # Create a placeholder image
                        color = random.choice(wedding_colors)
                        img = create_placeholder_image(
                            800, 600,
                            category.name,
                            i+1,
                            wedding.title,
                            color
                        )

                        # Save the image to a BytesIO object
                        img_io = BytesIO()
                        img.save(img_io, format='JPEG', quality=85)
                        img_io.seek(0)

                        # Create the media object with the image
                        media = Media(
                            wedding=wedding,
                            category=category,
                            title=f"{category.name} - Image {i+1}",
                            description=f"Image {i+1} in the {category.name} category",
                            media_type='photo',  # All demo items are photos
                            uploaded_by=uploader,
                            is_featured=random.random() > 0.8,  # 20% chance of being featured
                            is_private=random.random() > 0.9  # 10% chance of being private
                        )

                        # Save the image to the file field
                        media.file.save(filename, ContentFile(img_io.getvalue()), save=False)

                        # Create a thumbnail (smaller version of the same image)
                        thumb = img.copy()
                        thumb.thumbnail((300, 300))
                        thumb_io = BytesIO()
                        thumb.save(thumb_io, format='JPEG', quality=85)
                        thumb_io.seek(0)

                        # Save the thumbnail
                        media.thumbnail.save(f"thumb_{filename}", ContentFile(thumb_io.getvalue()), save=False)

                        # Save the media object
                        media.save()
                        all_media.append(media)

                        # Add 0-3 comments per media item
                        num_comments = random.randint(0, 3)
                        if num_comments > 0:
                            # Get potential commenters
                            team_members = [team.member for team in WeddingTeam.objects.filter(wedding=wedding)]
                            guests_with_users = [guest.user for guest in Guest.objects.filter(wedding=wedding, user__isnull=False)]
                            potential_commenters = [wedding.admin] + team_members + guests_with_users

                            for _ in range(num_comments):
                                commenter = random.choice(potential_commenters)
                                comment = MediaComment.objects.create(
                                    media=media,
                                    user=commenter,
                                    comment=fake.sentence()
                                )
                                all_comments.append(comment)

                        # Add 0-5 likes per media item
                        num_likes = random.randint(0, 5)
                        if num_likes > 0:
                            # Get potential likers
                            team_members = [team.member for team in WeddingTeam.objects.filter(wedding=wedding)]
                            guests_with_users = [guest.user for guest in Guest.objects.filter(wedding=wedding, user__isnull=False)]
                            potential_likers = [wedding.admin] + team_members + guests_with_users

                            # Ensure we don't try to add more likes than available users
                            num_likes = min(num_likes, len(potential_likers))
                            likers = random.sample(potential_likers, num_likes)

                            for liker in likers:
                                try:
                                    like = MediaLike.objects.create(
                                        media=media,
                                        user=liker
                                    )
                                    all_likes.append(like)
                                except Exception as e:
                                    # Silently handle duplicate likes
                                    pass

                    print(f"  ✓ Created category: {category.name} with {num_media_items} media items")
                except Exception as e:
                    print(f"  ✗ Error creating media category {category_template['name']}: {str(e)}")

    print(f"Created {len(all_categories)} media categories")
    print(f"Created {len(all_media)} media items")
    print(f"Created {len(all_comments)} media comments")
    print(f"Created {len(all_likes)} media likes")

    return {
        'categories': all_categories,
        'media_items': all_media,
        'comments': all_comments,
        'likes': all_likes
    }

def seed_database(preserve_users=True):
    """Main function to seed the database with comprehensive data

    Args:
        preserve_users (bool): If True, existing users will be preserved
    """
    start_time = time.time()

    print("Starting comprehensive database seeding process...")
    print("This will create a complete set of data for demonstration purposes.")
    print("The process may take a few minutes to complete.")

    # Step 1: Reset the database (clear all data except users if preserve_users=True)
    reset_database(preserve_users=preserve_users)

    # Step 2: Create users (will skip existing users if they already exist)
    users = create_users()

    # Step 3: Create weddings
    weddings = create_weddings(users)

    # Step 4: Create wedding teams
    wedding_teams = create_wedding_teams(weddings, users)

    # Step 5: Create wedding events
    wedding_events = create_wedding_events(weddings)

    # Step 6: Create wedding themes
    wedding_themes = create_wedding_themes(weddings)

    # Step 7: Create guests
    guest_data = create_guests(weddings, users)

    # Step 8: Create tasks and checklists
    task_data = create_tasks(weddings, users)

    # Step 9: Create media
    media_data = create_media(weddings, users)

    # Calculate statistics
    total_users = len(users['admins']) + len(users['team_members']) + len(users['guests'])
    total_weddings = len(weddings)
    total_wedding_teams = len(wedding_teams)
    total_wedding_events = len(wedding_events)
    total_wedding_themes = len(wedding_themes)
    total_guests = len(guest_data['guests'])
    total_credentials = len(guest_data['credentials'])
    total_invitations = len(guest_data['invitations'])
    total_tasks = len(task_data['tasks'])
    total_task_comments = len(task_data['comments'])
    total_checklists = len(task_data['checklists'])
    total_checklist_items = len(task_data['checklist_items'])
    total_reminders = len(task_data['reminders'])
    total_media_categories = len(media_data['categories'])
    total_media_items = len(media_data['media_items'])
    total_media_comments = len(media_data['comments'])
    total_media_likes = len(media_data['likes'])

    # Print summary
    print("\n=== Seeding Complete! ===")
    print(f"Total time: {time.time() - start_time:.2f} seconds")
    print("\nData Summary:")
    print(f"- Users: {total_users}")
    print(f"  - Admins: {len(users['admins'])}")
    print(f"  - Team Members: {len(users['team_members'])}")
    print(f"  - Guests: {len(users['guests'])}")
    print(f"- Weddings: {total_weddings}")
    print(f"- Wedding Teams: {total_wedding_teams}")
    print(f"- Wedding Events: {total_wedding_events}")
    print(f"- Wedding Themes: {total_wedding_themes}")
    print(f"- Guests: {total_guests}")
    print(f"- Guest Credentials: {total_credentials}")
    print(f"- Invitations: {total_invitations}")
    print(f"- Tasks: {total_tasks}")
    print(f"- Task Comments: {total_task_comments}")
    print(f"- Checklists: {total_checklists}")
    print(f"- Checklist Items: {total_checklist_items}")
    print(f"- Reminders: {total_reminders}")
    print(f"- Media Categories: {total_media_categories}")
    print(f"- Media Items: {total_media_items}")
    print(f"- Media Comments: {total_media_comments}")
    print(f"- Media Likes: {total_media_likes}")

    print("\nThe system now has enough data to demonstrate all features.")
    print("You can log in with the following credentials:")
    print("- Admin: username='admin', password='admin123'")
    print("- Team Member: username='team1', password='team123'")
    print("- Guest: username='guest1', password='guest123'")

    return {
        'users': users,
        'weddings': weddings,
        'wedding_teams': wedding_teams,
        'wedding_events': wedding_events,
        'wedding_themes': wedding_themes,
        'guests': guest_data,
        'tasks': task_data,
        'media': media_data
    }

if __name__ == "__main__":
    import argparse

    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Seed the database with comprehensive data.')
    parser.add_argument('--preserve-users', action='store_true', default=True,
                        help='Preserve existing users when seeding (default: True)')
    parser.add_argument('--reset-users', action='store_false', dest='preserve_users',
                        help='Reset users when seeding (removes existing users)')

    args = parser.parse_args()

    # Run the seeding process with the specified options
    seed_database(preserve_users=args.preserve_users)
