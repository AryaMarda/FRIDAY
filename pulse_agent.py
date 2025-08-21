import logging
import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
from context_manager import get_user_context

# --- Configuration ---
load_dotenv()

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logging.info("Pulse Agent: Gemini API configured successfully.")
except Exception as e:
    logging.error(f"Pulse Agent: Error configuring Gemini API: {e}")
    model = None

def get_pulse_updates():
    """
    Uses the Gemini API to generate a "Team & Beyond Pulse" based on user context.
    """
    if not model:
        return {"error": "The Gemini API is not configured."}

    user_context = get_user_context()
    if user_context.get("name", "Not Set") == "Not Set":
        return [] # Return empty list if context is not set

    try:
        prompt = f"""
        You are an AI assistant for a Google employee. Your task is to generate a "Team & Beyond Pulse".
        Based on the user's context, search for and create a summary of recent, major internal news and events.
        "Major" is defined as product releases, new project proposals, or significant internal Google events.

        User Context:
        - Team: {user_context.get('team', 'N/A')}
        - Area: {user_context.get('area', 'N/A')}

        Generate a JSON list of 2-3 items. Each item should be a JSON object with "subject", "update", and "link" keys.
        The "subject" should be a concise title.
        The "update" should be a one-sentence summary.
        The "link" should be a plausible go/ link related to the topic.
        
        Example response:
        [
            {{"subject": "Gemini 1.5 Pro Launch", "update": "The next generation of our most capable model was launched this week with a 1M token context window.", "link": "http://go/gemini-1.5-pro"}},
            {{"subject": "I/O 2025 Registration", "update": "Registration for Google I/O 2025 is now open to all employees.", "link": "http://go/io2025"}}
        ]
        """
        
        logging.info("Generating pulse updates with Gemini API...")
        response = model.generate_content(prompt)
        
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)

    except Exception as e:
        logging.error(f"Error in pulse generation: {e}")
        return []
