import unittest
import time
import random
import string
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from relation_extraction import RelationExtractor
from query_engine import QueryEngine
from query_optimizer import QueryOptimizer
from graph_visualization import GraphVisualizer
from graph_analysis import GraphAnalyzer
from performance_monitor import PerformanceMonitor
from graph_models import Node, Edge, Graph

class TestPerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before all tests."""
        cls.extractor = RelationExtractor()
        cls.optimizer = QueryOptimizer()
        cls.engine = QueryEngine(optimizer=cls.optimizer)
        cls.visualizer = GraphVisualizer()
        cls.analyzer = GraphAnalyzer()
        cls.monitor = PerformanceMonitor()
        
        # Generate test data
        cls.generate_test_data()
        
    @classmethod
    def generate_test_data(cls):
        """Generate test data of various sizes."""
        cls.test_graphs = {}
        cls.test_texts = {}
        
        sizes = [10, 100, 1000, 10000]  # Number of nodes
        
        for size in sizes:
            # Generate random text
            texts = []
            for _ in range(size // 2):  # Each text generates ~2 nodes
                subject = ''.join(random.choices(string.ascii_letters, k=5))
                predicate = random.choice(['developed', 'discovered', 'created', 'studied'])
                object = ''.join(random.choices(string.ascii_letters, k=5))
                text = f"{subject} {predicate} {object}."
                texts.append(text)
            cls.test_texts[size] = texts
            
            # Generate random graph
            graph = Graph()
            for i in range(size):
                node = Node(f"Node{i}", random.choice(['PERSON', 'CONCEPT', 'THEORY']))
                graph.add_node(node)
            
            # Add random edges
            edge_count = size * 2  # Average degree of 2
            for _ in range(edge_count):
                source = random.choice(list(graph.nodes))
                target = random.choice(list(graph.nodes))
                if source != target:
                    edge = Edge(source, target, random.choice(['related', 'developed', 'studied']))
                    graph.add_edge(edge)
                    
            cls.test_graphs[size] = graph
            
    def test_extraction_performance(self):
        """Test relation extraction performance."""
        results = {}
        
        for size, texts in self.test_texts.items():
            start_time = time.time()
            
            with self.monitor.measure(f"extraction_{size}"):
                graph = self.extractor.build_graph(texts)
                
            duration = time.time() - start_time
            memory_usage = self.monitor.get_memory_usage()
            
            results[size] = {
                'time': duration,
                'memory': memory_usage,
                'nodes_per_second': len(graph.nodes) / duration
            }
            
        # Log results
        self.log_performance_results("Extraction Performance", results)
        
    def test_query_performance(self):
        """Test query performance."""
        results = {}
        
        for size, graph in self.test_graphs.items():
            self.engine.load_graph(graph)
            
            queries = [
                "MATCH (n) RETURN n",  # Simple query
                "MATCH (n)-[r]->(m) RETURN n, r, m",  # Medium complexity
                "MATCH (n)-[r*1..3]->(m) RETURN n, m"  # Complex query
            ]
            
            query_results = {}
            for query in queries:
                start_time = time.time()
                
                with self.monitor.measure(f"query_{size}_{query[:10]}"):
                    results = self.engine.execute_query(query)
                    
                duration = time.time() - start_time
                memory_usage = self.monitor.get_memory_usage()
                
                query_results[query] = {
                    'time': duration,
                    'memory': memory_usage,
                    'results_count': len(results)
                }
                
            results[size] = query_results
            
        # Log results
        self.log_performance_results("Query Performance", results)
        
    def test_analysis_performance(self):
        """Test graph analysis performance."""
        results = {}
        
        for size, graph in self.test_graphs.items():
            analysis_results = {}
            
            # Test different analysis functions
            analyses = [
                ('basic_metrics', lambda: self.analyzer.calculate_basic_metrics(graph)),
                ('centrality', lambda: self.analyzer.calculate_centrality(graph)),
                ('community_detection', lambda: self.analyzer.detect_communities(graph)),
                ('path_analysis', lambda: self.analyzer.analyze_paths(graph))
            ]
            
            for name, func in analyses:
                start_time = time.time()
                
                with self.monitor.measure(f"analysis_{size}_{name}"):
                    func()
                    
                duration = time.time() - start_time
                memory_usage = self.monitor.get_memory_usage()
                
                analysis_results[name] = {
                    'time': duration,
                    'memory': memory_usage
                }
                
            results[size] = analysis_results
            
        # Log results
        self.log_performance_results("Analysis Performance", results)
        
    def test_visualization_performance(self):
        """Test visualization performance."""
        results = {}
        
        for size, graph in self.test_graphs.items():
            viz_results = {}
            
            # Test different visualization formats and layouts
            configs = [
                ('json_force', {'format': 'json', 'layout': 'force'}),
                ('json_circular', {'format': 'json', 'layout': 'circular'}),
                ('cytoscape', {'format': 'cytoscape'}),
                ('d3', {'format': 'd3'})
            ]
            
            for name, config in configs:
                start_time = time.time()
                
                with self.monitor.measure(f"visualization_{size}_{name}"):
                    self.visualizer.prepare_visualization(graph, **config)
                    
                duration = time.time() - start_time
                memory_usage = self.monitor.get_memory_usage()
                
                viz_results[name] = {
                    'time': duration,
                    'memory': memory_usage
                }
                
            results[size] = viz_results
            
        # Log results
        self.log_performance_results("Visualization Performance", results)
        
    def test_memory_leaks(self):
        """Test for memory leaks during extended operation."""
        initial_memory = self.monitor.get_memory_usage()
        
        # Perform multiple operations
        for _ in range(10):
            graph = self.test_graphs[1000]  # Use medium-sized graph
            
            # Sequence of operations
            self.engine.load_graph(graph)
            self.engine.execute_query("MATCH (n) RETURN n")
            self.analyzer.analyze_graph(graph)
            self.visualizer.prepare_visualization(graph)
            
        final_memory = self.monitor.get_memory_usage()
        
        # Check for significant memory increase
        memory_increase = final_memory - initial_memory
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # Less than 100MB increase
        
    @staticmethod
    def log_performance_results(test_name, results):
        """Log performance test results."""
        print(f"\n=== {test_name} ===")
        for size, data in results.items():
            print(f"\nSize: {size}")
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"  {key}: {value}")
                    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.test_graphs.clear()
        cls.test_texts.clear()

if __name__ == '__main__':
    unittest.main()
