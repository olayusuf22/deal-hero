from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import SignUpForm

# Create your views here.
# main_app/views.py

def about(request):
    return render(request, 'about.html')

class Home(LoginView):
    template_name = 'home.html'

class Login(LoginView):
    template_name = 'login.html'

# class SignUp(LoginView):
#     template_name = 'signup.html'
    
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully!')
            return redirect('login')  # Replace 'login' with your login URL name
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})