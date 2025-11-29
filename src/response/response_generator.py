"""
Response Generation Module
Fast response generation with template and dynamic modes
"""

import json
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger


@dataclass
class Response:
    """Generated response"""
    text: str
    intent: str
    confidence: float
    metadata: Dict[str, Any]
    generation_time: float = 0.0
    source: str = "template"  # template, dynamic, hybrid


class ResponseGenerator:
    """Response generation with multiple strategies"""
    
    def __init__(
        self,
        mode: str = "hybrid",
        template_file: Optional[str] = None,
        enable_cache: bool = True,
        cache_size: int = 1000
    ):
        """
        Initialize response generator
        
        Args:
            mode: Generation mode (template, dynamic, hybrid)
            template_file: Path to template JSON file
            enable_cache: Enable response caching
            cache_size: Maximum cache size
        """
        self.mode = mode
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        
        # Load templates
        self.templates = self._load_templates(template_file)
        
        # Response cache
        self.cache: Dict[str, Response] = {}
        
        # Statistics
        self.stats = {
            "total_generated": 0,
            "cache_hits": 0,
            "template_used": 0,
            "dynamic_used": 0
        }
        
        logger.info(f"ResponseGenerator initialized: mode={mode}, cache={enable_cache}")
    
    def _load_templates(self, template_file: Optional[str]) -> Dict[str, Any]:
        """Load response templates from file"""
        if not template_file:
            template_file = "config/response_templates.json"
        
        template_path = Path(template_file)
        
        if template_path.exists():
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                logger.info(f"Loaded templates from {template_file}")
                return templates
            except Exception as e:
                logger.error(f"Failed to load templates: {e}")
        else:
            logger.warning(f"Template file not found: {template_file}")
        
        return self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, Any]:
        """Get default templates"""
        return {
            "general": {
                "acknowledgment": [
                    "I understand.",
                    "Got it.",
                    "Okay."
                ],
                "greeting": [
                    "Hello! How can I help you?",
                    "Hi there! What would you like to practice?",
                    "Hey! Ready to learn?"
                ],
                "goodbye": [
                    "Goodbye! Have a great day!",
                    "See you later! Keep practicing!",
                    "Bye! Talk to you soon!"
                ],
                "unknown": [
                    "I'm not sure I understand. Could you rephrase that?",
                    "Sorry, I didn't get that. Can you say it differently?",
                    "Can you clarify what you mean?"
                ]
            }
        }
    
    def generate(
        self,
        intent: str,
        context: Optional[Dict[str, Any]] = None,
        entities: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Generate response based on intent and context
        
        Args:
            intent: Classified intent
            context: Conversation context
            entities: Extracted entities
            
        Returns:
            Response object
        """
        start_time = time.time()
        
        # Check cache
        if self.enable_cache:
            cache_key = self._get_cache_key(intent, context, entities)
            if cache_key in self.cache:
                self.stats["cache_hits"] += 1
                cached_response = self.cache[cache_key]
                logger.debug(f"Cache hit for intent: {intent}")
                return cached_response
        
        # Generate response based on mode
        if self.mode == "template" or (self.mode == "hybrid" and self._has_template(intent)):
            response_text = self._generate_from_template(intent, context, entities)
            source = "template"
            self.stats["template_used"] += 1
        else:
            response_text = self._generate_dynamic(intent, context, entities)
            source = "dynamic"
            self.stats["dynamic_used"] += 1
        
        generation_time = time.time() - start_time
        
        # Create response object
        response = Response(
            text=response_text,
            intent=intent,
            confidence=0.9 if source == "template" else 0.7,
            metadata={
                "context": context or {},
                "entities": entities or {}
            },
            generation_time=generation_time,
            source=source
        )
        
        # Cache response
        if self.enable_cache:
            if len(self.cache) >= self.cache_size:
                # Remove oldest entry (simple FIFO)
                self.cache.pop(next(iter(self.cache)))
            self.cache[cache_key] = response
        
        self.stats["total_generated"] += 1
        
        logger.debug(
            f"Generated response: intent={intent}, source={source}, "
            f"time={generation_time:.3f}s"
        )
        
        return response
    
    def _has_template(self, intent: str) -> bool:
        """Check if template exists for intent"""
        # Check in language learning templates
        if "language_learning" in self.templates:
            for category, intents in self.templates["language_learning"].items():
                if intent in intents:
                    return True
        
        # Check in general templates
        if "general" in self.templates:
            if intent in self.templates["general"]:
                return True
        
        return False
    
    def _generate_from_template(
        self,
        intent: str,
        context: Optional[Dict[str, Any]],
        entities: Optional[Dict[str, Any]]
    ) -> str:
        """Generate response from template"""
        templates = []
        
        # Get template category based on intent
        if context and context.get("mode") == "language-learning":
            # Look in language learning templates
            if "language_learning" in self.templates:
                for category, intents in self.templates["language_learning"].items():
                    if intent in intents:
                        templates = intents[intent]
                        break
        
        # Fall back to general templates
        if not templates and "general" in self.templates:
            # Map intent to template key
            template_key = self._map_intent_to_template(intent)
            templates = self.templates["general"].get(template_key, [])
        
        # Default templates
        if not templates:
            templates = self.templates["general"].get("acknowledgment", ["I understand."])
        
        # Select random template
        response_text = random.choice(templates)
        
        # Fill in entities if any
        if entities:
            response_text = self._fill_template(response_text, entities)
        
        return response_text
    
    def _generate_dynamic(
        self,
        intent: str,
        context: Optional[Dict[str, Any]],
        entities: Optional[Dict[str, Any]]
    ) -> str:
        """Generate dynamic response (placeholder for ML model)"""
        # This would use a language model in production
        # For now, use simple rules
        
        if intent.startswith("question_"):
            return "That's a great question. Let me think about that..."
        elif intent.startswith("command_"):
            return "Okay, I'll do that right away."
        elif "greeting" in intent:
            return "Hello! How can I assist you today?"
        elif "goodbye" in intent:
            return "Goodbye! It was nice talking to you!"
        else:
            return "I understand. Please continue."
    
    def _map_intent_to_template(self, intent: str) -> str:
        """Map intent name to template key"""
        # Remove prefixes
        for prefix in ["request_", "ask_", "command_", "question_", "express_"]:
            if intent.startswith(prefix):
                intent = intent[len(prefix):]
        
        # Map specific intents
        intent_map = {
            "practice": "request_practice",
            "correction": "ask_correction",
            "repeat": "request_repeat",
            "translation": "request_translation",
            "understanding": "acknowledgment",
            "confusion": "clarification",
            "help": "acknowledgment"
        }
        
        return intent_map.get(intent, "acknowledgment")
    
    def _fill_template(self, template: str, entities: Dict[str, Any]) -> str:
        """Fill template with entity values"""
        for key, value in entities.items():
            placeholder = "{" + key + "}"
            if placeholder in template:
                template = template.replace(placeholder, str(value))
        
        return template
    
    def _get_cache_key(
        self,
        intent: str,
        context: Optional[Dict[str, Any]],
        entities: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key"""
        # Simple key based on intent and entities
        key_parts = [intent]
        
        if entities:
            # Sort entities for consistent key
            for k, v in sorted(entities.items()):
                key_parts.append(f"{k}:{v}")
        
        return "|".join(key_parts)
    
    def add_template(
        self,
        category: str,
        intent: str,
        templates: List[str]
    ) -> None:
        """
        Add custom template
        
        Args:
            category: Template category
            intent: Intent name
            templates: List of template strings
        """
        if category not in self.templates:
            self.templates[category] = {}
        
        self.templates[category][intent] = templates
        logger.info(f"Added template: {category}.{intent}")
    
    def clear_cache(self) -> None:
        """Clear response cache"""
        self.cache.clear()
        logger.info("Response cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / self.stats["total_generated"]
                if self.stats["total_generated"] > 0 else 0
            )
        }
