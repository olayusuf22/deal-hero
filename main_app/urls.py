from django.urls import path
from . import views


urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('about/', views.about, name='about'),
    path('login/', views.Login.as_view(), name='login'),
    path('signup/', views.signup, name='signup'),
    path('search/', views.product_search, name='product_search'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('product/<str:product_id>/fetch/', views.fetch_product_details, name='fetch-product-details'),
    path('wishlist/<int:pk>/delete/', views.DeleteProduct.as_view(), name='wishlist-delete'),
]