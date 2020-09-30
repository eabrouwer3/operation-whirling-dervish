from selenium import webdriver
from bs4 import BeautifulSoup
import time
from urllib import parse as urlparser
import json


def get_athlete_soup(athlete_id):
    browser = webdriver.Chrome()
    browser.get(f'https://www.digitalrock.de/egroupware/ranking/sitemgr/digitalrock/pstambl.html#person={athlete_id}')
    time.sleep(2.5)
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    browser.close()
    return soup


def get_athlete_data(soup):
    return {
        'first_name': soup.find(class_='firstname').string,
        'last_name': soup.find(class_='lastname').string,
        'country': soup.find(class_='profileNation').string,
        'age': soup.find(class_='profileAge').string,
        'birth_year': soup.find(class_='profileBirthdate').string,
        'height': soup.find(class_='profileHeight').string,
        'weight': soup.find(class_='profileWeight').string
    }


def get_athlete_comps(soup):
    results = soup.find_all(class_='profileResult')

    def parse_result(res):
        return {
            'result': res.find(class_='profileResultRank').string,
            'comp': urlparser.parse_qs(urlparser.urlparse(res.find('a')['href']).fragment)['comp'][0],
            'date': res.find(class_='profileResultDate').string
        }
    return list(map(parse_result, results))


if __name__ == '__main__':
    athletes_data = []
    athletes_comps = {}
    for i in range(1, 11):
        try:
            soup = get_athlete_soup(i)
            profile = soup.find(id='profile')
            if profile.contents:
                athletes_data.append(get_athlete_data(soup))
                athletes_comps[i] = get_athlete_comps(soup)
        except Exception as e:
            print(f'Error while processing id: {i}')
            print(e)

    with open('../data/athlete_data.json', 'w+') as f:
        f.write(json.dumps(athletes_data))
    with open('../data/authlete_comps.json', 'w+') as f:
        f.write(json.dumps(athletes_comps))
