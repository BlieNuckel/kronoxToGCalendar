import os
import subprocess
from utils.config_handler import ConfigHandler
import gui.main_gui
from utils.enums import Platform

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")

if not os.path.isfile(CONFIG_PATH):
    subprocess.call('"batch/install_requirements.bat"')

from logic import outlook_connector
from logic import google_connector
from logic import event_handler

config_handler = ConfigHandler()


def main():
    """Get config, initiate for chosen platform."""

    while config_handler.check_config() is None:
        gui.main_gui.run()

    platform = config_handler.get_value("platform")
    run_platform(platform)


def run_platform(platform: Platform) -> None:
    """Run flow dependent on platform."""

    if platform == Platform.OUTLOOK:
        (ical_file, lang) = config_handler.load_config()

        account = outlook_connector.creds()
        outlook_connector.create_default_calendar(account)

        calendar_id = config_handler.get_value("calendarId")
        event_list = event_handler.parse_ics(ical_file)
        parsed_event_list = event_handler.event_edit(event_list, lang)

        outlook_connector.clear_calendar(account, calendar_id)

        outlook_connector.insert_event(parsed_event_list, account, calendar_id)

    elif platform == Platform.GOOGLE:
        (ical_file, lang) = config_handler.load_config()

        service = google_connector.creds()
        google_connector.create_default_calendar(service)

        calendar_id = config_handler.get_value("calendarId")
        event_list = event_handler.parse_ics(ical_file)
        parsed_event_list = event_handler.event_edit(event_list, lang)

        google_connector.clear_calendar(service, calendar_id)

        google_connector.insert_event(parsed_event_list, service, calendar_id)


if __name__ == "__main__":
    main()
