import pickle
import os.path
from typing import List
import requests
import utils.config_handler as config_handler
from google.auth.transport.requests import Request
from googleapiclient.discovery import Resource, build
from google_auth_oauthlib.flow import InstalledAppFlow

CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "config.ini",
)

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar",
]


def insert_event(events: List[str], service: Resource, calendar_id: str) -> None:
    """Add events to calendar."""

    batch = service.new_batch_http_request()

    # Add each event to batch
    for i, event in enumerate(events):
        batch.add(service.events().insert(calendarId=calendar_id, body=event))
    batch.execute()


def create_default_calendar(service: Resource):
    calendar_data = {"summary": "CLASSES", "timeZone": "Europe/Copenhagen"}

    created_calendar = service.calendars().insert(body=calendar_data).execute()
    id = created_calendar["id"]
    config_handler.set_value(key="calendarId", val=id)


def clear_calendar(service: Resource, calendar_id: str) -> None:
    """Clears calendar."""

    events = (
        service.events().list(calendarId=calendar_id, singleEvents=True).execute()
    )

    batch = service.new_batch_http_request()

    # Add delete call for each event to batch
    for event in events["items"]:
        eId = event["id"]
        batch.add(service.events().delete(calendarId=calendar_id, eventId=eId))

    batch.execute()


def creds() -> Resource:
    """Load or obtain credentials for user."""
    token_path = os.path.join(os.path.dirname(__file__), "token.pickle")
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client = requests.get(
                "https://kronox-client-api.herokuapp.com/get_client"
            ).json()
            flow = InstalledAppFlow.from_client_config(client, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)
