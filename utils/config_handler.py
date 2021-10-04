from configparser import ConfigParser
import os
import ssl
import urllib.request
import urllib.error
from utils.enums import Platform

CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "config.ini",
)


parser = ConfigParser()


def check_config() -> ConfigParser:
    """Check for and read config file else run gui."""

    if os.path.isfile(CONFIG_PATH):
        parser.read(CONFIG_PATH)
        return parser

    return None


def load_config() -> tuple[str, str, str]:
    """Read and return values from config file."""

    ical_url = parser["SETTINGS"]["icalURL"]
    lang = parser["SETTINGS"]["LANGUAGE"]
    myssl = ssl.create_default_context()
    myssl.check_hostname = False
    myssl.verify_mode = ssl.CERT_NONE
    try:
        ical_file = (
            urllib.request.urlopen(ical_url, context=myssl).read().decode("utf-8")
        )
    except urllib.error.URLError:
        ical_url[8:14] = ["s", "c", "h", "e", "m", "a"]
        ical_file = (
            urllib.request.urlopen(ical_url, context=myssl).read().decode("utf-8")
        )

    return ical_file, lang


def set_section(val: str) -> str:
    """Set a new section with specified value."""

    with open(CONFIG_PATH, "w") as config:
        parser.add_section(val)
        parser.write(config)


def get_value(key: str):
    """Get a value depending on the given key."""

    return parser.get("SETTINGS", key)


def set_value(key: str, val: str) -> None:
    """Set value of option, with key as option and val as value."""

    with open(CONFIG_PATH, "w") as config:
        parser.set("SETTINGS", key, val)
        parser.write(config)
