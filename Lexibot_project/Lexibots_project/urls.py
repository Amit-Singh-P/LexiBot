from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from Lexibots_app import views

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'), 
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('contact', views.contact_view, name='contact'),
    path('about', views.about_view, name='about'),
    path('password_reset/', views.custom_reset_password_view, name='custom_reset_password'),
    # Bot Chat Interface
    path('bot_chat/', views.bot_chat_view, name='bot_chat'),
    path('api/upload-document/', views.upload_document, name='upload_document'),
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/rate-response/', views.rate_response, name='rate_response'),
    # Document Management
    path('documents/', views.document_list, name='document_list'),
    path('documents/<uuid:document_id>/', views.document_detail, name='document_detail'),
    path('documents/<uuid:document_id>/delete/', views.delete_document, name='delete_document'),
    path('search/', views.search_documents, name='search_documents'),
    # Chat and History
    path('history/', views.chat_history, name='chat_history'),   
    # User Settings
    path('settings/', views.user_settings, name='user_settings'),

    path('__reload__/', include('django_browser_reload.urls')),
    path("api/", include("legal_bot.api.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

