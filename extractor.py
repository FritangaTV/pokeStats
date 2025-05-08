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
from http.cookies import SimpleCookie

cookie = SimpleCookie()

logger = logging.getLogger(__name__)
logging.basicConfig(filename='extractor.log', encoding='utf-8', level=logging.ERROR)


cj = browser_cookie3.chrome()
baseUrl = 'https://www.pokemon.com'


listUrl = 'https://www.pokemon.com/us/pokemon-trainer-club/api/play-pokemon-stats/play_points?cycle=2025&period=56&product=tcg&use_spar_data=false'
#listUrl = 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-tournaments/standings/7869671'
s = requests.Session()

reqHeaders = {
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'sec-ch-ua-mobile':'?0',
    'sec-ch-ua-platform': "macOS",
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
}

s.headers.update(reqHeaders)
listEvents = s.get(listUrl, cookies=cj)
print('List events: {}'.format(listEvents.text))
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

allEventData = []

def getEventInfo(eventContent, selector, eventDict):
    element = eventContent.select_one(selector)
    for eventInfo in element.find_all('li'):
        infoKey = eventInfo.select_one('label').text
        infoData = eventInfo.text.replace(infoKey, '').strip()
        eventDict[infoKey] = infoData
    return eventDict

def getEventType(premiereString):
    eventString = 'None'
    if premiereString == "None":
        eventString = 'League'
    elif "League Cup" in premiereString:
        eventString = 'League Cup'
    elif "Regional Championships" in premiereString:
        eventString = 'Regional Championships'
    elif "International Championships" in premiereString:
        eventString = 'International Championships'
    elif "World Championships" in premiereString:
        eventString = 'World Championships'
    elif "Special Event" in premiereString:
        eventString = 'Special Event'
    elif "Midseason Showdown" in premiereString:
        eventString = 'Midseason Showdown'
    elif "League Challenge" in premiereString:
        eventString = 'League Challenge'
    elif "Prerelease" in premiereString:
        eventString = 'Pre Release'
    return eventString

for i in trange(len(eventUrls)):
    
    eventUrl = eventUrls[i]
    try:
        r = requests.get(baseUrl + eventUrl, cookies=cj)
        eventContent = BeautifulSoup(r.content, "lxml")
        eventDict = {}
        infoSelector = '#mainContent > div > div.roundedBucket-mid > div.oneColumn-twoColumns > div.col2 > div > div > div > div > form:nth-child(1) > fieldset > div.bot > dl > div > ol'
        eventDict = getEventInfo(eventContent, infoSelector, eventDict)
            
        venueInfoSelector = '#mainContent > div > div.roundedBucket-mid > div.oneColumn-twoColumns > div.col2 > div > div > div > div > form:nth-child(3) > fieldset:nth-child(2) > div.bot > ol'    
        eventDict = getEventInfo(eventContent, venueInfoSelector, eventDict)
        
        otherInfoSelector = '#mainContent > div > div.roundedBucket-mid > div.oneColumn-twoColumns > div.col2 > div > div > div > div > form:nth-child(3) > fieldset:nth-child(4) > div.bot > ol'
        
        eventDict = getEventInfo(eventContent, otherInfoSelector, eventDict)
        
        playersSelector = '#mainContent > div > div.roundedBucket-mid > div.oneColumn-twoColumns > div.col2 > div > div > div > div > form:nth-child(3) > fieldset:nth-child(5) > div.bot > ol'
        eventDict = getEventInfo(eventContent, playersSelector, eventDict)

        eventDict['Event Type'] = getEventType(eventDict["Premier Event"])
        allEventData.append(eventDict)
        if os.path.exists('data/events/{}.json'.format(eventDict['Tournament ID'])):
            continue
        
        with open('data/events/{}.json'.format(eventDict['Tournament ID']), 'w') as f:
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
                        df['event_type'] = getEventType(eventDict["Premier Event"])
                        df["event_name"] = eventDict["Tournament Name"]
                        df.to_csv('data/standings/{}.csv'.format(eventDict['Tournament ID']), index=False)
                        break    
                break
    except Exception as e:
        logger.error('Error in event: ' + eventUrl)
        logger.error(e)
        logger.error(eventContent)
        
        

event_df = pd.DataFrame(allEventData)
event_df.to_csv('data/events/all_events.csv', index=False)

all_files = glob.glob(os.path.join('./data/standings/', "*.csv"))
df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
df.to_csv('data/standings/all.csv', index=False)