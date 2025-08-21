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
        prompt1 = f"""You are FRIDAY, an expert career development partner at Google. Your task is to identify and recommend upskilling topics for a Google employee based on their professional role and team.

        **User Context:**
        - Role: {user_role}
        - Team: {user_team}
        - Area: {user_area}

        **Instructions:**
        1.  **Identify Core Competencies:** Based on the user's role and team, determine the 3-5 most critical skills or knowledge areas that someone in their position should master.
        2.  **Suggest Actionable Topics:** For each core competency, list 2-3 specific, actionable learning topics. These should be things they can immediately start exploring, such as a particular technology, a design pattern, or a project management technique.
        3.  **Provide a Brief Rationale:** For each topic, add a one-sentence explanation of why it is relevant and important for a person in their role.

        **Output Format:**
        Use markdown headings for each core competency, followed by a bulleted list of the recommended topics and their rationales.

        **Example:**
        *If the user's role is "Software Engineer" and their team is "Cloud Infrastructure"*:

        #### Core Competency: Cloud-Native Development
        - **Topic: Containerization with Docker and Kubernetes.** Rationale: Understanding container orchestration is fundamental for managing and deploying scalable applications on Google Cloud.
        - **Topic: Serverless Architecture with Cloud Functions.** Rationale: This enables you to build and deploy event-driven applications without managing servers, a key skill for efficient cloud development.

        #### Core Competency: System Reliability
        - **Topic: Site Reliability Engineering (SRE) Principles.** Rationale: This is a core part of Google's engineering culture and is essential for building robust and scalable systems.
        - **Topic: Incident Management & Post-mortems.** Rationale: Learning how to respond to and analyze system failures is a critical skill for maintaining service health and preventing future issues."""
        logging.info("Step 1: Getting role-specific skills...")
        role_skills_response = model.generate_content(prompt1)
        role_skills = role_skills_response.text.strip().split(',')

        # Step 2: Get trending topics
        prompt2 = f"""
        **User Context:**
        - Role: {user_role}
        - Team: {user_team}
        - Area: {user_area}

        **Instructions:**
        1.  **Identify Trending Fields:** Based on your knowledge of Google and the broader tech industry, identify 2-3 major trending fields (e.g., Generative AI, Quantum Computing, etc.)
        2.  **Propose Sub-topics:** For each field, propose one specific, accessible sub-topic or technology that a person in the user's area could learn about.
        3.  **Explain the "Why":** For each sub-topic, provide a clear, one-sentence rationale explaining its relevance to Google and the user's long-term career.

        **Output Format:**
        Use a structured, brief format with a clear heading for each trending topic.

        **Example:**
        *If the user's area is "Android Development"*:

        #### AI/ML for Mobile
        - **Topic: On-device Machine Learning with TensorFlow Lite.** Rationale: As AI becomes ubiquitous, understanding how to run machine learning models locally on mobile devices is a critical skill for building powerful, low-latency apps.

        #### Cloud & Edge Computing
        - **Topic: IoT and Edge Device Management.** Rationale: With the rise of smart devices, exploring how edge computing complements mobile devices is key to building applications for the next generation of hardware.
        """
        logging.info("Step 2: Getting trending topics...")
        trending_topics_response = model.generate_content(prompt2)
        trending_topics = trending_topics_response.text.strip().split(',')

        # Step 3: Get event ideas
        prompt3 = f"""You are FRIDAY, an internal events curator for Google employees. Your task is to suggest relevant internal events, workshops, and speaker series to a Google employee based on their team, location, and potential interests.

        **User Context:**
        - Role: {user_role}
        - Team: {user_team}
        - Area: {user_area}

        **Instructions:**
        1.  **Categorize Events:** Group event suggestions into two logical categories: a) **Professional Development** (e.g., workshops directly related to their work) and b) **Community & Broader Topics** (e.g., social events, talks on cross-functional subjects).
        2.  **Suggest 2-3 Events per Category:** For each category, propose a few event ideas. These ideas should be plausible for a real Google employee.
        3.  **Provide a Hook:** For each event, add a brief, engaging description of what the event is about and why they might find it valuable. Use a direct, inviting tone.

        **Output Format:**
        Use clear headings for each category, followed by a bulleted list of event ideas.

        **Example:**
        *If the user is a "Product Manager" in "Mountain View, CA"*:

        #### Professional Development
        - **"Navigating the OKR Planning Process" Workshop:** Get hands-on guidance from senior leaders on how to write effective OKRs that drive impact across product teams.
        - **"User Research Fundamentals" Speaker Series:** Learn best practices for conducting user interviews and synthesizing insights to inform your product roadmap.

        #### Community & Broader Topics
        - **"AI & Ethics in Product Design" Tech Talk:** Join a discussion on the ethical considerations of building AI-powered products, featuring speakers from the Responsible AI team.
        - **"Google Foodie Club" Happy Hour:** Connect with fellow Googlers in the Bay Area who share your passion for food and network in a casual, fun setting.
        """

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