from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm
from django.http import HttpResponse
from pprint import pprint
from .models import Product, Retailer
from .models import Wishlist
import urllib.parse
import requests
import re
import os

# Create your views here.
# main_app/views.py

def about(request):
    return render(request, 'about.html')

class Home(LoginView):
    template_name = 'home.html'

class Login(LoginView):
    template_name = 'login.html'
    
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

def fetch_product_data(payload):
    response = requests.request(
        'POST',
        'https://realtime.oxylabs.io/v1/queries',
        auth=(os.environ.get('OXYLABS_USERNAME'), os.environ.get('OXYLABS_PASSWORD')),
        json=payload,
    )
    return response.json()

def get_logo_url(merchant_name):
    if '.' in merchant_name:
        cleaned_name = re.split(r'\.com|\.net|\.org', merchant_name)[0] + ".com"
        return f"https://img.logo.dev/{cleaned_name}?token=pk_MHqHMYHhSPqsrHGnE0dW1Q"
    
    cleaned_name = merchant_name.replace("'", "")
    cleaned_name = cleaned_name.replace(" ", "")
    
    return f"https://img.logo.dev/{cleaned_name}.com?token=pk_MHqHMYHhSPqsrHGnE0dW1Q"

def extract_url(full_url):
    parsed_url = urllib.parse.urlparse(full_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    return query_params.get('url', [full_url])[0]


def product_search(request):
    if request.method == 'POST':
        query = request.POST.get('query')

        amazon_payload = {
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

        google_payload = {
            'source': 'google_shopping_search',
            'domain': 'com',
            'query': query,
            'pages': 1,
            'parse': True,
            'context': [
                {'key': 'min_price', 'value': 1},  # Minimum price filter
            ]
        }

        amz_data = fetch_product_data(amazon_payload)
        ggl_data = fetch_product_data(google_payload)

        # Print the google data to see the structure
        # print(ggl_data)
                                                     
        amz_results = amz_data['results'][0]['content']['results']['organic']
        ggl_results = ggl_data['results'][0]['content']['results']['organic']

        for product in amz_results:
            product['logo_url'] = get_logo_url('Amazon.com')
        
        for product in ggl_results:
            merchant_name = product['merchant']['name']
            product['logo_url'] = get_logo_url(merchant_name)

        valid_amz_products = [
            product for product in amz_results if product.get('price', 0) > 0
        ]
        
        valid_ggl_products = [
            product for product in ggl_results if product.get('price', 0) > 0
        ]

        if not valid_ggl_products and not valid_amz_products:
            return HttpResponse("Your search didn't produce any results.")

        def sorting_key(product):
            return (
                    -product.get('pos', 0),  # Lower position is better
                    1 if product.get('is_amazons_choice', False) else 0,  # Prioritize Amazon's Choice products
                    1 if product.get('best_seller', False) else 0,  # Prioritize Best Seller products
                    product.get('reviews_count', 0),  # Higher review count is better
                    product.get('rating', 0),  # Higher rating is better
                    -product['price'],  # Lower price is better
            )

        amz_sorted_products = sorted(valid_amz_products, key=sorting_key, reverse=True)
        amz_best_product = amz_sorted_products[0]

        ggl_sorted_products = sorted(valid_ggl_products, key=sorting_key, reverse=True)
        ggl_best_product = ggl_sorted_products[0] if ggl_sorted_products else None

        return render(request, 'products/products_index.html', {
            'amz_best_product': amz_best_product,
            'amz_products': amz_sorted_products,
            'gg_best_product': ggl_best_product,
            'ggl_products': ggl_sorted_products,
        })

    return redirect('home')

from django.contrib.auth.decorators import login_required

@login_required
def fetch_product_details(request, product_id):
    if request.method == 'POST':
        payload = {
            'source': 'amazon_product',
            'domain': 'com',
            'query': f'{product_id}',
            'parse': True,
        }
        response = requests.request(
            'POST',
            'https://realtime.oxylabs.io/v1/queries',
            auth=(os.environ.get('OXYLABS_USERNAME'), os.environ.get('OXYLABS_PASSWORD')),
            json=payload,
        )
        data = response.json()

        # Extract relevant fields from the API response
        product_name = data.get('product_name', '')
        category = data.get('category', [{}])[0].get('ladder', [{}])[-1].get('name', '')
        product_url = data.get('url', '')
        image_url = data.get('images', [''])[0]
        description = data.get('description', '')
        rating = data.get('rating', 0)
        in_stock = data.get('stock', '').lower() == 'in stock.'
        price = data.get('price', 0)
        retailer_name = data.get('featured_merchant', {}).get('name', 'Amazon')
        
        # Get or create the retailer
        retailer, created = Retailer.objects.get_or_create(name=retailer_name)

        # Check if the product already exists to avoid duplicates
        product, created = Product.objects.get_or_create(
            name=product_name,
            defaults={
                'category': category,
                'product_url': product_url,
                'image_url': image_url,
                'description': description,
                'rating': rating,
                'in_stock': in_stock,
                'price_drop_threshold': price,
                'user': request.user,
                'retailer': retailer
            }
        )

        # Save the product to the user's wishlist
        Wishlist.objects.get_or_create(
            product_id=product,
            user=request.user
        )

        return HttpResponse(f"Product details fetched and saved successfully for {product_id}.")
    
    return redirect('home')