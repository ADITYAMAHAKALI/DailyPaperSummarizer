
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
def configure_gemini():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

configure_gemini()

# Create the model
generation_config = {
    "temperature": 0.1,
    "top_p": 0.90,
    "top_k": 50,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

def generate_insights(formatted_prompt: str):
    try:
        result = model.generate_content(formatted_prompt)
        api_output = result.text
        return api_output
    except Exception as e:
        print(f"Error generating insights: {e}")
        return None
    
if __name__ == "__main__":
    prompt = "What are the top 5 most popular books in the world?"
    insights = generate_insights(prompt)
    if insights:
        print(insights)