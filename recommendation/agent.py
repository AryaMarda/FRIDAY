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
    logging.info("Recommendation Agent: Gemini API configured successfully.")
except Exception as e:
    logging.error(f"Recommendation Agent: Error configuring Gemini API: {e}")
    model = None

def generate_recommendations():
    """
    Orchestrates a multi-step LLM process to generate personalized recommendations.
    """
    if not model:
        return {"error": "The Gemini API is not configured."}

    user_context = get_user_context()
    # Use .get() for safe access to context keys
    if user_context.get("name", "Not Set") == "Not Set":
        return {"error": "User context is not set. Please edit context.json."}

    try:
        # Safely access context values with defaults
        user_role = user_context.get('role', 'employee')
        user_team = user_context.get('team', 'team')
        user_area = user_context.get('area', 'area')

        # Step 1: Get role-specific skill topics
        prompt1 = f"Based on a Google employee with the role '{user_role}' on the '{user_team}' team, what are 3 highly relevant, specific technical skills or tools they should learn about? Respond with a simple comma-separated list."
        logging.info("Step 1: Getting role-specific skills...")
        role_skills_response = model.generate_content(prompt1)
        role_skills = role_skills_response.text.strip().split(',')

        # Step 2: Get trending topics
        prompt2 = f"What are 2 major, trending topics in the tech industry that would be valuable for a Googler in a '{user_area}' role to learn about? Respond with a simple comma-separated list."
        logging.info("Step 2: Getting trending topics...")
        trending_topics_response = model.generate_content(prompt2)
        trending_topics = trending_topics_response.text.strip().split(',')

        # Step 3: Get event ideas
        prompt3 = f"Suggest 2 types of internal Google events (like workshops, tech talks, or speaker series) that would be relevant for a '{user_role}'. Respond with a simple comma-separated list."
        logging.info("Step 3: Getting event ideas...")
        event_ideas_response = model.generate_content(prompt3)
        event_ideas = event_ideas_response.text.strip().split(',')

        # Step 4: Final Synthesis
        final_prompt = f"""
        You are a personalized recommendation engine for Google employees.
        Your task is to create a structured JSON feed of career opportunities.
        Use the provided user context and the generated topic lists to create a final, user-friendly recommendation object.
        For each recommendation, provide a brief, compelling reason why it's relevant to the user.
        
        User Context: {json.dumps(user_context)}
        
        Identified Role-Specific Skills: {role_skills}
        Identified Trending Topics: {trending_topics}
        Identified Event Types: {event_ideas}

        Generate a JSON object with three keys: "role_specific_upskilling", "trending_topics", and "internal_events".
        Each key should contain a list of JSON objects, where each object has "recommendation" and "reason" fields.
        Example for a single item: {{"recommendation": "Advanced Kubernetes Workshop", "reason": "Deepens your expertise in cloud infrastructure, which is crucial for your role on the SRE team."}}
        """
        logging.info("Step 4: Synthesizing final recommendations...")
        final_response = model.generate_content(final_prompt)
        
        # Clean up the response to be valid JSON
        cleaned_response = final_response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)

    except Exception as e:
        logging.error(f"Error in recommendation generation: {e}")
        return {"error": str(e)}