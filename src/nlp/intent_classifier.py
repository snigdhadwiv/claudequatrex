"""
Intent Classification Module
Fast intent recognition and entity extraction
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from loguru import logger
import time


@dataclass
class Intent:
    """Classified intent with entities"""
    name: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    processing_time: float = 0.0


class IntentClassifier:
    """Intent classification and entity extraction"""
    
    def __init__(
        self,
        model_name: str = "rule-based",
        confidence_threshold: float = 0.7
    ):
        """
        Initialize intent classifier
        
        Args:
            model_name: Model type (rule-based, ml)
            confidence_threshold: Minimum confidence threshold
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        
        # Define intents and patterns
        self.intents = self._load_intents()
        
        logger.info(
            f"IntentClassifier initialized: model={model_name}, "
            f"threshold={confidence_threshold}"
        )
    
    def _load_intents(self) -> Dict[str, Any]:
        """Load intent patterns"""
        return {
            # Greetings
            "greeting": {
                "patterns": [
                    r"\b(hello|hi|hey|hola|buenos días|buenas tardes)\b",
                    r"\b(good morning|good afternoon|good evening)\b",
                ],
                "responses": ["greeting"]
            },
            "goodbye": {
                "patterns": [
                    r"\b(goodbye|bye|see you|adiós|hasta luego|chao)\b",
                    r"\b(take care|talk to you later)\b",
                ],
                "responses": ["goodbye"]
            },
            "how_are_you": {
                "patterns": [
                    r"\b(how are you|how're you|cómo estás|qué tal)\b",
                    r"\b(how is it going|how do you do)\b",
                ],
                "responses": ["how_are_you"]
            },
            
            # Language learning specific
            "request_practice": {
                "patterns": [
                    r"\b(let's practice|practice|help me practice)\b",
                    r"\b(can we practice|want to practice)\b",
                ],
                "responses": ["request_practice"]
            },
            "request_scenario": {
                "patterns": [
                    r"\b(restaurant|ordering food|cafeteria)\b",
                    r"\b(job interview|interview)\b",
                    r"\b(shopping|store|buying)\b",
                    r"\b(travel|airport|hotel)\b",
                ],
                "responses": ["request_scenario"]
            },
            "ask_correction": {
                "patterns": [
                    r"\b(is this correct|did I say that right|how do I say)\b",
                    r"\b(correct me|was that right)\b",
                ],
                "responses": ["ask_correction"]
            },
            "request_repeat": {
                "patterns": [
                    r"\b(repeat|say that again|what did you say|pardon)\b",
                    r"\b(didn't catch that|one more time)\b",
                ],
                "responses": ["request_repeat"]
            },
            "request_translation": {
                "patterns": [
                    r"\b(how do you say|what is|translate)\b",
                    r"\b(what does .* mean|meaning of)\b",
                ],
                "responses": ["request_translation"]
            },
            
            # Questions
            "question_who": {
                "patterns": [r"\b(who|quién)\b"],
                "responses": ["question"]
            },
            "question_what": {
                "patterns": [r"\b(what|qué)\b"],
                "responses": ["question"]
            },
            "question_when": {
                "patterns": [r"\b(when|cuándo)\b"],
                "responses": ["question"]
            },
            "question_where": {
                "patterns": [r"\b(where|dónde)\b"],
                "responses": ["question"]
            },
            "question_why": {
                "patterns": [r"\b(why|por qué)\b"],
                "responses": ["question"]
            },
            "question_how": {
                "patterns": [r"\b(how|cómo)\b"],
                "responses": ["question"]
            },
            
            # Commands
            "command_start": {
                "patterns": [
                    r"\b(start|begin|let's go|vamos)\b",
                ],
                "responses": ["command"]
            },
            "command_stop": {
                "patterns": [
                    r"\b(stop|pause|wait|espera)\b",
                ],
                "responses": ["command"]
            },
            "command_help": {
                "patterns": [
                    r"\b(help|ayuda|assist)\b",
                ],
                "responses": ["command"]
            },
            
            # Feedback
            "express_understanding": {
                "patterns": [
                    r"\b(I understand|I see|got it|entiendo|ya veo)\b",
                    r"\b(makes sense|I get it)\b",
                ],
                "responses": ["acknowledgment"]
            },
            "express_confusion": {
                "patterns": [
                    r"\b(I don't understand|confused|no entiendo)\b",
                    r"\b(I'm lost|what do you mean)\b",
                ],
                "responses": ["clarification"]
            },
            
            # Default
            "unknown": {
                "patterns": [],
                "responses": ["unknown"]
            }
        }
    
    def classify(self, text: str) -> Intent:
        """
        Classify intent from text
        
        Args:
            text: Input text
            
        Returns:
            Intent object
        """
        start_time = time.time()
        
        text_lower = text.lower()
        
        # Try to match patterns
        best_intent = "unknown"
        best_confidence = 0.0
        
        for intent_name, intent_data in self.intents.items():
            if intent_name == "unknown":
                continue
            
            for pattern in intent_data["patterns"]:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    # Calculate confidence based on match length
                    confidence = min(0.9, len(match.group(0)) / len(text) + 0.5)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent_name
        
        # Extract entities
        entities = self._extract_entities(text, best_intent)
        
        processing_time = time.time() - start_time
        
        result = Intent(
            name=best_intent,
            confidence=best_confidence,
            entities=entities,
            raw_text=text,
            processing_time=processing_time
        )
        
        logger.debug(
            f"Intent: {best_intent} (confidence={best_confidence:.2f}, "
            f"time={processing_time:.3f}s)"
        )
        
        return result
    
    def _extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """
        Extract entities from text based on intent
        
        Args:
            text: Input text
            intent: Classified intent
            
        Returns:
            Dictionary of entities
        """
        entities = {}
        
        # Extract scenario entity
        if intent == "request_scenario":
            scenarios = {
                "restaurant": ["restaurant", "ordering food", "cafeteria", "menu"],
                "job_interview": ["job interview", "interview", "hiring"],
                "shopping": ["shopping", "store", "buying", "purchase"],
                "travel": ["travel", "airport", "hotel", "vacation"]
            }
            
            text_lower = text.lower()
            for scenario, keywords in scenarios.items():
                if any(keyword in text_lower for keyword in keywords):
                    entities["scenario"] = scenario
                    break
        
        # Extract language entity
        languages = ["spanish", "french", "german", "italian", "portuguese", 
                    "chinese", "japanese", "korean"]
        text_lower = text.lower()
        for lang in languages:
            if lang in text_lower:
                entities["language"] = lang
                break
        
        # Extract numbers
        numbers = re.findall(r'\d+', text)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]
        
        # Extract quoted text (for translations)
        quoted = re.findall(r'"([^"]*)"', text)
        if quoted:
            entities["quoted_text"] = quoted
        
        return entities
    
    def get_response_type(self, intent: Intent) -> str:
        """
        Get response type for intent
        
        Args:
            intent: Classified intent
            
        Returns:
            Response type
        """
        if intent.name in self.intents:
            return self.intents[intent.name]["responses"][0]
        return "unknown"
    
    def is_question(self, intent: Intent) -> bool:
        """Check if intent is a question"""
        return intent.name.startswith("question_")
    
    def is_command(self, intent: Intent) -> bool:
        """Check if intent is a command"""
        return intent.name.startswith("command_")
    
    def requires_context(self, intent: Intent) -> bool:
        """Check if intent requires conversation context"""
        context_intents = [
            "ask_correction",
            "request_repeat",
            "express_confusion",
            "request_translation"
        ]
        return intent.name in context_intents
