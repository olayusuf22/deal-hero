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
        payload = {
            'source': 'amazon_search',
            'domain_name': 'usa',
            'query': query,
            'start_page': 1,
            'pages': 1,
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
        # We are only interested in the 'organic' results (not sponsored or paid results).
        organic_results = response.json()['results'][0]['content']['results']['organic']

         # Filter out products with invalid or zero price
        valid_products = [
            product for product in organic_results
            if product['price'] > 0
        ]

        if not valid_products:
            # Todo: Handle the case where no valid products are found
            # return render(request, 'products/no_products_found.html')
            return HttpResponse("No valid products found.")

        # This is our helper function to define how we sort products.
        def sorting_key(product):
            return (
                -product['pos'],     # Position in Amazon's results. Lower is better.
                1 if product['is_amazons_choice'] else 0, 
                1 if product['best_seller'] else 0, 
                -product['price'],  # Lower price is better
                product['reviews_count'], 
                product['rating'], 
            )

        # Sort the valid products in descending order.
        sorted_products = sorted(valid_products, key=sorting_key, reverse=True)
        # The best product is the first one in the sorted list.
        best_product = sorted_products[0]

        return render(request, 'products/products_index.html', {
            'best_product': best_product,
            'products': sorted_products,
        })

    return redirect('home')