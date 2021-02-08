# Introduction

The scripts function is to import any kronox schedule into a Google Calendar. When the script is run, it will only sync classes _once_ and as such it must be run periodically, either automatically or manually to ensure that all data is up to date.

The first time the script is run it must be run either from an IDE or through some other terminal. This is important, as the script generates a config file based on several terminal inputs on the first run. Besides this the first run will also generate a Google authentication token, where the scripts will request access to the relevant Google account's calendars.

# Setup

During the setup there are a set of options. **THE FOLLOWING SECTIONS ARE IMPORTANT TO READ BEFORE USING THE SCRIPT**

## Requirements

1. The script requires PIP to be installed and configured as a PATH variable. **IMPORTANT: The script uses pip to install the libraries listed in the Requirements.txt. If you do not wish for the script to download and install these libraries do _not_ run the script**



## Google Calendar ID

This is the ID that Google uses to know which calendar to modify and add the classes to. This can be found under the settings for a calendar in Google Calendar.

**IMPORTANT: Create a new calendar for the script to import into. The script deletes _all_ events before adding to avoid duplicates and as such the calendar tied to the script should _only_ be used for the script.**

## Kronox iCal file URL

This is the URL for the download of the calendar information that can be found on the schedule site on Kronox. It can be found in the top left of the schedule and is labeled "Hämta iCal fil." Make sure to copy the URL by right-clicking and choosing "Copy link" instead of downloading the file manually.

## Language

This setting helps filter between Swedish and English classes. Due to the way some courses have been added to Kronox both English and Swedish classes are visible to everyone. This option allows you to select whether you want to see all classes, only English classes, or only Swedish Classes.

**IMPORTANT: As this removes some classes from the schedule based on a hardcoded filter, which may not perfectly apply to all classes (depending on the teacher's naming etc.) there is a risk that this will filter out important classes/events from your schedule. A safety has been added to ensure that if the event includes "tenta" or "exam" it will _never_ be removed, but beware that there is still a risk in using it.**

## Discord Webhook 

This setting allows you to choose whether you wish to connect a Discord Webhook to the script, that sends update messages every time the script is run. The messages specify whether the call to Google's API was successful.

If this option is enabled you will be asked to enter your personal webhook's URL. You can follow this link for a simple guide on setting up a webhook: [Webhook setup](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

## Google Login

After the setup process a browser window should open, wherein the script requests access to Google Calendar. Since the script is very basic and is not official, there will be a warning saying that the script has not been verified by Google and that it is not secure to connect.

To move on and give the script access,   follow these steps:

1. Select the google account you wish to connect to
2. Click "advanced" in the bottom left of the warning message
3. Click "Go to KronoxToGCal (unsafe)"
4. Click "Allow" in the pop-up, giving the scrip access to Google Calendar
5. Click "Allow" again
6. Close the browser window

After this the events should be added to the calendar specified in the setup process.

**IMPORTANT: The script does _not_ access anything other than the one calendar you specify by the calendar ID and as such is safe to use. All login information and authentication is _only_ stored locally in the directory where the script is placed. The warning from Google is simply based on the fact that Google has not manually reviewed the script and confirmed that it is safe for use.**

# Other options

The config file also takes these following options, however only if edited manually:

## decodeFix

```
[SETTINGS]
decodeFix = y
```

A fix that may help solve the script crashing because of a ```.decode("utf-8")``` error.

# Cloud Service

If you wish to have the script running automatically, I can recommend [Heroku](https://www.heroku.com/) as a free solution, to have the script run at scheduled intervals.
