import json
import os
from tqdm import tqdm
from typing import Dict, List, Optional, Tuple

import osmium

BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
# OSM_PBF = os.path.join(BASE_DIR, 'hebei-260420.osm.pbf')  # https://download.geofabrik.de/asia/china/hebei.html
OSM_PBF = 'D:\\hebei-260421.osm.pbf'  # 禁止中文路径
OUTPUT_DIR = os.path.join(ROOT_DIR, 'data', 'osm')


def tags_to_dict(tags) -> Dict[str, str]:
    return {tag.k: tag.v for tag in tags}

def count_objects(file_path):
    class CounterHandler(osmium.SimpleHandler):
        def __init__(self):
            super().__init__()
            self.nodes = 0
            self.ways = 0
            self.relations = 0
        
        def node(self, n): self.nodes += 1
        def way(self, w): self.ways += 1
        def relation(self, r): self.relations += 1

    c = CounterHandler()
    c.apply_file(file_path, locations=False) 
    return c.nodes, c.ways, c.relations

class StopHandler(osmium.SimpleHandler):
    def __init__(self, n_total, w_total, r_total):
        super().__init__()
        self.data: Dict[str, Dict[str, Dict]] = {}
        self.n_total = n_total
        self.w_total = w_total
        self.r_total = r_total
        self.pbar_n = tqdm(total=n_total, desc="Nodes....", unit='个')
        self.pbar_w = tqdm(total=w_total, desc="Ways.....", unit='个')
        self.pbar_r = tqdm(total=r_total, desc="Relations", unit='个')
        self.n_ids = set()
        
    def relation(self, relation):
        self.pbar_r.update(1)
        tags = tags_to_dict(relation.tags) 
        if tags.get('public_transport') == 'stop_area':
            data_type = 'stop_area'
        elif tags.get('public_transport') == 'stop_area_group':
            data_type = 'stop_area_group'
        elif tags.get('route') in ['light_rail', 'tram', 'subway', 'monorail']:
            data_type = 'route'
        elif tags.get('route_master') in ['light_rail', 'tram', 'subway', 'monorail']:
            data_type = 'route_master'
        else:
            return
        if not data_type in self.data:
            self.data[data_type] = {}
        self.data[data_type]['r' + str(relation.id)] = {
            'type': 'r',
            'tags': tags,
            'members': [{'type': member.type, 'ref': member.ref, 'role': member.role} for member in relation.members],
        }
            
    def node(self, node):
        self.pbar_n.update(1)
        tags = tags_to_dict(node.tags)
        if tags.get('public_transport') == 'station' or tags.get('railway') == 'station':
            data_type = 'station'
        elif tags.get('public_transport') == 'stop_position' or tags.get('railway') in ['stop', 'tram_stop']:
            data_type = 'stop_position'
        elif tags.get('railway') == 'subway_entrance':
            data_type = 'entrance'
        else:
            return
        if not data_type in self.data:
            self.data[data_type] = {}
        self.data[data_type]['n' + str(node.id)] = {
            'tags': tags,
            'lon': node.location.lon if node.location else None,
            'lat': node.location.lat if node.location else None,
        }

    def way(self, way):
        self.pbar_w.update(1)
        tags = tags_to_dict(way.tags)
        if tags.get('public_transport') == 'platform' or tags.get('railway') == 'platform':
            data_type = 'platform'
        if tags.get('public_transport') == 'station' or tags.get('railway') == 'station':
            data_type = 'station'
        else:
            return
        if not data_type in self.data:
            self.data[data_type] = {}
        self.data[data_type]['w' + str(way.id)] = {
            'type': 'w',
            'tags': tags,
            'nodes': [node.ref for node in way.nodes],
        }
        self.n_ids.update(node.ref for node in way.nodes)
        
    def __del__(self):
        self.pbar_n.close()
        self.pbar_w.close()
        self.pbar_r.close()

class PathHandler(osmium.SimpleHandler):
    def __init__(self, n_total, n_ids):
        super().__init__()
        self.data: Dict[str, Dict[str, Dict]] = {}
        self.n_total = n_total
        self.pbar_n = tqdm(total=n_total, desc="Nodes....", unit='个')
        self.n_ids = n_ids
        
    def node(self, node):
        self.pbar_n.update(1)
        if node.id in self.n_ids:
            self.data['n' + str(node.id)] = {
                'lon': node.location.lon if node.location else None,
                'lat': node.location.lat if node.location else None,
            }
            
    def __del__(self):
        self.pbar_n.close()
        
if __name__ == '__main__':
    if not os.path.exists(OSM_PBF):
        raise FileNotFoundError(f'未找到 OSM 数据文件: {OSM_PBF}')

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # n_count, w_count, r_count = count_objects(OSM_PBF)
    n_count, w_count, r_count = 14482155, 1505944, 28529
    

    stop_handler = StopHandler(n_count, w_count, r_count)
    stop_handler.apply_file(OSM_PBF, locations=True)
    stop_handler.__del__()

    data = stop_handler.data
    n_ids = stop_handler.n_ids
    for data_type in data:
        with open(os.path.join(OUTPUT_DIR, f'{data_type}.json'), 'w', encoding='utf-8') as f:
            json.dump(data[data_type], f, ensure_ascii=False, indent=2)
    
    path_handler = PathHandler(n_count, n_ids)
    path_handler.apply_file(OSM_PBF, locations=True)
    path_handler.__del__()
    with open(os.path.join(OUTPUT_DIR, 'node.json'), 'w', encoding='utf-8') as f:
        json.dump(path_handler.data, f, ensure_ascii=False, indent=2)
    


    
