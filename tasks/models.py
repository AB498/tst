from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from weddings.models import Wedding, WeddingTeam

class Task(models.Model):
    """Task model for wedding planning tasks"""
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_tasks', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    due_date = models.DateField()
    task_time = models.TimeField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completion_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.wedding}"

    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status != 'completed'

    @property
    def is_completed(self):
        return self.status == 'completed'

    def complete_task(self, user):
        self.status = 'completed'
        self.completion_date = timezone.now()
        self.save()

        # Create a task comment
        TaskComment.objects.create(
            task=self,
            user=user,
            comment=f"Task marked as completed by {user.username}"
        )

class TaskComment(models.Model):
    """Comments on tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.task.title} by {self.user.username}"

class Checklist(models.Model):
    """Predefined checklist templates for weddings"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_template = models.BooleanField(default=False)
    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name='checklists', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_checklists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.is_template:
            return f"Template: {self.title}"
        return f"{self.title} - {self.wedding}"

class ChecklistItem(models.Model):
    """Individual items in a checklist"""
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(blank=True, null=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='completed_checklist_items', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.checklist}"

    def complete(self, user):
        self.is_completed = True
        self.completed_date = timezone.now()
        self.completed_by = user
        self.save()

class Reminder(models.Model):
    """Automated reminders for tasks and events"""
    REMINDER_TYPES = (
        ('task', 'Task'),
        ('event', 'Event'),
        ('checklist', 'Checklist Item'),
        ('custom', 'Custom'),
    )

    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name='reminders')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    reminder_date = models.DateTimeField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.wedding}"

    def mark_as_sent(self):
        self.is_sent = True
        self.sent_date = timezone.now()
        self.save()
