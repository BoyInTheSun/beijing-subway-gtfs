import os
import requests
import json
from tqdm import tqdm
import os

from tools import tool

API_KEY = open(os.path.join(os.path.dirname(__file__), 'api_key.txt')).read().strip()
DATA_DIR = os.path.join('data', 'amap')


def get_stops():
    os.makedirs(os.path.join(DATA_DIR, 'stations'), exist_ok=True)
    map_h5 = tool.map_h5
    for each in tqdm(map_h5['stations_data']):
        station_name = each['cn_name']
        station_id = each['id']
        city_code = 110000  # 北京市的行政区划代码
        if station_name in ['大兴机场', '沙城站']:
            city_code = ''

        url = "https://restapi.amap.com/v3/bus/stopname"
        params = {
            "keywords": station_name + '地铁站',
            "city": city_code,
            "offset": 100,
            "page": 1,
            "key": API_KEY
        }
        
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            if data['status'] == '1':
                busstops = data.get('busstops', [])
                if busstops:
                    with open(os.path.join(DATA_DIR, 'stations', f"{station_id}.json"), 'w', encoding='utf-8') as f:
                        json.dump(busstops, f, ensure_ascii=False, indent=2)
                else:
                    print(f"未找到 {station_name} 的公交站点信息")
            else:
                print(f"请求失败，错误信息: {data.get('info', '未知错误')}")
        else:
            print(f"HTTP请求失败，状态码: {r.status_code}")

def get_line(line_id):
    url = "https://restapi.amap.com/v3/bus/lineid"
    params = {
        "key": API_KEY,
        "id": line_id,
        "extensions": 'all',
    }
    r = requests.get(url, params=params)
    print(r.json())

def get_path(origin, destination, origin_id='', destination_id=''):
    url = "https://restapi.amap.com/v5/direction/transit/integrated"
    params = {
        "key": API_KEY,
        "origin": origin,
        "destination": destination,
        "originpoi": origin_id,
        "destinationpoi": destination_id,
        "strategy": 0,
        "city1": "010",
        "city2": "010",
    }
    r = requests.get(url, params=params)
    print(r.json())

if __name__ == '__main__':
    # get_stops()
    # get_line('110100033067')
    get_path('116.353226,39.941670', '116.355426,39.940474', 'BV10001595', 'BV10001595')