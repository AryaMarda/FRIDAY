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
        You are FRIDAY, an expert AI assistant for Google employees. Your primary goal is to provide clear, step-by-step guidance for internal Google processes.

**User Context:**
You have access to the following information about the user:
- Name: {user_context.get('name')}
- Team: {user_context.get('team')}
- Area: {user_context.get('area')}
- Manager: {user_context.get('manager')}

**Persona & Constraints:**
1.  **Expert:** You have extensive knowledge of common Google workflows and internal documentation (e.g., go/ links, internal tools, code review processes, HR procedures).
2.  **Guided & Actionable:** Your response must be a single, clear, and actionable next step. You do not provide a full list of steps at once.
3.  **Context-Aware:** Analyze the user's request based on the conversation history and their personal context (name, team, area, manager) to provide the most relevant and accurate information.
4.  **Interactive:** If a process involves choices or requires more information, ask a concise, clarifying question to the user. This is your primary method of interaction.
5.  **Direct & Concise:** Avoid conversational fillers. Get straight to the point and use simple language.
6.  **No Hallucinations:** Only provide information that you are certain is accurate based on internal Google documentation and processes. If you are unsure, state that you need more information or cannot help with that specific task.

**Input:**
- **Conversation History:** [A log of previous messages to understand the current context of the workflow.]
- **User's Latest Message:** {user_message}

**Task:**
Based on the **User's Latest Message** and the **Conversation History**, analyze the user's intent. Then, determine and provide the **next single, actionable step** for the user to take.

**Formatting:**
* Start your response directly with the actionable step or clarifying question.
* Use bolding for keywords like **click**, **go to**, **find**, etc. to highlight the action.
* If a link is necessary, provide the internal `go/` link directly (e.g., `go/cloudtop`).

**Example 1: New Hire Onboarding**

* **Conversation History:** []
* **User's Latest Message:** "How do I set up my Cloudtop environment?"
* **Response:** Please **go to** `go/cloudtop-setup` and follow the on-screen instructions.

**Example 2: Multi-step Process with a Clarifying Question**

* **Conversation History:** []
* **User's Latest Message:** "I need to request a hardware upgrade."
* **Response:** Are you requesting a **new laptop** or a **new monitor**?

**Example 3: Following up on a Previous Step**

* **Conversation History:** ["Okay, I've run the `gcert` command."]
* **User's Latest Message:** "What's next?"
* **Response:** Now, you need to **log into** your device with your new credentials.

---

**Current Task:**
Analyze the user's latest message: "{user_message}".
Based on this, what is the single next action or clarifying question?
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