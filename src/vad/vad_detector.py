"""
Voice Activity Detection Module
Real-time speech detection with minimal latency
"""

import collections
import numpy as np
import webrtcvad
from loguru import logger
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class VADState:
    """VAD state information"""
    is_speech: bool = False
    speech_frames: int = 0
    silence_frames: int = 0
    speech_started: bool = False


class VADDetector:
    """Voice Activity Detector using WebRTC VAD"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        aggressiveness: int = 3,
        padding_duration_ms: int = 300,
        min_speech_duration_ms: int = 250
    ):
        """
        Initialize VAD detector
        
        Args:
            sample_rate: Audio sample rate (8000, 16000, 32000, 48000)
            frame_duration_ms: Frame duration (10, 20, or 30 ms)
            aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
            padding_duration_ms: Padding duration around speech
            min_speech_duration_ms: Minimum speech duration to trigger
        """
        if sample_rate not in [8000, 16000, 32000, 48000]:
            raise ValueError(f"Unsupported sample rate: {sample_rate}")
        
        if frame_duration_ms not in [10, 20, 30]:
            raise ValueError(f"Unsupported frame duration: {frame_duration_ms}")
        
        if not 0 <= aggressiveness <= 3:
            raise ValueError(f"Aggressiveness must be 0-3, got {aggressiveness}")
        
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.aggressiveness = aggressiveness
        
        # Calculate frame parameters
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.num_padding_frames = int(padding_duration_ms / frame_duration_ms)
        self.num_min_speech_frames = int(min_speech_duration_ms / frame_duration_ms)
        
        # Initialize WebRTC VAD
        self.vad = webrtcvad.Vad(aggressiveness)
        
        # State tracking
        self.state = VADState()
        self.ring_buffer = collections.deque(maxlen=self.num_padding_frames)
        self.triggered = False
        
        # Callbacks
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        
        logger.info(
            f"VADDetector initialized: {sample_rate}Hz, "
            f"{frame_duration_ms}ms frames, aggressiveness={aggressiveness}"
        )
    
    def is_speech(self, audio_frame: np.ndarray) -> bool:
        """
        Detect if audio frame contains speech
        
        Args:
            audio_frame: Audio data (must be frame_size samples)
            
        Returns:
            True if speech detected
        """
        # Convert to int16 if needed
        if audio_frame.dtype != np.int16:
            audio_frame = (audio_frame * 32768).astype(np.int16)
        
        # Ensure correct size
        if len(audio_frame) != self.frame_size:
            # Pad or truncate
            if len(audio_frame) < self.frame_size:
                audio_frame = np.pad(
                    audio_frame,
                    (0, self.frame_size - len(audio_frame)),
                    mode='constant'
                )
            else:
                audio_frame = audio_frame[:self.frame_size]
        
        # Convert to bytes
        audio_bytes = audio_frame.tobytes()
        
        try:
            return self.vad.is_speech(audio_bytes, self.sample_rate)
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False
    
    def process_frame(self, audio_frame: np.ndarray) -> tuple[bool, Optional[list]]:
        """
        Process audio frame and detect speech segments
        
        Args:
            audio_frame: Audio data
            
        Returns:
            Tuple of (is_speaking, voiced_audio_frames)
        """
        is_speech = self.is_speech(audio_frame)
        
        # Update state
        if is_speech:
            self.state.speech_frames += 1
            self.state.silence_frames = 0
        else:
            self.state.silence_frames += 1
            if self.state.speech_frames > 0:
                self.state.speech_frames = 0
        
        # Add to ring buffer
        self.ring_buffer.append((audio_frame, is_speech))
        
        # Check for speech start
        if not self.triggered:
            num_voiced = len([f for f, speech in self.ring_buffer if speech])
            
            if num_voiced > 0.5 * self.ring_buffer.maxlen:
                self.triggered = True
                self.state.speech_started = True
                
                # Call speech start callback
                if self.on_speech_start:
                    self.on_speech_start()
                
                logger.debug("Speech started")
                
                # Return buffered frames
                voiced_frames = [f[0] for f in self.ring_buffer]
                self.ring_buffer.clear()
                return True, voiced_frames
        
        # Check for speech end
        else:
            num_unvoiced = len([f for f, speech in self.ring_buffer if not speech])
            
            if num_unvoiced > 0.9 * self.ring_buffer.maxlen:
                self.triggered = False
                self.state.speech_started = False
                
                # Call speech end callback
                if self.on_speech_end:
                    self.on_speech_end()
                
                logger.debug("Speech ended")
                
                # Return final frames
                voiced_frames = [f[0] for f in self.ring_buffer]
                self.ring_buffer.clear()
                return False, voiced_frames
        
        # Return current state
        return self.triggered, None
    
    def reset(self) -> None:
        """Reset VAD state"""
        self.state = VADState()
        self.ring_buffer.clear()
        self.triggered = False
        logger.debug("VAD state reset")
    
    def set_aggressiveness(self, level: int) -> None:
        """
        Set VAD aggressiveness level
        
        Args:
            level: Aggressiveness level (0-3)
        """
        if not 0 <= level <= 3:
            raise ValueError(f"Aggressiveness must be 0-3, got {level}")
        
        self.aggressiveness = level
        self.vad.set_mode(level)
        logger.info(f"VAD aggressiveness set to {level}")
    
    def register_callbacks(
        self,
        on_speech_start: Optional[Callable] = None,
        on_speech_end: Optional[Callable] = None
    ) -> None:
        """
        Register callbacks for speech events
        
        Args:
            on_speech_start: Callback when speech starts
            on_speech_end: Callback when speech ends
        """
        if on_speech_start:
            self.on_speech_start = on_speech_start
        if on_speech_end:
            self.on_speech_end = on_speech_end
        
        logger.debug("VAD callbacks registered")
    
    def get_state(self) -> VADState:
        """Get current VAD state"""
        return self.state
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self.triggered
