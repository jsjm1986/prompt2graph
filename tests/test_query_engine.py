import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_engine import QueryEngine
from query_optimizer import QueryOptimizer
from graph_models import Node, Edge, Graph

class TestQueryEngine(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.optimizer = QueryOptimizer()
        self.engine = QueryEngine(optimizer=self.optimizer)
        
        # Create test graph
        self.graph = Graph()
        
        # Add test nodes
        self.einstein = Node("Albert Einstein", "PERSON")
        self.relativity = Node("Theory of Relativity", "THEORY")
        self.physics = Node("Physics", "FIELD")
        
        self.graph.add_node(self.einstein)
        self.graph.add_node(self.relativity)
        self.graph.add_node(self.physics)
        
        # Add test edges
        self.graph.add_edge(Edge(self.einstein, self.relativity, "developed"))
        self.graph.add_edge(Edge(self.einstein, self.physics, "contributed_to"))
        
        self.engine.load_graph(self.graph)
        
    def test_basic_query(self):
        """Test basic query functionality."""
        query = "MATCH (p:PERSON)-[r:developed]->(t:THEORY) RETURN p, r, t"
        results = self.engine.execute_query(query)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['p'].name, "Albert Einstein")
        self.assertEqual(results[0]['t'].name, "Theory of Relativity")
        
    def test_complex_query(self):
        """Test complex query with multiple patterns."""
        query = """
        MATCH (p:PERSON)-[:developed]->(t:THEORY)
        MATCH (p)-[:contributed_to]->(f:FIELD)
        RETURN p, t, f
        """
        results = self.engine.execute_query(query)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['f'].name, "Physics")
        
    def test_query_optimization(self):
        """Test query optimization."""
        with patch.object(self.optimizer, 'optimize_query') as mock_optimize:
            mock_optimize.return_value = "OPTIMIZED QUERY"
            
            query = "MATCH (n) RETURN n"
            self.engine.execute_query(query)
            
            mock_optimize.assert_called_once_with(query)
            
    def test_query_validation(self):
        """Test query validation."""
        invalid_query = "INVALID QUERY SYNTAX"
        with self.assertRaises(ValueError):
            self.engine.execute_query(invalid_query)
            
    def test_query_parameters(self):
        """Test parameterized queries."""
        query = "MATCH (p:PERSON {name: $name}) RETURN p"
        params = {"name": "Albert Einstein"}
        
        results = self.engine.execute_query(query, params)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['p'].name, "Albert Einstein")
        
    def test_query_cache(self):
        """Test query caching mechanism."""
        query = "MATCH (p:PERSON) RETURN p"
        
        # First execution
        with patch.object(self.engine, '_execute_uncached') as mock_execute:
            mock_execute.return_value = [{"p": self.einstein}]
            results1 = self.engine.execute_query(query)
            mock_execute.assert_called_once()
            
        # Second execution (should use cache)
        with patch.object(self.engine, '_execute_uncached') as mock_execute:
            results2 = self.engine.execute_query(query)
            mock_execute.assert_not_called()
            
        self.assertEqual(results1, results2)
        
    def test_query_pagination(self):
        """Test query result pagination."""
        # Add more test data
        for i in range(10):
            person = Node(f"Person{i}", "PERSON")
            self.graph.add_node(person)
            
        query = "MATCH (p:PERSON) RETURN p"
        page_size = 5
        
        # Test first page
        results1 = self.engine.execute_query(query, page=1, page_size=page_size)
        self.assertEqual(len(results1), page_size)
        
        # Test second page
        results2 = self.engine.execute_query(query, page=2, page_size=page_size)
        self.assertEqual(len(results2), page_size)
        
        # Verify different results
        self.assertNotEqual(results1, results2)
        
    def test_query_timeout(self):
        """Test query timeout mechanism."""
        query = "MATCH (p:PERSON)-[*]->(t) RETURN p, t"  # Complex query
        
        with self.assertRaises(TimeoutError):
            self.engine.execute_query(query, timeout=0.001)  # Very short timeout
            
    def test_query_statistics(self):
        """Test query execution statistics."""
        query = "MATCH (p:PERSON) RETURN p"
        results, stats = self.engine.execute_query(query, include_stats=True)
        
        self.assertIn('execution_time', stats)
        self.assertIn('nodes_scanned', stats)
        self.assertIn('cache_hit', stats)
        
    def test_concurrent_queries(self):
        """Test concurrent query execution."""
        import threading
        
        def execute_query():
            query = "MATCH (p:PERSON) RETURN p"
            results = self.engine.execute_query(query)
            self.assertTrue(len(results) > 0)
            
        threads = [threading.Thread(target=execute_query) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
    def tearDown(self):
        """Clean up after each test method."""
        self.engine = None
        self.graph = None

if __name__ == '__main__':
    unittest.main()
