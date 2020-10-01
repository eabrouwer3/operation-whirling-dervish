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
BATCH_SIZE = 1000
END = 1000000
WORKERS = 50


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


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main():
    try:
        loop = asyncio.get_event_loop()
    except Exception as e:
        print(e)
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

    ranges = chunks(list(range(BEGIN, END+1)), BATCH_SIZE)
    for r in ranges:
        start = time.time()
        results = list(filter(lambda x: x, loop.run_until_complete(asyncio.ensure_future(run_async_tasks(loop, scrape, r)))))
        print(f'Finished scraping {r[0]}-{r[-1]} in {time.time() - start} seconds')

        athletes_data = {}
        athletes_comps = {}
        for i, data, comps in results:
            athletes_data[i] = data,
            athletes_comps[i] = comps
    
        start = time.time()
        with open(f'../data/athlete_data_{r[0]}_{r[-1]}.json', 'w+') as f:
            f.write(json.dumps(athletes_data))
        with open(f'../data/athlete_comps_{r[0]}_{r[-1]}.json', 'w+') as f:
            f.write(json.dumps(athletes_comps))
        print(f'Finished writing to files for {r[0]}-{r[-1]} in {time.time() - start} seconds')


if __name__ == '__main__':
    main()
