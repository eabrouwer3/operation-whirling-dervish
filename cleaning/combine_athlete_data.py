import glob
from toolz.curried import *
import json
import csv


if __name__ == '__main__':
    comps_paths = glob.glob('../data/athlete_comps*.json')
    data_paths = glob.glob('../data/athlete_data*.json')

    comps = {}
    for path in comps_paths:
        with open(path) as f:
            comps = merge(comps, json.loads(f.read()))
    data = {}
    for path in data_paths:
        with open(path) as f:
            data = merge(data, json.loads(f.read()))

    with open('../data/athlete_comps.json', 'w+') as f:
        f.write(json.dumps(comps))
    with open('../data/athlete_data.json', 'w+') as f:
        f.write(json.dumps(data))

    data_arr = [merge({'id': i}, data[0]) for i, data in data.items()]
    with open('../data/athlete_data.csv', 'w+') as f:
        writer = csv.DictWriter(f, fieldnames=data_arr[0].keys())
        writer.writeheader()
        writer.writerows(data_arr)
