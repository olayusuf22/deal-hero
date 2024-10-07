from django.shortcuts import render

# Create your views here.
# main_app/views.py

def about(request):
    return render(request, 'about.html')
