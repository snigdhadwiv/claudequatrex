"""
Speech-to-Text Engine
Low-latency streaming speech recognition
"""

import asyncio
import numpy as np
from dataclasses import dataclass
from typing import Optional, Callable, List
from loguru import logger
import time

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not available, falling back to whisper")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("whisper not available")


@dataclass
class TranscriptionResult:
    """Speech recognition result"""
    text: str
    confidence: float
    is_partial: bool
    language: Optional[str] = None
    segments: Optional[List[dict]] = None
    processing_time: float = 0.0


class STTEngine:
    """Speech-to-Text engine with streaming support"""
    
    def __init__(
        self,
        model_name: str = "base.en",
        language: str = "en",
        device: str = "auto",
        compute_type: str = "float16",
        beam_size: int = 5,
        enable_streaming: bool = True
    ):
        """
        Initialize STT engine
        
        Args:
            model_name: Whisper model name (tiny, base, small, medium, large)
            language: Language code
            device: Device to use (auto, cpu, cuda)
            compute_type: Computation type (float32, float16, int8)
            beam_size: Beam size for decoding
            enable_streaming: Enable streaming recognition
        """
        self.model_name = model_name
        self.language = language
        self.device = device if device != "auto" else None
        self.compute_type = compute_type
        self.beam_size = beam_size
        self.enable_streaming = enable_streaming
        
        self.model = None
        self.is_initialized = False
        
        # Streaming state
        self.audio_buffer = []
        self.last_transcription = ""
        
        # Callbacks
        self.on_partial_result: Optional[Callable[[TranscriptionResult], None]] = None
        self.on_final_result: Optional[Callable[[TranscriptionResult], None]] = None
        
        logger.info(
            f"STTEngine initialized: model={model_name}, language={language}, "
            f"device={device}, streaming={enable_streaming}"
        )
    
    def initialize(self) -> None:
        """Load and initialize the model"""
        if self.is_initialized:
            return
        
        start_time = time.time()
        
        try:
            if FASTER_WHISPER_AVAILABLE:
                logger.info("Loading faster-whisper model...")
                self.model = WhisperModel(
                    self.model_name,
                    device=self.device or "auto",
                    compute_type=self.compute_type
                )
                self.engine_type = "faster-whisper"
                
            elif WHISPER_AVAILABLE:
                logger.info("Loading whisper model...")
                self.model = whisper.load_model(
                    self.model_name,
                    device=self.device or "cpu"
                )
                self.engine_type = "whisper"
                
            else:
                raise RuntimeError("No speech recognition engine available")
            
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f}s")
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize STT engine: {e}")
            raise
    
    def transcribe(
        self,
        audio_data: np.ndarray,
        is_final: bool = True
    ) -> TranscriptionResult:
        """
        Transcribe audio data
        
        Args:
            audio_data: Audio data as numpy array
            is_final: Whether this is the final transcription
            
        Returns:
            TranscriptionResult object
        """
        if not self.is_initialized:
            self.initialize()
        
        start_time = time.time()
        
        try:
            # Ensure float32 format
            if audio_data.dtype != np.float32:
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                else:
                    audio_data = audio_data.astype(np.float32)
            
            # Flatten if needed
            if audio_data.ndim > 1:
                audio_data = audio_data.flatten()
            
            # Transcribe based on engine type
            if self.engine_type == "faster-whisper":
                result = self._transcribe_faster_whisper(audio_data)
            else:
                result = self._transcribe_whisper(audio_data)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            result.is_partial = not is_final
            
            # Update state
            if is_final:
                self.last_transcription = result.text
                if self.on_final_result:
                    self.on_final_result(result)
            else:
                if self.on_partial_result:
                    self.on_partial_result(result)
            
            logger.debug(
                f"Transcription: '{result.text}' "
                f"(confidence={result.confidence:.2f}, time={processing_time:.3f}s)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return TranscriptionResult(
                text="",
                confidence=0.0,
                is_partial=not is_final,
                processing_time=time.time() - start_time
            )
    
    def _transcribe_faster_whisper(self, audio_data: np.ndarray) -> TranscriptionResult:
        """Transcribe using faster-whisper"""
        segments, info = self.model.transcribe(
            audio_data,
            language=self.language,
            beam_size=self.beam_size,
            vad_filter=False,  # We handle VAD separately
            word_timestamps=False
        )
        
        # Collect segments
        segments_list = []
        full_text = []
        total_confidence = 0.0
        num_segments = 0
        
        for segment in segments:
            segments_list.append({
                "text": segment.text,
                "start": segment.start,
                "end": segment.end,
                "confidence": getattr(segment, 'confidence', 0.0)
            })
            full_text.append(segment.text)
            total_confidence += getattr(segment, 'confidence', 0.0)
            num_segments += 1
        
        text = " ".join(full_text).strip()
        confidence = total_confidence / num_segments if num_segments > 0 else 0.0
        
        return TranscriptionResult(
            text=text,
            confidence=confidence,
            is_partial=False,
            language=info.language,
            segments=segments_list
        )
    
    def _transcribe_whisper(self, audio_data: np.ndarray) -> TranscriptionResult:
        """Transcribe using standard whisper"""
        result = self.model.transcribe(
            audio_data,
            language=self.language,
            beam_size=self.beam_size,
            fp16=self.compute_type == "float16"
        )
        
        text = result.get("text", "").strip()
        segments = result.get("segments", [])
        
        # Calculate average confidence
        confidences = [s.get("confidence", 0.0) for s in segments]
        confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return TranscriptionResult(
            text=text,
            confidence=confidence,
            is_partial=False,
            language=result.get("language"),
            segments=segments
        )
    
    def add_audio_chunk(self, audio_chunk: np.ndarray) -> Optional[TranscriptionResult]:
        """
        Add audio chunk for streaming transcription
        
        Args:
            audio_chunk: Audio chunk to add
            
        Returns:
            Partial transcription result if available
        """
        if not self.enable_streaming:
            return None
        
        self.audio_buffer.append(audio_chunk)
        
        # Check if we have enough audio for transcription
        total_samples = sum(len(chunk) for chunk in self.audio_buffer)
        
        # Transcribe every 1 second of audio
        if total_samples >= 16000:  # Assuming 16kHz sample rate
            audio_data = np.concatenate(self.audio_buffer)
            result = self.transcribe(audio_data, is_final=False)
            
            # Keep last 0.5 seconds for context
            overlap_samples = 8000
            if len(audio_data) > overlap_samples:
                self.audio_buffer = [audio_data[-overlap_samples:]]
            
            return result
        
        return None
    
    def finalize_transcription(self) -> Optional[TranscriptionResult]:
        """
        Finalize and return complete transcription
        
        Returns:
            Final transcription result
        """
        if not self.audio_buffer:
            return None
        
        audio_data = np.concatenate(self.audio_buffer)
        result = self.transcribe(audio_data, is_final=True)
        
        self.audio_buffer.clear()
        
        return result
    
    def reset(self) -> None:
        """Reset transcription state"""
        self.audio_buffer.clear()
        self.last_transcription = ""
        logger.debug("STT state reset")
    
    def register_callbacks(
        self,
        on_partial_result: Optional[Callable[[TranscriptionResult], None]] = None,
        on_final_result: Optional[Callable[[TranscriptionResult], None]] = None
    ) -> None:
        """
        Register callbacks for transcription results
        
        Args:
            on_partial_result: Callback for partial results
            on_final_result: Callback for final results
        """
        if on_partial_result:
            self.on_partial_result = on_partial_result
        if on_final_result:
            self.on_final_result = on_final_result
        
        logger.debug("STT callbacks registered")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return ["tiny", "tiny.en", "base", "base.en", "small", "small.en", 
                "medium", "medium.en", "large"]
    
    def __del__(self):
        """Cleanup"""
        if self.model:
            del self.model
