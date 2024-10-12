from django.urls import path
from . import views
from .views import WishlistView

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('about/', views.about, name='about'),
    path('login/', views.Login.as_view(), name='login'),
    path('signup/', views.signup, name='signup'),
    path('search/', views.product_search, name='product_search'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('product/<str:product_id>/fetch/', views.fetch_product_details, name='fetch-product-details'),
]