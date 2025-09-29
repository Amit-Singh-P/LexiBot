from django.contrib import admin
from .models import Contact, Document, ChatSession, ChatMessage, UserProfile, LegalQuery
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

admin.site.register(Contact)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'document_type', 'file_size_formatted', 'processed', 'uploaded_at']
    list_filter = ['document_type', 'processed', 'uploaded_at']
    search_fields = ['title', 'user__username', 'user__email']
    readonly_fields = ['id', 'uploaded_at', 'file_size', 'mime_type', 'original_filename']
    
    def file_size_formatted(self, obj):
        if obj.file_size:
            return f"{obj.file_size / 1024:.1f} KB"
        return "N/A"
    file_size_formatted.short_description = "File Size"
    
    fieldsets = (
        ('Document Info', {
            'fields': ('id', 'title', 'document_type', 'user')
        }),
        ('File Details', {
            'fields': ('file', 'original_filename', 'file_size', 'mime_type')
        }),
        ('Processing', {
            'fields': ('processed', 'processing_error', 'extracted_text')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',)
        })
    )

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'document', 'message_count', 'is_active', 'created_at', 'last_activity']
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['title', 'user__username']
    readonly_fields = ['id', 'created_at', 'message_count']
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Messages"

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['id', 'timestamp']
    fields = ['message_type', 'content', 'timestamp']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['chat_session', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['content', 'chat_session__user__username']
    readonly_fields = ['id', 'timestamp']
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = "Content"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_language', 'timezone', 'notifications_enabled', 'created_at']
    list_filter = ['preferred_language', 'notifications_enabled', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(LegalQuery)
class LegalQueryAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'query_preview', 'confidence_score', 'helpful_rating', 'created_at']
    list_filter = ['category', 'confidence_score', 'helpful_rating', 'created_at']
    search_fields = ['query', 'user__username']
    readonly_fields = ['id', 'created_at']
    
    def query_preview(self, obj):
        return obj.query[:100] + "..." if len(obj.query) > 100 else obj.query
    query_preview.short_description = "Query"

# Customize admin site
admin.site.site_header = "LexiBots Administration"
admin.site.site_title = "LexiBots Admin"
admin.site.index_title = "Welcome to LexiBots Administration"