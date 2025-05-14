import os
import django
import random

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

def create_team_members():
    """Create users with team_member role if none exist"""
    
    # Check if there are any team members
    team_members = User.objects.filter(profile__role='team_member')
    
    if team_members.exists():
        print(f"Found {team_members.count()} existing team members.")
        for member in team_members:
            print(f"- {member.username} ({member.email})")
        return
    
    # Create some team members
    team_member_data = [
        {
            'username': 'photographer',
            'email': 'photographer@example.com',
            'password': 'password123',
            'first_name': 'Photo',
            'last_name': 'Grapher',
            'role': 'team_member'
        },
        {
            'username': 'florist',
            'email': 'florist@example.com',
            'password': 'password123',
            'first_name': 'Flora',
            'last_name': 'Bloom',
            'role': 'team_member'
        },
        {
            'username': 'caterer',
            'email': 'caterer@example.com',
            'password': 'password123',
            'first_name': 'Chef',
            'last_name': 'Delicious',
            'role': 'team_member'
        },
        {
            'username': 'dj',
            'email': 'dj@example.com',
            'password': 'password123',
            'first_name': 'DJ',
            'last_name': 'Beats',
            'role': 'team_member'
        },
        {
            'username': 'coordinator',
            'email': 'coordinator@example.com',
            'password': 'password123',
            'first_name': 'Cora',
            'last_name': 'Planner',
            'role': 'team_member'
        }
    ]
    
    for data in team_member_data:
        # Check if user already exists
        if User.objects.filter(username=data['username']).exists():
            print(f"User {data['username']} already exists, skipping.")
            continue
            
        # Create user
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        
        # Create or update profile
        try:
            profile = UserProfile.objects.get(user=user)
            profile.role = data['role']
            profile.save()
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(
                user=user,
                role=data['role']
            )
        
        print(f"Created team member: {user.username} ({user.email})")
    
    print(f"Created {len(team_member_data)} team members.")

if __name__ == "__main__":
    create_team_members()
