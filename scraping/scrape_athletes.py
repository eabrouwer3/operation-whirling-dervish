from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from urllib import parse as urlparser
import json
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")

# GLOBAL OPTIONS
BEGIN = 1
END = 1000
WORKERS = 10


def get_athlete_soup(athlete_id):
    browser = webdriver.Chrome(options=chrome_options)
    browser.get(f'https://www.digitalrock.de/egroupware/ranking/sitemgr/digitalrock/pstambl.html#person={athlete_id}')
    time.sleep(3)
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


def scrape(i):
    print(f'Scraping id: {i}')
    try:
        soup = get_athlete_soup(i)
        profile = soup.find(id='profile')
        if profile and profile.contents:
            data = get_athlete_data(soup)
            comps = get_athlete_comps(soup)
            return i, data, comps
    except Exception as e:
        print(f'Error while processing id: {i}')
        print(e)


async def run_async_tasks(loop, func, i_list):
    with ThreadPoolExecutor(WORKERS) as executor:
        result = []
        for response in await asyncio.gather(*[loop.run_in_executor(executor, func, i) for i in i_list]):
            result.append(response)
        return result


def main():
    try:
        loop = asyncio.get_event_loop()
    except Exception as e:
        print(e)
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
    start = time.time()
    results = list(filter(lambda x: x, loop.run_until_complete(asyncio.ensure_future(run_async_tasks(loop, scrape, range(BEGIN, END+1))))))
    print(f'Finished scraping in {time.time() - start} seconds')

    athletes_data = {}
    athletes_comps = {}
    for i, data, comps in results:
        athletes_data[i] = data,
        athletes_comps[i] = comps

    start = time.time()
    with open('../data/athlete_data.json', 'w+') as f:
        f.write(json.dumps(athletes_data))
    with open('../data/athlete_comps.json', 'w+') as f:
        f.write(json.dumps(athletes_comps))
    print(f'Finished writing to files in {time.time() - start} seconds')


if __name__ == '__main__':
    main()
