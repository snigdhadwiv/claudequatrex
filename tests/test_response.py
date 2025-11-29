"""Tests for response generation module"""

import pytest
from src.response import ResponseGenerator


class TestResponseGenerator:
    """Test ResponseGenerator class"""
    
    def test_initialization(self):
        """Test generator initialization"""
        generator = ResponseGenerator(mode="hybrid")
        assert generator.mode == "hybrid"
        assert generator.enable_cache is True
    
    def test_generate_template_response(self):
        """Test template-based generation"""
        generator = ResponseGenerator(mode="template")
        
        response = generator.generate(intent="greeting")
        
        assert response.text != ""
        assert response.intent == "greeting"
        assert response.source == "template"
    
    def test_generate_with_entities(self):
        """Test generation with entities"""
        generator = ResponseGenerator()
        
        response = generator.generate(
            intent="greeting",
            entities={"name": "John"}
        )
        
        assert response.text != ""
    
    def test_cache(self):
        """Test response caching"""
        generator = ResponseGenerator(enable_cache=True)
        
        # Generate twice with same intent
        response1 = generator.generate(intent="greeting")
        response2 = generator.generate(intent="greeting")
        
        assert generator.stats["cache_hits"] > 0
    
    def test_add_template(self):
        """Test adding custom template"""
        generator = ResponseGenerator()
        
        generator.add_template(
            category="custom",
            intent="test_intent",
            templates=["Custom response"]
        )
        
        assert "custom" in generator.templates
        assert "test_intent" in generator.templates["custom"]
    
    def test_clear_cache(self):
        """Test cache clearing"""
        generator = ResponseGenerator(enable_cache=True)
        
        # Generate some responses
        generator.generate(intent="greeting")
        generator.generate(intent="goodbye")
        
        # Clear cache
        generator.clear_cache()
        
        assert len(generator.cache) == 0
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        generator = ResponseGenerator()
        
        # Generate some responses
        generator.generate(intent="greeting")
        generator.generate(intent="greeting")
        
        stats = generator.get_stats()
        
        assert "total_generated" in stats
        assert stats["total_generated"] == 2


if __name__ == "__main__":
    pytest.main([__file__])
