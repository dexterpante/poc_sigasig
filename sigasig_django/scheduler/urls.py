from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('schedule/', views.generate_schedule, name='generate_schedule'),
]