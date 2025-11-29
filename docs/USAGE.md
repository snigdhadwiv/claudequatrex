# Usage Guide

## Installation

### Prerequisites

- Python 3.9 or higher
- Microphone and speakers
- (Optional) CUDA-capable GPU for better performance

### Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd real-time-voice-assistant
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Download models**

```bash
python scripts/download_models.py
```

5. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your preferences
```

## Quick Start

### General Voice Assistant

```bash
python main.py
```

This starts the general-purpose voice assistant. Simply speak into your microphone and the assistant
will respond.

### Language Learning Mode

```bash
python main.py --mode language-learning --language spanish --level intermediate
```

Available languages:

- spanish
- french
- german
- italian
- portuguese

Available levels:

- beginner
- intermediate
- advanced

## Configuration

### Config File

Edit `config/config.yaml` to customize:

```yaml
audio:
  input:
    sample_rate: 16000
    channels: 1
    chunk_size: 1024

stt:
  model: "base.en"
  streaming: true

tts:
  engine: "pyttsx3"
  voice_speed: 1.0
```

### Command Line Options

```bash
python main.py --help
```

Options:

- `--mode`: Application mode (general, language-learning)
- `--language`: Target language
- `--level`: Proficiency level
- `--config`: Config file path
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--stt-model`: Speech recognition model
- `--tts-engine`: Text-to-speech engine

## Usage Examples

### Example 1: Basic Conversation

```bash
python main.py
```

```
[YOU]: Hello, how are you?
[ASSISTANT]: I'm doing well, thank you! How can I help you today?

[YOU]: What's the weather like?
[ASSISTANT]: I don't have access to weather information, but I can help you with other things!
```

### Example 2: Spanish Practice

```bash
python main.py --mode language-learning --language spanish
```

```
[ASSISTANT]: ¡Hola! Bienvenido a tu clase de español. ¿Qué te gustaría practicar hoy?

[YOU]: I want to practice ordering food
[ASSISTANT]: ¡Perfecto! Welcome to our restaurant. What would you like to order?

[YOU]: Me gustaría una pizza, por favor
[ASSISTANT]: Excelente! ¿Algo para beber?
```

### Example 3: Custom Configuration

```bash
python main.py \
  --config my_config.yaml \
  --stt-model small.en \
  --tts-engine coqui \
  --log-level DEBUG
```

## API Server

### Start Server

```bash
python api_server.py
```

The server starts on `http://localhost:8000`

### API Endpoints

#### GET /health

Health check endpoint

```bash
curl http://localhost:8000/health
```

#### GET /models

List available models

```bash
curl http://localhost:8000/models
```

#### WebSocket /ws/voice

WebSocket endpoint for real-time voice interaction

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/voice');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'command',
    command: 'start'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## Testing

### Run Tests

```bash
pytest tests/
```

### Test Audio System

```bash
python scripts/test_audio.py
```

This will:

1. List available audio devices
2. Test microphone recording
3. Test speaker playback

### Profile Pipeline

```bash
python scripts/profile_pipeline.py
```

This profiles each component and reports latency metrics.

## Troubleshooting

### Audio Issues

**Problem**: No audio input detected

**Solutions**:

1. Check microphone permissions
2. Verify correct input device: `python scripts/test_audio.py`
3. Adjust audio settings in config
4. Try different sample rate

**Problem**: Audio playback fails

**Solutions**:

1. Check speaker settings
2. Verify output device
3. Try different audio backend
4. Update audio drivers

### Performance Issues

**Problem**: High latency

**Solutions**:

1. Use smaller STT model (tiny, base)
2. Reduce buffer sizes
3. Enable GPU acceleration
4. Disable unnecessary features
5. Profile pipeline: `python scripts/profile_pipeline.py`

**Problem**: High CPU usage

**Solutions**:

1. Use lighter models
2. Reduce sample rate
3. Disable streaming if not needed
4. Limit max workers

### Model Issues

**Problem**: Model not found

**Solutions**:

1. Run: `python scripts/download_models.py`
2. Check models/ directory
3. Verify model name in config

**Problem**: Out of memory

**Solutions**:

1. Use smaller model (tiny, base)
2. Reduce batch size
3. Enable int8 quantization
4. Close other applications

### Recognition Issues

**Problem**: Poor transcription accuracy

**Solutions**:

1. Use larger model (small, medium)
2. Improve audio quality (better mic)
3. Reduce background noise
4. Adjust VAD aggressiveness
5. Speak more clearly

**Problem**: Language not recognized

**Solutions**:

1. Verify language code in config
2. Use language-specific model
3. Check supported languages

## Best Practices

### For Best Performance

1. **Use appropriate model size**
    - Development: tiny, base
    - Production: small, medium
    - High accuracy: large

2. **Optimize buffer sizes**
    - Smaller = lower latency
    - Larger = better accuracy
    - Balance based on needs

3. **Enable GPU if available**
    - 2-5x faster processing
    - Lower latency
    - Better for real-time

4. **Use streaming mode**
    - Enables partial results
    - Lower perceived latency
    - Better user experience

### For Best Accuracy

1. **Use quality audio equipment**
    - Good microphone
    - Quiet environment
    - Proper positioning

2. **Configure VAD properly**
    - Higher aggressiveness for noisy environments
    - Lower for clean audio
    - Test different settings

3. **Use larger models when possible**
    - Better accuracy
    - More robust
    - Trade-off with latency

## Advanced Usage

### Custom Application

```python
from src.pipeline import VoicePipeline, PipelineConfig

# Create custom config
config = PipelineConfig(
    sample_rate=16000,
    enable_vad=True,
    max_latency_ms=150
)

# Initialize pipeline
pipeline = VoicePipeline(config=config)

# Setup callbacks
pipeline.on_transcription = lambda text: print(f"Heard: {text}")
pipeline.on_response = lambda resp: print(f"Response: {resp.text}")

# Initialize and start
pipeline.initialize_components()
pipeline.start()

# Your application logic here
# ...

# Stop when done
pipeline.stop()
```

### Custom Intent Handler

```python
from src.nlp import IntentClassifier

classifier = IntentClassifier()

# Add custom patterns
classifier.intents["custom_intent"] = {
    "patterns": [r"\bcustom pattern\b"],
    "responses": ["custom"]
}

# Classify
intent = classifier.classify("This is a custom pattern")
```

### Custom Response Templates

Edit `config/response_templates.json`:

```json
{
  "custom_category": {
    "custom_intent": [
      "Custom response 1",
      "Custom response 2",
      "Custom response 3"
    ]
  }
}
```

## Getting Help

- Check documentation in `docs/`
- Review examples in `examples/`
- Check logs in `logs/`
- Open an issue on GitHub
- Join our community chat
