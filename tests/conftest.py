import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from relation_extraction import RelationExtractor
from query_engine import QueryEngine
from query_optimizer import QueryOptimizer
from graph_visualization import GraphVisualizer
from graph_analysis import GraphAnalyzer
from performance_monitor import PerformanceMonitor
from cache_manager import CacheManager
from graph_models import Node, Edge, Graph

@pytest.fixture(scope="session")
def test_data():
    """Provide test data for all tests."""
    return {
        "texts": [
            "Albert Einstein developed the theory of relativity.",
            "Isaac Newton discovered the law of gravity.",
            "Marie Curie conducted pioneering research on radioactivity."
        ],
        "queries": [
            "MATCH (p:PERSON) RETURN p",
            "MATCH (p:PERSON)-[r]->(t) RETURN p, r, t",
            "MATCH (p)-[r*1..2]->(t) RETURN p, r, t"
        ]
    }

@pytest.fixture(scope="session")
def sample_graph():
    """Provide a sample graph for testing."""
    graph = Graph()
    
    # Create nodes
    einstein = Node("Albert Einstein", "PERSON")
    relativity = Node("Theory of Relativity", "THEORY")
    physics = Node("Physics", "FIELD")
    
    graph.add_node(einstein)
    graph.add_node(relativity)
    graph.add_node(physics)
    
    # Create edges
    graph.add_edge(Edge(einstein, relativity, "developed"))
    graph.add_edge(Edge(einstein, physics, "contributed_to"))
    
    return graph

@pytest.fixture(scope="function")
def extractor():
    """Provide a fresh RelationExtractor instance."""
    return RelationExtractor()

@pytest.fixture(scope="function")
def query_engine():
    """Provide a fresh QueryEngine instance."""
    optimizer = QueryOptimizer()
    return QueryEngine(optimizer=optimizer)

@pytest.fixture(scope="function")
def visualizer():
    """Provide a fresh GraphVisualizer instance."""
    return GraphVisualizer()

@pytest.fixture(scope="function")
def analyzer():
    """Provide a fresh GraphAnalyzer instance."""
    return GraphAnalyzer()

@pytest.fixture(scope="session")
def performance_monitor():
    """Provide a PerformanceMonitor instance."""
    return PerformanceMonitor()

@pytest.fixture(scope="function")
def cache_manager():
    """Provide a fresh CacheManager instance."""
    cache = CacheManager()
    yield cache
    cache.clear()  # Cleanup after each test

@pytest.fixture(scope="function")
def mock_graph():
    """Provide a mock graph for testing."""
    def create_mock_graph(size=100):
        graph = Graph()
        
        # Create nodes
        for i in range(size):
            node = Node(f"Node{i}", f"Type{i % 5}")
            graph.add_node(node)
            
        # Create edges (each node connects to next 2 nodes)
        nodes = list(graph.nodes)
        for i in range(size):
            for j in range(1, 3):
                if i + j < size:
                    edge = Edge(nodes[i], nodes[i + j], f"relation{j}")
                    graph.add_edge(edge)
                    
        return graph
        
    return create_mock_graph

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "cache": {
            "enabled": True,
            "max_size": 1000
        },
        "performance": {
            "measure_memory": True,
            "measure_time": True
        },
        "visualization": {
            "default_format": "json",
            "default_layout": "force"
        },
        "query": {
            "timeout": 5000,
            "max_results": 1000
        }
    }

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow to run"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    # Skip slow tests unless --runslow is specified
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
                
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
