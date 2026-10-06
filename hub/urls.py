from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Feature 1: Feedback Analysis
    path('feedback/', views.feedback_view, name='feedback'),
    path('result/<int:file_id>/', views.result_detail_view, name='result_detail'),
    path('feedback/delete/<int:file_id>/', views.feedback_delete_view, name='feedback_delete'),
    
    
    # Feature 2: Retail Insight Engine
    path('retail/', views.retail_dashboard_view, name='retail_dashboard'), 
    path('retail/chat/<int:file_id>/', views.retail_chat_view, name='retail_chat'),
    path('retail/dashboard/<int:file_id>/', views.retail_auto_dashboard_view, name='retail_auto_dashboard'),
    path('retail/delete/<int:file_id>/', views.retail_delete_view, name='retail_delete'),
    
    # --- THIS IS THE NEW LINE FOR THE SIMULATION ---
    path('retail/forecast/<int:file_id>/', views.retail_forecast_view, name='retail_forecast'),
    # --- END NEW LINE ---
]