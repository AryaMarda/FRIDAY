import json
import logging

CONTEXT_FILE = "context.json"

def get_user_context():
    """Reads the user context from the context.json file."""
    try:
        with open(CONTEXT_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"{CONTEXT_FILE} not found. Using default empty context.")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {CONTEXT_FILE}. Please check its format.")
        return {}