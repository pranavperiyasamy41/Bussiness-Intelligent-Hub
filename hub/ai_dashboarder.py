import google.generativeai as genai
from django.conf import settings
import pandas as pd
import json

# --- Global AI Configuration ---
api_key = settings.GOOGLE_AI_API_KEY
if api_key:
    genai.configure(api_key=api_key)
# --- THIS IS THE FIX: Reverted to the Flash model ---

model = genai.GenerativeModel('gemini-2.5-flash-lite')
# --- END OF FIX ---
# -----------------------------

def get_dashboard_layout(schema: dict):
    """
    AI Call #1: The "Planner"
    Asks the AI to generate a JSON "plan" for 4-6 charts.
    """
    if not api_key:
        return {"error": "API key not configured."}
        
    schema_string = "\n".join([f"- {col} (type: {dtype})" for col, dtype in schema.items()])
    
    prompt = f"""
    You are a senior data analyst. Your job is to design a beautiful and insightful
    dashboard for a business user.
    
    You will be given the schema (column names and data types) of a sales file.
    
    Your task is to generate a JSON object that defines 4 to 6 charts for a dashboard.
    You MUST return ONLY the JSON object and no other text.
    
    --- DATAFRAME SCHEMA ---
    {schema_string}
    ---
    
    --- REQUIRED JSON FORMAT ---
    You must generate a JSON object with a single key, "charts", which is a list.
    Each chart object in the list MUST have:
    1.  "title": A human-readable title (e.g., "Sales by City").
    2.  "chart_type": "bar", "pie", or "line".
    3.  "x_col": The column to use for the X-axis (labels).
    4.  "y_col": The column to use for the Y-axis (values).
    5.  "agg_func": The function to use ("sum", "mean", or "count").
    
    --- INTELLIGENT CHART SELECTION RULES ---
    1.  **Line Charts:** You MUST use `chart_type: "line"` if you find a good time-series
        column (e.g., 'OrderMonth', 'OrderYear', 'OrderDate').
    2.  **Pie Charts:** You SHOULD use `chart_type: "pie"` for categorical data with only
        a few (2-6) unique values (e.g., 'ProductCategory', 'PaymentMethod', 'Gender').
    3.  **Bar Charts:** You SHOULD use `chart_type: "bar"` for rankings with many
        categories (e.g., 'Top 10 Products by Sales', 'Sales by City').
    4.  **Variety:** You MUST provide a good mix of chart types. Do NOT just use 'bar' for everything.
    
    ---
    
    Now, generate the JSON for the schema I provided.
    """
    
    print("Calling Gemini Flash for dashboard layout...")
    try:
        # Removed the 'generation_config' as the prompt is now strict enough
        response = model.generate_content(prompt)
        json_response_text = response.text.strip()
        
        if json_response_text.startswith("```json"):
            json_response_text = json_response_text[7:]
        if json_response_text.endswith("```"):
            json_response_text = json_response_text[:-3]
        
        layout_json = json.loads(json_response_text)
        return layout_json
        
    except Exception as e:
        print(f"Error calling/parsing Gemini JSON: {e}")
        return {"error": str(e)}

def execute_dashboard_queries(df: pd.DataFrame, chart_list: list):
    """
    The "Executor"
    (This function is unchanged, it's already correct)
    """
    chart_data_list = []
    available_columns = {col.lower(): col for col in df.columns} # {lower: RealCase}

    def get_col(col_name):
        if not col_name: return None
        real_col = available_columns.get(col_name.lower())
        if not real_col:
            raise KeyError(f"AI planned to use column '{col_name}', but it wasn't found in the file.")
        return real_col

    for chart_plan in chart_list:
        try:
            title = chart_plan.get("title", "Untitled Chart")
            chart_type = chart_plan.get("chart_type", "bar")
            x_col = get_col(chart_plan.get("x_col"))
            y_col = get_col(chart_plan.get("y_col"))
            agg_func = chart_plan.get("agg_func", "sum")
            
            # --- Perform the Pandas Query ---
            if chart_type == "line":
                chart_data = df.groupby(x_col)[y_col].agg(agg_func)
                try:
                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                    chart_data = chart_data.reindex(month_order, fill_value=0)
                except Exception as e:
                    print(f"Could not sort by month, using default sort: {e}")
                    chart_data = chart_data.sort_index()
            elif chart_type == "bar":
                chart_data = df.groupby(x_col)[y_col].agg(agg_func).nlargest(10).sort_values(ascending=False)
            elif chart_type == "pie":
                chart_data = df.groupby(x_col)[y_col].agg(agg_func).nlargest(5)
            else:
                continue
            
            # --- Format for Chart.js ---
            chart_data_list.append({
                "title": title,
                "chart_type": chart_type,
                "labels": list(chart_data.index.astype(str)),
                # This is the fix for the 'TypeError: int64 is not JSON serializable'
                "values": [float(v) for v in chart_data.values],
            })
            
        except KeyError as e:
            print(f"Skipping chart '{title}' due to error: {e}")
            chart_data_list.append({
                "title": f"{title} (Failed)",
                "chart_type": "error",
                "error_message": str(e),
            })
        except Exception as e:
            print(f"Skipping chart '{title}' due to unexpected error: {e}")
            chart_data_list.append({
                "title": f"{title} (Failed)",
                "chart_type": "error",
                "error_message": str(e),
            })
            
    return chart_data_list