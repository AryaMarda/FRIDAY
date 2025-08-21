from googleapiclient.errors import HttpError
from auth import get_gmail_service
import datetime

def get_todays_emails(service):
    """Gets all unread emails from today."""
    today = datetime.date.today()
    query = f"is:unread after:{today.strftime('%Y/%m/%d')}"
    try:
        results = service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])
        
        emails = []
        if not messages:
            print("No new messages found.")
        else:
            for message in messages:
                msg = service.users().messages().get(userId="me", id=message["id"]).execute()
                emails.append(msg)
        return emails

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []