"""
Language Learning Application
Real-time language practice partner with instant feedback
"""

import time
import random
from typing import Dict, Any, Optional
from loguru import logger

from ..pipeline import VoicePipeline, PipelineConfig
from ..nlp import Intent


class LanguageLearningApp:
    """Language learning application with real-time practice"""
    
    def __init__(
        self,
        target_language: str = "spanish",
        proficiency_level: str = "intermediate",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize language learning app
        
        Args:
            target_language: Target language to practice
            proficiency_level: User proficiency level
            config: Application configuration
        """
        self.target_language = target_language
        self.proficiency_level = proficiency_level
        self.config = config or {}
        
        # Pipeline
        self.pipeline: Optional[VoicePipeline] = None
        
        # Scenarios
        self.scenarios = {
            "greetings": {
                "description": "Basic greetings and introductions",
                "difficulty": "beginner",
                "prompts": [
                    "Hello! How are you?",
                    "Nice to meet you. What's your name?",
                    "How was your day?"
                ]
            },
            "ordering_food": {
                "description": "Ordering at a restaurant",
                "difficulty": "intermediate",
                "prompts": [
                    "Welcome to our restaurant! What would you like to order?",
                    "Would you like something to drink?",
                    "Will that be for here or to go?"
                ]
            },
            "job_interview": {
                "description": "Job interview practice",
                "difficulty": "advanced",
                "prompts": [
                    "Tell me about yourself and your experience.",
                    "What are your greatest strengths?",
                    "Why do you want to work here?"
                ]
            }
        }
        
        self.current_scenario: Optional[str] = None
        self.conversation_count = 0
        
        # Feedback tracking
        self.pronunciation_scores = []
        self.grammar_corrections = []
        
        logger.info(
            f"LanguageLearningApp initialized: "
            f"language={target_language}, level={proficiency_level}"
        )
    
    def initialize(self) -> None:
        """Initialize the application"""
        logger.info("Initializing language learning app...")
        
        # Create pipeline configuration
        pipeline_config = PipelineConfig(
            sample_rate=16000,
            chunk_size=1024,
            enable_vad=True,
            enable_streaming=True,
            max_latency_ms=200,
            enable_interruption=True
        )
        
        # Initialize pipeline
        self.pipeline = VoicePipeline(config=pipeline_config)
        
        # Setup callbacks
        self.pipeline.on_transcription = self._on_transcription
        self.pipeline.on_intent = self._on_intent
        self.pipeline.on_response = self._on_response
        
        # Initialize components
        self.pipeline.initialize_components(
            stt_model=self.config.get('stt', {}).get('model', 'base.en'),
            tts_engine=self.config.get('tts', {}).get('engine', 'pyttsx3'),
            language=self._get_language_code()
        )
        
        logger.info("Language learning app initialized")
    
    def run(self) -> None:
        """Run the language learning application"""
        logger.info("Starting language learning session...")
        
        # Welcome message
        self._speak_welcome()
        
        # Start pipeline
        self.pipeline.start()
        
        logger.info("Language learning app is ready. Start practicing!")
        logger.info("Press Ctrl+C to stop")
        
        try:
            # Keep running
            while True:
                time.sleep(1)
                
                # Check for scenario changes
                if self.current_scenario:
                    self._manage_scenario()
                
                # Print progress every minute
                if int(time.time()) % 60 == 0:
                    self._print_progress()
                    
        except KeyboardInterrupt:
            logger.info("Ending language learning session...")
        finally:
            self._print_final_report()
            self.pipeline.stop()
            logger.info("Language learning app stopped")
    
    def _speak_welcome(self) -> None:
        """Speak welcome message"""
        welcome_messages = {
            "spanish": "¡Hola! Bienvenido a tu clase de español. ¿Qué te gustaría practicar hoy?",
            "french": "Bonjour! Bienvenue à votre cours de français. Que voudriez-vous pratiquer?",
            "german": "Hallo! Willkommen zu Ihrem Deutschkurs. Was möchten Sie üben?",
        }
        
        message = welcome_messages.get(
            self.target_language,
            "Hello! Welcome to your language practice session. What would you like to practice?"
        )
        
        print(f"\n[ASSISTANT]: {message}\n")
    
    def _on_transcription(self, text: str) -> None:
        """Handle transcription"""
        print(f"[YOU]: {text}")
        
        # Analyze pronunciation (placeholder)
        score = self._analyze_pronunciation(text)
        if score < 0.7:
            self.pronunciation_scores.append(score)
    
    def _on_intent(self, intent: Intent) -> None:
        """Handle classified intent"""
        logger.debug(f"Intent: {intent.name} (confidence: {intent.confidence:.2f})")
        
        # Check for scenario request
        if intent.name == "request_scenario" and "scenario" in intent.entities:
            scenario = intent.entities["scenario"]
            if scenario in self.scenarios:
                self.current_scenario = scenario
                logger.info(f"Starting scenario: {scenario}")
    
    def _on_response(self, response) -> None:
        """Handle generated response"""
        print(f"[ASSISTANT]: {response.text}\n")
        
        self.conversation_count += 1
        
        # Provide feedback occasionally
        if self.conversation_count % 5 == 0:
            self._provide_feedback()
    
    def _analyze_pronunciation(self, text: str) -> float:
        """
        Analyze pronunciation quality (placeholder)
        
        Args:
            text: Transcribed text
            
        Returns:
            Pronunciation score (0.0 to 1.0)
        """
        # This would use actual phonetic analysis in production
        # For now, return a random score
        return random.uniform(0.6, 1.0)
    
    def _provide_feedback(self) -> None:
        """Provide learning feedback"""
        feedback_messages = [
            "You're doing great! Keep practicing!",
            "Good job! Your pronunciation is improving.",
            "Excellent! You're making good progress.",
            "Well done! Try to speak a bit more naturally."
        ]
        
        message = random.choice(feedback_messages)
        print(f"\n💡 FEEDBACK: {message}\n")
    
    def _manage_scenario(self) -> None:
        """Manage scenario-based practice"""
        if not self.current_scenario:
            return
        
        scenario = self.scenarios[self.current_scenario]
        
        # Occasionally prompt with scenario-specific questions
        if random.random() < 0.1:  # 10% chance
            prompt = random.choice(scenario["prompts"])
            logger.debug(f"Scenario prompt: {prompt}")
    
    def _print_progress(self) -> None:
        """Print learning progress"""
        metrics = self.pipeline.get_metrics()
        
        print("\n" + "="*50)
        print("📊 PROGRESS REPORT")
        print("="*50)
        print(f"Conversations: {self.conversation_count}")
        print(f"Utterances processed: {metrics['utterances_processed']}")
        print(f"Average latency: {metrics['avg_total_latency_ms']:.0f}ms")
        
        if self.pronunciation_scores:
            avg_score = sum(self.pronunciation_scores) / len(self.pronunciation_scores)
            print(f"Average pronunciation score: {avg_score:.2%}")
        
        print("="*50 + "\n")
    
    def _print_final_report(self) -> None:
        """Print final session report"""
        metrics = self.pipeline.get_metrics()
        
        print("\n" + "="*50)
        print("📈 SESSION SUMMARY")
        print("="*50)
        print(f"Language: {self.target_language.title()}")
        print(f"Level: {self.proficiency_level.title()}")
        print(f"Total conversations: {self.conversation_count}")
        print(f"Utterances processed: {metrics['utterances_processed']}")
        print(f"\nPerformance:")
        print(f"  Average total latency: {metrics['avg_total_latency_ms']:.0f}ms")
        print(f"  Average STT latency: {metrics['avg_stt_latency_ms']:.0f}ms")
        print(f"  Average NLP latency: {metrics['avg_nlp_latency_ms']:.0f}ms")
        print(f"  Average TTS latency: {metrics['avg_tts_latency_ms']:.0f}ms")
        
        if self.pronunciation_scores:
            avg_score = sum(self.pronunciation_scores) / len(self.pronunciation_scores)
            print(f"\nPronunciation:")
            print(f"  Average score: {avg_score:.2%}")
            print(f"  Samples analyzed: {len(self.pronunciation_scores)}")
        
        print("\n" + "="*50)
        print("Great job! Keep practicing! 🎉")
        print("="*50 + "\n")
    
    def _get_language_code(self) -> str:
        """Get language code for STT"""
        language_codes = {
            "spanish": "es",
            "french": "fr",
            "german": "de",
            "italian": "it",
            "portuguese": "pt",
            "chinese": "zh",
            "japanese": "ja",
            "korean": "ko"
        }
        
        return language_codes.get(self.target_language, "en")
    
    def set_scenario(self, scenario: str) -> bool:
        """
        Set practice scenario
        
        Args:
            scenario: Scenario name
            
        Returns:
            True if successful
        """
        if scenario in self.scenarios:
            self.current_scenario = scenario
            scenario_data = self.scenarios[scenario]
            
            print(f"\n🎭 Starting scenario: {scenario_data['description']}")
            print(f"   Difficulty: {scenario_data['difficulty']}\n")
            
            return True
        
        logger.warning(f"Unknown scenario: {scenario}")
        return False
    
    def get_available_scenarios(self) -> list:
        """Get list of available scenarios"""
        return [
            {
                "name": name,
                "description": data["description"],
                "difficulty": data["difficulty"]
            }
            for name, data in self.scenarios.items()
        ]
