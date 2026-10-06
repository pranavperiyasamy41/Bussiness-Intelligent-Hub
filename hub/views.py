from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import FileUploadForm, RetailFileUploadForm
from .models import (
    UploadedFile, 
    AnalysisResult,
    RetailFile,
    ChatMessage
)
from .ai_analyzer import perform_analysis
from .ai_chatter import get_ai_chat_response
from .ai_dashboarder import get_dashboard_layout, execute_dashboard_queries
# --- THIS IMPORT IS NOW UPDATED ---
from .ai_simulator import get_forecast_columns, run_sales_forecast
import pandas as pd
import json


# --- Home View ---
def home(request):
    return render(request, 'hub/home.html')

# --- Auth Views (unchanged) ---
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'hub/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'hub/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# --- Feedback App Views (unchanged) ---
@login_required
def feedback_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save(commit=False)
            uploaded_file.user = request.user
            uploaded_file.save()
            
            perform_analysis(uploaded_file.id)
            return redirect('result_detail', file_id=uploaded_file.id)
    else:
        form = FileUploadForm()
    
    feedback_files = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    
    return render(request, 'hub/feedback.html', {
        'form': form,
        'feedback_files': feedback_files
    })

@login_required
def result_detail_view(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    analysis_result = AnalysisResult.objects.filter(file=uploaded_file).first()
    
    return render(request, 'hub/result_detail.html', {
        'file': uploaded_file,
        'result': analysis_result
    })

@require_POST
@login_required
def feedback_delete_view(request, file_id):
    file_to_delete = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    file_to_delete.delete()
    return redirect('feedback')


# --- RETAIL INSIGHT ENGINE VIEWS ---

@login_required
def retail_dashboard_view(request):
    """
    This is the main "list" page for retail files
    """
    if request.method == 'POST':
        form = RetailFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            retail_file = form.save(commit=False)
            retail_file.user = request.user
            retail_file.save()
            
            try:
                file_path = retail_file.file.path
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                schema = {col: str(df[col].dtype) for col in df.columns}
                retail_file.schema_json = schema
                retail_file.save()
            except Exception as e:
                print(f"Error reading schema for {retail_file.id}: {e}")
            
            return redirect('retail_chat', file_id=retail_file.id)
    else:
        form = RetailFileUploadForm()
    
    retail_files = RetailFile.objects.filter(user=request.user).order_by('-uploaded_at')
    
    return render(request, 'hub/retail_dashboard.html', {
        'form': form,
        'retail_files': retail_files
    })

@login_required
def retail_chat_view(request, file_id):
    """
    This is the main chat page
    """
    retail_file = get_object_or_404(RetailFile, id=file_id, user=request.user)
    
    if request.method == 'POST':
        user_message = request.POST.get('message')
        
        if user_message:
            ChatMessage.objects.create(
                retail_file=retail_file,
                message=user_message,
                is_from_user=True
            )
            
            ai_response_text = get_ai_chat_response(retail_file, user_message)
            
            ChatMessage.objects.create(
                retail_file=retail_file,
                response=ai_response_text,
                is_from_user=False
            )
        
        return redirect('retail_chat', file_id=file_id)
    
    chat_history = ChatMessage.objects.filter(retail_file=retail_file).order_by('timestamp')
    
    return render(request, 'hub/retail_chat.html', {
        'file': retail_file,
        'chat_history': chat_history
    })

@login_required
def retail_auto_dashboard_view(request, file_id):
    """
    This is the AI-generated PowerBI-style dashboard.
    """
    retail_file = get_object_or_404(RetailFile, id=file_id, user=request.user)
    
    if not retail_file.schema_json:
        return render(request, 'hub/retail_auto_dashboard.html', {
            'file': retail_file, 
            'error': 'File schema was not generated. Please re-upload the file.'
        })

    dashboard_layout = get_dashboard_layout(retail_file.schema_json)
    
    if "error" in dashboard_layout or "charts" not in dashboard_layout or not dashboard_layout["charts"]:
        return render(request, 'hub/retail_auto_dashboard.html', {
            'file': retail_file, 
            'error': f"AI Planner failed: {dashboard_layout.get('error', 'The AI did not return a valid chart plan.')}"
        })
    
    try:
        file_path = retail_file.file.path
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        return render(request, 'hub/retail_auto_dashboard.html', {
            'file': retail_file, 
            'error': f"Error loading data file: {e}"
        })

    chart_data = execute_dashboard_queries(df, dashboard_layout["charts"])
    
    if not chart_data:
        return render(request, 'hub/retail_auto_dashboard.html', {
            'file': retail_file, 
            'error': "The AI generated a plan, but the data execution failed for all charts."
        })
    
    return render(request, 'hub/retail_auto_dashboard.html', {
        'file': retail_file,
        'chart_data_for_template': chart_data # Pass the raw Python list
    })

@require_POST
@login_required
def retail_delete_view(request, file_id):
    file_to_delete = get_object_or_404(RetailFile, id=file_id, user=request.user)
    file_to_delete.delete()
    return redirect('retail_dashboard')

# --- THIS IS THE UPDATED SIMULATION VIEW FUNCTION ---
@login_required
def retail_forecast_view(request, file_id):
    """
    This page runs the SARIMA forecast model and displays the result.
    """
    retail_file = get_object_or_404(RetailFile, id=file_id, user=request.user)
    
    # 1. Check for schema
    if not retail_file.schema_json:
        return render(request, 'hub/retail_forecast.html', {
            'file': retail_file, 
            'error': 'File schema was not generated. Please re-upload the file.'
        })

    # 2. AI Call: Get the date and sales columns
    column_names = get_forecast_columns(retail_file.schema_json)
    
    if "error" in column_names:
        return render(request, 'hub/retail_forecast.html', {
            'file': retail_file, 
            'error': f"AI Column-Finder failed: {column_names.get('error')}"
        })

    # 3. Load the data file
    try:
        file_path = retail_file.file.path
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        return render(request, 'hub/retail_forecast.html', {
            'file': retail_file, 
            'error': f"Error loading data file: {e}"
        })

    # 4. Run the forecast!
    # --- THIS IS THE NEW LOGIC ---
    sales_col = column_names.get('sales_col')
    month_col = column_names.get('month_col')
    year_col = column_names.get('year_col') # This can be null
    
    if not month_col or not sales_col:
        return render(request, 'hub/retail_forecast.html', {
            'file': retail_file, 
            'error': f"AI failed to identify valid date/month or sales columns. Identified: {column_names}"
        })
    
    forecast_data = run_sales_forecast(df, sales_col, month_col, year_col)
    # --- END OF NEW LOGIC ---
    
    # 5. Pass data to template
    if "error" in forecast_data:
        return render(request, 'hub/retail_forecast.html', {
            'file': retail_file, 
            'error': f"Forecast Failed: {forecast_data.get('error')}"
        })

    return render(request, 'hub/retail_forecast.html', {
        'file': retail_file,
        'forecast_data_for_template': forecast_data # Pass the raw Python dict
    })
# --- END NEW SIMULATION VIEW FUNCTION ---