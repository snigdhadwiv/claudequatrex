"""
Audio Output Module
Handles real-time audio playback with minimal latency
"""

import queue
import threading
import numpy as np
import sounddevice as sd
from loguru import logger
from typing import Optional


class AudioOutput:
    """Real-time audio output handler with streaming support"""
    
    def __init__(
        self,
        sample_rate: int = 22050,
        channels: int = 1,
        buffer_size: int = 2048,
        device_index: Optional[int] = None
    ):
        """
        Initialize audio output
        
        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            buffer_size: Size of output buffer
            device_index: Output device index (None for default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_size = buffer_size
        self.device_index = device_index
        
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.stream = None
        self._play_thread = None
        self._stop_event = threading.Event()
        
        logger.info(
            f"AudioOutput initialized: {sample_rate}Hz, "
            f"{channels} channel(s), buffer_size={buffer_size}"
        )
    
    def start(self) -> None:
        """Start audio output stream"""
        if self.is_playing:
            logger.warning("Audio output already playing")
            return
        
        self.is_playing = True
        self._stop_event.clear()
        
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.buffer_size,
                device=self.device_index,
                callback=self._audio_callback,
                dtype=np.float32
            )
            self.stream.start()
            logger.info("Audio output started")
        except Exception as e:
            logger.error(f"Failed to start audio output: {e}")
            self.is_playing = False
            raise
    
    def stop(self) -> None:
        """Stop audio output stream"""
        if not self.is_playing:
            return
        
        self.is_playing = False
        self._stop_event.set()
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Clear remaining audio
        self.clear_queue()
        
        logger.info("Audio output stopped")
    
    def _audio_callback(self, outdata, frames, time, status) -> None:
        """Callback for audio stream"""
        if status:
            logger.warning(f"Audio output status: {status}")
        
        try:
            # Get audio from queue
            audio_data = self.audio_queue.get_nowait()
            
            # Ensure correct shape
            if audio_data.ndim == 1:
                audio_data = audio_data.reshape(-1, 1)
            
            # Handle size mismatch
            if len(audio_data) < frames:
                # Pad with zeros
                padding = np.zeros((frames - len(audio_data), self.channels), dtype=np.float32)
                audio_data = np.vstack([audio_data, padding])
            elif len(audio_data) > frames:
                # Trim excess
                audio_data = audio_data[:frames]
            
            outdata[:] = audio_data
            
        except queue.Empty:
            # No audio available, output silence
            outdata.fill(0)
    
    def write(self, audio_data: np.ndarray, block: bool = False) -> None:
        """
        Write audio data to output queue
        
        Args:
            audio_data: Audio data as numpy array
            block: Whether to block until queue has space
        """
        # Ensure float32 format
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Normalize if needed
        if audio_data.max() > 1.0 or audio_data.min() < -1.0:
            audio_data = audio_data / np.abs(audio_data).max()
        
        try:
            if block:
                self.audio_queue.put(audio_data)
            else:
                self.audio_queue.put_nowait(audio_data)
        except queue.Full:
            logger.warning("Audio output queue full, dropping frame")
    
    def play(self, audio_data: np.ndarray) -> None:
        """
        Play audio data immediately
        
        Args:
            audio_data: Audio data as numpy array
        """
        if not self.is_playing:
            self.start()
        
        self.write(audio_data, block=True)
    
    def play_blocking(self, audio_data: np.ndarray) -> None:
        """
        Play audio data and wait for completion
        
        Args:
            audio_data: Audio data as numpy array
        """
        self.play(audio_data)
        
        # Wait for queue to empty
        while not self.audio_queue.empty():
            self._stop_event.wait(0.01)
            if not self.is_playing:
                break
    
    def clear_queue(self) -> None:
        """Clear audio output queue"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def is_queue_empty(self) -> bool:
        """Check if output queue is empty"""
        return self.audio_queue.empty()
    
    def get_devices(self) -> list:
        """Get list of available output devices"""
        devices = sd.query_devices()
        output_devices = [
            d for d in devices 
            if d.get('max_output_channels', 0) > 0
        ]
        return output_devices
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
