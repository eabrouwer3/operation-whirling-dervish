from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from urllib import parse as urlparser
import json
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
import pandas as pd
from toolz.curried import *

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")

def get_comp_soup(comp_id):
    browser = webdriver.Chrome(options=chrome_options)
    browser.get(f'https://www.digitalrock.de/egroupware/ranking/sitemgr/digitalrock/eliste.html#comp={comp_id}')
    time.sleep(3)
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    browser.quit()
    return soup

def get_comp_data(soup):
    return {
        'name': soup.find(class_='compHeader').string,
        'dates': soup.find(class_='resultDate').string
    }

def scrape(i):
    print(f'Scraping Comp id: {i}')
    try:
        soup = get_comp_soup(i)
        data = get_comp_data(soup)
        return i, data
    except Exception as e:
        print(f'Error while processing id: {i}')
        print(e)


async def run_async_tasks(loop, func, i_list):
    with ThreadPoolExecutor(20) as executor:
        result = []
        for response in await asyncio.gather(*[loop.run_in_executor(executor, func, i) for i in i_list]):
            result.append(response)
        return result

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
    except Exception as e:
        print(e)
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

    with open('../data/athlete_comps.json') as f:
        data = json.loads(f.read())
        athlete_comp_result = {athlete_id: merge(*[{comp['comp']: comp['result']} for comp in comps]) for athlete_id, comps in data.items()}
        event_df = pd.read_json(json.dumps(athlete_comp_result), orient='index')

    start = time.time()
    results = list(filter(lambda x: x, loop.run_until_complete(asyncio.ensure_future(run_async_tasks(loop, scrape, event_df.columns.unique()[:10])))))
    print(f'Finished scraping in {time.time() - start} seconds')

    comp_data = {}
    for i, data in results:
        comp_data[i] = data,

    start = time.time()
    with open('../data/comp_data.json', 'w+') as f:
        f.write(json.dumps(comp_data))
    print(f'Finished writing comps to file in {time.time() - start} seconds')
