from django.urls import path
from . import views


urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('about/', views.about, name='about'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.signup, name='signup'),
    path('search/', views.product_search, name='product_search'),
    path('product/<int:pk>/', views.ProductDetail.as_view(), name='product-detail'),
    path('product/<int:pk>/update-price', views.update_price, name='update-price'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/<str:product_asin>/add/', views.add_to_wishlist, name='add-to-wishlist'),
    path('wishlist/<int:pk>/delete/', views.DeleteProduct.as_view(), name='wishlist-delete'),
    path('deals/', views.deals_of_the_day, name='deals'),
]