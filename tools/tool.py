import json
import os

DATA_DIR = 'data'

acclocation = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'acclocation.json'), encoding='utf-8'))    
map_h5 = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'map-h5.json'), encoding='utf-8'))
excess_fare_ticket_station_select = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'excessFareTicketStationSelect.json'), encoding='utf-8'))
fare_region_mapping = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'fareRegionMapping.json'), encoding='utf-8'))
pis_station_select = json.load(open(os.path.join(DATA_DIR, 'ruubypay', 'pisStationSelect.json'), encoding='utf-8'))

def device_location2station_id(device_location):
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