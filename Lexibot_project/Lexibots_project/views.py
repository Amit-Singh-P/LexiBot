from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'index.html')
