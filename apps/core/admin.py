from django.contrib import admin
from .models import ContactMessage, FAQ


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'created_at', 'is_resolved')
    list_filter = ('is_resolved',)
    search_fields = ('name', 'email', 'subject')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order')
    ordering = ('order',)
