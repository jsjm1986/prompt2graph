import unittest
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

class TestSystemIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.extractor = RelationExtractor()
        self.optimizer = QueryOptimizer()
        self.engine = QueryEngine(optimizer=self.optimizer)
        self.visualizer = GraphVisualizer()
        self.analyzer = GraphAnalyzer()
        self.monitor = PerformanceMonitor()
        self.cache = CacheManager()
        
        # Test data
        self.test_texts = [
            "Albert Einstein developed the theory of relativity.",
            "Isaac Newton discovered the law of gravity.",
            "Marie Curie conducted pioneering research on radioactivity."
        ]
        
    def test_end_to_end_workflow(self):
        """Test complete workflow from text input to visualization."""
        # 1. Extract relations and build graph
        with self.monitor.measure("extraction"):
            graph = self.extractor.build_graph(self.test_texts[0])
            
        # 2. Query the graph
        self.engine.load_graph(graph)
        query = "MATCH (p:PERSON)-[r]->(t) RETURN p, r, t"
        results = self.engine.execute_query(query)
        
        # Verify results
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]['p'].name, "Albert Einstein")
        
        # 3. Analyze graph
        metrics = self.analyzer.analyze_graph(graph)
        self.assertIn('node_count', metrics)
        self.assertIn('edge_count', metrics)
        
        # 4. Visualize results
        viz_data = self.visualizer.prepare_visualization(graph)
        self.assertIn('nodes', viz_data)
        self.assertIn('edges', viz_data)
        
    def test_batch_processing(self):
        """Test batch processing of multiple texts."""
        # 1. Process multiple texts
        graphs = []
        for text in self.test_texts:
            graph = self.extractor.build_graph(text)
            graphs.append(graph)
            
        # 2. Merge graphs
        merged_graph = graphs[0]
        for g in graphs[1:]:
            merged_graph.merge(g)
            
        # 3. Analyze merged graph
        metrics = self.analyzer.analyze_graph(merged_graph)
        
        # Verify results
        self.assertEqual(metrics['node_count'], len(merged_graph.nodes))
        self.assertTrue(metrics['node_count'] >= 6)  # At least 2 nodes per text
        
    def test_caching_integration(self):
        """Test integration of caching system."""
        # 1. Build and cache graph
        graph = self.extractor.build_graph(self.test_texts[0])
        cache_key = "test_graph"
        self.cache.set(cache_key, graph)
        
        # 2. Retrieve from cache
        cached_graph = self.cache.get(cache_key)
        self.assertEqual(len(graph.nodes), len(cached_graph.nodes))
        
        # 3. Query cached graph
        self.engine.load_graph(cached_graph)
        query = "MATCH (p:PERSON) RETURN p"
        results = self.engine.execute_query(query)
        
        self.assertTrue(len(results) > 0)
        
    def test_performance_monitoring(self):
        """Test performance monitoring across components."""
        with self.monitor.measure("full_workflow") as workflow_metrics:
            # 1. Extract relations
            with self.monitor.measure("extraction"):
                graph = self.extractor.build_graph(self.test_texts[0])
                
            # 2. Query processing
            with self.monitor.measure("querying"):
                self.engine.load_graph(graph)
                query = "MATCH (p:PERSON) RETURN p"
                results = self.engine.execute_query(query)
                
            # 3. Analysis
            with self.monitor.measure("analysis"):
                metrics = self.analyzer.analyze_graph(graph)
                
        # Verify metrics
        self.assertIn('extraction', workflow_metrics)
        self.assertIn('querying', workflow_metrics)
        self.assertIn('analysis', workflow_metrics)
        
    def test_error_handling(self):
        """Test error handling and recovery across components."""
        # 1. Test invalid text input
        with self.assertRaises(ValueError):
            self.extractor.build_graph("")
            
        # 2. Test invalid query
        graph = self.extractor.build_graph(self.test_texts[0])
        self.engine.load_graph(graph)
        
        with self.assertRaises(ValueError):
            self.engine.execute_query("INVALID QUERY")
            
        # 3. Test recovery - should still be able to execute valid query
        results = self.engine.execute_query("MATCH (n) RETURN n")
        self.assertTrue(len(results) > 0)
        
    def test_visualization_formats(self):
        """Test different visualization formats and exports."""
        graph = self.extractor.build_graph(self.test_texts[0])
        
        # Test different formats
        formats = ['json', 'cytoscape', 'd3']
        for format in formats:
            viz_data = self.visualizer.prepare_visualization(graph, format=format)
            self.assertIsNotNone(viz_data)
            
        # Test layout algorithms
        layouts = ['force', 'circular', 'hierarchical']
        for layout in layouts:
            viz_data = self.visualizer.prepare_visualization(graph, layout=layout)
            self.assertIsNotNone(viz_data)
            
    def tearDown(self):
        """Clean up after each test method."""
        self.cache.clear()
        self.engine = None
        self.extractor = None

if __name__ == '__main__':
    unittest.main()
