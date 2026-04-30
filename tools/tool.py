import json
import os

DATA_DIR = 'data'

RUUBYPAY_LINE_ID2ROUTE_ID = {
    1: '01',
    2: '02',
    3: '03',
    4: '04',
    5: '05',
    6: '06',
    7: '07',
    8: '08',
    9: '09',
    10: '10',
    11: '11',
    12: '12',
    13: '13',
    14: '14',
    15: '15',
    16: '16',
    17: '17',
    18: '18',
    19: '19',
    79: 't1',
    88: 'da',
    89: 'xj',
    90: '10',
    91: 's1',
    92: 'yf',
    93: '04',
    94: 'cp',
    95: 'fs',
    96: 'yz',
    97: '01',
    98: 'ca',
}

acclocation = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'acclocation.json'), encoding='utf-8'))    
map_h5 = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'map-h5.json'), encoding='utf-8'))
excess_fare_ticket_station_select = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'excessFareTicketStationSelect.json'), encoding='utf-8'))
fare_region_mapping = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'fareRegionMapping.json'), encoding='utf-8'))
pis_station_select = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'pisStationSelect.json'), encoding='utf-8'))


ruubypay_station_name2station_id = {each['cn_name']: each['id'] for each in map_h5['stations_data']}
ruubypay_device_location2fare_location = {}
ruubypay_device_location2line_id = {}
ruubypay_route_id_station_id2device_location = {}
ruubypay_line_id_station_id2device_location = {}
for each in acclocation:
    line_id = each['line_id']
    if line_id not in RUUBYPAY_LINE_ID2ROUTE_ID: continue
    if line_id == 4 and each['station_id'] == 40: continue  # 公益西桥使用大兴线
    station_id = each['station_id']
    device_location = each['device_location']
    ruubypay_device_location2fare_location[device_location] = each['fare_location']
    ruubypay_device_location2line_id[device_location] = line_id
    ruubypay_route_id_station_id2device_location[(RUUBYPAY_LINE_ID2ROUTE_ID[line_id], station_id)] = device_location
    ruubypay_line_id_station_id2device_location[(line_id, station_id)] = device_location
    
line_station = {}
for line_item in excess_fare_ticket_station_select:
    for show_stations_item in line_item['show_stations']:
        line_id = show_stations_item['line']
        line_station[line_id] = []
        route_id = RUUBYPAY_LINE_ID2ROUTE_ID.get(int(line_id))
        for station_item in show_stations_item['stations']:
            station_id = station_item['id']
            device_location = ruubypay_line_id_station_id2device_location.get((line_id, station_id))
            line_station[line_id].append(device_location)


def device_location2internal_station_id(device_location):
    if not device_location: return None
    hex_str = hex(device_location)
    line_id = int(hex_str[-4: -2], 16)
    station_id = int(hex_str[-2:], 16)
    return f'{line_id:02d}00{station_id:02d}'

def compute_center_location(locations):
    if not locations: return None, None
    lon = sum(loc[0] for loc in locations) / len(locations)
    lat = sum(loc[1] for loc in locations) / len(locations)
    return lon, lat