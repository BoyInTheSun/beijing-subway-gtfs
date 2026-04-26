import os
import json
import datetime

DATE_WEEKDAY = datetime.datetime(year=2026, month=1, day=15)
DATE_WEEKEND = datetime.datetime(year=2026, month=1, day=17)

if __name__ == '__main__':

    device_location = '150995457'
    json_names = os.listdir(os.path.join('realtime', device_location))
    result = {}  # 
    for json_name in json_names:
        this_datetime = datetime.datetime.fromtimestamp(int(json_name[:-5]))
        for target_date, is_weekday in ((DATE_WEEKEND, False), (DATE_WEEKDAY, True)):
            if not (target_date + datetime.timedelta(hours=3)) <= this_datetime < (target_date + datetime.timedelta(days=1, hours=3)):
                continue
            with open(os.path.join('realtime', device_location, json_name)) as f:
                data = json.load(f)
            for each in data[0]['metroInfo']:
                directDeviceLocation = each['directDeviceLocation']
                if directDeviceLocation not in result:
                    result[directDeviceLocation] = {}
                print(each)
                if is_weekday not in result[directDeviceLocation]:
                    result[directDeviceLocation][is_weekday] = set()
                result[directDeviceLocation][is_weekday] |= {x['arriveTime'] for x in each['nextTrains']}

    print(result)

    output = {
        "deviceLocation": device_location,
        "locations": [
            {
                "directDeviceLocation": "",
                "direction": [
                    {
                        "isWeekDay": 0,
                        "timetables": []
                    },
                    {
                        "isWeekDay": 0,
                        "timetables": []
                    }
                ]
            },
            {
                "directDeviceLocation": "",
                "direction": [
                    {
                        "isWeekDay": 0,
                        "timetables": []
                    },
                    {
                        "isWeekDay": 0,
                        "timetables": []
                    }
                ]
            }
        ]
    }

    for i, directDeviceLocation in enumerate(result):
        output['locations'][i]['directDeviceLocation'] = directDeviceLocation
        for j, is_weekday in enumerate(result[directDeviceLocation]):
            output['locations'][i]['direction'][j]['isWeekDay'] = 1 if is_weekday else 0
            arriveTime_sorted = sorted(list(result[directDeviceLocation][is_weekday]))
            output['locations'][i]['direction'][j]['timetables'] = [
                {
                    "isHalf": 0,
                    "startDeviceLocation": "150995457",
                    "destDeviceLocation": "150995457",
                    "arriveTime": x
                }
                for x in arriveTime_sorted
            ]
    with open(device_location + '.json', 'w') as f:
        json.dump([output], f)
            