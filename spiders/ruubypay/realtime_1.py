import os
import time
import datetime
import json

import spider

SLEEP_SECONDS = 5 * 60

def main():
    device_location = '150995457'
    realtime_path = os.path.join('data', 'realtime', device_location)
    if not os.path.isdir(realtime_path):
        os.makedirs(realtime_path, exist_ok=True)
    while True:
        data = spider.get_data('getRealtimeStationInfo', device_location)
        print(data)
        time_now = time.time()
        with open(os.path.join(realtime_path, str(int(time_now)) + '.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print('下次', datetime.datetime.fromtimestamp(time_now + SLEEP_SECONDS))
        time.sleep(SLEEP_SECONDS)


if __name__ == '__main__':
    main()
            