import json
import os
import csv
import re
from turtle import pd
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
        if line_id is None:
            continue
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
                                (item_timetable.get('arriveTime') + (8 - 3) * 3600) % (24 * 3600) + 3 * 3600,  # 北京+8时区，0-3点视为前一天
                            ])

def compute_interstation_time():
    '''
    使用第一趟全程车计算站间时间。
    '''
    for is_week_day in ['0', '1']:
        timetable_root = os.path.join(DATA_DIR, 'interim', 'timetable', is_week_day)
        output_root = os.path.join(DATA_DIR, 'interim', 'interstation_time', is_week_day)
        os.makedirs(output_root, exist_ok=True)

        for line_id in tqdm(os.listdir(timetable_root)):
            line_dir = os.path.join(timetable_root, line_id)
            rows_to_write = []

            for direct_device_location in os.listdir(line_dir):
                direction_dir = os.path.join(line_dir, direct_device_location)
                station_first_full = {}
                route_key_count = {}

                for device_location_csv in os.listdir(direction_dir):
                    if not device_location_csv.endswith('.csv'):
                        continue

                    device_location = device_location_csv[:-4]
                    station_file = os.path.join(direction_dir, device_location_csv)
                    with open(station_file, 'r', encoding='utf-8') as fr:
                        reader = csv.DictReader(fr)
                        full_rows = []
                        for row in reader:
                            if row.get('isHalf') == '1':
                                continue
                            if not row.get('arriveTime'):
                                continue
                            full_rows.append(row)

                    if not full_rows:
                        continue

                    full_rows.sort(key=lambda x: int(x['arriveTime']))
                    station_first_full[device_location] = full_rows

                    first_row = full_rows[0]
                    route_key = (first_row.get('startDeviceLocation'), first_row.get('destDeviceLocation'))
                    route_key_count[route_key] = route_key_count.get(route_key, 0) + 1

                if not station_first_full:
                    continue

                selected_route_key = max(route_key_count.items(), key=lambda item: item[1])[0]

                station_arrivals = {}
                for device_location, rows in station_first_full.items():
                    selected_row = None
                    for row in rows:
                        if (row.get('startDeviceLocation'), row.get('destDeviceLocation')) == selected_route_key:
                            selected_row = row
                            break
                    if selected_row is None:
                        continue
                    station_arrivals[device_location] = int(selected_row['arriveTime'])

                if len(station_arrivals) < 2:
                    continue

                canonical_order = [
                    str(device_location)
                    for device_location in tool.line_station.get(int(line_id), [])
                    if device_location is not None
                ]

                if canonical_order:
                    start_device_location = selected_route_key[0]
                    dest_device_location = selected_route_key[1]
                    ordered_stations = canonical_order

                    if start_device_location in canonical_order and dest_device_location in canonical_order:
                        if canonical_order.index(start_device_location) > canonical_order.index(dest_device_location):
                            ordered_stations = list(reversed(canonical_order))
                    elif start_device_location in canonical_order and dest_device_location not in canonical_order:
                        if start_device_location == canonical_order[-1]:
                            ordered_stations = list(reversed(canonical_order))
                    elif dest_device_location in canonical_order and start_device_location not in canonical_order:
                        if dest_device_location == canonical_order[0]:
                            ordered_stations = list(reversed(canonical_order))
                else:
                    ordered_stations = sorted(station_arrivals, key=lambda station: station_arrivals[station])

                for index in range(1, len(ordered_stations)):
                    from_station = ordered_stations[index - 1]
                    to_station = ordered_stations[index]
                    if from_station not in station_arrivals or to_station not in station_arrivals:
                        continue
                    from_time = station_arrivals[from_station]
                    to_time = station_arrivals[to_station]
                    interstation_time = to_time - from_time
                    if interstation_time <= 0:
                        interstation_time += 24 * 3600
                    if interstation_time <= 0:
                        continue
                    rows_to_write.append([from_station, to_station, interstation_time])

            output_file = os.path.join(output_root, line_id + '.csv')
            with open(output_file, 'w', encoding='utf-8', newline='') as fw:
                writer = csv.writer(fw)
                writer.writerow([
                    'fromDeviceLocation',
                    'toDeviceLocation',
                    'interstationTime',
                ])
                writer.writerows(rows_to_write)

def compute_timetable():
    line_station = tool.line_station
    for is_week_day in ['0', '1']:
        for line_id in os.listdir(os.path.join(DATA_DIR, 'interim', 'timetable', is_week_day)):
            line_id = int(line_id)
            route_id = tool.RUUBYPAY_LINE_ID2ROUTE_ID.get(line_id)
            if route_id in ['2', '10', '6']:
                continue
            for device_location in line_station[line_id]:
                print(line_id, device_location)


if __name__ == '__main__':
    # parse_timetable()
    compute_interstation_time()
    # compute_timetable()
