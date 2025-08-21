import base64
from bs4 import BeautifulSoup
import logging
import os
import google.generativeai as genai
import json
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logging.info("Gmail Agent: Gemini API configured successfully.")
except Exception as e:
    logging.error(f"Gmail Agent: Error configuring Gemini API: {e}")
    model = None

def analyze_emails(emails):
    """
    Analyzes a list of emails using the Gemini API to extract to-dos.
    """
    if not model:
        return {"todos": [], "team_updates": []} # Return empty structure on error

    todos = []
    for email in emails:
        try:
            payload = email.get("payload", {})
            headers = payload.get("headers", [])
            
            subject = ""
            sender = ""
            for header in headers:
                if header["name"].lower() == "subject":
                    subject = header["value"]
                if header["name"].lower() == "from":
                    sender = header["value"]

            body_html = ""
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/html":
                        data = part["body"].get("data")
                        if data:
                            body_html = base64.urlsafe_b64decode(data).decode("utf-8")
                        break
            elif "body" in payload and "data" in payload["body"]:
                data = payload["body"]["data"]
                body_html = base64.urlsafe_b64decode(data).decode("utf-8")

            soup = BeautifulSoup(body_html, "lxml")
            text_body = soup.get_text(separator="\n", strip=True)[:4000]

            prompt = f"""
            Analyze the content of the following email.
            
            From: {sender}
            Subject: {subject}
            Body Snippet: {text_body}

            1.  **Classification**: Is this email a 'to-do' that requires a direct action from the recipient? Answer 'yes' or 'no'.
            2.  **Summary**: If it is a 'to-do', provide a concise one-sentence summary of the required action.
            3.  **Link**: Extract the single most relevant hyperlink from the email body, if one exists.

            Respond with a single JSON object with the keys "is_todo", "summary", and "link".
            """

            logging.info(f"Analyzing email for to-dos from {sender} with subject '{subject}'...")
            response = model.generate_content(prompt)
            
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            analysis = json.loads(cleaned_response)

            if analysis.get("is_todo") == "yes":
                todos.append({
                    "task": analysis.get("summary", subject),
                    "link": analysis.get("link", "")
                })

        except Exception as e:
            logging.error(f"Could not process email for to-do: {subject}. Error: {e}")
            continue

    return {"todos": todos}
