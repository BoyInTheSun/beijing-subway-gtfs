import json
import os
import csv
import re
from tqdm import tqdm

from tools import tool

DATA_DIR = 'data'
GTFS_DIR = 'gtfs'

def parse_timetable():
    for timetable_json in tqdm(os.listdir(os.path.join(DATA_DIR, 'ruubypay', 'timetable'))):
        if not timetable_json.endswith('.json'): 
            continue
        device_location = timetable_json[:-5]
        line_id = tool.ruubypay_device_location2line_id.get(int(device_location))
        with open(os.path.join(DATA_DIR, 'ruubypay', 'timetable', timetable_json), 'r', encoding='utf-8') as f:
            timetable_data = json.load(f)[0]
            if not timetable_data.get('locations'): 
                continue
            for item_location in timetable_data.get('locations', []):
                direct_device_location = item_location.get('directDeviceLocation')
                for item_direction in item_location.get('direction', []):
                    is_week_day = item_direction.get('isWeekDay')
                    target_dir = os.path.join(DATA_DIR, 'interim', 'timetable', str(is_week_day), str(line_id), str(direct_device_location))
                    os.makedirs(target_dir, exist_ok=True)
                    with open(os.path.join(target_dir, f'{device_location}.csv'), 'w', encoding='utf-8', newline='') as f_out:
                        writer = csv.writer(f_out)
                        writer.writerow([
                            'isHalf', 
                            'startDeviceLocation', 
                            'destDeviceLocation', 
                            'arriveTime', 
                        ])
                        for item_timetable in item_direction.get('timetables', []):
                            writer.writerow([
                                item_timetable.get('isHalf'), 
                                item_timetable.get('startDeviceLocation'), 
                                item_timetable.get('destDeviceLocation'), 
                                item_timetable.get('arriveTime') % (24 * 3600), 
                            ])

def compute_timetable():
    for direction_id in ['0', '1']:
        pass


if __name__ == '__main__':
    parse_timetable()
