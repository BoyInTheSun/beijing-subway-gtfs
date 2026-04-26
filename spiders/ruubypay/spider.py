import requests
import os
import time
import datetime
import hmac
import hashlib
import json
from typing import Any, Dict
from tqdm import tqdm

KEY_HEX_DEFAULT = open(os.path.join(os.path.dirname(__file__), 'key_hex.txt')).read().strip()
JSON_NAMES = (
    'acclocation', # device_location对应站点以及线路
    'map-h5',  # 站点以及线路详情 原始信息
    'excessFareTicketStationSelect',  # 站点以及线路详情 虚拟线路信息
    'fareRegionMapping',  # 线路收费区域信息
    'pisStationSelect'  # PIS选站过滤参数
)
# APPCONFIG_HOST = 'https://appconfig-ft.ruubypay.com'  # test?
APPCONFIG_HOST = 'https://appconfig.ruubypay.com'
API_HOST = 'https://api.ruubypay.com'
WEB_HOST = 'https://appconfig.ruubypay.com'
UA = 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36'
DATA_DIR = os.path.join('data', 'ruubypay')
SLEEP_SECONDS = 1

def _js_stringify_value(v: Any) -> str:
    """模仿 JS String() 行为的简单转换。
    - None -> 'null'
    - bool -> 'true'/'false'
    - numbers and strings -> str(v)
    """
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    # 对于 bytes 不特别处理，转为 str
    return str(v)


def _serialize(obj: Any) -> str:
    """按前端实现的规则序列化对象/数组/原子值为签名字符串片段。"""
    # 数组（列表/元组）
    if isinstance(obj, (list, tuple)):
        inner = "".join(_serialize(x) for x in obj)
        return f"[{inner}]"
    # 对象（字典）
    if isinstance(obj, dict):
        # 按键的小写字母序排序，但保留原键名用于拼接
        keys = sorted(obj.keys(), key=lambda k: str(k).lower())
        s = ""
        for k in keys:
            s += f"{k}{_serialize(obj[k])}||"
        return s
    # 其它原子值
    return _js_stringify_value(obj)


def make_mac(params: Dict[str, Any], key_hex: str = KEY_HEX_DEFAULT) -> Dict[str, Any]:
    """返回包含 `ts` 与 `mac` 的新参数字典（不会修改原始字典）。"""
    data = dict(params)  # shallow copy
    data["ts"] = str(int(time.time()))
    serialized = _serialize(data)
    key_bytes = bytes.fromhex(key_hex)
    mac = hmac.new(key_bytes, serialized.encode("utf-8"), hashlib.sha1).hexdigest().upper()
    data["mac"] = mac
    return data


def get_base():
    for json_name in JSON_NAMES:
        print(json_name)
        r = requests.get(
            APPCONFIG_HOST + '/stations/' + json_name + '.json',
            headers={
                'referer': WEB_HOST,
                'user-agent': UA,
            }
        )
        with open(os.path.join(DATA_DIR, json_name + '.json'), 'wb') as f:
            f.write(r.content)
        time.sleep(SLEEP_SECONDS)

def get_data(api, device_location):
    '''
    Docstring for get_data
    
    :param api: getStationTimetable | getRealtimeStationInfo | getStationEquipment
    :param device_location: 
    '''
    device_location = str(device_location)
    # print(device_location)
    params = {
        "cityCode": "1101",
        "deviceLocation": device_location,  # str或int均可，且可用str“,”隔开多个
    }
    signed = make_mac(params)
    r = requests.post(
        API_HOST + '/marketingpis/appSides/' + api,
        headers={
            'accept': 'application/json, text/plain, */*',
            'referer': WEB_HOST,
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'content-type': 'application/json;charset=UTF-8',
            'user-agent': UA,
        },
        data=json.dumps(signed)
    )
    res = json.loads(r.text)
    if not res['resCode'] == "00000000":
        print(res)
        return None
    data = res['resData']
    return data
 
def download_data(api, device_location):
    '''
    Docstring for download_data_all
    
    :param api: getStationTimetable | getRealtimeStationInfo | getStationEquipment
    '''
    data_name = {'getStationTimetable': 'timetable', 'getRealtimeStationInfo': 'realtime', 'getStationEquipment': 'equipment'}[api]
    if not os.path.exists(os.path.join(DATA_DIR, data_name)):
        os.mkdir(os.path.join(DATA_DIR, data_name))
    data = get_data(api, device_location)
    with open(os.path.join(DATA_DIR, data_name, str(device_location) + '.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    time.sleep(SLEEP_SECONDS)


def download_data_all(api):
    '''
    Docstring for download_data_all
    
    :param api: getStationTimetable | getRealtimeStationInfo | getStationEquipment
    '''
    data_name = {'getStationTimetable': 'timetable', 'getRealtimeStationInfo': 'realtime', 'getStationEquipment': 'equipment'}[api]
    with open(os.path.join(DATA_DIR, 'acclocation.json'), encoding='utf-8') as f:
        acclocation = json.load(f)
    print(f'Get data for {data_name}...')
    if not os.path.isdir(data_name):
        os.mkdir(data_name)
    for each in tqdm(acclocation):
        device_location = each['device_location']
        download_data(api, device_location)

     
if __name__ == '__main__':
    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)
    # get_base()
    download_data_all('getStationEquipment')
    download_data_all('getStationTimetable')
    