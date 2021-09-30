# Introduction

The scripts function is to import any kronox schedule into a Google Calendar. When the script is run, it will only sync classes _once_ and as such it must be run periodically, either automatically or manually to ensure that all data is up to date.

The first time the script is run it generates a config file based on several user inputs. Besides this the first run will also generate a Google or Outlook authentication token, where the scripts will request access to the relevant calendars.

# Privacy Notice

**This app _only_ uses its access to your Google Calendar for the purpose of deleting and adding events to the calendar which you specify upon setup. The program will never access any other files from your computer, other calendars from your google account, or other information it doesn't need. The only thing the app connects to is the specified Calendar on your google account and its events. Any events on the calendar are only deleted, and such no content in the events is ever read.**

# Setup

During the setup there are a set of options. **THE FOLLOWING SECTIONS ARE IMPORTANT TO READ BEFORE USING THE SCRIPT**

## Kronox iCal file URL

This is the URL for the download of the calendar information that can be found on the schedule site on [Kronox](https://kronox.hkr.se/). It can be found in the top left of the schedule and is labeled "Hämta iCal fil"/"Get iCal file." Make sure to copy the URL by right-clicking and choosing "Copy link" instead of downloading the file manually.

For the HKR computer science class, below are your schedule links. You will still have to copy the link from the "Get iCal file" button as mentioned above:

[1st year Swedish](https://kronox.hkr.se/setup/jsp/Schema.jsp?startDatum=idag&intervallTyp=m&intervallAntal=6&sprak=SV&sokMedAND=true&forklaringar=true&resurser=p.TGDU3+2021+35+100+NML+sv)

[1st year English](https://kronox.hkr.se/setup/jsp/Schema.jsp?startDatum=idag&intervallTyp=m&intervallAntal=6&sprak=SV&sokMedAND=true&forklaringar=true&resurser=p.TBSE2+2021+35+100+NML+en)

[2nd year English](https://kronox.hkr.se/setup/jsp/Schema.jsp?startDatum=idag&intervallTyp=m&intervallAntal=6&sprak=SV&sokMedAND=true&forklaringar=true&resurser=p.TBSE2+2020+36+100+NML+en)

## Language

This setting helps filter between Swedish and English classes. Due to the way some courses have been added to Kronox both English and Swedish classes are visible to everyone. This option allows you to select whether you want to see all classes, only English classes, or only Swedish Classes.

**IMPORTANT: As this removes some classes from the schedule based on a hardcoded filter, which may not perfectly apply to all classes (depending on the teacher's naming etc.) there is a risk that this will filter out important classes/events from your schedule. A safety has been added to ensure that if the event includes "tenta" or "exam" it will _never_ be removed, but beware that there is still a small risk in using it.**

## Google Login

After the setup process a browser window should open, wherein the script requests access to Google Calendar. Since the script is very basic and is not official, there will be a warning saying that the script has not been verified by Google and that it is not secure to connect.

To move on and give the script access,   follow these steps:

1. Select the google account you wish to connect to
2. Click "advanced" in the bottom left of the warning message
3. Click "Go to KronoxToGCal (unsafe)"
4. Check off the checkboxes giving the script access to editing your calendar
5. Click "Allow"
6. Close the browser window when it goes white, with a success message in the top left

After this the events should be added to your calendar.

**IMPORTANT: The script does _not_ access anything other than the one calendar it creates and as such is safe to use. All login information and authentication is _only_ stored locally in the directory where the script is placed.**

# Trouble Shooting

## General issues and fix

Most issues stem from an incomplete config.ini file. The file can be found in <install-dir>/kronoxToGCalendar/config.ini. Deleting this and running the script will prompt a new setup. Make sure to fill in the settings correctly and then most issues should be fixed.

# Cloud Service

If you wish to have the script running automatically without it running locally on your computer, I can recommend [Heroku](https://www.heroku.com/) as a free solution.

Be aware that setting this up requires knowledge of what you're doing and so it may break the script if done incorrectly, as the .exe and .zip files released don't work with Herokus services directly.
