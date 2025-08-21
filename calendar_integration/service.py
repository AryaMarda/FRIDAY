from googleapiclient.errors import HttpError
from auth import get_calendar_service
import datetime

def get_todays_calendar_events(service):
    """Fetches today's events from the user's primary calendar."""
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        today_end = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=today_start,
            timeMax=today_end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            formatted_events.append({
                "summary": event.get("summary", "No Title"),
                "link": event.get("hangoutLink", ""),
                "start_time": start
            })
        return formatted_events

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []