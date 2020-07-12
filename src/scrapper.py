import time
import pickle
import os
from datetime import datetime
import requests
import git
from slugify import slugify
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import pandas as pd


dir_project = git.Repo('.', search_parent_directories=True).working_tree_dir
dir_data = dir_project + '/data'
dir_houses = dir_data + '/houses'
URL_BASE = 'https://www.willhaben.at'
today = datetime.today().strftime('%Y-%m-%d')

for dir_tmp in [dir_data, dir_houses]:
    if not os.path.exists(dir_tmp):
        os.mkdir(dir_tmp)


def get_houses_index(payload):
    houses = {}
    payload.update({'rows': 100})
    page = 1
    while True:
        payload['page'] = page
        response = requests.get(URL_BASE + '/iad/immobilien/haus-kaufen/haus-angebote', params=payload)
        response = BeautifulSoup(response.text, features="html.parser").findAll('section', {'class': 'isRealestate'})
        for house in response:
            houses[house.find('a')['data-ad-link']] = {'url': house.find('a')['href']}
        if len(response) < 100:
            break
        page += 1
        time.sleep(1)
    return houses


def get_houses(houses):
    for house in houses:
        fname = '{}/{}.pickle'.format(dir_houses, house)
        print(house)
        if os.path.exists(fname):
            print('Existing file found')
            houses[house] = pickle.load(open(fname, 'rb'))
        else:
            while not os.path.exists(fname):
                print('Getting raw data')
                session = HTMLSession()
                response = session.get(URL_BASE + houses[house]['url'])
                response.html.render()
                response = BeautifulSoup(response.text, features="html.parser")
                content = {}

                print('Processing Address')
                content['location'] = response.find('div', {'data-testid': 'object-location-address'}).text.strip()

                print('Processing tables')
                for block in response.findAll('div', {'class': 'Box-wfmb7k-0 hmwkCc'}):
                    try:
                        key = block.find('h2').text.strip()
                    except AttributeError:
                        pass
                    if key in ['Objektinformationen', 'Ausstattung und Freiflächen']:
                        content[key] = {}
                        for item in block.findAll('li'):
                            content[key][item.findAll('div')[0].text.strip()] = item.findAll('div')[1].text.strip()

                print('Processing lists')
                for block in response.findAll('div', {'class': 'Box-wfmb7k-0 fvbBAP'}):
                    try:
                        key = block.find('h2').text.strip()
                    except AttributeError:
                        pass
                    if key in['Preisinformation', 'Energieausweis']:
                        content[key] = {}
                        if key == 'Energieausweis':
                            block_inner = block.findAll('div', {'class':'Box-wfmb7k-0 gYXGcz'})
                        elif key == 'Preisinformation':
                            block_inner = block.findAll('div', {'class': 'Box-wfmb7k-0 ejiEOL'})
                        for item in block_inner:
                            content[key][item.findAll('span')[0].text.strip()] = item.findAll('span')[1].text.strip()

                content['date'] = today
                houses[house].update(content)
                pickle.dump(houses[house], open(fname, 'wb'))

                session.close()
                time.sleep(1)
    return houses


def check_status(houses):
    print('Compiling data')
    for house in houses:
        houses[house]['live'] = True
    for fname in os.listdir(dir_houses):
        if os.path.isfile(dir_houses + '/' + fname):
            house = fname.split('.')[0]
            if house not in houses:
                houses[house] = pickle.load(open('{}/{}'.format(dir_houses, fname), 'rb'))
                houses[house]['live'] = False
    return houses


def munging(houses):
    dataframe = pd.DataFrame.from_dict(houses, orient='index')
    dataframe = pd.concat([dataframe.drop(['Objektinformationen'], axis=1),
                           dataframe['Objektinformationen'].apply(pd.Series)], axis=1)
    dataframe = pd.concat([dataframe.drop(['Ausstattung und Freiflächen'], axis=1),
                           dataframe['Ausstattung und Freiflächen'].apply(pd.Series).notnull()], axis=1)
    dataframe = pd.concat([dataframe.drop(['Energieausweis'], axis=1),
                           dataframe['Energieausweis'].apply(pd.Series)], axis=1)
    dataframe = pd.concat([dataframe.drop(['Preisinformation'], axis=1),
                           dataframe['Preisinformation'].apply(pd.Series)], axis=1)
    dataframe = dataframe.rename(columns={x: slugify(str(x)) for x in dataframe.columns})
    return dataframe


def main():
    regions = {
        'baden': {'parent_areaid': 3, 'areaId': 306},
        'modling': {'parent_areaid': 3, 'areaId': 317},
    }
    houses = [get_houses_index(regions[region]) for region in regions]
    houses = {k: v for region in houses for k, v in region.items()}
    houses = get_houses(houses)
    houses = check_status(houses)
    houses = munging(houses)
    houses.to_csv(dir_data+'/houses.csv')


if __name__ == '__main__':
    main()
