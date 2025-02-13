import requests
import browser_cookie3
from bs4 import BeautifulSoup
import json
import pandas as pd
import logging
import glob
import os
from io import StringIO
from tqdm import trange


logger = logging.getLogger(__name__)
logging.basicConfig(filename='extractor.log', encoding='utf-8', level=logging.ERROR)


cj = browser_cookie3.chrome()
baseUrl = 'https://www.pokemon.com'


listUrl = 'https://www.pokemon.com/us/pokemon-trainer-club/api/play-pokemon-stats/play_points?cycle=2025&period=56&product=tcg&use_spar_data=false'

listEvents = requests.get(listUrl, cookies=cj)
eventsDict = json.loads(listEvents.text)

eventUrls = []

for event in eventsDict['rows']:
    for eventData in event['columns']:
        if 'html' in eventData.keys():
            try:
                eventUrl = BeautifulSoup(eventData['html'], 'html.parser').a['href']
                eventUrls.append(eventUrl)
            except:
                continue

print('Found {} events'.format(len(eventUrls)))

for i in trange(len(eventUrls)):
    eventUrl = eventUrls[i]
    try:
        r = requests.get(baseUrl + eventUrl, cookies=cj)
        eventContent = BeautifulSoup(r.content, "lxml")
        infoSelector = '#mainContent > div > div.roundedBucket-mid > div.oneColumn-twoColumns > div.col2 > div > div > div > div > form:nth-child(1) > fieldset > div.bot > dl > div > ol'
        eventInfoContainer = eventContent.select_one(infoSelector)
        eventData = eventInfoContainer.find_all('li')
        eventDict = {}
        for eventInfo in eventData:
            infoKey = eventInfo.select_one('label').text
            infoData = eventInfo.text.replace(infoKey, '').strip()
            eventDict[infoKey] = infoData
            
        with open('data/{}.json'.format(eventDict['Tournament ID']), 'w') as f:
            json.dump(eventDict, f, ensure_ascii=False, indent=4)


        for anchor in eventContent.find_all('a'):
            if anchor.get('href') and 'standings' in anchor.get('href'):
                standings = requests.get(baseUrl + anchor.get('href'), cookies=cj)
                standingsContent = BeautifulSoup(standings.content, "lxml")
                for eventAnchor in standingsContent.find_all('a'):
                    if eventAnchor.get('href') and 'master' in eventAnchor.get('href'):
                        positionRequest = requests.get(baseUrl + eventAnchor.get('href'), cookies=cj)
                        positionContent = BeautifulSoup(positionRequest.content, "lxml")
                        positionTable = positionContent.find_all('table')[0]
                        df = pd.read_html(StringIO(str(positionTable)))[0]
                        df['pct_pos'] = df['Position'].rank(pct=True)
                        df['rank'] = (df['pct_pos']*100).round()
                        df['date'] = eventDict['Date']
                        df['event'] = eventDict['Tournament ID']
                        if eventDict["Premier Event"] == "None":
                            df['event_type'] = 'League'
                        elif "League Cup" in eventDict["Premier Event"]:
                            df['event_type'] = 'League Cup'
                        elif "Regional Championships" in eventDict["Premier Event"]:
                            df['event_type'] = 'Regional Championships'
                        elif "International Championships" in eventDict["Premier Event"]:
                            df['event_type'] = 'International Championships'
                        elif "World Championships" in eventDict["Premier Event"]:
                            df['event_type'] = 'World Championships'
                        elif "Special Event" in eventDict["Premier Event"]:
                            df['event_type'] = 'Special Event'
                        elif "Midseason Showdown" in eventDict["Premier Event"]:
                            df['event_type'] = 'Midseason Showdown'
                        elif "League Challenge" in eventDict["Premier Event"]:
                            df['event_type'] = 'League Challenge'
                        elif "Prerelease" in eventDict["Premier Event"]:
                            df['event_type'] = 'Pre Release'
                        df["event_name"] = eventDict["Tournament Name"]
                        df.to_csv('data/{}.csv'.format(eventDict['Tournament ID']), index=False)
                        break    
                break
    except Exception as e:
        logger.error('Error in event: ' + eventUrl)
        logger.error(eventContent)
        logger.error(e)
        
all_files = glob.glob(os.path.join('./data/', "*.csv"))

df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
df.to_csv('data/all.csv', index=False)