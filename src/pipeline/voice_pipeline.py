"""
Voice Pipeline Module
Orchestrates all components for zero-latency voice interaction
"""

import asyncio
import threading
import queue
import time
import numpy as np
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any
from loguru import logger

from ..audio import AudioInput, AudioOutput, AudioProcessor
from ..vad import VADDetector
from ..stt import STTEngine, TranscriptionResult
from ..nlp import IntentClassifier, ContextManager, Intent
from ..response import ResponseGenerator, Response
from ..tts import TTSEngine


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    sample_rate: int = 16000
    chunk_size: int = 1024
    enable_vad: bool = True
    enable_streaming: bool = True
    max_latency_ms: int = 200
    enable_interruption: bool = True
    enable_monitoring: bool = True


class VoicePipeline:
    """Real-time voice processing pipeline"""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize voice pipeline
        
        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        
        # Components
        self.audio_input: Optional[AudioInput] = None
        self.audio_output: Optional[AudioOutput] = None
        self.audio_processor: Optional[AudioProcessor] = None
        self.vad: Optional[VADDetector] = None
        self.stt: Optional[STTEngine] = None
        self.intent_classifier: Optional[IntentClassifier] = None
        self.context_manager: Optional[ContextManager] = None
        self.response_generator: Optional[ResponseGenerator] = None
        self.tts: Optional[TTSEngine] = None
        
        # State
        self.is_running = False
        self.is_speaking = False
        self.session_id = f"session_{int(time.time())}"
        
        # Queues for async processing
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Threads
        self.processing_threads = []
        
        # Callbacks
        self.on_transcription: Optional[Callable[[str], None]] = None
        self.on_intent: Optional[Callable[[Intent], None]] = None
        self.on_response: Optional[Callable[[Response], None]] = None
        self.on_speaking_start: Optional[Callable] = None
        self.on_speaking_end: Optional[Callable] = None
        
        # Metrics
        self.metrics = {
            "total_latency_ms": [],
            "stt_latency_ms": [],
            "nlp_latency_ms": [],
            "response_latency_ms": [],
            "tts_latency_ms": [],
            "utterances_processed": 0
        }
        
        logger.info("VoicePipeline initialized")
    
    def initialize_components(
        self,
        stt_model: str = "base.en",
        tts_engine: str = "pyttsx3",
        language: str = "en"
    ) -> None:
        """
        Initialize all pipeline components
        
        Args:
            stt_model: Speech recognition model
            tts_engine: Text-to-speech engine
            language: Primary language
        """
        logger.info("Initializing pipeline components...")
        
        # Audio components
        self.audio_input = AudioInput(
            sample_rate=self.config.sample_rate,
            chunk_size=self.config.chunk_size
        )
        
        self.audio_output = AudioOutput(
            sample_rate=22050,
            buffer_size=2048
        )
        
        self.audio_processor = AudioProcessor(
            sample_rate=self.config.sample_rate
        )
        
        # VAD
        if self.config.enable_vad:
            self.vad = VADDetector(
                sample_rate=self.config.sample_rate,
                aggressiveness=3
            )
            self.vad.register_callbacks(
                on_speech_start=self._on_speech_start,
                on_speech_end=self._on_speech_end
            )
        
        # STT
        self.stt = STTEngine(
            model_name=stt_model,
            language=language,
            enable_streaming=self.config.enable_streaming
        )
        self.stt.register_callbacks(
            on_partial_result=self._on_partial_transcription,
            on_final_result=self._on_final_transcription
        )
        
        # NLP
        self.intent_classifier = IntentClassifier()
        self.context_manager = ContextManager(max_history=10)
        self.context_manager.create_context(
            session_id=self.session_id,
            language=language
        )
        
        # Response generation
        self.response_generator = ResponseGenerator(mode="hybrid")
        
        # TTS
        self.tts = TTSEngine(
            engine=tts_engine,
            enable_streaming=True
        )
        self.tts.register_callbacks(
            on_synthesis_start=self._on_tts_start,
            on_synthesis_end=self._on_tts_end
        )
        
        logger.info("All components initialized")
    
    def start(self) -> None:
        """Start the voice pipeline"""
        if self.is_running:
            logger.warning("Pipeline already running")
            return
        
        logger.info("Starting voice pipeline...")
        
        # Initialize components if not already done
        if not self.audio_input:
            self.initialize_components()
        
        # Start audio I/O
        self.audio_input.start()
        self.audio_output.start()
        
        # Start processing threads
        self.is_running = True
        
        # Audio processing thread
        audio_thread = threading.Thread(
            target=self._audio_processing_loop,
            daemon=True,
            name="AudioProcessing"
        )
        audio_thread.start()
        self.processing_threads.append(audio_thread)
        
        # NLP processing thread
        nlp_thread = threading.Thread(
            target=self._nlp_processing_loop,
            daemon=True,
            name="NLPProcessing"
        )
        nlp_thread.start()
        self.processing_threads.append(nlp_thread)
        
        # Response processing thread
        response_thread = threading.Thread(
            target=self._response_processing_loop,
            daemon=True,
            name="ResponseProcessing"
        )
        response_thread.start()
        self.processing_threads.append(response_thread)
        
        logger.info("Voice pipeline started successfully")
    
    def stop(self) -> None:
        """Stop the voice pipeline"""
        if not self.is_running:
            return
        
        logger.info("Stopping voice pipeline...")
        
        self.is_running = False
        
        # Stop audio I/O
        if self.audio_input:
            self.audio_input.stop()
        if self.audio_output:
            self.audio_output.stop()
        
        # Wait for threads to finish
        for thread in self.processing_threads:
            thread.join(timeout=2.0)
        
        self.processing_threads.clear()
        
        logger.info("Voice pipeline stopped")
    
    def _audio_processing_loop(self) -> None:
        """Main audio processing loop"""
        logger.debug("Audio processing loop started")
        
        audio_buffer = []
        
        while self.is_running:
            try:
                # Read audio chunk
                audio_chunk = self.audio_input.read(timeout=0.1)
                
                if audio_chunk is None:
                    continue
                
                # Process audio
                processed_audio = self.audio_processor.process(audio_chunk.flatten())
                
                # VAD processing
                if self.vad:
                    is_speaking, voiced_frames = self.vad.process_frame(processed_audio)
                    
                    if voiced_frames:
                        # Add voiced frames to buffer
                        audio_buffer.extend(voiced_frames)
                    
                    # Check for speech end
                    if not is_speaking and audio_buffer:
                        # Process complete utterance
                        complete_audio = np.concatenate(audio_buffer)
                        self._process_utterance(complete_audio)
                        audio_buffer.clear()
                else:
                    # Without VAD, process chunks directly
                    audio_buffer.append(processed_audio)
                    
                    # Process every second
                    if len(audio_buffer) >= int(self.config.sample_rate / self.config.chunk_size):
                        complete_audio = np.concatenate(audio_buffer)
                        self._process_utterance(complete_audio)
                        audio_buffer.clear()
                        
            except Exception as e:
                logger.error(f"Error in audio processing: {e}")
                time.sleep(0.1)
        
        logger.debug("Audio processing loop stopped")
    
    def _process_utterance(self, audio_data: np.ndarray) -> None:
        """Process complete utterance"""
        start_time = time.time()
        
        try:
            # Speech-to-text
            stt_start = time.time()
            transcription = self.stt.transcribe(audio_data, is_final=True)
            stt_time = (time.time() - stt_start) * 1000
            
            if transcription.text.strip():
                # Add to processing queue
                self.text_queue.put({
                    "text": transcription.text,
                    "confidence": transcription.confidence,
                    "start_time": start_time
                })
                
                # Metrics
                self.metrics["stt_latency_ms"].append(stt_time)
                
                logger.info(f"Transcribed: '{transcription.text}' (STT: {stt_time:.0f}ms)")
                
        except Exception as e:
            logger.error(f"Error processing utterance: {e}")
    
    def _nlp_processing_loop(self) -> None:
        """NLP processing loop"""
        logger.debug("NLP processing loop started")
        
        while self.is_running:
            try:
                # Get text from queue
                item = self.text_queue.get(timeout=0.1)
                
                text = item["text"]
                start_time = item["start_time"]
                
                # Intent classification
                nlp_start = time.time()
                intent = self.intent_classifier.classify(text)
                nlp_time = (time.time() - nlp_start) * 1000
                
                # Update context
                self.context_manager.add_turn(
                    speaker="user",
                    text=text,
                    intent=intent.name,
                    entities=intent.entities
                )
                
                # Add to response queue
                self.response_queue.put({
                    "intent": intent,
                    "start_time": start_time
                })
                
                # Metrics
                self.metrics["nlp_latency_ms"].append(nlp_time)
                
                # Callback
                if self.on_intent:
                    self.on_intent(intent)
                
                logger.debug(f"Intent: {intent.name} (NLP: {nlp_time:.0f}ms)")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in NLP processing: {e}")
        
        logger.debug("NLP processing loop stopped")
    
    def _response_processing_loop(self) -> None:
        """Response generation and TTS loop"""
        logger.debug("Response processing loop started")
        
        while self.is_running:
            try:
                # Get intent from queue
                item = self.response_queue.get(timeout=0.1)
                
                intent = item["intent"]
                start_time = item["start_time"]
                
                # Generate response
                response_start = time.time()
                response = self.response_generator.generate(
                    intent=intent.name,
                    context={"mode": "general"},
                    entities=intent.entities
                )
                response_time = (time.time() - response_start) * 1000
                
                # Update context
                self.context_manager.add_turn(
                    speaker="assistant",
                    text=response.text
                )
                
                # Synthesize speech
                tts_start = time.time()
                audio_data = self.tts.synthesize(response.text)
                tts_time = (time.time() - tts_start) * 1000
                
                # Play audio
                if len(audio_data) > 0:
                    self.audio_output.play(audio_data)
                
                # Calculate total latency
                total_latency = (time.time() - start_time) * 1000
                
                # Metrics
                self.metrics["response_latency_ms"].append(response_time)
                self.metrics["tts_latency_ms"].append(tts_time)
                self.metrics["total_latency_ms"].append(total_latency)
                self.metrics["utterances_processed"] += 1
                
                # Callback
                if self.on_response:
                    self.on_response(response)
                
                logger.info(
                    f"Response: '{response.text}' "
                    f"(Total: {total_latency:.0f}ms, TTS: {tts_time:.0f}ms)"
                )
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in response processing: {e}")
        
        logger.debug("Response processing loop stopped")
    
    def _on_speech_start(self) -> None:
        """Callback for speech start"""
        logger.debug("Speech started")
        
        # Handle interruption if assistant is speaking
        if self.is_speaking and self.config.enable_interruption:
            self.interrupt_assistant()
    
    def _on_speech_end(self) -> None:
        """Callback for speech end"""
        logger.debug("Speech ended")
    
    def _on_partial_transcription(self, result: TranscriptionResult) -> None:
        """Callback for partial transcription"""
        if self.on_transcription:
            self.on_transcription(result.text)
    
    def _on_final_transcription(self, result: TranscriptionResult) -> None:
        """Callback for final transcription"""
        if self.on_transcription:
            self.on_transcription(result.text)
    
    def _on_tts_start(self, text: str) -> None:
        """Callback for TTS start"""
        self.is_speaking = True
        if self.on_speaking_start:
            self.on_speaking_start()
    
    def _on_tts_end(self, audio_data: np.ndarray) -> None:
        """Callback for TTS end"""
        self.is_speaking = False
        if self.on_speaking_end:
            self.on_speaking_end()
    
    def interrupt_assistant(self) -> None:
        """Interrupt assistant speech"""
        logger.info("Interrupting assistant")
        
        # Stop TTS
        if self.tts:
            self.tts.stop()
        
        # Clear audio output
        if self.audio_output:
            self.audio_output.clear_queue()
        
        self.is_speaking = False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        def avg(values):
            return sum(values) / len(values) if values else 0
        
        return {
            "utterances_processed": self.metrics["utterances_processed"],
            "avg_total_latency_ms": avg(self.metrics["total_latency_ms"]),
            "avg_stt_latency_ms": avg(self.metrics["stt_latency_ms"]),
            "avg_nlp_latency_ms": avg(self.metrics["nlp_latency_ms"]),
            "avg_response_latency_ms": avg(self.metrics["response_latency_ms"]),
            "avg_tts_latency_ms": avg(self.metrics["tts_latency_ms"]),
            "is_running": self.is_running,
            "is_speaking": self.is_speaking
        }
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
