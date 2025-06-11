# Generated code for VisitPokemonAndLogin
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
from io import StringIO
import glob
import config

baseUrl = 'https://www.pokemon.com'


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


def run_getstandings(standingsURL, endpointURL):
    """Execute the GraphQL query and handle the response."""
    # Read the GraphQL query from file
    
    standingsFileName = 'bql/getStandings.graphql'

    standingsQuery = config.ROOT_DIR / standingsFileName


    with open(standingsQuery, 'r', encoding='utf-8') as f:
        query = f.read()
    query = query.replace('___REPLACE_URL___', standingsURL)
    # Prepare the payload
    standingsQuery = {
        "query": query
    }

    try:
        response = requests.post(
            endpointURL,
            params=config.QUERY_STRING,
            json=standingsQuery
        )
        data = response.json()

        if data.get('errors'):
            print('Errors:', json.dumps(data['errors'], indent=2))
            return data
        return data
    except Exception as e:
        print('Error:', e)
        raise



def run_visitpokemonandlogin():
    """Execute the GraphQL query and handle the response."""
    # Read the GraphQL query from file
    print("Getting events")
    eventsFilename = 'bql/getEvents.graphql'
    eventsQuery = config.ROOT_DIR / eventsFilename

    with open(eventsQuery, 'r', encoding='utf-8') as f:
        query = f.read()

    query= query.replace('__REPLACE__USER__', config.default_user)
    query= query.replace('__REPLACE__PASSWORD__', config.default_pass)

    # Prepare the payload


    try:
        with open(config.ROOT_DIR / 'bql/init.graphql', 'r', encoding='utf-8') as f:
            initQuery = f.read()
        initResponse = requests.post(
            config.ENDPOINT,
            params=config.QUERY_STRING,
            headers=config.HEADERS,
            json={
                "query": initQuery
            }
        )
        initData = initResponse.json()
        print(initData)
        if initData.get('errors'):
            print('Errors:', json.dumps(initData['errors'], indent=2))
            return
        payload = {
            "query": query,
            "operationName": "VisitPokemonAndLogin",
        }
        response = requests.post(
            initData['data']['reconnectBrowser']['browserQLEndpoint'],
            params=config.QUERY_STRING,
            json=payload
        )
        data = response.json()
        if data.get('errors'):
            print('Errors:', json.dumps(data['errors'], indent=2))
            return
        with open('../processing/listData.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        eventsDict = json.loads(data['data']['getText']['text'])
        reconnectEndpoint = data['data']['reconnectBrowser']['browserQLEndpoint']
        eventUrls = []

        for event in eventsDict['rows']:
            for eventData in event['columns']:
                if 'html' in eventData.keys():
                    try:
                        eventUrl = BeautifulSoup(eventData['html'], 'html.parser').a['href']
                        print(eventUrl)
                        if eventUrl is not None:
                            if 'leagues' in eventUrl:
                                continue
                            eventID = os.path.basename(os.path.normpath(eventUrl))
                            if os.path.exists('../data/events/{}.json'.format(eventID)):
                                continue
                            eventUrls.append(eventUrl)
                    except Exception as e:
                        print('Error processing event URL:', e)
                        print(eventData)

        print('Found {} events'.format(len(eventUrls)))
        for eventURL in eventUrls:
            eventID = os.path.basename(os.path.normpath(eventURL))

            print('Processing event:', eventURL)
            if '/leagues' in eventURL:
                continue
            standingData = run_getstandings(baseUrl + eventURL, reconnectEndpoint)
            with open('../processing/session_{}.json'.format(eventID), 'w') as f:
                json.dump(standingData, f, ensure_ascii=False, indent=4)
            
            reconnectEndpoint = standingData['data']['reconnectBrowser']['browserQLEndpoint']
            eventContent = BeautifulSoup(standingData['data']['eventsText']["html"], "lxml")
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
            if 'errors' not in eventDict.keys():
                with open('../processing/{}.json'.format(eventDict['Tournament ID']), 'w') as f:
                    json.dump(eventDict, f, ensure_ascii=False, indent=4)
            else:
                break
            for anchor in eventContent.find_all('a'):
                if anchor.get('href') and 'standings' in anchor.get('href'):
                    standingsLink = anchor.get('href')
                    masterData = run_getstandings(baseUrl + standingsLink + '/master', reconnectEndpoint)
                    positionContent = BeautifulSoup(masterData['data']['eventsText']["html"], "lxml")
                    positionTable = positionContent.find_all('table')[0]
                    df = pd.read_html(StringIO(str(positionTable)))[0]
                    df['pct_pos'] = df['Position'].rank(pct=True)
                    df['rank'] = (df['pct_pos']*100).round()
                    df['date'] = eventDict['Date']
                    df['event'] = eventDict['Tournament ID']
                    df['event_type'] = getEventType(eventDict["Premier Event"])
                    df["event_name"] = eventDict["Tournament Name"]
                    df.to_csv('../processing/{}.csv'.format(eventDict['Tournament ID']), index=False)
                    reconnectEndpoint = masterData['data']['reconnectBrowser']['browserQLEndpoint']
                    break
            os.replace('../processing/{}.json'.format(eventDict['Tournament ID']), '../data/events/{}.json'.format(eventDict['Tournament ID']))
            os.replace('../processing/{}.csv'.format(eventDict['Tournament ID']), '../data/standings/{}.csv'.format(eventDict['Tournament ID']))
        print('All events processed successfully.')
    except Exception as e:
        print('Error:', e)
        raise

if __name__ == '__main__':
    run_visitpokemonandlogin()
    all_events_files = glob.glob(os.path.join('../data/events/', "*.json"))
    all_events_list = []
    for f in all_events_files:
        with open(f) as filedata:
            d = json.load(filedata)
            all_events_list.append(d)
    event_df = pd.DataFrame(all_events_list)
    os.remove('../data/events/all_events.csv')
    event_df.to_csv('../data/events/all_events.csv', index=False)
    
    all_files = glob.glob(os.path.join('../data/standings/', "*.csv"))
    df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
    os.remove('../data/standings/all.csv')
    df.to_csv('../data/standings/all.csv', index=False)
    
    files = glob.glob('../processing/*')
    for f in files:
        os.remove(f)
    