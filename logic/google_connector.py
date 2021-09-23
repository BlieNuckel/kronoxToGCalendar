import pickle
import os.path
from typing import List
import urllib
from configparser import ConfigParser
import ssl
import requests
from google.auth.transport.requests import Request
from googleapiclient.discovery import Resource, build
from google_auth_oauthlib.flow import InstalledAppFlow
from discord_webhook import DiscordWebhook

CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "config.ini",
)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def config_loader() -> tuple[str, str, str, str]:
    """Read and return values from config file."""

    parser = ConfigParser(allow_no_value=True)
    parser.read(CONFIG_PATH)

    calendar_id = parser["SETTINGS"]["calendarId"]
    ical_url = parser["SETTINGS"]["icalURL"]
    lang = parser["SETTINGS"]["LANGUAGE"]
    global discord_integration
    discord_integration = parser["SETTINGS"]["discordIntegration"]
    webhook_url = None
    if discord_integration == "y":
        webhook_url = parser["DISCORD_SETTINGS"]["webhook"]
    myssl = ssl.create_default_context()
    myssl.check_hostname = False
    myssl.verify_mode = ssl.CERT_NONE
    ical_file = (
        urllib.request.urlopen(ical_url, context=myssl).read().decode("utf-8")
    )

    return calendar_id, ical_file, lang, webhook_url


def insert_event(
    events: List[str], service: Resource, calendar_id: str, webhook_url: str
) -> None:
    """Add events to calendar."""

    global error_set
    error_set = set()
    global error_count
    error_count = 0

    batch = service.new_batch_http_request(callback=cb_insert_event)

    # Add each event to batch
    for i, event in enumerate(events):
        batch.add(service.events().insert(calendarId=calendar_id, body=event))
    batch.execute()

    if discord_integration == "y":

        if error_count > 0:
            joinedString = ", ".join([str(i) for i in error_set])
            content = (
                f"{error_count} errors, following errors found: " + joinedString
            )
            DiscordWebhook(url=webhook_url, content=content).execute()


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


def cb_insert_event(request_id, response, e) -> None:
    """Callback from adding events"""

    global discord_integration
    if discord_integration == "y":
        if e:
            global error_set
            global error_count

            error_set.add(str(e))
            error_count += 1


def creds() -> Resource:
    """Load or obtain credentials for user."""

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(os.path.join(os.path.dirname(__file__), "token.pickle")):
        with open(
            os.path.join(os.path.dirname(__file__), "token.pickle"), "rb"
        ) as token:
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
        with open(
            os.path.join(os.path.dirname(__file__), "token.pickle"), "wb"
        ) as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)
