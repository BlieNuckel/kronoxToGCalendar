from configparser import ConfigParser
import os
import subprocess
import gui.main_gui
from enum import Enum

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")

if not os.path.isfile(CONFIG_PATH):
    subprocess.call('"batch/install_requirements.bat"')

from logic import outlook_connector
from logic import google_connector
from logic import event_handler


class Platform(Enum):
    """Defines different possible calendar platforms."""

    OUTLOOK = "outlook"
    GOOGLE = "google"


def main():
    """Get config, initiate for chosen platform."""

    parser = config_check()
    platform: Platform = parser["SETTINGS"]["platform"]
    run_platform(platform)


def config_check() -> ConfigParser:
    """Check for and read config file else run gui."""

    parser = ConfigParser(allow_no_value=True)

    if os.path.isfile(CONFIG_PATH):
        parser.read(CONFIG_PATH)
    else:
        gui.main_gui.run()
        parser.read(CONFIG_PATH)
    return parser


def run_platform(platform: Platform) -> None:
    """Run flow dependent on platform."""

    if platform == Platform.OUTLOOK:
        (calendar_id, ical_file, lang) = outlook_connector.config_loader()

        account = outlook_connector.creds()
        event_list = event_handler.parse_ics(ical_file)
        parsed_event_list = event_handler.event_edit(event_list, lang)

        outlook_connector.clear_calendar(account, calendar_id)

        outlook_connector.insert_event(parsed_event_list, account, calendar_id)

    elif platform == Platform.GOOGLE:
        (
            calendar_id,
            ical_file,
            lang,
            webhook_url,
        ) = google_connector.config_loader()

        service = google_connector.creds()
        event_list = event_handler.parse_ics(ical_file)
        parsed_event_list = event_handler.event_edit(event_list, lang)

        google_connector.clear_calendar(service, calendar_id)

        google_connector.insert_event(
            parsed_event_list, service, calendar_id, webhook_url
        )


if __name__ == "__main__":
    main()
