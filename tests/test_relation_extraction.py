import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from relation_extraction import RelationExtractor
from graph_models import Node, Edge, Graph

class TestRelationExtractor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.extractor = RelationExtractor()
        self.test_text = "Albert Einstein was a German-born theoretical physicist who developed the theory of relativity."
        
    def test_extract_entities(self):
        """Test entity extraction functionality."""
        entities = self.extractor.extract_entities(self.test_text)
        
        # Verify that key entities are extracted
        self.assertIn("Albert Einstein", [e.name for e in entities])
        self.assertIn("physicist", [e.type for e in entities])
        
        # Verify entity attributes
        einstein = next(e for e in entities if e.name == "Albert Einstein")
        self.assertEqual(einstein.type, "PERSON")
        
    def test_extract_relations(self):
        """Test relation extraction between entities."""
        relations = self.extractor.extract_relations(self.test_text)
        
        # Verify that key relations are extracted
        self.assertTrue(any(r for r in relations if r.source.name == "Albert Einstein" 
                          and r.target.name == "theory of relativity" 
                          and r.type == "developed"))
                          
    def test_build_graph(self):
        """Test graph construction from extracted information."""
        graph = self.extractor.build_graph(self.test_text)
        
        # Verify graph structure
        self.assertIsInstance(graph, Graph)
        self.assertTrue(any(n for n in graph.nodes if n.name == "Albert Einstein"))
        self.assertTrue(any(e for e in graph.edges if e.type == "developed"))
        
    @patch('relation_extraction.RelationExtractor._preprocess_text')
    def test_preprocessing(self, mock_preprocess):
        """Test text preprocessing with mocked function."""
        mock_preprocess.return_value = "processed text"
        result = self.extractor._preprocess_text(self.test_text)
        self.assertEqual(result, "processed text")
        mock_preprocess.assert_called_once_with(self.test_text)
        
    def test_invalid_input(self):
        """Test handling of invalid input."""
        with self.assertRaises(ValueError):
            self.extractor.extract_entities("")
        with self.assertRaises(TypeError):
            self.extractor.extract_entities(None)
            
    def test_batch_processing(self):
        """Test batch processing of multiple texts."""
        texts = [
            "Albert Einstein developed relativity.",
            "Isaac Newton discovered gravity."
        ]
        graphs = self.extractor.process_batch(texts)
        
        self.assertEqual(len(graphs), 2)
        self.assertTrue(all(isinstance(g, Graph) for g in graphs))
        
    def test_confidence_scores(self):
        """Test confidence scores for extracted relations."""
        relations = self.extractor.extract_relations(self.test_text, include_scores=True)
        
        for relation in relations:
            self.assertIsInstance(relation.confidence, float)
            self.assertTrue(0 <= relation.confidence <= 1)
            
    def test_entity_disambiguation(self):
        """Test entity disambiguation functionality."""
        text = "Paris is the capital of France. Paris Hilton is a celebrity."
        entities = self.extractor.extract_entities(text)
        
        paris_entities = [e for e in entities if "Paris" in e.name]
        self.assertTrue(len(paris_entities) >= 2)
        self.assertNotEqual(paris_entities[0].type, paris_entities[1].type)
        
    def test_relation_validation(self):
        """Test validation of extracted relations."""
        invalid_text = "This text contains no valid relations."
        relations = self.extractor.extract_relations(invalid_text)
        
        self.assertEqual(len(relations), 0)
        
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        with patch('relation_extraction.PerformanceMonitor') as mock_monitor:
            mock_monitor.return_value.measure.return_value = {'time': 1.0, 'memory': 100}
            
            self.extractor.extract_entities(self.test_text)
            mock_monitor.return_value.measure.assert_called()
            
    def tearDown(self):
        """Clean up after each test method."""
        self.extractor = None

if __name__ == '__main__':
    unittest.main()
