from django.shortcuts import render, redirect, get_object_or_404
from .forms import SignUpForm, LoginForm, ContactForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, get_backends, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from .models import Document, ChatSession, ChatMessage, UserProfile, LegalQuery, Contact
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, DocumentUploadForm,
    ChatMessageForm, UserProfileForm, PasswordResetRequestForm, ContactForm, CustomPasswordResetForm
)
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
import uuid
import os
from PIL import Image
import pytesseract
import PyPDF2
import docx2txt
import magic
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail

def home(request):
    return render(request, 'index.html')

# Sign up view
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            backend = get_backends()[0]  # usually the default one provided by Django
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user)
            messages.success(request, "Signup successful! Please log in.")
            return redirect('bot_chat')        
        else:
            print(form.errors)
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form':form})

# Login view
def login_view(request):
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('bot_chat')
        else:
            print(form.errors)
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# Contact View
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

# Loguot View
def logout_view(request):
    logout(request)
    return redirect('home')

# Custom Reset Password View
def custom_reset_password_view(request):
    form = CustomPasswordResetForm()
    success = False
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['new_password1']
            user = User.objects.get(email=email)
            user.password = make_password(password)
            user.save()
            form = None
            success = True
    return render(request, 'password_reset.html', {'form': form, 'success': success})

def about_view(request):
    return render(request, 'about.html')


# Lexibot
# Main Bot Chat Views
@login_required
def bot_chat_view(request):
    """Main bot chat interface"""
    # Get or create active chat session
    chat_session, created = ChatSession.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'title': 'Legal Consultation'}
    )
    
    # Get recent documents
    recent_documents = Document.objects.filter(user=request.user)[:5]
    
    # Get chat messages
    messages_list = ChatMessage.objects.filter(chat_session=chat_session)
    
    context = {
        'chat_session': chat_session,
        'messages': messages_list,
        'recent_documents': recent_documents,
        'document_form': DocumentUploadForm(),
        'chat_form': ChatMessageForm(),
    }
    
    return render(request, 'bot.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_document(request):
    """Handle document upload via AJAX"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'})
        
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()
            
            # Process document text extraction in background
            extract_text_from_document(document)
            
            return JsonResponse({
                'success': True,
                'document_id': str(document.id),
                'filename': document.original_filename,
                'message': f'Document "{document.title}" uploaded successfully!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid file format or size'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        })

def extract_text_from_document(document):
    """Extract text from uploaded document"""
    try:
        file_path = document.file.path
        mime_type = document.mime_type
        
        if mime_type == 'application/pdf':
            text = extract_text_from_pdf(file_path)
        elif mime_type in ['image/jpeg', 'image/png', 'image/jpg']:
            text = extract_text_from_image(file_path)
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            text = extract_text_from_docx(file_path)
        else:
            text = "Text extraction not supported for this file type."
        
        document.extracted_text = text
        document.processed = True
        document.save()
        
    except Exception as e:
        document.processing_error = str(e)
        document.save()

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        text = f"Error extracting PDF text: {str(e)}"
    return text

def extract_text_from_image(file_path):
    """Extract text from image using OCR"""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return f"Error extracting image text: {str(e)}"

def extract_text_from_docx(file_path):
    """Extract text from Word document"""
    try:
        text = docx2txt.process(file_path)
        return text
    except Exception as e:
        return f"Error extracting document text: {str(e)}"

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Handle chat message sending via AJAX"""
    try:
        data = json.loads(request.body)
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return JsonResponse({'success': False, 'error': 'Empty message'})
        
        # Get or create active chat session
        chat_session, created = ChatSession.objects.get_or_create(
            user=request.user,
            is_active=True,
            defaults={'title': 'Legal Consultation'}
        )
        
        # Save user message
        user_message = ChatMessage.objects.create(
            chat_session=chat_session,
            message_type='user',
            content=message_content
        )
        
        # Generate bot response
        bot_response = generate_legal_response(message_content, request.user)
        
        # Save bot message
        bot_message = ChatMessage.objects.create(
            chat_session=chat_session,
            message_type='bot',
            content=bot_response
        )
        
        # Update session activity
        chat_session.last_activity = timezone.now()
        chat_session.save()
        
        return JsonResponse({
            'success': True,
            'bot_response': bot_response,
            'message_id': str(bot_message.id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Message processing failed: {str(e)}'
        })

def generate_legal_response(message, user):
    """Generate AI-powered legal response"""
    # Simple rule-based responses (in production, you'd use AI/ML)
    message_lower = message.lower()
    
    # Get user's documents for context
    user_documents = Document.objects.filter(user=user, processed=True)
    
    responses = {
        'contract': "Based on contract law principles, I can help you understand the key elements: offer, acceptance, consideration, and legal capacity. If you have a contract document uploaded, I can analyze specific clauses for you.",
        'indemnify': "Indemnification means to compensate someone for harm or loss. In legal contracts, an indemnity clause protects one party from liability by requiring the other party to cover costs, damages, or losses.",
        'liability': "Liability refers to legal responsibility for one's acts or omissions. In contracts, liability clauses determine who is responsible for damages, losses, or injuries that may occur.",
        'breach': "A breach of contract occurs when one party fails to fulfill their obligations as specified in the agreement. This can result in legal remedies including damages or specific performance.",
        'termination': "Contract termination can occur by performance, agreement, frustration, or breach. The terms of termination should be clearly specified in the contract to avoid disputes.",
        'copyright': "Copyright protects original works of authorship including literary, dramatic, musical, and artistic works. It gives the owner exclusive rights to reproduce, distribute, and display the work.",
        'trademark': "A trademark is a recognizable sign, design, or expression which identifies products or services of a particular source. It helps consumers distinguish between different brands.",
        'patent': "A patent grants inventors exclusive rights to their inventions for a limited time, typically 20 years. It prevents others from making, using, or selling the invention without permission."
    }
    
    # Check if message contains any keywords
    for keyword, response in responses.items():
        if keyword in message_lower:
            if user_documents.exists():
                response += f" I can also analyze your uploaded document for specific {keyword}-related clauses if needed."
            return response
    
    # Default response
    if user_documents.exists():
        return "I've analyzed your question in the context of your uploaded documents. Could you please be more specific about which aspect of your legal document you'd like me to explain? I can help with contracts, agreements, terms and conditions, and other legal documents."
    else:
        return "I'd be happy to help with your legal question. For more accurate assistance, please upload your legal document so I can provide specific guidance based on its content. You can also ask me general legal questions about contracts, intellectual property, or other areas of law."

@login_required
def document_list(request):
    """List user's documents"""
    documents = Document.objects.filter(user=request.user)
    paginator = Paginator(documents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'document_list.html', {'page_obj': page_obj})

@login_required
def document_detail(request, document_id):
    """View document details"""
    document = get_object_or_404(Document, id=document_id, user=request.user)
    return render(request, 'document_detail.html', {'document': document})

@login_required
def delete_document(request, document_id):
    """Delete a document"""
    document = get_object_or_404(Document, id=document_id, user=request.user)
    if request.method == 'POST':
        document.file.delete()  # Delete file from storage
        document.delete()
        messages.success(request, 'Document deleted successfully.')
    return redirect('document_list')

@login_required
def chat_history(request):
    """View chat history"""
    sessions = ChatSession.objects.filter(user=request.user)
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'chat_history.html', {'page_obj': page_obj})

@login_required
def user_settings(request):
    """User settings and profile"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully.')
            return redirect('user_settings')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'settings.html', {'form': form})

@login_required
@csrf_exempt
def rate_response(request):
    """Rate bot response"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            rating = data.get('rating')
            
            message = get_object_or_404(ChatMessage, id=message_id, chat_session__user=request.user)
            
            # Save rating (you might want to create a separate Rating model)
            # For now, we'll store it in metadata
            if 'rating' not in message.metadata:
                message.metadata['rating'] = rating
                message.save()
                
                return JsonResponse({'success': True, 'message': 'Thank you for your feedback!'})
            else:
                return JsonResponse({'success': False, 'error': 'Already rated'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def search_documents(request):
    """Search through user's documents"""
    query = request.GET.get('q', '')
    documents = Document.objects.filter(user=request.user)
    
    if query:
        documents = documents.filter(
            Q(title__icontains=query) | 
            Q(extracted_text__icontains=query)
        )
    
    paginator = Paginator(documents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'search_results.html', {
        'page_obj': page_obj,
        'query': query
    })