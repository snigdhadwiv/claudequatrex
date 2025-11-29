"""Tests for NLP modules"""

import pytest
from src.nlp import IntentClassifier, ContextManager


class TestIntentClassifier:
    """Test IntentClassifier class"""
    
    def test_initialization(self):
        """Test classifier initialization"""
        classifier = IntentClassifier()
        assert classifier.confidence_threshold == 0.7
    
    def test_classify_greeting(self):
        """Test greeting classification"""
        classifier = IntentClassifier()
        
        intent = classifier.classify("Hello, how are you?")
        
        assert intent.name == "greeting"
        assert intent.confidence > 0.0
        assert intent.raw_text == "Hello, how are you?"
    
    def test_classify_goodbye(self):
        """Test goodbye classification"""
        classifier = IntentClassifier()
        
        intent = classifier.classify("Goodbye, see you later!")
        
        assert intent.name == "goodbye"
        assert intent.confidence > 0.0
    
    def test_classify_question(self):
        """Test question classification"""
        classifier = IntentClassifier()
        
        intent = classifier.classify("What is your name?")
        
        assert intent.name.startswith("question_")
    
    def test_extract_entities(self):
        """Test entity extraction"""
        classifier = IntentClassifier()
        
        intent = classifier.classify("I want to practice at a restaurant")
        
        assert "scenario" in intent.entities
        assert intent.entities["scenario"] == "restaurant"
    
    def test_unknown_intent(self):
        """Test unknown intent"""
        classifier = IntentClassifier()
        
        intent = classifier.classify("asdfghjkl qwertyuiop")
        
        assert intent.name == "unknown"


class TestContextManager:
    """Test ContextManager class"""
    
    def test_initialization(self):
        """Test manager initialization"""
        manager = ContextManager(max_history=10)
        assert manager.max_history == 10
    
    def test_create_context(self):
        """Test context creation"""
        manager = ContextManager()
        
        context = manager.create_context(
            session_id="test_session",
            language="en"
        )
        
        assert context.session_id == "test_session"
        assert context.language == "en"
        assert len(context.turns) == 0
    
    def test_add_turn(self):
        """Test adding conversation turn"""
        manager = ContextManager()
        context = manager.create_context("test_session")
        
        manager.add_turn(
            speaker="user",
            text="Hello!",
            intent="greeting"
        )
        
        assert len(context.turns) == 1
        assert context.turns[0].speaker == "user"
        assert context.turns[0].text == "Hello!"
    
    def test_get_last_turn(self):
        """Test getting last turn"""
        manager = ContextManager()
        context = manager.create_context("test_session")
        
        manager.add_turn("user", "Hello!")
        manager.add_turn("assistant", "Hi there!")
        
        last_turn = manager.get_last_turn()
        assert last_turn.speaker == "assistant"
        assert last_turn.text == "Hi there!"
    
    def test_history_limit(self):
        """Test history limit"""
        manager = ContextManager(max_history=3)
        context = manager.create_context("test_session")
        
        # Add more turns than limit
        for i in range(5):
            manager.add_turn("user", f"Message {i}")
        
        assert len(context.turns) == 3
    
    def test_set_scenario(self):
        """Test setting scenario"""
        manager = ContextManager()
        context = manager.create_context("test_session")
        
        manager.set_scenario("restaurant")
        
        assert context.scenario == "restaurant"


if __name__ == "__main__":
    pytest.main([__file__])
