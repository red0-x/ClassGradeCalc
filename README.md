<img width="1920" height="1050" alt="image" src="https://github.com/user-attachments/assets/a38a894e-a574-4ee5-a247-ac29b4e579f3" />### 🤓 red0-x/ClassGradeCalc 🖩 - The Google Classroom Grade Calculator 

# [WIP]
###### -> Does NOT scrape properly at the time of 10/15/2025! 😥

 Adds all of your Google Classroom grades together to give a letter grade
 - I made this because my school grades everything in the classroom and only announces the grades quarterly; I don't want to fall behind :)
 - ⚠️ Use with caution, scraping Google is AGAINST their tos.
 - ️️⚠️ It's possible your Google account could get banned, and you might get in trouble with your school! ⚠



### Usage: 
 - clone repo & create virtual environment 

 ``$> git clone https://github.com/red0-x/ClassGradeCalc.git && python3 -m venv .venv``
 
 - activate virtual environment 
 
 ``$> source .venv/bin/activate``
 
 - head to root dir and install modules
 
 ``$> cd main && pip install -r requirements.txt``
 
 - Not sure if this works on Windows, but for Linux, you need to install geckodriver and Firefox. 
 
 - Check --> https://github.com/mozilla/geckodriver/releases and add to usr/bin
 
 - You will probably run into many problems while installing this. 
 ### ‼️ You NEED to create a Firefox profile called "dev-classroom" 
 ###### You can do so by typing firefox -p to create the new profile 
 ###### after that, you need to login to classroom.google.com with the googe account you want to scrape. 
 ###### The bot should use the profile that is already logged in, and you're good!
 - Once set up simply start scraping grades.

Example:
<img width="1920" height="1050" alt="image" src="https://github.com/user-attachments/assets/88d0ed2b-22dd-4d68-9907-9ab9915c991d" />

## Changelog:

 ### 10/15/2025
 - Added Usage Image + ReadMe & Menu. 
 - Made Link cleaner so it only provides the work page.
### 10/16/2025
 - Made the menu cool with a gradient & typing effect
 - Segregated Utility functions so main.py isn't very big (better readability)
 - cleaned JS injection payload

