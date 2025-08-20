from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging
import os

# Gmail agent imports
from gmail.service import get_gmail_service, get_todays_emails
from agent.agent import analyze_emails as analyze_gmail_emails

# FRIDAY chatbot import
from friday_chatbot_agent import get_friday_response

# Context Manager import
from context_manager import get_user_context

# New Recommendation agent import
from recommendation.agent import generate_recommendations

# --- Basic Setup ---
app = FastAPI(title="Personal AI Assistant")
logging.basicConfig(level=logging.INFO)

# --- API Routers ---
api_router = APIRouter(prefix="/api")

# --- Gmail Agent API ---
@api_router.get("/gmail/today", tags=["API - Gmail Agent"])
def get_today_summary_api():
    """API endpoint to get email summary data."""
    logging.info("Fetching Gmail service...")
    service = get_gmail_service()
    if not service:
        raise HTTPException(status_code=500, detail="Failed to connect to Gmail service.")
    
    logging.info("Fetching today's emails...")
    emails = get_todays_emails(service)
    if emails is None:
        raise HTTPException(status_code=500, detail="Failed to fetch emails.")
    
    logging.info(f"Found {len(emails)} emails to analyze.")
    summary = analyze_gmail_emails(emails)
    logging.info(f"Summary generated: {summary}")
    return summary

# --- FRIDAY Chatbot API ---
class ChatRequest(BaseModel):
    message: str
    session_id: str

@api_router.post("/friday/chat", tags=["API - FRIDAY Chatbot"])
def chat_with_friday(request: ChatRequest):
    return get_friday_response(request.message, request.session_id)

# --- Recommendation API ---
@api_router.get("/recommendations", tags=["API - Recommendation Engine"])
def get_recommendations_api():
    """API endpoint to get recommendation data."""
    recommendations = generate_recommendations()
    if "error" in recommendations:
        raise HTTPException(status_code=500, detail=recommendations["error"])
    return recommendations

# --- Context API ---
@api_router.get("/context", tags=["API - Context"])
def read_user_context():
    """Endpoint to get the current user's details from context.json."""
    return get_user_context()

# --- Main Application Setup ---
app.include_router(api_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Page Serving ---
@app.get("/", response_class=FileResponse, tags=["Pages"])
async def read_chatbot_page():
    return FileResponse("./static/index.html")

@app.get("/today", response_class=FileResponse, tags=["Pages"])
async def read_today_page():
    return FileResponse("./static/gmail_today.html")

@app.get("/recommendations", response_class=FileResponse, tags=["Pages"])
async def read_recommendations_page():
    return FileResponse("./static/recommendations.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
