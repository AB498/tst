from django.contrib import admin
from .models import Guest, GuestCredential, Invitation

class GuestCredentialInline(admin.StackedInline):
    model = GuestCredential
    extra = 0
    readonly_fields = ('token', 'qr_code')

class InvitationInline(admin.TabularInline):
    model = Invitation
    extra = 0
    readonly_fields = ('sent_date', 'viewed', 'viewed_date')

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'wedding', 'email', 'status', 'invitation_sent', 'is_checked_in')
    list_filter = ('status', 'invitation_sent', 'wedding')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('check_in_date',)
    inlines = [GuestCredentialInline, InvitationInline]

    def is_checked_in(self, obj):
        return obj.is_checked_in
    is_checked_in.boolean = True
    is_checked_in.short_description = 'Checked In'

@admin.register(GuestCredential)
class GuestCredentialAdmin(admin.ModelAdmin):
    list_display = ('guest', 'username', 'token', 'expiry_date', 'is_valid')
    list_filter = ('created_at', 'expiry_date')
    search_fields = ('guest__name', 'username')
    readonly_fields = ('token', 'qr_code')

    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Valid'

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('guest', 'wedding', 'sent_date', 'viewed', 'viewed_date')
    list_filter = ('viewed', 'sent_date')
    search_fields = ('guest__name', 'wedding__title')
    readonly_fields = ('sent_date', 'viewed_date')
