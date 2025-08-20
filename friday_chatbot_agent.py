import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv
from context_manager import get_user_context # Import the context manager

# --- Configuration ---
load_dotenv()

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logging.info("Gemini API configured successfully.")
except Exception as e:
    logging.error(f"Error configuring Gemini API: {e}")
    model = None

# In-memory session storage
SESSIONS = {}

def get_friday_response(user_message, session_id):
    """
    Generates a response using the live Gemini API, enriched with user context.
    """
    if not model:
        return {"response": "Error: The Gemini API is not configured."}

    if session_id not in SESSIONS:
        SESSIONS[session_id] = {"history": []}
    
    session = SESSIONS[session_id]
    
    gemini_history = []
    for message in session["history"]:
        gemini_history.append({'role': message['role'], 'parts': message['parts']})

    # Fetch the user's global context
    user_context = get_user_context()

    try:
        chat = model.start_chat(history=gemini_history)
        
        # The prompt is now enriched with the user's details
        prompt = f"""
        You are FRIDAY, an expert AI assistant for Google employees.
        
        Here is the context about the user you are assisting:
        - Name: {user_context.get('name')}
        - Team: {user_context.get('team')}
        - Area: {user_context.get('area')}
        - Manager: {user_context.get('manager')}

        Your goal is to provide clear, step-by-step guidance for internal Google processes.
        Analyze the user's request based on the conversation history and their context.
        Use your extensive knowledge of common Google workflows to provide the next single, actionable step.
        If a process involves choices, ask a clarifying question.
        
        User's latest message: "{user_message}"
        """
        
        logging.info(f"Sending enriched prompt to Gemini for session {session_id}...")
        response = chat.send_message(prompt)
        bot_message = response.text
        
        session["history"].append({"role": "user", "parts": [user_message]})
        session["history"].append({"role": "model", "parts": [bot_message]})
        
        return {"response": bot_message}

    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return {"response": f"An error occurred while contacting the Gemini API: {e}"}