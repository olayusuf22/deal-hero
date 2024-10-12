from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm
from django.http import HttpResponse
from pprint import pprint
from .models import Product, Retailer, Wishlist, PriceHistory
import urllib.parse
import requests
import re
import os

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
            return redirect('login')  
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
            'geo_location': 'New York,New York,United States',
            'context': [
                {'key': 'min_price', 'value': 1},
                {"key": "results_language", "value": "en"}, 
            ]
        }

        amz_data = fetch_product_data(amazon_payload)
        ggl_data = fetch_product_data(google_payload)
                                                     
        amz_results = amz_data['results'][0]['content']['results']['organic']
        ggl_results = ggl_data['results'][0]['content']['results']['organic']

        for product in amz_results:
            product['logo_url'] = get_logo_url('Amazon.com')
        
        for product in ggl_results:
            merchant_name = product['merchant']['name']
            product['logo_url'] = get_logo_url(merchant_name)

        valid_amz_products = [
            product for product in amz_results
            if all([
                product.get('url'),
                product.get('asin'),
                product.get('price'),
                product.get('title'),
                product.get('url_image'),
            ])
        ]
        
        valid_ggl_products = [
            product for product in ggl_results
            if all([
                product.get('price'),
                product.get('title'),
                product.get('merchant'),
                product.get('thumbnail'),
                product.get('rating'),
            ])
        ]

        if not valid_ggl_products and not valid_amz_products:
            return HttpResponse("Your search didn't produce any results. Refine your search and try again! 🦸‍♀️")

        def sorting_key(product):
            return (
                    -product.get('pos', 0),  
                    1 if product.get('is_amazons_choice', False) else 0,  
                    1 if product.get('best_seller', False) else 0,  
                    product.get('reviews_count', 0),  
                    product.get('rating', 0),  
                    -product['price'],  
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
        
        product_name = data['results'][0]['content']['product_name']        
        category = data['results'][0]['content'].get('category', [{}])[0].get('ladder', [{}])[0].get('name', 'Miscelaneous')        
        product_url = data['results'][0]['content']['url']        
        image_url = data['results'][0]['content']['images'][0]        
        description = data['results'][0]['content']['description']        
        rating = data['results'][0]['content']['rating']        
        stock_value = data['results'][0]['content'].get('stock', "in stock")
        in_stock = stock_value.lower() == 'in stock'
        

        price = data['results'][0]['content']['price']        
        retailer_name = data['results'][0].get('manufacturer', product_name.split()[0])
        retailer, created = Retailer.objects.get_or_create(name=retailer_name)      
        product, created = Product.objects.get_or_create(
            name=product_name,
            defaults={
                'category': category,
                'product_url': product_url,
                'image_url': image_url,
                'description': description,
                'rating': rating,
                'in_stock': in_stock,
                'price_drop_threshold': 1,
                'user': request.user,
                'retailer': retailer
            }
        )

        PriceHistory.objects.create(
            product=product,
            price=price
        )
       
        Wishlist.objects.get_or_create(
            product_id=product,
            user=request.user
        )

        return HttpResponse(
            f"Product details fetched and saved successfully for {product_name}.<br>"
            f"Category: {category}.<br>"
            f"URL: {product_url}.<br>"
            f"Image URL: {image_url}.<br>"
            f"Description: {description}.<br>"
            f"Rating: {rating}.<br>"
            f"Price: {price}.<br>"
            f"In Stock: {in_stock}.<br>"
            f"Price Drop Threshold: {product.price_drop_threshold}.<br>"
            f"Retailer: {retailer_name}."
        )
    
    return redirect('home')