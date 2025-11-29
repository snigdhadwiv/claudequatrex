"""
Audio Input Module
Handles real-time audio capture with low-latency buffering
"""

import queue
import threading
import numpy as np
import sounddevice as sd
from loguru import logger
from typing import Callable, Optional


class AudioInput:
    """Real-time audio input handler with streaming support"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        device_index: Optional[int] = None
    ):
        """
        Initialize audio input
        
        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            chunk_size: Size of audio chunks
            device_index: Input device index (None for default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device_index = device_index
        
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
        self.callbacks = []
        
        logger.info(
            f"AudioInput initialized: {sample_rate}Hz, "
            f"{channels} channel(s), chunk_size={chunk_size}"
        )
    
    def start(self) -> None:
        """Start audio capture"""
        if self.is_recording:
            logger.warning("Audio input already recording")
            return
        
        self.is_recording = True
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.chunk_size,
                device=self.device_index,
                callback=self._audio_callback,
                dtype=np.int16
            )
            self.stream.start()
            logger.info("Audio input started")
        except Exception as e:
            logger.error(f"Failed to start audio input: {e}")
            self.is_recording = False
            raise
    
    def stop(self) -> None:
        """Stop audio capture"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        logger.info("Audio input stopped")
    
    def _audio_callback(self, indata, frames, time, status) -> None:
        """Callback for audio stream"""
        if status:
            logger.warning(f"Audio input status: {status}")
        
        # Copy data to prevent buffer issues
        audio_data = indata.copy()
        
        # Add to queue for processing
        try:
            self.audio_queue.put_nowait(audio_data)
        except queue.Full:
            logger.warning("Audio queue full, dropping frame")
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(audio_data)
            except Exception as e:
                logger.error(f"Error in audio callback: {e}")
    
    def read(self, timeout: float = None) -> Optional[np.ndarray]:
        """
        Read audio chunk from queue
        
        Args:
            timeout: Maximum time to wait for audio
            
        Returns:
            Audio data as numpy array or None if timeout
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def register_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """
        Register callback for real-time audio processing
        
        Args:
            callback: Function to call with audio data
        """
        self.callbacks.append(callback)
        logger.debug(f"Registered audio callback: {callback.__name__}")
    
    def clear_queue(self) -> None:
        """Clear audio queue"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def get_devices(self) -> list:
        """Get list of available input devices"""
        devices = sd.query_devices()
        input_devices = [
            d for d in devices 
            if d.get('max_input_channels', 0) > 0
        ]
        return input_devices
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
