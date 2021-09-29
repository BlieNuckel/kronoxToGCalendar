import os.path
from typing import List
import webbrowser
import utils.config_handler as config_handler

from gui import get_token_url
import datetime
from O365 import MSGraphProtocol
from O365.connection import Connection
from O365.account import Account
from O365.utils.token import FileSystemTokenBackend
from dateutil.relativedelta import relativedelta
import dateutil.parser

CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "config.ini",
)

SCOPES = ["basic", "calendar_all"]


def insert_event(events: List[str], account: Account, calendar_id: str) -> None:
    """Add events to calendar."""

    schedule = account.schedule()
    calendar = schedule.get_calendar(calendar_id=calendar_id)

    for event in events:
        new_event = calendar.new_event()
        new_event.subject = event["summary"]
        new_event.location = event["location"]
        new_event.start = dateutil.parser.isoparse(event["start"]["dateTime"])
        new_event.end = dateutil.parser.isoparse(event["end"]["dateTime"])
        try:
            new_event.body = event["description"]
        except KeyError:
            pass
        new_event.save()


def create_default_calendar(account: Account) -> None:
    """Create CLASSES calendar and save ID in config."""
    schedule = account.schedule()
    calendar = schedule.new_calendar("CLASSES")

    id = calendar.calendar_id
    config_handler.set_value(key="calendarId", val=id)


def clear_calendar(account: Account, calendar_id: str) -> None:
    """Get current available events and delete them."""

    schedule = account.schedule()
    calendar = schedule.get_calendar(calendar_id=calendar_id)

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    twelve_months = today + relativedelta(months=+13)

    q = calendar.new_query("start").greater_equal(yesterday)
    q.chain("and").on_attribute("end").less_equal(twelve_months)

    events = calendar.get_events(query=q, limit=1000)

    for event in events:
        event.delete()


def creds() -> Account:
    """Load or obtain credentials for user."""

    credentials = "8da780f3-5ea0-4d97-ab13-9e7976370624"
    protocol = MSGraphProtocol(timezone="Europe/Stockholm")
    scopes = protocol.get_scopes_for(SCOPES)
    token_backend = FileSystemTokenBackend(
        token_path=os.path.dirname(__file__), token_filename="o365_token.txt"
    )
    connection = Connection(
        credentials, auth_flow_type="public", token_backend=token_backend
    )
    account = Account(
        credentials,
        auth_flow_type="public",
        protocol=protocol,
        token_backend=token_backend,
    )

    if (
        not os.path.exists("kronoxToGCalendar/logic/o365_token.txt")
        and not account.is_authenticated
    ):
        print("AUTH TRIGGERED")
        auth_url = connection.get_authorization_url(
            requested_scopes=scopes,
        )

        webbrowser.open_new(auth_url[0])

        app = get_token_url.Application()
        app.mainloop()

        token_url = app.token_url

        connection.request_token(token_url)

    print("AUTH PASSED")
    account.is_authenticated

    return account
