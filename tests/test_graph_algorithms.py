import pytest
import networkx as nx
from graph_algorithms import KnowledgeGraphAlgorithms

@pytest.fixture
def sample_graph_data():
    """创建测试用的图数据"""
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

def test_graph_initialization(sample_graph_data):
    """测试图初始化"""
    entities, relations = sample_graph_data
    kg = KnowledgeGraphAlgorithms(entities, relations)
    
    assert isinstance(kg.graph, nx.DiGraph)
    assert len(kg.graph.nodes()) == len(entities)
    assert len(kg.graph.edges()) == len(relations)
    
    # 检查节点属性
    for entity in entities:
        node = kg.graph.nodes[entity['id']]
        assert node['name'] == entity['name']
        assert node['type'] == entity['type']
        
    # 检查边属性
    for relation in relations:
        edge = kg.graph.edges[relation['source_id'], relation['target_id']]
        assert edge['type'] == relation['relation_type']
        assert edge['weight'] == relation['confidence']

def test_centrality_metrics(sample_graph_data):
    """测试中心性指标计算"""
    entities, relations = sample_graph_data
    kg = KnowledgeGraphAlgorithms(entities, relations)
    metrics = kg.calculate_centrality_metrics()
    
    assert len(metrics) == len(entities)
    for node_id in metrics:
        assert 'degree' in metrics[node_id]
        assert 'betweenness' in metrics[node_id]
        assert 'closeness' in metrics[node_id]
        assert 'eigenvector' in metrics[node_id]
        
        # 检查指标值是否在合理范围内
        assert 0 <= metrics[node_id]['degree'] <= 1
        assert 0 <= metrics[node_id]['betweenness'] <= 1
        assert 0 <= metrics[node_id]['closeness'] <= 1
        assert 0 <= metrics[node_id]['eigenvector'] <= 1

def test_community_detection(sample_graph_data):
    """测试社区检测"""
    entities, relations = sample_graph_data
    kg = KnowledgeGraphAlgorithms(entities, relations)
    communities = kg.detect_communities()
    
    assert len(communities) == len(entities)
    for node_id in communities:
        assert isinstance(communities[node_id], int)
        assert communities[node_id] >= 0

def test_shortest_path(sample_graph_data):
    """测试最短路径查找"""
    entities, relations = sample_graph_data
    kg = KnowledgeGraphAlgorithms(entities, relations)
    
    # 测试存在的路径
    path = kg.find_shortest_path(1, 4)
    assert path is not None
    assert path[0] == 1
    assert path[-1] == 4
    
    # 测试不存在的路径
    non_existent_path = kg.find_shortest_path(4, 1)
    assert non_existent_path is None

def test_semantic_similarity(sample_graph_data):
    """测试语义相似度计算"""
    entities, relations = sample_graph_data
    kg = KnowledgeGraphAlgorithms(entities, relations)
    
    # 测试相同类型实体的相似度
    similarity = kg.calculate_semantic_similarity(1, 3)
    assert 0 <= similarity <= 1
    
    # 测试不同类型实体的相似度
    similarity = kg.calculate_semantic_similarity(1, 2)
    assert 0 <= similarity <= 1

def test_important_subgraphs(sample_graph_data):
    """测试重要子图识别"""
    entities, relations = sample_graph_data
    kg = KnowledgeGraphAlgorithms(entities, relations)
    subgraphs = kg.find_important_subgraphs(min_size=2)
    
    assert isinstance(subgraphs, list)
    for sg in subgraphs:
        assert len(sg) >= 2
        assert isinstance(sg, set)

def test_relation_recommendations(sample_graph_data):
    """测试关系推荐"""
    entities, relations = sample_graph_data
    kg = KnowledgeGraphAlgorithms(entities, relations)
    recommendations = kg.recommend_relations(threshold=0.3)
    
    assert isinstance(recommendations, list)
    for rec in recommendations:
        assert len(rec) == 3
        source_id, target_id, score = rec
        assert isinstance(source_id, int)
        assert isinstance(target_id, int)
        assert 0 <= score <= 1
        # 确保推荐的关系不存在于原图中
        assert not kg.graph.has_edge(source_id, target_id)

def test_relation_patterns(sample_graph_data):
    """测试关系模式分析"""
    entities, relations = sample_graph_data
    kg = KnowledgeGraphAlgorithms(entities, relations)
    patterns = kg.analyze_relation_patterns()
    
    assert isinstance(patterns, dict)
    for relation_type, type_patterns in patterns.items():
        assert isinstance(type_patterns, list)
        for pattern in type_patterns:
            assert len(pattern) == 2
            source_type, target_type = pattern
            assert isinstance(source_type, str)
            assert isinstance(target_type, str)

def test_graph_metrics(sample_graph_data):
    """测试图整体指标计算"""
    entities, relations = sample_graph_data
    kg = KnowledgeGraphAlgorithms(entities, relations)
    metrics = kg.calculate_graph_metrics()
    
    assert isinstance(metrics, dict)
    assert 'density' in metrics
    assert 'average_clustering' in metrics
    assert 'reciprocity' in metrics
    assert 'number_of_nodes' in metrics
    assert 'number_of_edges' in metrics
    
    assert 0 <= metrics['density'] <= 1
    assert 0 <= metrics['average_clustering'] <= 1
    assert 0 <= metrics['reciprocity'] <= 1
    assert metrics['number_of_nodes'] == len(entities)
    assert metrics['number_of_edges'] == len(relations)

@pytest.mark.benchmark
def test_performance_large_graph(benchmark):
    """测试大规模图的性能"""
    # 创建一个较大的随机图
    n_entities = 1000
    n_relations = 5000
    
    entities = [
        {'id': i, 'name': f'Entity{i}', 'type': ['Person', 'Organization', 'Location'][i % 3],
         'properties': {'prop': i}}
        for i in range(n_entities)
    ]
    
    import random
    relations = [
        {'source_id': random.randint(0, n_entities-1),
         'target_id': random.randint(0, n_entities-1),
         'relation_type': ['KNOWS', 'WORKS_FOR', 'LOCATED_IN'][random.randint(0, 2)],
         'confidence': random.random()}
        for _ in range(n_relations)
    ]
    
    def run_analysis():
        kg = KnowledgeGraphAlgorithms(entities, relations)
        kg.calculate_centrality_metrics()
        kg.detect_communities()
        kg.calculate_graph_metrics()
    
    # 使用pytest-benchmark测量性能
    benchmark(run_analysis)

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--benchmark-only'])
