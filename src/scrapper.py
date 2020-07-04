import requests
import time
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import pandas as pd
from slugify import slugify
import pickle
import os
import pyppeteer.errors


dir_project = '/home/alistair/workspace/willhaben_houses'
dir_data = dir_project + '/data'
dir_houses = dir_data + '/houses'
url_base = 'https://www.willhaben.at'
payload_baden = {'parent_areaid': 3, 'areaId': 306}
payload_modling = {'parent_areaid': 3, 'areaId': 317}

houses = {}
for payload in [payload_baden,payload_modling]:
    payload.update({'rows': 100})
    page = 1
    while True:
        payload['page'] = page
        r = requests.get(url_base + '/iad/immobilien/haus-kaufen/haus-angebote', params=payload)
        bs = BeautifulSoup(r.text, features="html.parser").findAll('section', {'class': 'isRealestate'})
        for house in bs:
            houses[house.find('a')['data-ad-link']] = {'url' :house.find('a')['href']}
        if len(bs) < 100:
            break
        else:
            page += 1
        time.sleep(1)


if not os.path.exists(dir_houses):
    os.mkdir(dir_houses)
#houses = {house: houses[house] for house in list(houses)[:10]}

for house in houses:
    fname = '{}/{}.pickle'.format(dir_houses, house)
    print(house)
    if os.path.exists(fname):
        print('Existing file found')
        houses[house] = pickle.load(open(fname, 'rb'))
    else:
        while not os.path.exists(fname):
            #try:
                print('Getting raw data')
                session = HTMLSession()
                print(1)
                r = session.get(url_base + houses[house]['url'])
                print(2)
                r.html.render()
                print(3)
                bs = BeautifulSoup(r.text, features="html.parser")
                content = {}

                print('Processing Address')
                content['location'] = bs.find('div', {'data-testid': 'object-location-address'}).text.strip()

                print('Processing tables')
                for block in bs.findAll('div', {'class': 'Box-wfmb7k-0 hmwkCc'}):
                    try:
                        key = block.find('h2').text.strip()
                    except AttributeError:
                        pass
                    if key in ['Objektinformationen', 'Ausstattung und Freiflächen']:
                        content[key] = {}
                        for x in block.findAll('li'):
                            content[key][x.findAll('div')[0].text.strip()] = x.findAll('div')[1].text.strip()

                print('Processing lists')
                for block in bs.findAll('div', {'class': 'Box-wfmb7k-0 fvbBAP'}):
                    try:
                        key = block.find('h2').text.strip()
                    except AttributeError:
                        pass
                    if key in['Preisinformation','Energieausweis']:
                        content[key] = {}
                        if key == 'Energieausweis':
                            block_inner = block.findAll('div',{'class':'Box-wfmb7k-0 gYXGcz'})
                        elif key == 'Preisinformation':
                            block_inner = block.findAll('div', {'class': 'Box-wfmb7k-0 ejiEOL'})
                        for x in block_inner:
                            content[key][x.findAll('span')[0].text.strip()] = x.findAll('span')[1].text.strip()

                houses[house].update(content)
                pickle.dump(houses[house], open(fname, 'wb'))

                session.close()
                time.sleep(1)

print('Compiling data')
for house in houses:
    houses[house]['live'] = True
for fname in os.listdir(dir_houses):
    if os.path.isfile(dir_houses + '/' + fname):
        house = fname.split('.')[0]
        if house not in houses:
            houses[house] = pickle.load(open(dir_houses + '/' + fname,'rb'))
            houses[house]['live'] = False


df = pd.DataFrame.from_dict(houses, orient='index')

df = pd.concat([df.drop(['Objektinformationen'],axis=1), df['Objektinformationen'].apply(pd.Series)], axis=1)
df = pd.concat([df.drop(['Ausstattung und Freiflächen'],axis=1),
                df['Ausstattung und Freiflächen'].apply(pd.Series).notnull()], axis=1)
#df = pd.concat([df.drop(['Ausstattung und Freifläche'],axis=1),
#                df['Ausstattung und Freifläche'].apply(pd.Series).replace('','True').fillna('No')], axis=1)
df = pd.concat([df.drop(['Energieausweis'],axis=1), df['Energieausweis'].apply(pd.Series)], axis=1)
df = pd.concat([df.drop(['Preisinformation'],axis=1), df['Preisinformation'].apply(pd.Series)], axis=1)

df = df.rename(columns={x:slugify(str(x)) for x in df.columns})

#for key in ['wohnflache', 'grundflache', 'gesamtflache', 'nutzflache']:
#    df[key] = pd.to_numeric(df[key].fillna('').str.slice(0,-3))

df.to_csv(dir_data+'/houses.csv')