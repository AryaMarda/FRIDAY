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
            You are an expert at analyzing email content to help users prioritize their work. You will be given an email's sender, subject, and body text. Your task is to perform three specific actions based on the content.
            Analyze the content of the following email and classify it.
            
            From: {sender}
            Subject: {subject}
            Body Snippet: {text_body}

            1.  **Classification**: **Classify the email's purpose.** Determine if the email is a 'to-do', 'team_update', or 'none'.
    * A **'to-do'** email requires a direct action or response from the recipient. Look for clear requests, questions, or assigned tasks.
    * A **'team_update'** email provides information, such as a status report, meeting minutes, or a general announcement. It doesn't typically require a direct action from the recipient.
    * If the email does not fit into either category, classify it as **'none'**
            2.  **Summary**: **Provide a one-sentence summary.** If the email is classified as 'to-do' or 'team_update', create a concise, single-sentence summary of its main point. This summary should capture the essence of the email without unnecessary details.
            3.  **Link**: **Extract a single hyperlink.** Scan the email body for any hyperlinks (URLs). If a link exists, extract the most relevant one. If there are multiple links, prioritize the one most central to the email's purpose. If no links are present, return 'null'

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