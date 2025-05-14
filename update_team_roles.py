import os
import django
import random

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms_project.settings')
django.setup()

from weddings.models import WeddingTeam

def update_team_roles():
    """Update existing WeddingTeam records with valid roles from ROLE_CHOICES"""
    
    # Get all team members
    team_members = WeddingTeam.objects.all()
    
    # Define the available roles (same as in the model)
    roles = [role[0] for role in WeddingTeam.ROLE_CHOICES]
    
    # Update each team member with a valid role
    for member in team_members:
        # Assign a random role from the available choices
        member.role = random.choice(roles)
        member.save()
        print(f"Updated {member.member.username} with role: {member.get_role_display()}")
    
    print(f"Updated {len(team_members)} team members with valid roles.")

if __name__ == "__main__":
    update_team_roles()
