from django.contrib import admin
from .models import Task, TaskComment, Checklist, ChecklistItem, Reminder

class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0

class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'wedding', 'assigned_to', 'due_date', 'task_time', 'priority', 'status', 'is_overdue')
    list_filter = ('status', 'priority', 'due_date', 'wedding')
    search_fields = ('title', 'description', 'wedding__title')
    date_hierarchy = 'due_date'
    inlines = [TaskCommentInline]

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('task__title', 'user__username', 'comment')

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('title', 'wedding', 'is_template', 'created_by', 'created_at')
    list_filter = ('is_template', 'created_at')
    search_fields = ('title', 'description', 'wedding__title')
    inlines = [ChecklistItemInline]

@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'checklist', 'due_date', 'is_completed', 'completed_by')
    list_filter = ('is_completed', 'due_date')
    search_fields = ('title', 'description', 'checklist__title')
    date_hierarchy = 'due_date'

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'wedding', 'reminder_type', 'reminder_date', 'is_sent')
    list_filter = ('reminder_type', 'is_sent', 'reminder_date')
    search_fields = ('title', 'description', 'wedding__title')
    date_hierarchy = 'reminder_date'
