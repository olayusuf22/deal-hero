from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import SignUpForm
from django.http import HttpResponse
from django.http import JsonResponse
import requests
import os

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
           auth=(os.environ.get('OXYLABS_USERNAME'), os.environ.get('OXYLABS_PASSWORD')),
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
        amz_sorted_products = sorted(valid_products, key=sorting_key, reverse=True)
        # The best product is the first one in the sorted list.
        amz_best_product = amz_sorted_products[0]

        ggl_payload = {
            'source': 'google_shopping_search',
            'domain': 'com',
            'query': query,
            'pages': 1,  # You can adjust pages based on your needs
            'parse': True,
            'context': [
                {'key': 'sort_by', 'value': 'pd'},  # Sort by price descending (pd)
                {'key': 'min_price', 'value': 20},  # Minimum price filter (example)
            ]
        }
        ggl_response = requests.request(
            'POST',
            'https://realtime.oxylabs.io/v1/queries',
            auth=(os.environ.get('OXYLABS_USERNAME'), os.environ.get('OXYLABS_PASSWORD')),
            json=ggl_payload,
        )
        
        # Process ggl Shopping data
        ggl_results = ggl_response.json().get('results', [])[0]['content']['results']['organic']
        valid_ggl_products = [
            {
                'title': product.get('title'),
                'price': product.get('price_str'),
                'url': product.get('url'),
                'thumbnail': product.get('thumbnail'),
                'rating': product.get('rating'),
                'merchant_name': product['merchant'].get('name'),
                'merchant_url': product['merchant'].get('url')
            } for product in ggl_results if product.get('price', 0) > 0
        ]
        

        def sorting_key_ggl(product):
            return (
                -product.get('pos', 0),  # Position in Google Shopping results, lower is better.
                product.get('reviews_count', 0),  # Higher number of reviews is better.
                product.get('rating', 0),  # Higher rating is better.
                -float(product['price'].replace('$', '').replace(',', '')),  # Lower price is better, remove symbols.
            )

        # Sort the valid Google products in descending order
        ggl_sorted_products = sorted(valid_ggl_products, key=sorting_key_ggl, reverse=True)

        # The best product is the first one in the sorted list
        ggl_best_product = ggl_sorted_products[0] if ggl_sorted_products else None

        return render(request, 'products/products_index.html', {
            'amz_best_product': amz_best_product,
            'amz_products': amz_sorted_products,
            'gg_best_product': ggl_best_product,
            'ggl_products': valid_ggl_products,
        })

    return redirect('home')