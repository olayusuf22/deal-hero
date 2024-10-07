from django.shortcuts import render
from django.contrib.auth.views import LoginView

# Create your views here.
# main_app/views.py

def about(request):
    return render(request, 'about.html')

class Home(LoginView):
    template_name = 'home.html'
