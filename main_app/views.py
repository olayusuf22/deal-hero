from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import SignUpForm
from django.http import HttpResponse
from django.http import JsonResponse
import requests

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

def product_search(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        # return HttpResponse(f'You searched for: {query}')
        payload = {
            'source': 'amazon_search',
            'domain_name': 'usa',
            'query': query,
            'start_page': 2,
            'pages': 2,
            'parse': True,
            'context': [
            {'key': 'category_id', 'value': 16391693031}
            ],
        }   
        response = requests.request(
            'POST',
            'https://realtime.oxylabs.io/v1/queries',
            auth=('batman_WI3g8', 'Team4batman23456_'),
            json=payload,
        )
        return JsonResponse(response.json(), safe=False)
    return redirect('home')