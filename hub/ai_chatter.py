import google.generativeai as genai
from django.conf import settings
import pandas as pd
from .models import RetailFile, ChatMessage
import json
import io
import sys

# --- Global AI Configuration ---
api_key = settings.GOOGLE_AI_API_KEY
if api_key:
    genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash-lite')
# -----------------------------

# --- THIS IS THE NEW, SAFER "NATURALIZER" ---
def naturalize_response(user_message: str, data_answer: str):
    """
    AI Call #3: Turns a data-heavy answer into a natural, human-like response.
    This version has a very strict prompt to prevent hallucination.
    """
    print(f"Naturalizing: Question='{user_message}', Answer='{data_answer}'")
    if not api_key:
        return data_answer # Failsafe

    # If the answer is already a sentence, just return it.
    if "I'm sorry" in data_answer:
        return data_answer

    naturalizer_prompt = f"""
    You are a helpful AI assistant. Your ONLY job is to take a User's Question and
    a pre-calculated Data Answer and combine them into a single, natural-sounding, 
    human-like sentence.

    --- CRITICAL RULE ---
    You MUST use the exact "Data Answer" provided. You are NOT allowed to
    change, invent, or hallucinate any numbers.
    ---

    Example 1:
    User Question: "how many male customers are there?"
    Data Answer: "52"
    Your Response: "There are 52 male customers."
    
    Example 2:
    User Question: "what is the total sales?"
    Data Answer: "45,123.50"
    Your Response: "The total sales are 45,123.50."
    
    Example 3:
    User Question: "which brand's product is sold more?"
    Data Answer: "Sony"
    Your Response: "The brand with the most products sold is Sony."
    
    Example 4:
    User Question: "chennai la sales evlo?"
    Data Answer: "12,500.00"
    Your Response: "In Chennai, the total sales are 12,500.00."

    Now, do this for the following:
    
    User Question: "{user_message}"
    Data Answer: "{data_answer}"
    Your Response:
    """
    
    try:
        response = model.generate_content(naturalizer_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error during naturalization: {e}")
        return data_answer # Failsafe, just return the raw data

def execute_json_query(df: pd.DataFrame, query_json: dict, user_message: str):
    """
    Safely builds and executes a Pandas query from a JSON object.
    This function now returns ONLY the raw data answer (e.g., "148").
    """
    try:
        operation = query_json.get("operation")
        available_columns = {col.lower(): col for col in df.columns} # {lower: RealCase}
        
        # --- Helper function to safely get real column name ---
        def get_col(col_name):
            if not col_name: return None
            real_col = available_columns.get(str(col_name).lower())
            if not real_col:
                raise KeyError(f"I'm sorry, I couldn't find a column in your file that matches '{col_name}'.")
            return real_col
        # --------------------------------------------------------

        # 1. Start with the full DataFrame
        filtered_df = df.copy()
        
        # 2. Apply All Filters (if any)
        query_filters = query_json.get('filters', [])
        if query_filters:
            for f in query_filters:
                filter_col_name = f.get('column')
                filter_val = f.get('value')
                
                real_col_name = get_col(filter_col_name) # This can raise KeyError
                
                # Apply the filter (case-insensitive)
                filtered_df = filtered_df[filtered_df[real_col_name].astype(str).str.lower() == str(filter_val).lower()]

        # 3. Perform Aggregation
        
        # --- OPERATION: SUM or MEAN ---
        if operation == 'sum' or operation == 'mean':
            agg_col_name = query_json.get('agg_col')
            agg_col = get_col(agg_col_name)
            
            if operation == 'sum':
                result = filtered_df[agg_col].sum()
            else:
                result = filtered_df[agg_col].mean()
            return f"{result:,.2f}" # Return just the formatted number

        # --- OPERATION: COUNT ---
        elif operation == 'count':
            result = filtered_df.shape[0]
            return f"{result}" # Return just the number
            
        # --- OPERATION: GROUPBY (e.g., which brand sold most) ---
        elif operation == 'groupby_agg':
            groupby_col_name = query_json.get('groupby_col')
            agg_col_name = query_json.get('agg_col')
            agg_func = query_json.get('agg_func')
            
            groupby_col = get_col(groupby_col_name)
            agg_col = get_col(agg_col_name)
            
            result_series = filtered_df.groupby(groupby_col)[agg_col].agg(agg_func)
            
            if agg_func == 'idxmax':
                result = result_series.idxmax()
                return f"{result}" # Return just the winning name
            else:
                # Return Top 5 for a general groupby
                result = result_series.nlargest(5)
                return f"Here are the Top 5 {groupby_col_name} by {agg_col_name}:\n{result.to_string()}"

        else:
            return f"I'm sorry, I'm not set up to perform the operation '{operation}' yet."

    except KeyError as e:
        return str(e) # This will return our "I'm sorry, I couldn't find..." message
    except Exception as e:
        return f"I'm sorry, I ran into a Python error: {e}"
# ----------------------------------------------------------------

def get_ai_chat_response(retail_file: RetailFile, user_message: str):
    """
    Main function. Uses 3 AI calls: Classify, Generate JSON, Naturalize
    """
    if not api_key:
        return "Error: GOOGLE_AI_API_KEY not configured."
    
    # --- STEP 1: Classify the user's intent (Unchanged) ---
    classification_prompt = f"""
    You are an intent classifier. You must classify the user's message into one of two categories:
    1.  **GREETING**: For hellos, goodbyes, thank-yous, or simple small talk.
    2.  **DATA_QUERY**: For any question that requires looking at data.
    User Message: "{user_message}"
    Category:
    """
    try:
        response = model.generate_content(classification_prompt)
        intent = response.text.strip().upper()
    except Exception as e:
        print(f"Error during classification: {e}")
        return f"Error connecting to AI: {e}"

    print(f"User Message: '{user_message}' -> Intent Classified as: {intent}")

    # --- STEP 2: Execute based on the intent ---
    
    # ** IF IT'S A GREETING ** (Unchanged)
    if "GREETING" in intent or user_message.lower() in ["hi", "hello", "vanakkam", "thanks", "nandri"]:
        # (This part is working, so we keep it)
        print("Intent is GREETING. Returning a manual response.")
        if user_message.lower() in ["hi", "hello"]:
            return "Hello! I'm InsightBot. How can I help you with your sales data today?"
        if user_message.lower() in ["vanakkam"]:
            return "Vanakkam! Unga data pathi enna kelvi iruku?"
        if user_message.lower() in ["thanks", "nandri"]:
            return "You're welcome! Is there anything else I can help you with?"
        return "Hello! I'm InsightBot, your data assistant. How can I help?"

    # ** IF IT'S A DATA_QUERY **
    elif "DATA_QUERY" in intent:
        print("Intent is DATA_QUERY. Proceeding to JSON generation.")
        try:
            file_path = retail_file.file.path
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            return f"Error loading data file: {e}"
            
        schema = retail_file.schema_json
        schema_string = "\n".join([f"- {col} (type: {dtype})" for col, dtype in schema.items()])
        
        history = ChatMessage.objects.filter(retail_file=retail_file).order_by('timestamp')
        chat_history_str = "\n".join(
            [f"User: {msg.message}\nAI: {msg.response}" for msg in history]
        )
        
        # --- AI Call #2: Generate JSON Query (Prompt is unchanged) ---
        data_prompt = f"""
        You are a data analyst. Your job is to translate a user's question into a
        JSON object that can be used to query a Pandas DataFrame.
        
        You MUST follow these rules:
        1.  Look at the user's question and the "DATAFRAME SCHEMA".
        2.  Find the *actual* column names from the schema that match the user's intent.
        3.  Generate ONLY a valid JSON object. Do not add any text before or after it.
        
        --- DATAFRAME SCHEMA ---
        {schema_string}
        ---
        
        --- AVAILABLE JSON FORMATS ---
        1.  For SUM or MEAN (with optional filters):
            {{"operation": "sum", "agg_col": "ACTUAL_COLUMN_NAME", "filters": [{{"column": "COL_NAME", "value": "FILTER_VAL"}}]}}
            (agg_func can be "sum" or "mean")
            
        2.  For COUNT (with optional filters):
            {{"operation": "count", "filters": [{{"column": "COL_NAME", "value": "FILTER_VAL"}}]}}
            
        3.  For GROUPBY & FIND MAX/MEAN (e.g., "which brand sold most?"):
            {{"operation": "groupby_agg", "groupby_col": "GROUPBY_COLUMN", "agg_col": "AGGREGATE_COLUMN", "agg_func": "idxmax"}}
            (agg_func can be "idxmax" for "which is best" or "mean" for "average by group")
            
        4.  If you cannot understand or find a column:
            {{"operation": "clarify", "message": "I'm sorry, I couldn't find a column for [user's term]. Which column should I use?"}}
        ---
        
        Chat History (for context):
        {chat_history_str}
        
        User Question:
        "{user_message}"
        
        --- EXAMPLES (Based on schema in user's prompt) ---
        
        User: "Which brand generated the most revenue (Total Price)?"
        AI: {{"operation": "groupby_agg", "groupby_col": "Brand", "agg_col": "Total Price", "agg_func": "idxmax"}}

        User: "How many 'Negative' reviews did the 'Electronics' category receive?"
        AI: {{"operation": "count", "filters": [{{"column": "ReviewSentiment", "value": "Negative"}}, {{"column": "Product Category", "value": "Electronics"}}]}}
        
        User: "What were the total sales for 'Clothing' in 'Chennai'?"
        AI: {{"operation": "sum", "agg_col": "Total Price", "filters": [{{"column": "Product Category", "value": "Clothing"}}, {{"column": "CustomerCity", "value": "Chennai"}}]}}
        
        User: "Coimbatore-la, '18-25' age group la irukavanga ethana per UPI use pannirukanga?"
        AI: {{"operation": "count", "filters": [{{"column": "CustomerCity", "value": "Coimbatore"}}, {{"column": "AgeGroup", "value": "18-25"}}, {{"column": "PaymentMethod", "value": "UPI"}}]}}
        
        User: "Which 'Product Category' has the highest average 'CustomerRating'?"
        AI: {{"operation": "groupby_agg", "groupby_col": "Product Category", "agg_col": "CustomerRating", "agg_func": "idxmax"}}
        
        User: "What was the total profit?"
        AI: {{"operation": "clarify", "message": "I'm sorry, I couldn't find a 'Profit' column in your file. Which column should I use to calculate profit?"}}
        ---
        
        Now, generate ONLY the JSON object for the user's question:
        """
        
        try:
            response = model.generate_content(data_prompt)
            json_response_text = response.text.strip()
            
            if json_response_text.startswith("```json"):
                json_response_text = json_response_text[7:]
            if json_response_text.endswith("```"):
                json_response_text = json_response_text[:-3]
            
            query_json = json.loads(json_response_text)
            
        except Exception as e:
            print(f"Error calling/parsing Gemini JSON: {e}")
            return f"Error connecting to AI: {e}"
        
        print(f"AI-generated JSON: {query_json}")
        
        # --- Python Code: Execute the JSON query ---
        if query_json.get("operation") == "clarify":
            return query_json.get("message", "I'm not sure how to answer that. Can you rephrase?")
        
        # This function now returns the raw data (e.g., "148" or "Sony")
        data_answer = execute_json_query(df, query_json, user_message)
        
        # Check for errors from our code
        if "I'm sorry" in data_answer:
            return data_answer

        # --- AI Call #3: Naturalize the response ---
        final_answer = naturalize_response(user_message, data_answer)
        return final_answer
        
    else:
        # Fallback in case classification is unclear
        return "I'm not sure how to respond to that. Can you rephrase your question about the data?"