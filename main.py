from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import random

# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import json
from selenium import webdriver
import chromedriver_autoinstaller
import os
options = webdriver.ChromeOptions() 
 
# Adding argument to disable the AutomationControlled flag 
options.add_argument("--disable-blink-features=AutomationControlled") 
 
# Exclude the collection of enable-automation switches 
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
 
# Turn-off userAutomationExtension 
options.add_experimental_option("useAutomationExtension", False)
 
# Changing the property of the navigator value for webdriver to undefined 
# driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
options.add_argument('--disable-notifications')

driver = webdriver.Chrome(options=options)

def getListLinks(timewait = 0.4):
    keepwaiting = True
    count = 0
    while keepwaiting:
        try:
            mainblock = driver.find_element(By.CLASS_NAME, 'sc-hYmls.iJJmnR')

            HTML = mainblock.get_attribute('outerHTML')
            listlinks = re.findall(r'href="(/live/zapas/tenis.+?)>',HTML)
            keepwaiting = False
        except:
            count += 1
            time.sleep(timewait)
            if count == maxcount:
                keepwaiting = False
    return listlinks

def getDictLinks(listlinks):
    dictInfo = {}
    match_name_list = []

    # GET COMPLETE BLOCKS WITH NAMES AND LINKS

    playerRows = driver.find_elements(By.CLASS_NAME, 'sc-jdAjlr.gWNQbi.t-background')

    for KEY, playerRow in enumerate(playerRows):

        match_name = playerRow.find_element(By.CLASS_NAME,'sc-fvmNvC.kIWYhU').text

        match_name_clean = cleanText(match_name)

        if match_name_clean in listlinks[KEY]:
            dictInfo[KEY] = {'url_link': 'https://www.tipsport.sk' + listlinks[KEY].replace('"',''), 'match_name':match_name}
        else:
            for i2, link in enumerate(listlinks):
                if match_name in link:
                    dictInfo[KEY] = {'url_link': 'https://www.tipsport.sk' + listlinks[KEY].replace('"',''), 'match_name':match_name}
    return dictInfo

def getGameData(url, match_name):
    #site, type_of_game, url_link, match_name, type_,name, odds
    site  = re.findall(r'www\.(.+)\.', url)[0]
    type_of_game = re.findall(r'/zapas/(.+?)-', url)[0]
    return site, type_of_game

def ScrapingGame(countmax= 2, time_wait = 0.2):
    df_game = pd.DataFrame()
    keepwaiting = True	
    count = 0
    while keepwaiting:
        try:
            blocksEventsPlayers = driver.find_elements(By.CLASS_NAME, 'eventTable.column2')

            for subblock in blocksEventsPlayers:

                datablocks = subblock.find_elements(By.CLASS_NAME,'tdEventTable.opportunity')
                print("-", end='')
                df = getNameOdds(datablocks)

                ###### TYPE OF EVENT
                eventType = subblock.find_element(By.CLASS_NAME,'eventTableRow')
                df['type'] = eventType.text
                df_game = pd.concat([df_game, df])

            if len(df_game)!= 0:
                confirmdata = True
            else:
                confirmdata = False
            keepwaiting = False
        except:
            count +=1
            time.sleep(time_wait)
            if count == countmax:
                keepwaiting = False
                confirmdata = False

    return confirmdata, df_game

def getNameOdds(datablocks):
    
    dictSubBlock = {}
    names = []
    values = []

    for block in datablocks:
        name = block.find_element(By.CLASS_NAME, 'name').text
        try:
            value = block.find_element(By.CLASS_NAME, 'value').text            

        except:
            value = 'CLOSE'        
        names.append(name)
        values.append(value)

    dictSubBlock = {'name': names, 'odds':values} 
    return pd.DataFrame.from_dict(dictSubBlock)

def cleanText(txt):
    return txt.lower().replace(' ','-').replace('---','-').replace('.','').replace('/','')

def getPlayerNames(playerRow):
    global team_1, team_2
    players = playerRow.find_element(By.CLASS_NAME,'sc-fvmNvC.kIWYhU').text.split('-')    
    team_1.append(players[0])
    team_2.append(players[1])
    
def getplayerOdds(playerRow):
    global odds_1, odds_2
    if not 'Kurzy nie sú aktuálne k dispozícii.' in playerRow.text:
        oddsBlock = playerRow.find_element(By.CLASS_NAME, 'sc-hjTfOg.bhBPXw')
        odds = oddsBlock.find_elements(By.CSS_SELECTOR, 'div')

        if not "|null|" in odds[0].get_attribute('outerHTML'):
            odd1 = odds[0].text.split('\n')[1].replace(' ','')
            odds_1.append(odd1)
        else:
            odds_1.append('')

        if not "|null|" in odds[1].get_attribute('outerHTML'):
            odd2 = odds[1].text.split('\n')[1].replace(' ','')            
            odds_2.append(odd2)
        else:
            odds_2.append('')
    else:
        odds_1.append('')
        odds_2.append('')

def getURL_type():
    url_ = driver2.current_url
    type_ = re.sub(r'\d+','', url_.split('/')[-1]).replace('-','')
    return url_, type_

def loopOverLinks(URL, filename):
    driver.get(URL)
    listlinks = getListLinks()	
    dictInfo = getDictLinks(listlinks)
    df_all = pd.DataFrame()

    for i, KEY in enumerate(dictInfo.keys()):        
        url = dictInfo[KEY]['url_link']
        match_name = dictInfo[KEY]['match_name']        
        print(url)

        driver.get(url)
        # time.sleep(5)  ### -TIME SLEEP- ###        
        site, type_of_game = getGameData(url, match_name)	    
        confirmdata, df_game = ScrapingGame(countmax= 4, time_wait = 0.5)
        if confirmdata:
            df_game['url_link'] = url
            df_game['site'] = site
            df_game['type_of_game'] = type_of_game
            df_game['match_name'] = match_name            
            df_all = pd.concat([df_all, df_game])            
    df_all = df_all[['site', 'type_of_game','url_link','match_name', 'type', 'name', 'odds']]
    df_all = df_all.reset_index(drop= True)
    df_all.to_csv(filename)
    return df_all


def  __ini__():
    if not os.path.exists('files'):
        os.mkdir('files')

    URL = 'https://www.tipsport.sk/live/tenis-43'
    filename = "files/Players_Odds.csv"
    driver.get(URL)
    validInput = False
    while not validInput:
        strwait = input("Confirm Preferences and please type the number of seconds to update data ")
        try:
            updatetime = float(re.findall(r'\d+', strwait)[0])
            validInput = True
        except:
            validInput = False
    while True:
        
        df = loopOverLinks(URL, filename)
        print("File Updated")        
        driver.get(URL)
        time.sleep(updatetime)
        print("#"*100)
        print("#"*10,"TIME FINISHED NEW UPDATE","#"*10)        

__ini__()


