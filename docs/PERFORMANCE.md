# Performance Guide

## Overview

This guide provides detailed information about optimizing the Real-Time Voice Assistant for maximum
performance and minimal latency.

## Performance Targets

### Latency Goals

| Component | Target | Acceptable | Needs Improvement |
|-----------|--------|------------|-------------------|
| Total End-to-End | < 200ms | < 500ms | > 500ms |
| Audio Processing | < 10ms | < 20ms | > 20ms |
| VAD | < 5ms | < 10ms | > 10ms |
| STT (streaming) | < 50ms | < 100ms | > 100ms |
| NLP | < 30ms | < 50ms | > 50ms |
| Response Gen | < 40ms | < 80ms | > 80ms |
| TTS (first chunk) | < 80ms | < 150ms | > 150ms |

## Optimization Strategies

### 1. Model Selection

#### STT Models

**Tiny (39M params)**

- Latency: 20-40ms
- Accuracy: 70-80%
- Use case: Real-time demos, testing
- Memory: ~150MB

**Base (74M params)**

- Latency: 40-80ms
- Accuracy: 80-90%
- Use case: General production use
- Memory: ~250MB

**Small (244M params)**

- Latency: 80-150ms
- Accuracy: 90-95%
- Use case: High accuracy needed
- Memory: ~800MB

**Medium (769M params)**

- Latency: 150-300ms
- Accuracy: 95-97%
- Use case: Offline processing
- Memory: ~2.5GB

**Recommendation**: Use `base.en` for balanced performance/accuracy in real-time applications.

#### TTS Engines

**pyttsx3**

- Latency: 50-100ms
- Quality: Good
- Pros: Lightweight, offline
- Cons: Less natural

**Coqui TTS**

- Latency: 100-200ms
- Quality: Excellent
- Pros: Very natural
- Cons: Slower, larger

**Piper TTS**

- Latency: 60-120ms
- Quality: Very Good
- Pros: Fast, natural
- Cons: Limited voices

**Recommendation**: Use `pyttsx3` for lowest latency, Piper for balance, Coqui for quality.

### 2. Hardware Acceleration

#### GPU Acceleration

Enable CUDA for faster processing:

```yaml
# config/config.yaml
stt:
  optimization:
    device: "cuda"
    compute_type: "float16"
```

**Performance Gain**: 3-5x faster STT processing

**Requirements**:

- NVIDIA GPU (GTX 1060 or better)
- CUDA 11.0+
- cuDNN 8.0+

#### CPU Optimization

For CPU-only systems:

```yaml
stt:
  optimization:
    device: "cpu"
    compute_type: "int8"
    num_workers: 4
```

**Tips**:

- Use int8 quantization
- Enable multi-threading
- Use smaller models
- Close background apps

### 3. Audio Configuration

#### Sample Rate

**16kHz** (Recommended for speech)

- Lower processing overhead
- Sufficient for speech recognition
- Faster transmission

**22.05kHz** (For TTS output)

- Better audio quality
- Natural sound
- Standard for voice

**Configuration**:

```yaml
audio:
  input:
    sample_rate: 16000  # Lower for faster processing
  output:
    sample_rate: 22050  # Higher for better quality
```

#### Buffer Size

**Small buffers** (512-1024 samples)

- Lower latency
- More CPU overhead
- Risk of audio dropouts

**Large buffers** (2048-4096 samples)

- Higher latency
- Lower CPU overhead
- More stable

**Recommendation**: 1024 samples for input, 2048 for output

```yaml
audio:
  input:
    chunk_size: 1024
  output:
    buffer_size: 2048
```

### 4. Pipeline Optimization

#### Parallel Processing

Enable parallel pipeline processing:

```yaml
pipeline:
  processing:
    mode: "async"
    max_workers: 4
```

**Benefits**:

- Components run concurrently
- Reduced total latency
- Better CPU utilization

#### Streaming Mode

Enable streaming at all stages:

```yaml
stt:
  streaming: true
  partial_results: true

tts:
  streaming: true
  sentence_splitting: true
```

**Benefits**:

- Process data as it arrives
- Lower perceived latency
- Faster first response

#### Caching

Enable aggressive caching:

```yaml
response_generation:
  cache:
    enabled: true
    size: 2000  # Larger cache
    ttl: 7200   # 2 hour TTL
```

**Benefits**:

- Instant responses for common queries
- Reduced computation
- Lower latency

### 5. VAD Tuning

#### Aggressiveness Level

```yaml
vad:
  aggressiveness: 3  # 0-3
```

**Level 0**: Less aggressive

- More false positives
- Better for quiet speech
- Lower latency

**Level 3**: Most aggressive

- Fewer false positives
- Better for noisy environments
- Slightly higher latency

**Recommendation**: Use 3 for noisy environments, 2 for quiet.

#### Padding

```yaml
vad:
  padding_duration_ms: 300  # Audio before/after speech
  min_speech_duration_ms: 250  # Minimum to trigger
```

**Lower padding**:

- Faster speech detection
- Risk of cutting off speech
- Lower latency

**Higher padding**:

- More complete utterances
- Better recognition
- Slightly higher latency

### 6. Memory Optimization

#### Model Quantization

Use quantized models for lower memory:

```yaml
stt:
  optimization:
    compute_type: "int8"  # float32, float16, int8
```

**Memory Savings**:

- int8: ~75% reduction
- float16: ~50% reduction
- float32: No reduction (best quality)

#### Context Management

Limit conversation history:

```yaml
nlp:
  context_manager:
    max_history: 5  # Keep fewer turns
    context_timeout: 180  # Shorter timeout
```

## Profiling

### Built-in Profiling

Run the profiling script:

```bash
python scripts/profile_pipeline.py
```

Output:

```
Audio Processing:       8.23ms ( 4.1%)
VAD:                   3.45ms ( 1.7%)
Speech-to-Text:       67.89ms (33.9%)
NLP:                  12.34ms ( 6.2%)
Response Generation:  28.56ms (14.3%)
Text-to-Speech:       79.53ms (39.8%)
--------------------------------
TOTAL LATENCY:       200.00ms
```

### Python Profiling

Use cProfile for detailed profiling:

```bash
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats
```

### Memory Profiling

Use memory_profiler:

```bash
pip install memory_profiler
python -m memory_profiler main.py
```

## Benchmarking

### Latency Benchmark

```python
from src.pipeline import VoicePipeline
import time
import numpy as np

pipeline = VoicePipeline()
pipeline.initialize_components(stt_model="base.en")

# Generate test audio
audio = np.random.randn(16000).astype(np.float32)

# Measure latency
latencies = []
for _ in range(100):
    start = time.time()
    result = pipeline.stt.transcribe(audio)
    latency = (time.time() - start) * 1000
    latencies.append(latency)

print(f"Avg Latency: {np.mean(latencies):.2f}ms")
print(f"P50: {np.percentile(latencies, 50):.2f}ms")
print(f"P95: {np.percentile(latencies, 95):.2f}ms")
print(f"P99: {np.percentile(latencies, 99):.2f}ms")
```

### Throughput Benchmark

```python
import time

pipeline = VoicePipeline()
pipeline.initialize_components()

start_time = time.time()
utterances = 0

# Run for 60 seconds
while time.time() - start_time < 60:
    # Process utterance
    pipeline.stt.transcribe(audio)
    utterances += 1

throughput = utterances / 60
print(f"Throughput: {throughput:.2f} utterances/second")
```

## Performance Checklist

- [ ] Using appropriate model size for use case
- [ ] GPU acceleration enabled (if available)
- [ ] Audio buffer sizes optimized
- [ ] Streaming enabled at all stages
- [ ] Caching enabled
- [ ] VAD properly configured
- [ ] No unnecessary logging in production
- [ ] Background processes minimized
- [ ] System resources monitored
- [ ] Regular profiling performed

## Platform-Specific Tips

### Windows

- Use WASAPI audio backend
- Disable audio enhancements
- Set high process priority
- Close antivirus during benchmarking

### macOS

- Use CoreAudio backend
- Disable system sounds
- Grant microphone permissions
- Use Metal for GPU acceleration (if supported)

### Linux

- Use ALSA or PulseAudio
- Adjust audio buffer sizes in `/etc/pulse/daemon.conf`
- Use `nice` for process priority
- Enable CUDA if using NVIDIA GPU

## Troubleshooting Performance Issues

### High Latency

1. Check component latencies with profiler
2. Reduce model sizes
3. Enable GPU if available
4. Reduce buffer sizes
5. Disable unnecessary features

### Audio Dropouts

1. Increase buffer sizes
2. Reduce CPU usage
3. Close background apps
4. Check audio driver settings
5. Use wired connection (not Bluetooth)

### High Memory Usage

1. Use smaller models
2. Enable quantization
3. Reduce cache sizes
4. Limit context history
5. Clear caches periodically

### High CPU Usage

1. Use GPU acceleration
2. Reduce sample rate
3. Increase buffer sizes
4. Use simpler models
5. Limit concurrent processing

## Best Configurations

### Low-Latency Mode

```yaml
stt:
  model: "tiny.en"
  streaming: true
  
tts:
  engine: "pyttsx3"
  
audio:
  input:
    chunk_size: 512
  output:
    buffer_size: 1024
```

**Expected Latency**: 100-150ms

### Balanced Mode

```yaml
stt:
  model: "base.en"
  streaming: true
  
tts:
  engine: "piper"
  
audio:
  input:
    chunk_size: 1024
  output:
    buffer_size: 2048
```

**Expected Latency**: 150-250ms

### High-Quality Mode

```yaml
stt:
  model: "small.en"
  streaming: false
  
tts:
  engine: "coqui"
  
audio:
  input:
    chunk_size: 2048
  output:
    buffer_size: 4096
```

**Expected Latency**: 300-500ms

## Monitoring in Production

### Metrics to Track

- Average latency (total and per-component)
- P95 and P99 latency
- Throughput (utterances/minute)
- Error rate
- Cache hit rate
- CPU/Memory usage
- GPU utilization

### Alerting Thresholds

- Total latency > 500ms
- Error rate > 5%
- CPU usage > 80%
- Memory usage > 90%
- Queue sizes > threshold

## Conclusion

Performance optimization is an ongoing process. Regular profiling, monitoring, and tuning are
essential for maintaining optimal performance in production environments.
