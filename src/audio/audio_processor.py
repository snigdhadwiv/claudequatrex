"""
Audio Processor Module
Audio preprocessing and enhancement for optimal recognition
"""

import numpy as np
from scipy import signal
from scipy.signal import butter, lfilter
from loguru import logger
from typing import Optional


class AudioProcessor:
    """Audio preprocessing and enhancement"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        enable_noise_reduction: bool = True,
        enable_normalization: bool = True,
        enable_preemphasis: bool = True
    ):
        """
        Initialize audio processor
        
        Args:
            sample_rate: Audio sample rate in Hz
            enable_noise_reduction: Enable noise reduction
            enable_normalization: Enable audio normalization
            enable_preemphasis: Enable pre-emphasis filter
        """
        self.sample_rate = sample_rate
        self.enable_noise_reduction = enable_noise_reduction
        self.enable_normalization = enable_normalization
        self.enable_preemphasis = enable_preemphasis
        
        # Noise profile (estimated from silence)
        self.noise_profile = None
        
        logger.info(
            f"AudioProcessor initialized: "
            f"noise_reduction={enable_noise_reduction}, "
            f"normalization={enable_normalization}, "
            f"preemphasis={enable_preemphasis}"
        )
    
    def process(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Process audio data
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Processed audio data
        """
        # Convert to float32
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        
        # Remove DC offset
        audio_data = self._remove_dc_offset(audio_data)
        
        # Apply noise reduction
        if self.enable_noise_reduction:
            audio_data = self._reduce_noise(audio_data)
        
        # Apply pre-emphasis
        if self.enable_preemphasis:
            audio_data = self._preemphasis(audio_data)
        
        # Normalize
        if self.enable_normalization:
            audio_data = self._normalize(audio_data)
        
        return audio_data
    
    def _remove_dc_offset(self, audio_data: np.ndarray) -> np.ndarray:
        """Remove DC offset from audio"""
        return audio_data - np.mean(audio_data)
    
    def _reduce_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Simple noise reduction using spectral subtraction
        
        Args:
            audio_data: Input audio
            
        Returns:
            Noise-reduced audio
        """
        # Simple high-pass filter to remove low-frequency noise
        nyquist = self.sample_rate / 2
        cutoff = 80  # Hz
        
        if cutoff < nyquist:
            b, a = butter(4, cutoff / nyquist, btype='high')
            audio_data = lfilter(b, a, audio_data)
        
        return audio_data
    
    def _preemphasis(self, audio_data: np.ndarray, coeff: float = 0.97) -> np.ndarray:
        """
        Apply pre-emphasis filter
        
        Args:
            audio_data: Input audio
            coeff: Pre-emphasis coefficient
            
        Returns:
            Pre-emphasized audio
        """
        return np.append(audio_data[0], audio_data[1:] - coeff * audio_data[:-1])
    
    def _normalize(self, audio_data: np.ndarray, target_level: float = 0.9) -> np.ndarray:
        """
        Normalize audio to target level
        
        Args:
            audio_data: Input audio
            target_level: Target peak level (0.0 to 1.0)
            
        Returns:
            Normalized audio
        """
        max_val = np.abs(audio_data).max()
        
        if max_val > 0:
            audio_data = audio_data * (target_level / max_val)
        
        return audio_data
    
    def estimate_noise_profile(self, audio_data: np.ndarray) -> None:
        """
        Estimate noise profile from silence
        
        Args:
            audio_data: Audio containing silence/noise
        """
        # Simple noise estimation (can be improved)
        self.noise_profile = np.std(audio_data)
        logger.debug(f"Noise profile estimated: {self.noise_profile}")
    
    def apply_bandpass_filter(
        self,
        audio_data: np.ndarray,
        lowcut: float = 300,
        highcut: float = 3400
    ) -> np.ndarray:
        """
        Apply bandpass filter (useful for speech)
        
        Args:
            audio_data: Input audio
            lowcut: Low cutoff frequency in Hz
            highcut: High cutoff frequency in Hz
            
        Returns:
            Filtered audio
        """
        nyquist = self.sample_rate / 2
        low = lowcut / nyquist
        high = highcut / nyquist
        
        b, a = butter(4, [low, high], btype='band')
        return lfilter(b, a, audio_data)
    
    def resample(self, audio_data: np.ndarray, target_rate: int) -> np.ndarray:
        """
        Resample audio to target sample rate
        
        Args:
            audio_data: Input audio
            target_rate: Target sample rate
            
        Returns:
            Resampled audio
        """
        if self.sample_rate == target_rate:
            return audio_data
        
        # Calculate resampling ratio
        num_samples = int(len(audio_data) * target_rate / self.sample_rate)
        
        # Resample using scipy
        resampled = signal.resample(audio_data, num_samples)
        
        logger.debug(f"Resampled audio: {self.sample_rate}Hz -> {target_rate}Hz")
        
        return resampled
    
    def detect_silence(
        self,
        audio_data: np.ndarray,
        threshold: float = 0.01,
        min_duration: float = 0.3
    ) -> bool:
        """
        Detect if audio segment is silence
        
        Args:
            audio_data: Input audio
            threshold: Silence threshold
            min_duration: Minimum silence duration in seconds
            
        Returns:
            True if audio is silence
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_data ** 2))
        
        # Check if below threshold
        is_silent = rms < threshold
        
        return is_silent
    
    def calculate_energy(self, audio_data: np.ndarray) -> float:
        """
        Calculate audio energy (RMS)
        
        Args:
            audio_data: Input audio
            
        Returns:
            RMS energy value
        """
        return np.sqrt(np.mean(audio_data ** 2))
