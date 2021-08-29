from icalendar import Calendar
import datetime as dt
import re

PATTERN1 = re.compile("\s+")
PATTERN2 = re.compile(",+")
PATTERN3 = re.compile(r"(?:(?<=\s)|^)(?:[a-z]|\d+)", re.I)


def parse_ics(ics):  # Parses ics file into list of event dicts

    events = []
    ical = Calendar.from_ical(ics)
    for i, component in enumerate(ical.walk()):
        if component.name == "VEVENT":

            event = {}
            event["summary"] = component.get("summary")
            event["location"] = component.get("location")
            event["start"] = {
                "dateTime": component.get("dtstart").dt.isoformat(),
                "timeZone": str(component.get("dtstart").dt.tzinfo),
            }
            event["end"] = {
                "dateTime": component.get("dtend").dt.isoformat(),
                "timeZone": str(component.get("dtend").dt.tzinfo),
            }
            event["sequence"] = component.get("sequence")
            try:
                event["transparency"] = component.get("transparency").lower()
                event["visibility"] = component.get("class").lower()
                event["organizer"] = {
                    "displayName": component.get("organizer").params.get("CN")
                    or "",
                    "email": re.match(
                        "mailto:(.*)", component.get("organizer")
                    ).group(1)
                    or "",
                }

                desc = component.get("description").replace("\xa0", " ")
                if "description" in event:
                    event["description"] = desc + "\r\n" + event["description"]
                else:
                    event["description"] = desc

                event["description"] = component.get("description")
            except AttributeError:
                pass

            events.append(event)

    return events


def name_format(name):

    split_name = None
    # Split name and format SUMMARY in readable way
    if name[0] == "K":
        split_name = re.split("Kurs.grp: | Sign: | Moment: | Program: ", name)
        if "en" in split_name[3] and "sv" in split_name[3]:
            if len(split_name[1].split(" ")) == 1:
                return split_name[1] + " : " + split_name[2]
            else:
                return (
                    "".join(PATTERN3.findall(split_name[1])).upper()
                    + " : "
                    + split_name[2]
                )
        else:
            if len(split_name[1].split(" ")) == 1:
                return (
                    split_name[1]
                    + " : "
                    + split_name[3]
                    + " : "
                    + split_name[2]
                )
            else:
                return (
                    "".join(PATTERN3.findall(split_name[1])).upper()
                    + " : "
                    + split_name[3]
                    + " : "
                    + split_name[2]
                )

    elif name[0] == "S":
        split_name = re.split("Sign: | Moment: | Program: ", name)
        return split_name[2] + " : " + split_name[1]


def event_edit(event_list, lang):
    del_events = []  # List for events to be deleted

    for i in event_list:  # Loop through each event
        i["summary"] = name_format(i["summary"])  # Format name

        # Clean up the name
        edit_name = i["summary"]
        edit_name = edit_name.replace(":  :", ":")
        edit_name = edit_name.rstrip(" : ")
        for j in PATTERN1.findall(i["summary"]):
            edit_name = edit_name.replace(j, " ")
        for j in PATTERN2.findall(i["summary"]):
            edit_name = edit_name.replace(j, ",")
        edit_name = edit_name.replace(";", "")

        # NAZILA FIX: FILTERS ENGLISH OR SWEDISH CLASSES OUT #
        if lang.lower() == "en":
            if "sv" in edit_name.lower() or "föreläsning" in edit_name.lower():
                if (
                    "tenta" not in edit_name.lower()
                    or "guest" not in edit_name.lower()
                ):
                    del_events.append(i)

        elif lang.lower() == "sv":
            if "eng" in edit_name.lower() or "lecture" in edit_name.lower():
                if (
                    "exam" not in edit_name.lower()
                    and "guest" not in edit_name.lower()
                ):
                    del_events.append(i)

        if len(edit_name) > 63:
            i["description"] = edit_name
            edit_name = edit_name[:63] + "..."

        i["summary"] = edit_name

    # Delete events from Calendar
    for i in del_events:
        event_list.remove(i)

    return event_list
