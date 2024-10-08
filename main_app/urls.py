from django.urls import path
from . import views

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('about/', views.about, name='about'),
    path('login/', views.Login.as_view(), name='login'),
    path('signup/', views.signup, name='signup'),
]
