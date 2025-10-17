import sys, time, os, random
from random import randint
from os import system

# cool effect must add :) 
def txt(text, delay=0.0009):
    system(""); faded = ""
    red = 90
    for line in text.splitlines():
        faded += (f"\033[38;2;{red};0;220m{line}\033[0m\n")
        if not red == 255:
            red += 15
            if red > 255:
                red = 255
    text = faded
    for char in text:
        sys.stdout.write(char)  
        sys.stdout.flush()      
        time.sleep(delay)       
    print()  

def menu(bot):
    banner = """\n ██████╗██╗      █████╗ ███████╗███████╗       ██████╗ █████╗ ██╗      ██████╗
██╔════╝██║     ██╔══██╗██╔════╝██╔════╝      ██╔════╝██╔══██╗██║     ██╔════╝
██║     ██║     ███████║███████╗███████╗█████╗██║     ███████║██║     ██║     
██║     ██║     ██╔══██║╚════██║╚════██║╚════╝██║     ██╔══██║██║     ██║     
╚██████╗███████╗██║  ██║███████║███████║      ╚██████╗██║  ██║███████╗╚██████╗
 ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝       ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝
                            [ <3 @red0xx.top ]"""
    # I see you changing the banner >:(
    txt(banner)
    txt("Google Classroom Grade Scraper", delay=0.01)
    print("[1] Start scraping grades")
    option = input("\n>")
    if option.strip() == "1":
        bot()
    else:
        return