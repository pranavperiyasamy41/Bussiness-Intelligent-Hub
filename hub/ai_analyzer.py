import google.generativeai as genai
from django.conf import settings
from .models import UploadedFile, AnalysisResult
from .utils import read_file_content
import json

def perform_analysis(uploaded_file_id):
    """
    Main function to perform AI analysis on an uploaded file.
    """
    try:
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
    except UploadedFile.DoesNotExist:
        print(f"File ID {uploaded_file_id} not found.")
        return

    if AnalysisResult.objects.filter(file=uploaded_file).exists():
        print(f"File {uploaded_file.file.name} already analyzed.")
        return

    file_path = uploaded_file.file.path
    
    print(f"Reading content from {file_path}...")
    text_content = read_file_content(file_path)
    
    if not text_content or text_content.startswith("Error"):
        print(f"Could not read content: {text_content}")
        return

    api_key = settings.GOOGLE_AI_API_KEY
    if not api_key:
        print("GOOGLE_AI_API_KEY not found in settings.py")
        return
        
    genai.configure(api_key=api_key)
    
    # --- THIS IS THE FIX: Reverted to the Flash model ---
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    # --- END OF FIX ---

    prompt = f"""
    You are a professional business analyst. I will provide you with a document
    containing raw customer feedback.
    
    Your task is to analyze the text and return ONLY a valid JSON object.
    Do not add any text before or after the JSON.
    
    The JSON object MUST have the following structure:
    {{
      "overall_sentiment": "A one-sentence conclusion (e.g., 'Positive, with concerns about pricing.')",
      "sentiment_color": "One of: 'success' (for positive), 'warning' (for mixed), 'danger' (for negative)",
      "positive_themes": [
        "A key positive theme",
        "Another key positive theme",
        "..."
      ],
      "areas_for_improvement": [
        "A key area for improvement",
        "Another key area for improvement",
        "..."
      ],
      "sentiment_distribution": {{
        "positive": <number of positive comments>,
        "negative": <number of negative comments>,
        "neutral": <number of neutral comments>
      }}
    }}
    
    Here is the customer feedback text:
    ---
    {text_content}
    ---
    """

    print("Calling the Gemini Flash API...")
    try:
        # Removed the 'generation_config' as the prompt is now strict enough
        response = model.generate_content(prompt)
        ai_response_text = response.text.strip()
        
        # Clean the response to ensure it's valid JSON
        if ai_response_text.startswith("```json"):
            ai_response_text = ai_response_text[7:]
        if ai_response_text.endswith("```"):
            ai_response_text = ai_response_text[:-3]
        
        ai_json = json.loads(ai_response_text)
        
        ai_summary = f"""
        Overall Sentiment: {ai_json.get('overall_sentiment', 'N/A')}
        Positive: {', '.join(ai_json.get('positive_themes', []))}
        Improvements: {', '.join(ai_json.get('areas_for_improvement', []))}
        """

    except Exception as e:
        print(f"Error calling/parsing Gemini API: {e}")
        ai_summary = f"Error during analysis. Please try again. Details: {e}"
        ai_json = {"error": str(e)}

    AnalysisResult.objects.create(
        file=uploaded_file,
        result_text=ai_summary,
        result_json=ai_json
    )
    
    print(f"Analysis complete for {uploaded_file.file.name}. Result saved.")