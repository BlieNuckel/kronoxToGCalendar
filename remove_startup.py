import os
import winshell
from win32com import client

startup_folder = winshell.startup()
path = os.path.join(startup_folder, "kronoxToGCalendar_Startup.lnk")

if os.path.exists(path):
    os.remove(path)