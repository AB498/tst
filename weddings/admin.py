from django.contrib import admin
from .models import Wedding, WeddingTeam, WeddingEvent, WeddingTheme

class WeddingTeamInline(admin.TabularInline):
    model = WeddingTeam
    extra = 1

class WeddingEventInline(admin.TabularInline):
    model = WeddingEvent
    extra = 1

@admin.register(Wedding)
class WeddingAdmin(admin.ModelAdmin):
    list_display = ('title', 'bride_name', 'groom_name', 'date', 'status', 'admin')
    list_filter = ('status', 'date', 'created_at')
    search_fields = ('title', 'bride_name', 'groom_name', 'location')
    date_hierarchy = 'date'
    inlines = [WeddingTeamInline, WeddingEventInline]

@admin.register(WeddingTeam)
class WeddingTeamAdmin(admin.ModelAdmin):
    list_display = ('wedding', 'member', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('wedding__title', 'member__username', 'role')

@admin.register(WeddingEvent)
class WeddingEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'wedding', 'date', 'start_time', 'end_time', 'location')
    list_filter = ('date', 'created_at')
    search_fields = ('name', 'wedding__title', 'location')
    date_hierarchy = 'date'

@admin.register(WeddingTheme)
class WeddingThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'wedding', 'created_at')
    search_fields = ('name', 'wedding__title', 'color_scheme')
