#firefox profile with logged in classroom account (firefox -p)
PROFILE_NAME = "dev-classroom"

#Google element class names 
clwaffle = "pYTkkf-Bz112c-RLmnJb"
work = "rVhh3b"

import time
import os
import configparser
from pathlib import Path
import json
import csv

from utils.menu import menu

def main():
    # Import bot here to avoid circular imports when other modules import
    # `clean` at module import time (e.g. utils.webhandle imports clean).
    from utils.runner import bot
    menu(bot)

if __name__ == "__main__":
    main()