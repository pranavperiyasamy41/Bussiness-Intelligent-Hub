import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load your local .env file
load_dotenv()

# Get the key (checking both names you might have used)
my_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
genai.configure(api_key=my_key)

print("--- AVAILABLE MODELS ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print("Error:", e)