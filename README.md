# FRIDAY: A Personalized AI Assistant

FRIDAY is a web-based, AI-powered assistant designed to streamline a Google employee's daily workflow, reduce information overload, and foster career growth. It features a "Today's Summary" dashboard, a conversational chatbot for navigating internal workflows, and a personalized recommendation engine for career development.

## Features

*   **Today's Summary**: A dashboard that displays your daily to-do list, team updates, and calendar schedule.
*   **FRIDAY Chatbot**: An interactive chatbot that guides you through complex, multi-step tasks.
*   **Recommendation Engine**: A personalized feed of career opportunities, trainings, and events.

## Technical Details

### Backend

*   **Framework**: Python with FastAPI, utilizing APIRouters for modular endpoint management.
*   **Server**: Uvicorn ASGI server.
*   **Authentication**:
    *   **Google Workspace APIs**: OAuth 2.0 is used to gain `gmail.readonly` and `calendar.readonly` scopes. The flow is handled by the `google-auth-oauthlib` library, storing user consent in a `token.json` file.
    *   **Gemini API**: Authenticated via an API key stored in a `.env` file and loaded using `python-dotenv`.
*   **Configuration**: A local `context.json` file provides a persistent, user-editable global context (name, role, team, area) that is read on-demand by the agents.

### Core AI & Agents

*   **LLM**: The application directly integrates with the Google Gemini API (`gemini-1.5-flash`) via the `google-generativeai` Python library.
*   **Gmail "To-Do" Agent**:
    *   Fetches unread emails via the Gmail API.
    *   For each email, it sends the subject, sender, and a truncated body snippet to the Gemini API.
    *   The prompt instructs the LLM to classify if the email is a to-do, generate a one-sentence summary of the action, and extract the most relevant hyperlink. The response is parsed from a JSON format.
*   **"Team & Beyond Pulse" Agent**:
    *   Reads the user's team and area from `context.json`.
    *   Sends this context to the Gemini API with a prompt instructing it to act as an internal search and synthesis engine.
    *   The LLM generates a JSON list of recent, major internal news, product launches, and events relevant to the user's context, including plausible `go/` links.
*   **FRIDAY Chatbot Agent**:
    *   Maintains conversation history in an in-memory dictionary keyed by session ID.
    *   On each turn, it sends the user's latest message, the full conversation history, and the user's profile from `context.json` to the Gemini API.
    *   The prompt instructs the LLM to act as an expert on internal Google workflows, using its own knowledge base to provide the next actionable step or a clarifying question.
*   **Recommendation Engine Agent**:
    *   Employs a multi-step, "chain of thought" orchestration of Gemini API calls.
    *   **Step 1**: Generates role-specific skill topics based on user context.
    *   **Step 2**: Generates broad, trending tech topics.
    *   **Step 3**: Generates relevant internal event types.
    *   **Step 4 (Synthesis)**: The outputs from the previous steps are combined into a final prompt that instructs the LLM to act as a recommender engine, producing a structured JSON object of recommendations with detailed justifications.

### Frontend

*   **Technology**: The application serves three distinct static HTML pages (`index.html`, `gmail_today.html`, `recommendations.html`).
*   **Styling**: **Tailwind CSS** is used for all styling and layout.
*   **Interactivity**: Vanilla **JavaScript** handles all client-side logic. It uses the `fetch` API to make asynchronous calls to the backend's JSON API endpoints and dynamically renders the received data into the DOM.

## Installation and Setup

### Prerequisites

*   Python 3.10+
*   `pip` and `venv`
*   A Google Cloud project with the **Gmail API** and **Google Calendar API** enabled.
*   A **Gemini API Key**.

### Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Google Cloud Credentials:**
    *   Download your `credentials.json` file from the Google Cloud Console and place it in the root of the project directory.
    *   Run the following command to set up application-default credentials:
        ```bash
        gcloud auth application-default login
        ```

5.  **Configure API Keys:**
    *   Create a file named `.env` in the root of the project.
    *   Add your Gemini API key to the `.env` file:
        ```
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        ```

6.  **Set Your Personal Context:**
    *   Edit the `context.json` file to include your personal details.

## Running the Application

1.  **Start the server:**
    ```bash
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
    ```

2.  **Access the application:**
    *   **FRIDAY Chatbot**: [http://0.0.0.0:8000/](http://0.0.0.0:8000/)
    *   **Today's Summary**: [http://0.0.0.0:8000/today](http://0.0.0.0:8000/today)
    *   **Recommendations Hub**: [http://0.0.0.0:8000/recommendations](http://0.0.0.0:8000/recommendations)

3.  **First-Time Authorization:**
    *   The first time you access the "Today's Summary" page, you will need to authorize the application. Follow the URL printed in your terminal to grant the necessary permissions.
