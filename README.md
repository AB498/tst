# Wedding Management System (WMS)

A comprehensive wedding management system designed specifically for Bangladeshi weddings. This system streamlines the complex process of wedding planning by consolidating essential features into one easy-to-use platform.

## Features

- **Multi-Wedding Management**: Admins can manage multiple weddings at once with dedicated teams.
- **Role-Based Access**: Different access levels for admins, team members, and guests.
- **Guest Management with QR Code Check-In**: Unique credentials for guests with QR code system.
- **Virtual Wedding Invitations**: Digital invitation cards with RSVP links.
- **Task Management**: Assign tasks, track progress, and update statuses.
- **Live Event Status**: Real-time updates on wedding events and guest attendance.
- **Photo and Video Gallery**: Secure storage for wedding media.
- **Theme and Style Planner**: Customizable wedding themes with traditional Bangladeshi styles.
- **Checklist and Reminders**: Automated reminders for important wedding tasks.
- **Time-Limited Access**: Guest credentials expire after a specified period.

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Django
- **Database**: SQLite
- **Database Migration Policy**: No migrations, only destructive database seeding

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/wms.git
   cd wms
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the database:
   ```
   python manage.py migrate
   ```

4. Seed the database with sample data:
   ```
   python seed.py
   ```
5. reset database

     python reset_db.py

5. Run the development server:
   ```
   python manage.py runserver
   ```

6. Access the application at http://localhost:8000

## User Accounts

After seeding the database, the following accounts are available:

- **Admin**: Username: `admin`, Password: `admin123`
- **Team Members**: Username: `team1` through `team5`, Password: `team123`
- **Guests**: Username: `guest1` through `guest10`, Password: `guest123`

## Project Structure

- `core/`: Core functionality and user management
- `weddings/`: Wedding management features
- `guests/`: Guest management and QR code system
- `tasks/`: Task management and checklists
- `gallery/`: Photo and video gallery

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Northern University Bangladesh for project guidance
- All contributors and supporters of the project
