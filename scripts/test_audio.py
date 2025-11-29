"""
Test audio input/output devices
"""

import sys
from pathlib import Path
import sounddevice as sd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def list_audio_devices():
    """List all available audio devices"""
    print("\n" + "="*60)
    print("  Available Audio Devices")
    print("="*60 + "\n")
    
    devices = sd.query_devices()
    
    print("INPUT DEVICES:")
    print("-"*60)
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"[{i}] {device['name']}")
            print(f"    Channels: {device['max_input_channels']}")
            print(f"    Sample Rate: {device['default_samplerate']} Hz")
            print()
    
    print("\nOUTPUT DEVICES:")
    print("-"*60)
    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            print(f"[{i}] {device['name']}")
            print(f"    Channels: {device['max_output_channels']}")
            print(f"    Sample Rate: {device['default_samplerate']} Hz")
            print()
    
    print("="*60 + "\n")


def test_audio_recording(duration=3):
    """Test audio recording"""
    print(f"\nTesting audio recording for {duration} seconds...")
    print("Please speak into your microphone...")
    
    sample_rate = 16000
    
    try:
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        
        print("✓ Recording successful")
        
        # Calculate RMS to check if audio was captured
        import numpy as np
        rms = np.sqrt(np.mean(recording ** 2))
        
        print(f"  Audio RMS: {rms:.4f}")
        
        if rms > 0.01:
            print("✓ Audio signal detected")
        else:
            print("⚠ Warning: Very low audio signal. Check microphone.")
        
        return recording
        
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return None


def test_audio_playback(recording=None):
    """Test audio playback"""
    print("\nTesting audio playback...")
    
    try:
        if recording is not None:
            print("Playing back your recording...")
            sd.play(recording, samplerate=16000)
            sd.wait()
            print("✓ Playback successful")
        else:
            # Generate test tone
            import numpy as np
            duration = 1
            sample_rate = 22050
            frequency = 440  # A4 note
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            tone = 0.3 * np.sin(2 * np.pi * frequency * t)
            
            print(f"Playing test tone ({frequency}Hz)...")
            sd.play(tone, samplerate=sample_rate)
            sd.wait()
            print("✓ Playback successful")
            
    except Exception as e:
        print(f"❌ Playback failed: {e}")


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("  Audio System Test")
    print("="*60)
    
    # List devices
    list_audio_devices()
    
    # Test recording
    recording = test_audio_recording(duration=3)
    
    # Test playback
    test_audio_playback(recording)
    
    print("\n" + "="*60)
    print("  Audio test complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
