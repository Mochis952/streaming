from django.urls import path
from . import views

app_name = 'fb_manager'

urlpatterns = [
    path('session/new/', views.start_new_session_view, name='session_new'),
    path('session/load/', views.load_existing_session_view, name='session_load'),
]
