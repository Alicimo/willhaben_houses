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


DIR_PROJECT = git.Repo('.', search_parent_directories=True).working_tree_dir
DIR_DATA = DIR_PROJECT + '/data'
DIR_HOUSES = DIR_DATA + '/houses'
URL_BASE = 'https://www.willhaben.at'
TODAY = datetime.today().strftime('%Y-%m-%d')

for dir_tmp in [DIR_DATA, DIR_HOUSES]:
    if not os.path.exists(dir_tmp):
        os.mkdir(dir_tmp)


def get_houses_index(payload):
    houses = {}
    payload.update({'rows': 100, 'page': 1})
    while True:
        houses.update(_download_index(payload))
        if len(houses) % 100:
            break
        payload['page'] += 1
        time.sleep(1)
    return houses


def _download_index(payload):
    response = requests.get(URL_BASE + '/iad/immobilien/haus-kaufen/haus-angebote', params=payload)
    response = BeautifulSoup(response.text, features="html.parser")
    response = response.findAll('section', {'class': 'isRealestate'})
    response = {house.find('a')['data-ad-link']: {'url': house.find('a')['href']} for house in response}
    return response


def get_houses(houses):
    for house in houses:
        fname = '{}/{}.pickle'.format(DIR_HOUSES, house)
        new_count = 0
        if os.path.exists(fname):
            houses[house] = pickle.load(open(fname, 'rb'))
        else:
            print(house)
            new_count += 1
            while not os.path.exists(fname):
                content = get_house(houses[house]['url'])
                content['date'] = TODAY
                houses[house].update(content)
                pickle.dump(houses[house], open(fname, 'wb'))
                time.sleep(1)
    print("Found {} new houses".format(new_count))
    return houses


def get_house(url_house):
    content = {}
    print('Getting raw data')
    response = _download_house(url_house)
    print('Processing Address')
    content.update(_extract_house_location(response))
    print('Processing tables')
    content.update(_extract_house_tables(response))
    print('Processing lists')
    content.update(_extract_house_lists(response))
    return content


def _download_house(url_house):
    session = HTMLSession()
    response = session.get(URL_BASE + url_house)
    response.html.render()
    response = BeautifulSoup(response.text, features="html.parser")
    session.close()
    return response


def _extract_house_location(response):
    location = response.find('div', {'data-testid': 'object-location-address'}).text.strip()
    return {'location': location}


def _extract_house_tables(response):
    content = {}
    for block in response.findAll('div', {'class': 'Box-wfmb7k-0 hmwkCc'}):
        try:
            key = block.find('h2').text.strip()
        except AttributeError:
            pass
        if key in ['Objektinformationen', 'Ausstattung und Freiflächen']:
            content[key] = {}
            for item in block.findAll('li'):
                content[key][item.findAll('div')[0].text.strip()] = item.findAll('div')[1].text.strip()
    return content


def _extract_house_lists(response):
    content = {}
    for block in response.findAll('div', {'class': 'Box-wfmb7k-0 fvbBAP'}):
        try:
            key = block.find('h2').text.strip()
        except AttributeError:
            pass
        if key in ['Preisinformation', 'Energieausweis']:
            content[key] = {}
            if key == 'Energieausweis':
                block_inner = block.findAll('div', {'class': 'Box-wfmb7k-0 gYXGcz'})
            elif key == 'Preisinformation':
                block_inner = block.findAll('div', {'class': 'Box-wfmb7k-0 ejiEOL'})
            for item in block_inner:
                content[key][item.findAll('span')[0].text.strip()] = item.findAll('span')[1].text.strip()
    return content


def check_status(houses):
    print('Compiling data')
    for house in houses:
        houses[house]['live'] = True
    for fname in os.listdir(DIR_HOUSES):
        if os.path.isfile(DIR_HOUSES + '/' + fname):
            house = fname.split('.')[0]
            if house not in houses:
                houses[house] = pickle.load(open('{}/{}'.format(DIR_HOUSES, fname), 'rb'))
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
    houses.to_csv(DIR_DATA + '/houses.csv')


if __name__ == '__main__':
    main()
