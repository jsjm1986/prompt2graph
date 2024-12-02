import pytest
import sys
import os
import time
import random
from typing import Dict, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def sample_graph_data():
    """提供测试用的图数据"""
    entities = [
        {'id': 1, 'name': 'Entity1', 'type': 'Person', 'properties': {'age': 30}},
        {'id': 2, 'name': 'Entity2', 'type': 'Organization', 'properties': {'size': 100}},
        {'id': 3, 'name': 'Entity3', 'type': 'Person', 'properties': {'age': 25}},
        {'id': 4, 'name': 'Entity4', 'type': 'Location', 'properties': {'country': 'China'}},
        {'id': 5, 'name': 'Entity5', 'type': 'Organization', 'properties': {'size': 50}}
    ]
    
    relations = [
        {'source_id': 1, 'target_id': 2, 'relation_type': 'WORKS_FOR', 'confidence': 0.9},
        {'source_id': 2, 'target_id': 4, 'relation_type': 'LOCATED_IN', 'confidence': 0.8},
        {'source_id': 3, 'target_id': 2, 'relation_type': 'WORKS_FOR', 'confidence': 0.95},
        {'source_id': 5, 'target_id': 4, 'relation_type': 'LOCATED_IN', 'confidence': 0.85},
        {'source_id': 1, 'target_id': 3, 'relation_type': 'KNOWS', 'confidence': 0.7}
    ]
    
    return entities, relations

@pytest.fixture(scope="session")
def large_graph_data():
    """提供大规模图测试数据"""
    n_entities = 1000
    n_relations = 5000
    
    entity_types = ['Person', 'Organization', 'Location', 'Event', 'Product']
    relation_types = ['KNOWS', 'WORKS_FOR', 'LOCATED_IN', 'PARTICIPATES_IN', 'PRODUCES']
    
    entities = [
        {
            'id': i,
            'name': f'Entity{i}',
            'type': entity_types[i % len(entity_types)],
            'properties': {'prop': i}
        }
        for i in range(n_entities)
    ]
    
    relations = [
        {
            'source_id': random.randint(0, n_entities-1),
            'target_id': random.randint(0, n_entities-1),
            'relation_type': relation_types[random.randint(0, len(relation_types)-1)],
            'confidence': random.random()
        }
        for _ in range(n_relations)
    ]
    
    return entities, relations

class Timer:
    """性能计时器"""
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.measurements = {}
    
    def start(self, name: str = 'default'):
        """开始计时"""
        self.measurements[name] = {'start': time.time()}
    
    def stop(self, name: str = 'default'):
        """停止计时"""
        if name in self.measurements:
            self.measurements[name]['end'] = time.time()
            self.measurements[name]['duration'] = (
                self.measurements[name]['end'] - 
                self.measurements[name]['start']
            )
    
    def get_duration(self, name: str = 'default') -> float:
        """获取持续时间"""
        if name in self.measurements and 'duration' in self.measurements[name]:
            return self.measurements[name]['duration']
        return None
    
    def clear(self):
        """清除所有计时"""
        self.measurements.clear()

@pytest.fixture(scope="function")
def timer():
    """提供计时器实例"""
    return Timer()

@pytest.fixture(scope="session")
def test_config():
    """提供测试配置"""
    return {
        'min_confidence': 0.5,
        'max_path_length': 3,
        'community_resolution': 1.0,
        'similarity_threshold': 0.7,
        'min_subgraph_size': 3,
        'cache': {
            'enabled': True,
            'max_size': 1000,
            'ttl': 3600
        },
        'performance': {
            'parallel_threshold': 1000,
            'batch_size': 100,
            'timeout': 30
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }

@pytest.fixture(scope="session")
def benchmark_config():
    """提供基准测试配置"""
    return {
        'iterations': 5,
        'warmup': 1,
        'timeout': 60,
        'metrics': ['mean', 'std', 'min', 'max'],
        'sizes': [100, 1000, 10000]
    }
