import uuid
import os
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User 
from django.core.validators import FileExtensionValidator

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('contract', 'Contract'),
        ('legal_notice', 'Legal Notice'),
        ('agreement', 'Agreement'),
        ('lawsuit', 'Lawsuit'),
        ('patent', 'Patent'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    file = models.FileField(upload_to='legal_documents/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    extracted_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"

class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chat_sessions', null=True, blank=True)
    title = models.CharField(max_length=255, default="Legal Consultation")
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)  # For storing additional info like confidence scores, sources, etc.
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

class UserProfile(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('mr', 'Marathi'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preferred_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile: {self.user.username}"

class LegalQuery(models.Model):
    QUERY_CATEGORIES = [
        ('contract', 'Contract Law'),
        ('property', 'Property Law'),
        ('criminal', 'Criminal Law'),
        ('family', 'Family Law'),
        ('corporate', 'Corporate Law'),
        ('intellectual', 'Intellectual Property'),
        ('labor', 'Labor Law'),
        ('tax', 'Tax Law'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='queries')
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='queries')
    query = models.TextField()
    category = models.CharField(max_length=20, choices=QUERY_CATEGORIES, default='other')
    response = models.TextField()
    confidence_score = models.FloatField(default=0.0)
    sources_cited = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    helpful_rating = models.IntegerField(null=True, blank=True)  # 1-5 rating from user
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Query: {self.query[:50]}..."