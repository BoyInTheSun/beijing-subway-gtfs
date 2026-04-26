import json
import os
import csv
import re

from tqdm import tqdm
from tools import tool
import pandas as pd

DATA_DIR = 'data'
GTFS_DIR = 'gtfs'


ROUTE_ID2OSM_ROUTE_ID = {  # route_id: [上行, 下行]
    '01': [1667140, 1667139],
    '02': [1667237, 1667236],
    '03': [18420550, 18420549],
    '04': [2083780, 2083779],
    '05': [1721065, 1721064],
    '06': [4625141, 4625140],
    '07': [4623397, 4623396],
    '08': [1721067, 1721068],
    '09': [2063278, 2674583],
    '10': [1721075, 1721076],
    '11': [13623627, 13623625],
    '12': [18441519, 18441518],
    '13': [1667376, 1667375],
    '14': [4613036, 4611276],
    '15': [1350597, 2688948],
    '16': [8324249, 7800400],
    '17': [13625144, 13625142],
    '18': [20010805, 20010820],
    '19': [13625326, 13625325],
    's1': [8008812, 8008814],
    'ca': [2062998, 2062999],
    'cp': [2111425, 2111424],
    'da': [10136948, 10136949],
    'fs': [1721084, 1721085],
    't1': [12567201, 12567202],
    'xj': [8303695, 8008876],
    'yf': [12798054, 8469053],
    'yz': [2201487, 2201486],
}

if __name__ == '__main__':
    
    acclocation = tool.acclocation
    map_h5 = tool.map_h5
    ruubypay_station_name2station_id = {each['cn_name']: each['id'] for each in map_h5['stations_data']}
    ruubypay_station_id2device_location = {each['station_id']: each['device_location'] for each in acclocation}
    ruubypay_station_id2fare_location = {each['station_id']: each['fare_location'] for each in acclocation}
    
    with open(os.path.join(DATA_DIR, 'osm', 'route_master.json'),encoding='utf-8') as f:
        osm_route_master = json.load(f)
    with open(os.path.join(DATA_DIR, 'osm', 'route.json'),encoding='utf-8') as f:
        osm_route = json.load(f)
    with open(os.path.join(DATA_DIR, 'osm', 'stop_area.json'),encoding='utf-8') as f:
        osm_stop_area = json.load(f)
    with open(os.path.join(DATA_DIR, 'osm', 'stop_position.json'),encoding='utf-8') as f:
        osm_stop_position = json.load(f)
    with open(os.path.join(DATA_DIR, 'osm', 'station.json'),encoding='utf-8') as f:
        osm_station = json.load(f)
    with open(os.path.join(DATA_DIR, 'osm', 'entrance.json'),encoding='utf-8') as f:
        osm_entrance = json.load(f)
    with open(os.path.join(DATA_DIR, 'osm', 'node.json'),encoding='utf-8') as f:
        osm_node = json.load(f)
    
    arc_stop_area = {}
    for stop_area_id in osm_stop_area:
        for member in osm_stop_area[stop_area_id]['members']:
            arc_stop_area[member['type'] + str(member['ref'])] = stop_area_id
    arc_stop_area_group = {}
    for stop_area_group_id in osm_stop_area:
        for member in osm_stop_area[stop_area_group_id]['members']:
            arc_stop_area_group[member['type'] + str(member['ref'])] = stop_area_group_id
    arc_route = {}
    for route_id in osm_route:
        for member in osm_route[route_id]['members']:
            arc_route[member['type'] + str(member['ref'])] = route_id
    arc_route_master = {}
    for route_master_id in osm_route_master:
        for member in osm_route_master[route_master_id]['members']:
            arc_route_master[member['type'] + str(member['ref'])] = route_master_id
    osm_stop_area2station = {}
    for osm_stop_area_id in osm_stop_area:
        for member in osm_stop_area[osm_stop_area_id]['members']:
            if member['type'] in ['n', 'w'] and member['type'] + str(member['ref']) in osm_station:
                osm_stop_area2station[osm_stop_area_id] = member['type'] + str(member['ref'])
        for member in osm_stop_area[osm_stop_area_id]['members']:
            if member['type'] in ['n'] and member['type'] + str(member['ref']) in osm_station and osm_station[member['type'] + str(member['ref'])]['tags'].get('railway') == 'station' :
                osm_stop_area2station[osm_stop_area_id] = member['type'] + str(member['ref'])
                
    os.makedirs(os.path.join(DATA_DIR, 'interim'), exist_ok=True)
    with open(os.path.join(GTFS_DIR, 'stops.txt'), 'w', encoding='utf-8', newline='') as f_stops,\
         open(os.path.join(DATA_DIR, 'interim', 'relations.csv'), 'w', encoding='utf-8', newline='') as f_relations:
        writer_stops = csv.writer(f_stops)
        writer_stops.writerow([
            'stop_id', 
            'stop_code',
            'stop_name',
            'tts_stop_name',
            'stop_desc',
            'stop_lat',
            'stop_lon',
            'zone_id',
            'stop_url',
            'location_type',
            'parent_station',
            'stop_timezone',
            'wheelchair_boarding',
            'level_id',
            'platform_code',
            'stop_access'
        ])
    
        writer_relations = csv.writer(f_relations)
        writer_relations.writerow([
            'osm_stop_position_id',
            'osm_stop_area_group_id',
            'osm_stop_area_id',
            'osm_station_id',
            'osm_entrance_ids',
            'station_id',
            'device_location',
            'fare_location',
            'name_cn',
            'stop_code',
            'amap_id',
            'amap_name',
            'adcode',
        ])
        note_osm_stop_position_id = set()
        note_osm_station_id = set()
        note_osm_entrance_id = set()
        for route_id in tqdm(ROUTE_ID2OSM_ROUTE_ID, desc='Processing routes'):
            for direction_id, osm_route_id in enumerate(ROUTE_ID2OSM_ROUTE_ID[route_id]):
                members = osm_route['r' + str(osm_route_id)]['members']
                for member in members:
                    if member['role'] == 'stop':
                        osm_stop_position_id = member['type'] + str(member['ref'])
                        osm_stop_position_info = osm_stop_position.get(str(osm_stop_position_id), {})
                        osm_stop_area_id = arc_stop_area.get(str(osm_stop_position_id), None)
                        osm_stop_area_info = osm_stop_area.get(str(osm_stop_area_id), {})
                        osm_entrance_ids = [x['type'] + str(x['ref']) for x in osm_stop_area_info.get('members', []) if x['type'] + str(x['ref']) in osm_entrance]
                        osm_station_id = osm_stop_area2station.get(str(osm_stop_area_id), None)
                        osm_station_info = osm_station.get(str(osm_station_id), {})
                        osm_station_name = osm_station_info.get('tags', {}).get('name', None)
                        if osm_station_name:
                            osm_station_name = osm_station_name.replace('首都机场', '')
                            
                        ruubypay_station_id = ruubypay_station_name2station_id.get(osm_station_name, None)
                        ruubypay_device_location = ruubypay_station_id2device_location.get(ruubypay_station_id, None)
                        ruubypay_fare_location = ruubypay_station_id2fare_location.get(ruubypay_station_id, None)
                        writer_relations.writerow([
                            osm_stop_position_id,
                            'osm_stop_area_group_id',
                            osm_stop_area_id,
                            osm_station_id,
                            ','.join(osm_entrance_ids),
                            ruubypay_station_id,
                            ruubypay_device_location,
                            ruubypay_fare_location,
                            osm_station_name,
                            tool.device_location2station_id(ruubypay_device_location),
                            'amap_id',
                            'amap_name',
                            'adcode',
                        ])
                        
                        if osm_stop_position_id not in note_osm_stop_position_id:
                            if 'lat' in osm_stop_position_info and 'lon' in osm_stop_position_info:
                                center_lon, center_lat = osm_stop_position_info['lon'], osm_stop_position_info['lat']
                            else:
                                center_lon, center_lat = None, None
                            osm_station_name = osm_station_name or ''
                            if route_id in ['02', '10']:
                                stop_position_name = osm_station_name + {0: '(外环)', 1: '(内环)'}[direction_id]
                            elif route_id in ['ca']:
                                stop_position_name = osm_station_name
                            else:
                                stop_position_name = osm_station_name + {0: '(上行)', 1: '(下行)'}[direction_id]
                            writer_stops.writerow([
                                osm_stop_position_id, 
                                tool.device_location2station_id(ruubypay_device_location),
                                stop_position_name,
                                osm_station_name,
                                '',
                                center_lat,
                                center_lon,
                                '',
                                '',
                                0,
                                osm_station_id,
                                '',
                                '',
                                '',
                                '',
                                ''
                            ])
                            note_osm_stop_position_id.add(osm_stop_position_id)
                        if osm_station_id and osm_station_id not in note_osm_station_id:
                            if 'lat' in osm_station_info and 'lon' in osm_station_info:
                                center_lon, center_lat = osm_station_info['lon'], osm_station_info['lat']
                            elif 'nodes' in osm_station_info:
                                locations = []
                                for node_id in osm_station_info['nodes']:
                                    if 'n' + str(node_id) in osm_node:
                                        node_info = osm_node.get('n' + str(node_id), {})
                                        if 'lat' in node_info and 'lon' in node_info:
                                            locations.append((node_info['lon'], node_info['lat']))
                                center_lon, center_lat = tool.compute_center_location(locations)
                            else:
                                center_lon, center_lat = None, None
                            writer_stops.writerow([
                                osm_station_id, 
                                tool.device_location2station_id(ruubypay_device_location),
                                osm_station_name,
                                osm_station_name,
                                '',
                                center_lat,
                                center_lon,
                                '',
                                '',
                                1,
                                '',
                                '',
                                '',
                                '',
                                '',
                                ''
                            ])
                            note_osm_station_id.add(osm_station_id)
                        for osm_entrance_id in osm_entrance_ids:
                            if osm_entrance_id not in note_osm_entrance_id:
                                osm_entrance_info = osm_entrance.get(osm_entrance_id, {})
                                if 'lat' in osm_entrance_info and 'lon' in osm_entrance_info:
                                    center_lon, center_lat = osm_entrance_info['lon'], osm_entrance_info['lat']
                                else:
                                    center_lon, center_lat = None, None
                                entrance_info = osm_entrance.get(osm_entrance_id, {})
                                if entrance_info.get('tags', {}).get('ref'):
                                    entrance_code = entrance_info["tags"]["ref"]
                                elif entrance_info.get('tags', {}).get('name'):
                                    entrance_code = re.findall(r'([a-z,A-Z][0-9]*)', entrance_info["tags"]["name"])
                                    entrance_code = entrance_code[0] if entrance_code else ''
                                else:
                                    entrance_code = ''
                                writer_stops.writerow([
                                    osm_entrance_id, 
                                    tool.device_location2station_id(ruubypay_device_location),
                                    f'{osm_station_name}{entrance_code}出口',
                                    f'{osm_station_name}{entrance_code}出口',
                                    '',
                                    entrance_info.get('lat', ''),
                                    entrance_info.get('lon', ''),
                                    '',
                                    '',
                                    2,
                                    osm_station_id,
                                    '',
                                    '',
                                    '',
                                    '',
                                    ''
                                ])
                                note_osm_entrance_id.add(osm_entrance_id)