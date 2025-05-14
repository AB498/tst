import os
import django
import datetime
import random
import string
from django.utils import timezone
from django.contrib.auth.models import User

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms_project.settings')
django.setup()

def generate_simple_password(length=8):
    """Generate a simple password for guests"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Import models after Django setup
from core.models import UserProfile
from weddings.models import Wedding, WeddingTeam, WeddingEvent, WeddingTheme
from guests.models import Guest, GuestCredential, Invitation
from tasks.models import Task, TaskComment, Checklist, ChecklistItem, Reminder
from gallery.models import MediaCategory, Media

def clear_data():
    """Clear all data from the database"""
    print("Clearing existing data...")

    # Delete all data in reverse order of dependencies
    MediaCategory.objects.all().delete()
    Reminder.objects.all().delete()
    ChecklistItem.objects.all().delete()
    Checklist.objects.all().delete()
    TaskComment.objects.all().delete()
    Task.objects.all().delete()
    Invitation.objects.all().delete()
    GuestCredential.objects.all().delete()
    Guest.objects.all().delete()
    WeddingTheme.objects.all().delete()
    WeddingEvent.objects.all().delete()
    WeddingTeam.objects.all().delete()
    Wedding.objects.all().delete()
    UserProfile.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()

    print("All data cleared.")

def create_users():
    """Create admin, team members, and guest users"""
    print("Creating users...")

    # Create admin user
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        is_staff=True
    )
    UserProfile.objects.create(
        user=admin_user,
        role='admin',
        phone='123-456-7890',
        address='123 Admin St, Admin City'
    )

    # Create team members
    team_members = []
    for i in range(1, 6):
        team_user = User.objects.create_user(
            username=f'team{i}',
            email=f'team{i}@example.com',
            password='team123',
            first_name=f'Team{i}',
            last_name='Member'
        )
        UserProfile.objects.create(
            user=team_user,
            role='team_member',
            phone=f'123-456-{1000+i}',
            address=f'{i} Team St, Team City'
        )
        team_members.append(team_user)

    # Create guest users
    guest_users = []
    for i in range(1, 11):
        guest_user = User.objects.create_user(
            username=f'guest{i}',
            email=f'guest{i}@example.com',
            password='guest123',
            first_name=f'Guest{i}',
            last_name='User'
        )
        UserProfile.objects.create(
            user=guest_user,
            role='guest',
            phone=f'123-789-{1000+i}',
            address=f'{i} Guest St, Guest City'
        )
        guest_users.append(guest_user)

    return {
        'admin': admin_user,
        'team_members': team_members,
        'guests': guest_users
    }

def create_weddings(admin_user):
    """Create sample weddings"""
    print("Creating weddings...")

    weddings = []

    # Wedding 1 - Upcoming
    wedding1 = Wedding.objects.create(
        title='Rahman-Khan Wedding',
        description='A beautiful traditional Bangladeshi wedding',
        bride_name='Fatima Rahman',
        groom_name='Ahmed Khan',
        date=timezone.now().date() + datetime.timedelta(days=30),
        time=datetime.time(14, 0),  # 2:00 PM
        location='Grand Ballroom',
        address='123 Wedding Ave, Dhaka, Bangladesh',
        status='upcoming',
        admin=admin_user
    )

    # Wedding 2 - In Progress (Today)
    wedding2 = Wedding.objects.create(
        title='Hasan-Ali Wedding',
        description='Elegant wedding with modern touches',
        bride_name='Nusrat Hasan',
        groom_name='Karim Ali',
        date=timezone.now().date(),
        time=datetime.time(16, 0),  # 4:00 PM
        location='Royal Palace',
        address='456 Celebration Rd, Chittagong, Bangladesh',
        status='in_progress',
        admin=admin_user
    )

    # Wedding 3 - Completed
    wedding3 = Wedding.objects.create(
        title='Islam-Ahmed Wedding',
        description='Intimate family wedding',
        bride_name='Taslima Islam',
        groom_name='Rahim Ahmed',
        date=timezone.now().date() - datetime.timedelta(days=15),
        time=datetime.time(15, 0),  # 3:00 PM
        location='Garden Resort',
        address='789 Paradise Ln, Sylhet, Bangladesh',
        status='completed',
        admin=admin_user
    )

    weddings.extend([wedding1, wedding2, wedding3])
    return weddings

def create_wedding_teams(weddings, team_members):
    """Assign team members to weddings"""
    print("Creating wedding teams...")

    wedding_teams = []

    roles = ['Coordinator', 'Photographer', 'Decorator', 'Caterer', 'DJ']

    for wedding in weddings:
        # Assign 2-3 team members to each wedding
        num_members = random.randint(2, 3)
        selected_members = random.sample(team_members, num_members)

        for i, member in enumerate(selected_members):
            team = WeddingTeam.objects.create(
                wedding=wedding,
                member=member,
                role=roles[i]
            )
            wedding_teams.append(team)

    return wedding_teams

def create_wedding_events(weddings):
    """Create events for each wedding"""
    print("Creating wedding events...")

    events = []

    event_types = [
        ('Engagement Ceremony', 'Formal engagement ceremony'),
        ('Mehndi Night', 'Traditional henna ceremony'),
        ('Holud Ceremony', 'Turmeric ceremony'),
        ('Wedding Ceremony', 'Main wedding ceremony'),
        ('Reception', 'Wedding reception')
    ]

    for wedding in weddings:
        # Create 3-5 events for each wedding
        num_events = random.randint(3, 5)
        selected_events = random.sample(event_types, num_events)

        # Sort events by their index in the original list to maintain chronological order
        selected_events.sort(key=lambda x: event_types.index(x))

        for i, (name, description) in enumerate(selected_events):
            # Events are spread out over several days before the wedding
            days_offset = num_events - i - 1
            event_date = wedding.date - datetime.timedelta(days=days_offset)

            # For the main ceremony, use the wedding date
            if name == 'Wedding Ceremony':
                event_date = wedding.date

            start_time = datetime.time(hour=random.randint(10, 18), minute=0)
            end_time = datetime.time(hour=start_time.hour + 3, minute=0)

            event = WeddingEvent.objects.create(
                wedding=wedding,
                name=name,
                description=description,
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                location=wedding.location,
                address=wedding.address
            )
            events.append(event)

    return events

def create_wedding_themes(weddings):
    """Create themes for each wedding"""
    print("Creating wedding themes...")

    themes = []

    theme_options = [
        ('Traditional Red', 'Classic Bangladeshi wedding theme with red and gold colors', 'Red, Gold, White'),
        ('Royal Blue', 'Elegant theme with royal blue and silver accents', 'Blue, Silver, White'),
        ('Garden Fresh', 'Natural theme with green and floral elements', 'Green, Pink, Yellow'),
        ('Modern Minimalist', 'Contemporary theme with clean lines and neutral colors', 'Black, White, Grey'),
        ('Rustic Charm', 'Warm and inviting theme with earthy tones', 'Brown, Orange, Beige')
    ]

    for wedding in weddings:
        theme_choice = random.choice(theme_options)

        theme = WeddingTheme.objects.create(
            wedding=wedding,
            name=theme_choice[0],
            description=theme_choice[1],
            color_scheme=theme_choice[2],
            decoration_notes='Decorations should match the theme colors and style.',
            attire_notes='Guests are encouraged to dress according to the theme colors.'
        )
        themes.append(theme)

    return themes

def create_guests(weddings, guest_users):
    """Create guests for each wedding"""
    print("Creating guests...")

    all_guests = []

    # Create guests with user accounts
    for i, user in enumerate(guest_users):
        # Assign each guest user to a random wedding
        wedding = random.choice(weddings)

        guest = Guest.objects.create(
            wedding=wedding,
            user=user,
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
            phone=user.profile.phone,
            address=user.profile.address,
            status='confirmed',
            invitation_sent=True,
            invitation_sent_date=timezone.now() - datetime.timedelta(days=random.randint(10, 30)),
            rsvp_date=timezone.now() - datetime.timedelta(days=random.randint(5, 15)),
            plus_ones=random.randint(0, 2)
        )
        all_guests.append(guest)

        # Create credentials for the guest
        expiry_date = wedding.date + datetime.timedelta(days=7)
        password = generate_simple_password()
        credential = GuestCredential.objects.create(
            guest=guest,
            username=f"guest{i+1}",
            password=password,
            expiry_date=expiry_date
        )

        # Create invitation
        Invitation.objects.create(
            wedding=wedding,
            guest=guest,
            message=f"Dear {guest.name}, you are cordially invited to the wedding of {wedding.bride_name} and {wedding.groom_name} on {wedding.date}.",
            viewed=random.choice([True, False])
        )

    # Create additional guests without user accounts
    for i in range(20):
        wedding = random.choice(weddings)

        status_choices = ['invited', 'confirmed', 'declined', 'attended', 'no_show']
        status = random.choice(status_choices)

        guest = Guest.objects.create(
            wedding=wedding,
            name=f"Additional Guest {i+1}",
            email=f"guest{i+100}@example.com",
            phone=f"123-555-{1000+i}",
            address=f"{i+100} Guest Ave, Guest City",
            status=status,
            invitation_sent=True,
            invitation_sent_date=timezone.now() - datetime.timedelta(days=random.randint(10, 30)),
            rsvp_date=timezone.now() - datetime.timedelta(days=random.randint(5, 15)) if status != 'invited' else None,
            check_in_date=timezone.now() if status == 'attended' else None,
            plus_ones=random.randint(0, 2)
        )
        all_guests.append(guest)

        # Create credentials for the guest
        expiry_date = wedding.date + datetime.timedelta(days=7)
        password = generate_simple_password()
        credential = GuestCredential.objects.create(
            guest=guest,
            username=f"addguest{i+1}",
            password=password,
            expiry_date=expiry_date
        )

        # Create invitation
        Invitation.objects.create(
            wedding=wedding,
            guest=guest,
            message=f"Dear {guest.name}, you are cordially invited to the wedding of {wedding.bride_name} and {wedding.groom_name} on {wedding.date}.",
            viewed=random.choice([True, False])
        )

    return all_guests

def create_tasks(weddings, users):
    """Create tasks for each wedding"""
    print("Creating tasks...")

    all_tasks = []

    task_templates = [
        ('Book venue', 'Find and reserve the perfect venue for the wedding', 'high'),
        ('Hire photographer', 'Find a professional photographer for the event', 'medium'),
        ('Order cake', 'Select and order the wedding cake', 'medium'),
        ('Send invitations', 'Prepare and send out all wedding invitations', 'high'),
        ('Book caterer', 'Find and book a caterer for the reception', 'high'),
        ('Arrange transportation', 'Book vehicles for the wedding party', 'medium'),
        ('Buy wedding attire', 'Purchase wedding dress and groom\'s outfit', 'high'),
        ('Book makeup artist', 'Find a makeup artist for the bride and bridesmaids', 'medium'),
        ('Arrange decorations', 'Plan and purchase decorations for the venue', 'medium'),
        ('Hire DJ/Band', 'Book entertainment for the reception', 'low'),
        ('Plan honeymoon', 'Research and book honeymoon destination', 'low'),
        ('Purchase rings', 'Shop for wedding rings', 'high'),
        ('Arrange accommodations', 'Book hotel rooms for out-of-town guests', 'medium'),
        ('Create seating chart', 'Plan where guests will sit during the reception', 'low'),
        ('Finalize menu', 'Select final menu options with caterer', 'medium')
    ]

    status_options = ['pending', 'in_progress', 'completed', 'cancelled']

    for wedding in weddings:
        # Create 5-10 tasks for each wedding
        num_tasks = random.randint(5, 10)
        selected_tasks = random.sample(task_templates, num_tasks)

        admin = wedding.admin
        team_members = [team.member for team in wedding.team_members.all()]
        all_members = [admin] + team_members

        for title, description, priority in selected_tasks:
            # Randomly assign status
            status = random.choice(status_options)

            # Set due date based on status and wedding date
            if status == 'completed' or status == 'cancelled':
                due_date = wedding.date - datetime.timedelta(days=random.randint(10, 30))
            else:
                due_date = wedding.date - datetime.timedelta(days=random.randint(1, 15))

            # Randomly assign to a team member or admin
            assigned_to = random.choice(all_members)

            task = Task.objects.create(
                wedding=wedding,
                title=title,
                description=description,
                assigned_to=assigned_to,
                created_by=admin,
                due_date=due_date,
                priority=priority,
                status=status,
                completion_date=timezone.now() - datetime.timedelta(days=random.randint(1, 10)) if status == 'completed' else None
            )
            all_tasks.append(task)

            # Add 1-3 comments to each task
            num_comments = random.randint(1, 3)
            for _ in range(num_comments):
                commenter = random.choice(all_members)
                TaskComment.objects.create(
                    task=task,
                    user=commenter,
                    comment=f"Comment from {commenter.username} about the {title} task."
                )

    return all_tasks

def create_checklists(weddings, users):
    """Create checklists for each wedding"""
    print("Creating checklists...")

    all_checklists = []

    checklist_templates = [
        ('Pre-Wedding Checklist', 'Tasks to complete before the wedding day', [
            'Book venue',
            'Hire photographer',
            'Order flowers',
            'Send invitations',
            'Book caterer'
        ]),
        ('Wedding Day Checklist', 'Tasks for the wedding day', [
            'Confirm all vendors',
            'Prepare emergency kit',
            'Assign someone to collect gifts',
            'Confirm transportation',
            'Pack for honeymoon'
        ]),
        ('Post-Wedding Checklist', 'Tasks to complete after the wedding', [
            'Send thank you notes',
            'Return rented items',
            'Change name (if applicable)',
            'Preserve wedding dress',
            'Order wedding album'
        ])
    ]

    for wedding in weddings:
        admin = wedding.admin

        # Create 1-3 checklists for each wedding
        num_checklists = random.randint(1, 3)
        selected_checklists = random.sample(checklist_templates, num_checklists)

        for title, description, items in selected_checklists:
            checklist = Checklist.objects.create(
                title=title,
                description=description,
                is_template=False,
                wedding=wedding,
                created_by=admin
            )
            all_checklists.append(checklist)

            # Create checklist items
            for item_title in items:
                is_completed = random.choice([True, False])
                due_date = wedding.date - datetime.timedelta(days=random.randint(1, 30))

                ChecklistItem.objects.create(
                    checklist=checklist,
                    title=item_title,
                    description=f"Details for {item_title}",
                    due_date=due_date,
                    is_completed=is_completed,
                    completed_date=timezone.now() - datetime.timedelta(days=random.randint(1, 10)) if is_completed else None,
                    completed_by=admin if is_completed else None
                )

    # Create template checklists (not associated with a specific wedding)
    for title, description, items in checklist_templates:
        template_checklist = Checklist.objects.create(
            title=f"Template: {title}",
            description=description,
            is_template=True,
            wedding=None,
            created_by=users['admin']
        )
        all_checklists.append(template_checklist)

        # Create template checklist items
        for item_title in items:
            ChecklistItem.objects.create(
                checklist=template_checklist,
                title=item_title,
                description=f"Template details for {item_title}",
                due_date=None,
                is_completed=False
            )

    return all_checklists

def create_reminders(weddings, tasks):
    """Create reminders for tasks and events"""
    print("Creating reminders...")

    all_reminders = []

    for wedding in weddings:
        # Create 3-5 reminders for each wedding
        num_reminders = random.randint(3, 5)

        for i in range(num_reminders):
            reminder_type = random.choice(['task', 'event', 'custom'])

            if reminder_type == 'task' and wedding.tasks.exists():
                task = random.choice(wedding.tasks.all())
                title = f"Reminder: {task.title}"
                description = f"Don't forget to complete the task: {task.title}"
                reminder_date = task.due_date - datetime.timedelta(days=random.randint(1, 3))

                reminder = Reminder.objects.create(
                    wedding=wedding,
                    title=title,
                    description=description,
                    reminder_type='task',
                    reminder_date=datetime.datetime.combine(reminder_date, datetime.time(9, 0)),
                    task=task,
                    is_sent=random.choice([True, False])
                )

            elif reminder_type == 'event' and wedding.events.exists():
                event = random.choice(wedding.events.all())
                title = f"Reminder: {event.name}"
                description = f"The {event.name} is coming up soon!"
                reminder_date = event.date - datetime.timedelta(days=random.randint(1, 3))

                reminder = Reminder.objects.create(
                    wedding=wedding,
                    title=title,
                    description=description,
                    reminder_type='event',
                    reminder_date=datetime.datetime.combine(reminder_date, datetime.time(9, 0)),
                    is_sent=random.choice([True, False])
                )

            else:
                title = f"Custom Reminder {i+1}"
                description = f"This is a custom reminder for the {wedding.title}"
                reminder_date = wedding.date - datetime.timedelta(days=random.randint(1, 10))

                reminder = Reminder.objects.create(
                    wedding=wedding,
                    title=title,
                    description=description,
                    reminder_type='custom',
                    reminder_date=datetime.datetime.combine(reminder_date, datetime.time(9, 0)),
                    is_sent=random.choice([True, False])
                )

            all_reminders.append(reminder)

    return all_reminders

def create_media_categories(weddings):
    """Create media categories for each wedding"""
    print("Creating media categories...")

    all_categories = []

    category_names = [
        'Engagement Photos',
        'Pre-Wedding Ceremony',
        'Wedding Ceremony',
        'Reception',
        'Family Photos',
        'Couple Photos',
        'Guest Photos',
        'Venue Decoration',
        'Food and Cake',
        'Miscellaneous'
    ]

    for wedding in weddings:
        # Create 3-5 categories for each wedding
        num_categories = random.randint(3, 5)
        selected_categories = random.sample(category_names, num_categories)

        for name in selected_categories:
            category = MediaCategory.objects.create(
                wedding=wedding,
                name=name,
                description=f"Photos and videos from the {name.lower()}"
            )
            all_categories.append(category)

    return all_categories

def seed_data():
    """Main function to seed the database with sample data"""
    # Clear existing data
    clear_data()

    # Create users
    users = create_users()

    # Create weddings
    weddings = create_weddings(users['admin'])

    # Create wedding teams
    wedding_teams = create_wedding_teams(weddings, users['team_members'])

    # Create wedding events
    events = create_wedding_events(weddings)

    # Create wedding themes
    themes = create_wedding_themes(weddings)

    # Create guests
    guests = create_guests(weddings, users['guests'])

    # Create tasks
    tasks = create_tasks(weddings, users)

    # Create checklists
    checklists = create_checklists(weddings, users)

    # Create reminders
    reminders = create_reminders(weddings, tasks)

    # Create media categories
    categories = create_media_categories(weddings)

    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
