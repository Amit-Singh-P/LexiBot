from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from .models import Contact, Document, UserProfile, ChatMessage
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import magic
import os

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': ' ',
        'class': 'form-control'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': ' ',
        'class': 'form-control',
        'id': 'password'
    }))

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']

class CustomPasswordResetForm(forms.ModelForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )
    class Meta:
        model = User
        fields = ("email",)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        if not User.objects.filter(email=email).exists():
            self.add_error('email', "⚠️ This email is not registered.")
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', "⚠️ Passwords do not match.")
        return cleaned_data
    def save(self, commit=True):
        email = self.cleaned_data["email"]
        password = self.cleaned_data["new_password1"]
        user = User.objects.get(email=email)
        user.set_password(password)
        if commit:
            user.save()
        return user
    

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
        'placeholder': 'Enter your email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
        'placeholder': 'Last Name'
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
            'placeholder': 'Confirm Password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(user=user)
        return user

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
            'placeholder': 'Username or Email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
            'placeholder': 'Password'
        })

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'document_type', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
                'placeholder': 'Document Title (optional)'
            }),
            'document_type': forms.Select(attrs={
                'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border'
            }),
            'file': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = False

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size cannot exceed 10MB.')
            
            # Check file type
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'image/jpg',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            
            # Use python-magic to detect actual file type
            try:
                file_mime = magic.from_buffer(file.read(1024), mime=True)
                file.seek(0)  # Reset file pointer
                
                if file_mime not in allowed_types:
                    raise ValidationError('Unsupported file type. Please upload PDF, JPG, PNG, DOC, or DOCX files.')
            except Exception as e:
                raise ValidationError('Error validating file type.')
                
        return file

    def save(self, commit=True):
        document = super().save(commit=False)
        if self.cleaned_data['file']:
            document.original_filename = self.cleaned_data['file'].name
            document.file_size = self.cleaned_data['file'].size
            document.mime_type = magic.from_buffer(self.cleaned_data['file'].read(1024), mime=True)
            self.cleaned_data['file'].seek(0)
            
            if not document.title:
                document.title = os.path.splitext(document.original_filename)[0]
        
        if commit:
            document.save()
        return document

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'w-full bg-gray-900 border border-gray-700 rounded-full py-3 px-5 pr-14 glow-border',
                'placeholder': 'Type your legal question...',
                'autocomplete': 'off'
            })
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['preferred_language', 'timezone', 'notifications_enabled']
        widgets = {
            'preferred_language': forms.Select(attrs={
                'class': 'bg-charcoal border border-gray-600 rounded-md py-1 pl-3 pr-8 text-sm glow-border'
            }),
            'timezone': forms.TextInput(attrs={
                'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
                'placeholder': 'UTC'
            }),
            'notifications_enabled': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-600 bg-gray-900 text-accent-blue focus:ring-accent-blue'
            })
        }

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
            'placeholder': 'Enter your email address'
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise ValidationError("No user found with this email address.")
        return email

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
            'placeholder': 'Your Email'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-gray-900 border border-gray-700 rounded-lg py-3 px-4 glow-border h-32',
            'placeholder': 'Your Message'
        })
    )