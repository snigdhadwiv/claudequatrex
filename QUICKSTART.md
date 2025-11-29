# Quick Start Guide

Get up and running with the Real-Time Voice Assistant in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Microphone and speakers/headphones
- Windows/macOS/Linux

## Installation

### 1. Clone and Setup

```bash
# Clone the repository (or extract the zip)
cd real-time-voice-assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all necessary packages including:

- Audio processing libraries
- Speech recognition (Whisper)
- Text-to-speech engines
- NLP tools
- API server components

### 3. Download Models (Optional but Recommended)

```bash
python scripts/download_models.py
```

This downloads optimized speech recognition models for better performance.

### 4. Test Your Audio Setup

```bash
python scripts/test_audio.py
```

This will:

- List available audio devices
- Test microphone recording
- Test speaker playback

Make sure you hear the test tone and see audio levels when speaking.

## First Run

### General Voice Assistant

```bash
python main.py
```

**What happens:**

1. Application starts and loads models (may take 10-30 seconds first time)
2. You'll see: "Voice assistant is ready. Start speaking..."
3. Speak into your microphone
4. The assistant will transcribe and respond

**Example conversation:**

```
[YOU]: Hello, how are you?
[ASSISTANT]: I'm doing well, thank you! How can I help you today?

[YOU]: What can you do?
[ASSISTANT]: I can help you with various tasks. What would you like to try?
```

Press `Ctrl+C` to stop.

### Language Learning Mode

```bash
python main.py --mode language-learning --language spanish
```

**What happens:**

1. Starts in Spanish practice mode
2. Assistant greets you in Spanish
3. Practice conversations in Spanish
4. Get real-time feedback

**Example:**

```
[ASSISTANT]: ¡Hola! Bienvenido a tu clase de español. ¿Qué te gustaría practicar hoy?

[YOU]: Hello
[ASSISTANT]: ¡Hola! ¿Cómo estás?

[YOU]: Bien, gracias
[ASSISTANT]: ¡Excelente! You're doing great!
```

## Configuration

### Quick Settings

Edit `.env` file (copy from `.env.example`):

```bash
# Basic settings
LOG_LEVEL=INFO
WHISPER_MODEL=base.en
TTS_ENGINE=pyttsx3

# Performance
USE_GPU=True
ENABLE_STREAMING=True
```

### Advanced Configuration

Edit `config/config.yaml` for detailed control:

```yaml
# Faster response (lower accuracy)
stt:
  model: "tiny.en"

# Better accuracy (slower response)  
stt:
  model: "small.en"

# Adjust latency target
pipeline:
  processing:
    max_latency_ms: 200
```

## Common Commands

### Run with specific model

```bash
python main.py --stt-model small.en
```

### Run with debug logging

```bash
python main.py --log-level DEBUG
```

### Run API server

```bash
python api_server.py
```

Then visit http://localhost:8000/docs for API documentation.

### Profile performance

```bash
python scripts/profile_pipeline.py
```

## Troubleshooting

### No audio input detected

```bash
# List audio devices
python scripts/test_audio.py

# Or run with specific device
python main.py  # Check logs for device index
```

### ImportError: No module named 'X'

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### High latency / Slow responses

```bash
# Use smaller model
python main.py --stt-model tiny.en

# Or edit config to use GPU if available
```

### "Model not found" error

```bash
# Download models
python scripts/download_models.py
```

## Next Steps

### Learn More

- Read [README.md](README.md) for full overview
- Check [docs/USAGE.md](docs/USAGE.md) for detailed usage
- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical details
- Review [PROJECT_REPORT.md](PROJECT_REPORT.md) for comprehensive information

### Customize

- Add custom intents in `src/nlp/intent_classifier.py`
- Add response templates in `config/response_templates.json`
- Create custom applications in `src/applications/`

### Optimize

- Read [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for optimization tips
- Profile your setup: `python scripts/profile_pipeline.py`
- Adjust configuration based on your hardware

### Contribute

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
- Report issues on GitHub
- Submit pull requests with improvements

## Tips for Best Experience

1. **Use a good microphone** - Built-in laptop mics work but external mics are better
2. **Quiet environment** - Less background noise = better recognition
3. **Speak clearly** - Natural pace, clear enunciation
4. **Be patient first run** - Initial model loading takes time
5. **Check audio levels** - Not too loud, not too quiet
6. **Use headphones** - Prevents echo/feedback issues
7. **Start simple** - Try basic commands before complex conversations
8. **Experiment** - Try different models and settings to find what works best

## Support

- 📖 Documentation: `docs/` folder
- 🐛 Issues: GitHub Issues (if available)
- 💬 Questions: See README for contact info
- 📧 Email: Check README for maintainer contact

## Success Indicators

✅ You should see:

- Models loading successfully
- "Voice assistant is ready" message
- Transcriptions appearing as you speak
- Responses within 1-2 seconds
- Natural conversation flow

⚠️ If you don't see these, check:

- Audio device permissions
- Microphone is working
- Dependencies installed correctly
- Configuration is valid
- Check logs for errors

## Minimal Example

Want the absolute simplest code to get started?

```python
from src.pipeline import VoicePipeline

# Create and start pipeline
pipeline = VoicePipeline()
pipeline.initialize_components()
pipeline.start()

print("Speak into your microphone...")

# Pipeline runs in background
# Press Ctrl+C when done
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pipeline.stop()
```

Save as `simple.py` and run: `python simple.py`

---

**Ready to go?** 🚀

```bash
python main.py
```

Start speaking and enjoy real-time voice interaction!
