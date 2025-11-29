"""
Text-to-Speech Engine
Low-latency streaming speech synthesis
"""

import numpy as np
import time
from typing import Optional, Callable, Generator
from loguru import logger
import io

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available")

try:
    from TTS.api import TTS as CoquiTTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False
    logger.warning("Coqui TTS not available")


class TTSEngine:
    """Text-to-Speech engine with streaming support"""
    
    def __init__(
        self,
        engine: str = "pyttsx3",
        model_name: Optional[str] = None,
        sample_rate: int = 22050,
        voice_speed: float = 1.0,
        voice_pitch: float = 1.0,
        voice_volume: float = 1.0,
        enable_streaming: bool = True
    ):
        """
        Initialize TTS engine
        
        Args:
            engine: TTS engine (pyttsx3, coqui)
            model_name: Model name for advanced engines
            sample_rate: Audio sample rate
            voice_speed: Speech speed multiplier
            voice_pitch: Pitch multiplier
            voice_volume: Volume level (0.0 to 1.0)
            enable_streaming: Enable streaming synthesis
        """
        self.engine_type = engine
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.voice_speed = voice_speed
        self.voice_pitch = voice_pitch
        self.voice_volume = voice_volume
        self.enable_streaming = enable_streaming
        
        self.engine = None
        self.is_initialized = False
        
        # Callbacks
        self.on_synthesis_start: Optional[Callable] = None
        self.on_synthesis_end: Optional[Callable] = None
        
        logger.info(
            f"TTSEngine initialized: engine={engine}, "
            f"sample_rate={sample_rate}, streaming={enable_streaming}"
        )
    
    def initialize(self) -> None:
        """Initialize TTS engine"""
        if self.is_initialized:
            return
        
        start_time = time.time()
        
        try:
            if self.engine_type == "pyttsx3" and PYTTSX3_AVAILABLE:
                self._init_pyttsx3()
            elif self.engine_type == "coqui" and COQUI_AVAILABLE:
                self._init_coqui()
            else:
                # Fallback to pyttsx3
                if PYTTSX3_AVAILABLE:
                    logger.warning(f"Engine {self.engine_type} not available, using pyttsx3")
                    self._init_pyttsx3()
                else:
                    raise RuntimeError("No TTS engine available")
            
            load_time = time.time() - start_time
            logger.info(f"TTS engine loaded in {load_time:.2f}s")
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            raise
    
    def _init_pyttsx3(self) -> None:
        """Initialize pyttsx3 engine"""
        self.engine = pyttsx3.init()
        
        # Set properties
        self.engine.setProperty('rate', int(200 * self.voice_speed))
        self.engine.setProperty('volume', self.voice_volume)
        
        # List available voices
        voices = self.engine.getProperty('voices')
        logger.debug(f"Available voices: {len(voices)}")
        
        self.engine_type = "pyttsx3"
    
    def _init_coqui(self) -> None:
        """Initialize Coqui TTS engine"""
        if not self.model_name:
            self.model_name = "tts_models/en/ljspeech/tacotron2-DDC"
        
        self.engine = CoquiTTS(model_name=self.model_name)
        self.engine_type = "coqui"
    
    def synthesize(
        self,
        text: str,
        streaming: Optional[bool] = None
    ) -> np.ndarray:
        """
        Synthesize speech from text
        
        Args:
            text: Input text
            streaming: Override streaming setting
            
        Returns:
            Audio data as numpy array
        """
        if not self.is_initialized:
            self.initialize()
        
        if not text.strip():
            return np.array([], dtype=np.float32)
        
        start_time = time.time()
        
        # Notify start
        if self.on_synthesis_start:
            self.on_synthesis_start(text)
        
        try:
            # Synthesize based on engine
            if self.engine_type == "pyttsx3":
                audio_data = self._synthesize_pyttsx3(text)
            elif self.engine_type == "coqui":
                audio_data = self._synthesize_coqui(text)
            else:
                audio_data = np.array([], dtype=np.float32)
            
            synthesis_time = time.time() - start_time
            
            logger.debug(
                f"Synthesized: '{text[:50]}...' "
                f"({len(audio_data)} samples, {synthesis_time:.3f}s)"
            )
            
            # Notify end
            if self.on_synthesis_end:
                self.on_synthesis_end(audio_data)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return np.array([], dtype=np.float32)
    
    def _synthesize_pyttsx3(self, text: str) -> np.ndarray:
        """Synthesize using pyttsx3 (file-based)"""
        import tempfile
        import soundfile as sf
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Save to file
            self.engine.save_to_file(text, tmp_path)
            self.engine.runAndWait()
            
            # Read audio file
            audio_data, sample_rate = sf.read(tmp_path)
            
            # Convert to float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Resample if needed
            if sample_rate != self.sample_rate:
                audio_data = self._resample(audio_data, sample_rate, self.sample_rate)
            
            return audio_data
            
        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _synthesize_coqui(self, text: str) -> np.ndarray:
        """Synthesize using Coqui TTS"""
        # Generate audio
        audio_data = self.engine.tts(text)
        
        # Convert to numpy array
        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data, dtype=np.float32)
        
        return audio_data
    
    def synthesize_streaming(
        self,
        text: str,
        chunk_size: int = 512
    ) -> Generator[np.ndarray, None, None]:
        """
        Generate audio chunks for streaming playback
        
        Args:
            text: Input text
            chunk_size: Size of audio chunks
            
        Yields:
            Audio chunks as numpy arrays
        """
        # Split text into sentences
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            # Synthesize sentence
            audio_data = self.synthesize(sentence, streaming=True)
            
            # Yield chunks
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                yield chunk
    
    def _split_into_sentences(self, text: str) -> list:
        """Split text into sentences for streaming"""
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _resample(
        self,
        audio_data: np.ndarray,
        orig_sr: int,
        target_sr: int
    ) -> np.ndarray:
        """Resample audio data"""
        from scipy import signal
        
        num_samples = int(len(audio_data) * target_sr / orig_sr)
        resampled = signal.resample(audio_data, num_samples)
        
        return resampled.astype(np.float32)
    
    def set_voice(self, voice_id: int) -> None:
        """
        Set voice by ID
        
        Args:
            voice_id: Voice index
        """
        if self.engine_type == "pyttsx3" and self.engine:
            voices = self.engine.getProperty('voices')
            if 0 <= voice_id < len(voices):
                self.engine.setProperty('voice', voices[voice_id].id)
                logger.info(f"Set voice: {voices[voice_id].name}")
            else:
                logger.warning(f"Invalid voice ID: {voice_id}")
    
    def set_rate(self, rate: float) -> None:
        """
        Set speech rate
        
        Args:
            rate: Rate multiplier
        """
        self.voice_speed = rate
        
        if self.engine_type == "pyttsx3" and self.engine:
            self.engine.setProperty('rate', int(200 * rate))
    
    def set_volume(self, volume: float) -> None:
        """
        Set volume
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.voice_volume = max(0.0, min(1.0, volume))
        
        if self.engine_type == "pyttsx3" and self.engine:
            self.engine.setProperty('volume', self.voice_volume)
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if self.engine_type == "pyttsx3" and self.engine:
            voices = self.engine.getProperty('voices')
            return [{"id": i, "name": v.name, "languages": v.languages}
                    for i, v in enumerate(voices)]
        return []
    
    def register_callbacks(
        self,
        on_synthesis_start: Optional[Callable] = None,
        on_synthesis_end: Optional[Callable] = None
    ) -> None:
        """
        Register callbacks for synthesis events
        
        Args:
            on_synthesis_start: Callback when synthesis starts
            on_synthesis_end: Callback when synthesis ends
        """
        if on_synthesis_start:
            self.on_synthesis_start = on_synthesis_start
        if on_synthesis_end:
            self.on_synthesis_end = on_synthesis_end
        
        logger.debug("TTS callbacks registered")
    
    def stop(self) -> None:
        """Stop current synthesis"""
        if self.engine_type == "pyttsx3" and self.engine:
            self.engine.stop()
    
    def __del__(self):
        """Cleanup"""
        if self.engine:
            if self.engine_type == "pyttsx3":
                try:
                    self.engine.stop()
                except:
                    pass
