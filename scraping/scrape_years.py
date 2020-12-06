from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from urllib import parse as urlparser
import json
from concurrent.futures.thread import ThreadPoolExecutor
import pprint
import traceback
pp = pprint.PrettyPrinter(indent=4)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")

# GLOBAL OPTIONS
# WORKERS = 50


def get_year_soup(year):
    browser = webdriver.Chrome(options=chrome_options)
    browser.get(f'https://www.digitalrock.de/egroupware/ranking/sitemgr/digitalrock/eliste.html#!year={year}')
    time.sleep(1)
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    browser.quit()
    return soup

cat_types = [
    'm e n lead',
    'w o m e n lead',
    'm e n bouldering',
    'w o m e n bouldering',
    'm e n speed',
    'w o m e n speed',
]


def get_worldcups(soup):
    comp_divs = soup.find_all('div', class_='competition')
    def filter_comp(comp):
        title = str(comp.find(class_='title').text).lower()
        return 'worldcup' in title
    comp_divs = list(filter(filter_comp, comp_divs))
    comps = []
    for comp in comp_divs:
        title = str(comp.find(class_='title').text).lower()
        date = str(comp.find(class_='date').text)
        cats = comp.find('ul', class_='cats')
        for cat in cats or []:
            link = cat.find('a')
            link_text = str(link.text if link else '').lower()
            if link_text in cat_types:
                comp_id, cat_id = link['href'][2:].split('&')
                comp_id = comp_id.split('=')[1]
                cat_id = cat_id.split('=')[1]
                comps.append({
                    'title': title,
                    'date': date,
                    'comp_id': comp_id,
                    'cat_id': cat_id,
                    'type': link_text.split(' ')[-1]
                })
    return comps


def get_comp_soup(comp_id, cat_id):
    browser = webdriver.Chrome(options=chrome_options)
    browser.get(f'https://www.digitalrock.de/egroupware/ranking/sitemgr/digitalrock/eliste.html#!comp={comp_id}&cat={cat_id}')
    time.sleep(3)
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    browser.quit()
    return soup


def get_comp_athletes(soup):
    rows = soup.find(class_='DrTable').find('tbody').find_all('tr')
    ranked_athletes = []
    for row in rows:
        ranked_athletes.append({
            'athlete_id': int(row.get('id')),
            'rank': int(row.find(class_='result_rank').text)
        })
    return ranked_athletes


def scrape(comp_id, cat_id):
    print(f'Scraping: comp_id={comp_id}, cat_id={cat_id}')
    try:
        soup = get_comp_soup(comp_id, cat_id)
        return get_comp_athletes(soup)
    except Exception as e:
        print(f'Error while processing: comp_id={comp_id}, cat_id={cat_id}')
        print(e)
        traceback.print_exc()


def main():
    for year in range(2013,2020):
        print(year)
        start = time.time()
        year_soup = get_year_soup(year)
        worldcups = get_worldcups(year_soup)
        for worldcup in worldcups:
            ranked_athletes = scrape(worldcup['comp_id'], worldcup['cat_id'])
            worldcup['ranked_athletes'] = ranked_athletes
#         pp.pprint(worldcups)
        print(f'Finished scraping {year} in {time.time() - start} seconds')
    
        start = time.time()
        with open(f'../data/year_data_{year}.json', 'w+') as f:
            f.write(json.dumps(worldcups))
        print(f'Finished writing to file for {year} in {time.time() - start} seconds')


if __name__ == '__main__':
    main()
