import google.generativeai as genai
from django.conf import settings
import pandas as pd
import json
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import warnings

# Suppress warnings from the SARIMA model for a cleaner output
warnings.simplefilter('ignore', ConvergenceWarning)

# --- Global AI Configuration ---
api_key = settings.GOOGLE_AI_API_KEY
if api_key:
    genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash-lite')
# -----------------------------

# --- THIS IS THE NEW "AI SUMMARY" FUNCTION ---
def generate_forecast_summary(historical_data, forecast_data, sales_col_name):
    """
    AI Call #2: Asks the AI to write a human-like summary of the forecast.
    """
    if not api_key:
        return "Forecast complete." # Failsafe
    
    # Prepare data for the prompt
    last_historical_val = historical_data[-1]
    first_forecast_val = forecast_data[0]
    last_forecast_val = forecast_data[-1]
    
    prompt = f"""
    You are a senior business analyst. Your job is to provide a clear, insightful,
    and suggestive summary of a 12-month sales forecast.
    
    DO NOT just state the numbers. Provide actionable insights.
    
    Here is the data:
    - Last known sales month ({sales_col_name}): {last_historical_val:,.2f}
    - First forecasted month: {first_forecast_val:,.2f}
    - 12th forecasted month: {last_forecast_val:,.2f}

    Example 1:
    (Data shows a 20% increase)
    "The forecast looks positive, with a projected 20% increase in sales over the next year.
    This suggests strong momentum. We should prepare for increased demand by
    checking our inventory levels."
    
    Example 2:
    (Data shows a 10% decrease)
    "The model predicts a 10% decline in sales over the next 12 months.
    This is a critical warning. We should investigate the cause, perhaps by
    launching a new marketing campaign or analyzing customer feedback."
    
    Example 3:
    (Data is flat)
    "Sales are forecasted to be stable but flat for the next year.
    While stable, this indicates a lack of growth. It might be a good time to
    explore new market segments or product promotions."

    Now, generate a 2-3 sentence, insightful, and suggestive summary for the data above:
    """
    
    print("Calling Gemini to generate forecast summary...")
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error during summary generation: {e}")
        # Failsafe: return a simple, robotic summary
        change_percent = ((first_forecast_val - last_historical_val) / last_historical_val) * 100
        return f"Forecast complete. The model predicts sales for the next month to be {first_forecast_val:,.2f}, a {change_percent:+.2f}% change from the last known month."
# --- END OF NEW FUNCTION ---


def get_forecast_columns(schema: dict):
    """
    AI Call #1: Asks the AI to identify the correct Date and Sales columns.
    (This function is unchanged)
    """
    if not api_key:
        return {"error": "API key not configured."}
        
    schema_string = "\n".join([f"- {col} (type: {dtype})" for col, dtype in schema.items()])
    
    prompt = f"""
    You are a data scientist. Your job is to identify the correct columns for a
    time-series sales forecast from the given schema.
    
    You MUST return a JSON object with three keys:
    1. "month_col": The name of the column that represents the month (e.g., 'OrderMonth', 'Month').
    2. "year_col": The name of the column that represents the year (e.g., 'OrderYear', 'Year').
    3. "sales_col": The name of the column that represents the sales value (e.g., 'Total Price', 'Amount', 'Sales').
    
    * If a single, clean date column (like 'OrderDate') exists, you can put it in 'month_col' and set 'year_col' to null.
    
    --- DATAFRAME SCHEMA ---
    {schema_string}
    ---
    
    Example 1 (Separate Columns):
    (Schema has 'OrderMonth', 'OrderYear', 'Total Price')
    {{
      "month_col": "OrderMonth",
      "year_col": "OrderYear",
      "sales_col": "Total Price"
    }}
    
    Example 2 (Single Date Column):
    (Schema has 'OrderDate', 'Sales')
    {{
      "month_col": "OrderDate",
      "year_col": null,
      "sales_col": "Sales"
    }}
    
    Now, generate the JSON for the schema I provided.
    """
    
    print("Calling Gemini to identify forecast columns...")
    try:
        response = model.generate_content(prompt)
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_response_text)
    except Exception as e:
        print(f"Error calling/parsing Gemini JSON: {e}")
        return {"error": str(e)}

def run_sales_forecast(df: pd.DataFrame, sales_col: str, month_col: str, year_col: str = None):
    """
    The main Data Science function.
    It now calls the new AI summary function at the end.
    """
    try:
        # --- 1. Data Pre-processing (Unchanged) ---
        print(f"Running forecast on sales_col='{sales_col}', month_col='{month_col}', year_col='{year_col}'")
        
        if year_col:
            df['__temp_date_str'] = df[year_col].astype(str) + '-' + df[month_col].astype(str)
            df['__temp_date'] = pd.to_datetime(df['__temp_date_str'], format='%Y-%B')
        else:
            df['__temp_date'] = pd.to_datetime(df[month_col], errors='coerce')

        df = df.dropna(subset=['__temp_date', sales_col])
        
        if df.empty:
            return {"error": "The data was empty after cleaning. Check the date and sales columns."}

        df = df.set_index('__temp_date')
        monthly_sales = df[sales_col].resample('ME').sum()
        
        if len(monthly_sales) < 24:
            return {"error": f"Not enough data for a reliable forecast. Need at least 24 months of data, but found only {len(monthly_sales)}."}

        # --- 2. Train the SARIMA Model (Unchanged) ---
        print("Training SARIMA model...")
        model = SARIMAX(monthly_sales,
                        order=(1, 1, 1),
                        seasonal_order=(1, 1, 0, 12),
                        enforce_stationarity=False,
                        enforce_invertibility=False)
        
        results = model.fit(disp=False)

        # --- 3. Generate Forecast (Unchanged) ---
        print("Generating 12-month forecast...")
        forecast = results.get_forecast(steps=12)
        predicted_mean = forecast.predicted_mean
        confidence_intervals = forecast.conf_int(alpha=0.05)
        
        # --- 4. Format Data for Chart.js (Dates/Values) ---
        historical_labels = list(monthly_sales.index.strftime('%Y-%m'))
        historical_values = [float(v) for v in monthly_sales.values]
        
        forecast_labels = list(predicted_mean.index.strftime('%Y-%m'))
        forecast_values = [float(v) for v in predicted_mean.values]
        
        lower_ci = [float(v) for v in confidence_intervals.iloc[:, 0]]
        upper_ci = [float(v) for v in confidence_intervals.iloc[:, 1]]

        # --- 5. THIS IS THE NEW PART ---
        # Instead of writing a robotic summary, we call our new AI function
        print("Generating AI summary...")
        summary = generate_forecast_summary(historical_values, forecast_values, sales_col)
        # --- END OF NEW PART ---

        return {
            "summary": summary, # This is now the new AI-generated summary
            "historical_labels": historical_labels,
            "historical_values": historical_values,
            "forecast_labels": forecast_labels,
            "forecast_values": forecast_values,
            "lower_ci": lower_ci,
            "upper_ci": upper_ci,
        }

    except KeyError as e:
        print(f"Forecast failed with KeyError: {e}")
        return {"error": f"The AI picked a column that doesn't exist: {e}. Please check your file."}
    except Exception as e:
        print(f"Forecast failed with unexpected error: {e}")
        return {"error": f"An error occurred during forecasting: {e}"}