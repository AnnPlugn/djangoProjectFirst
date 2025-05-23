from django.urls import path
from . import views

app_name = 'firstblog'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('result/', views.result, name='result'),
    path('invoke_model/', views.invoke_model, name='invoke_model'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('result/', views.result, name='result'),
]