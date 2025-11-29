"""
Profile pipeline performance and identify bottlenecks
"""

import sys
import time
import numpy as np
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import VoicePipeline, PipelineConfig


def profile_components():
    """Profile individual components"""
    logger.info("Profiling pipeline components...")
    
    print("\n" + "="*60)
    print("  Pipeline Component Performance Profile")
    print("="*60 + "\n")
    
    # Create pipeline
    config = PipelineConfig(
        sample_rate=16000,
        chunk_size=1024,
        enable_vad=True,
        enable_streaming=True
    )
    
    pipeline = VoicePipeline(config=config)
    pipeline.initialize_components(stt_model="tiny.en", tts_engine="pyttsx3")
    
    # Test audio processing
    print("Testing Audio Processing...")
    audio_data = np.random.randn(16000).astype(np.float32)  # 1 second
    
    start = time.time()
    processed = pipeline.audio_processor.process(audio_data)
    audio_time = (time.time() - start) * 1000
    print(f"  ✓ Audio processing: {audio_time:.2f}ms")
    
    # Test VAD
    print("\nTesting Voice Activity Detection...")
    start = time.time()
    is_speech = pipeline.vad.is_speech(audio_data[:480])  # 30ms frame
    vad_time = (time.time() - start) * 1000
    print(f"  ✓ VAD processing: {vad_time:.2f}ms")
    
    # Test STT
    print("\nTesting Speech-to-Text...")
    start = time.time()
    result = pipeline.stt.transcribe(audio_data)
    stt_time = (time.time() - start) * 1000
    print(f"  ✓ STT processing: {stt_time:.2f}ms")
    
    # Test NLP
    print("\nTesting NLP (Intent Classification)...")
    test_text = "Hello, how are you?"
    start = time.time()
    intent = pipeline.intent_classifier.classify(test_text)
    nlp_time = (time.time() - start) * 1000
    print(f"  ✓ NLP processing: {nlp_time:.2f}ms")
    
    # Test Response Generation
    print("\nTesting Response Generation...")
    start = time.time()
    response = pipeline.response_generator.generate(intent.name)
    response_time = (time.time() - start) * 1000
    print(f"  ✓ Response generation: {response_time:.2f}ms")
    
    # Test TTS
    print("\nTesting Text-to-Speech...")
    start = time.time()
    audio = pipeline.tts.synthesize("Hello, this is a test.")
    tts_time = (time.time() - start) * 1000
    print(f"  ✓ TTS synthesis: {tts_time:.2f}ms")
    
    # Calculate total pipeline latency
    total_latency = audio_time + vad_time + stt_time + nlp_time + response_time + tts_time
    
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    print(f"Audio Processing:    {audio_time:7.2f}ms ({audio_time/total_latency*100:5.1f}%)")
    print(f"VAD:                 {vad_time:7.2f}ms ({vad_time/total_latency*100:5.1f}%)")
    print(f"Speech-to-Text:      {stt_time:7.2f}ms ({stt_time/total_latency*100:5.1f}%)")
    print(f"NLP:                 {nlp_time:7.2f}ms ({nlp_time/total_latency*100:5.1f}%)")
    print(f"Response Generation: {response_time:7.2f}ms ({response_time/total_latency*100:5.1f}%)")
    print(f"Text-to-Speech:      {tts_time:7.2f}ms ({tts_time/total_latency*100:5.1f}%)")
    print("-"*60)
    print(f"TOTAL LATENCY:       {total_latency:7.2f}ms")
    print("="*60 + "\n")
    
    # Performance assessment
    if total_latency < 200:
        print("✅ EXCELLENT: Pipeline achieves zero-latency target (<200ms)")
    elif total_latency < 500:
        print("✓ GOOD: Pipeline latency is acceptable (<500ms)")
    elif total_latency < 1000:
        print("⚠ WARNING: Pipeline latency is high (<1000ms)")
    else:
        print("❌ POOR: Pipeline latency exceeds acceptable threshold")
    
    print()


if __name__ == "__main__":
    profile_components()
