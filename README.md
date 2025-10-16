# ClassGradeCalc
 Adds all of your google classroom grades together  to give letter grade

# Usage: 
 - clone repo & create virtual enviroment 

 ``$> git clone [REPO LINK] && python3 -m venv .venv``
 
 - activate virtual enviroment 
 
 ``$> source .venv/bin/activate``
 
 - head to root dir and install modules
 
 ``$> cd main && pip install -r requirements.txt``
 
 - Not sure if this works on windows but for linux you need to install geckodriver and firefox. 
 
 - Check --> https://github.com/mozilla/geckodriver/releases and add to usr/bin
 
 - You will probably run into many problems while installing this. 
 ### You NEED to create a firefox profile called "dev-classroom" 
 #### you can doso by typing firefox -p to create the new profile 
 #### after that, you need to login to classroom.google.com with the googe account you want to scrape. 
 #### The bot should use that profile that is already logged in and you're good!
 - Once setup simply start scraping grades.

## Changelog:

 ### 10/15/2025
 - Added Usage Image + ReadMe & Menu. 
 - Made Link cleaner so it only provides the work page. 

