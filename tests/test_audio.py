"""Tests for audio processing modules"""

import pytest
import numpy as np
from src.audio import AudioProcessor


class TestAudioProcessor:
    """Test AudioProcessor class"""
    
    def test_initialization(self):
        """Test processor initialization"""
        processor = AudioProcessor(sample_rate=16000)
        assert processor.sample_rate == 16000
        assert processor.enable_normalization is True
    
    def test_process_audio(self):
        """Test audio processing"""
        processor = AudioProcessor(sample_rate=16000)
        
        # Create test audio
        audio_data = np.random.randn(1600).astype(np.float32)
        
        # Process
        processed = processor.process(audio_data)
        
        assert processed is not None
        assert len(processed) == len(audio_data)
        assert processed.dtype == np.float32
    
    def test_normalize(self):
        """Test audio normalization"""
        processor = AudioProcessor(sample_rate=16000)
        
        # Create loud audio
        audio_data = np.random.randn(1600).astype(np.float32) * 10
        
        # Normalize
        normalized = processor._normalize(audio_data)
        
        assert np.abs(normalized).max() <= 1.0
    
    def test_detect_silence(self):
        """Test silence detection"""
        processor = AudioProcessor(sample_rate=16000)
        
        # Create silence
        silence = np.zeros(1600, dtype=np.float32)
        assert processor.detect_silence(silence) is True
        
        # Create audio with signal
        signal = np.random.randn(1600).astype(np.float32) * 0.5
        assert processor.detect_silence(signal) is False
    
    def test_calculate_energy(self):
        """Test energy calculation"""
        processor = AudioProcessor(sample_rate=16000)
        
        # Test with known values
        audio_data = np.ones(1600, dtype=np.float32) * 0.5
        energy = processor.calculate_energy(audio_data)
        
        assert energy == pytest.approx(0.5, rel=1e-3)


if __name__ == "__main__":
    pytest.main([__file__])
