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
    Analyzes a list of emails using the Gemini API to extract to-dos and team updates.
    """
    if not model:
        return {"error": "The Gemini API is not configured."}

    todos = []
    team_updates = []

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
            text_body = soup.get_text(separator="\n", strip=True)[:4000] # Limit body size

            prompt = f"""
            Analyze the content of the following email and classify it.
            
            From: {sender}
            Subject: {subject}
            Body Snippet: {text_body}

            1.  **Classification**: Is this email primarily a 'to-do' (requiring a direct action from the recipient), a 'team_update' (a general announcement, meeting notes, or status update), or 'none'?
            2.  **Summary**: If it is a 'to-do' or 'team_update', provide a concise one-sentence summary.
            3.  **Link**: Extract the single most relevant hyperlink from the email body, if one exists.

            Respond with a single JSON object with the keys "classification", "summary", and "link".
            """

            logging.info(f"Analyzing email from {sender} with subject '{subject}'...")
            response = model.generate_content(prompt)
            
            # Clean up the response to be valid JSON
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            analysis = json.loads(cleaned_response)

            if analysis.get("classification") == "to-do":
                todos.append({
                    "task": analysis.get("summary", subject),
                    "link": analysis.get("link", "")
                })
            elif analysis.get("classification") == "team_update":
                team_updates.append({
                    "subject": subject,
                    "update": analysis.get("summary", "No summary available."),
                    "link": analysis.get("link", "")
                })

        except Exception as e:
            logging.error(f"Could not process email: {subject}. Error: {e}")
            continue

    return {"todos": todos, "team_updates": team_updates}