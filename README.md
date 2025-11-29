# Real-Time Voice Assistant

A zero-latency voice assistant implementation using edge computing and optimized voice processing
pipelines to achieve instantaneous, human-like conversational experiences.

## Overview

This project addresses the critical challenge of latency in cloud-based voice assistants by
implementing a local, edge-optimized voice pipeline that reduces end-to-end latency from typical
1500ms to under 200ms.

## Key Features

- **Zero-Latency Processing**: End-to-end latency under 200ms
- **Streaming Pipeline**: All components process audio streams in real-time
- **Edge Computing**: Local processing with optional cloud fallback
- **Natural Conversations**: Seamless turn-taking and interrupt handling
- **Offline Capable**: Full functionality without internet connection
- **Language Learning**: Specialized application for language practice

## Architecture

```
Audio Input → VAD → STT (Streaming) → NLP → Response Gen → TTS (Streaming) → Audio Output
     ↓                                                                              ↑
     └──────────────────────── Feedback Loop ───────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.9 or higher
- CUDA-capable GPU (optional, for better performance)
- Microphone and speakers/headphones

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd real-time-voice-assistant
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Download models:

```bash
python scripts/download_models.py
```

5. Configure environment:

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Quick Start

### Basic Voice Assistant

```bash
python main.py
```

### Language Practice Partner

```bash
python main.py --mode language-learning --language spanish
```

### API Server

```bash
python api_server.py
```

## Project Structure

```
real-time-voice-assistant/
├── src/
│   ├── audio/              # Audio input/output handling
│   ├── vad/                # Voice Activity Detection
│   ├── stt/                # Speech-to-Text engine
│   ├── nlp/                # Natural Language Processing
│   ├── response/           # Response generation
│   ├── tts/                # Text-to-Speech synthesis
│   ├── pipeline/           # Real-time processing pipeline
│   └── applications/       # Practical applications
├── models/                 # Pre-trained models
├── config/                 # Configuration files
├── tests/                  # Unit and integration tests
├── scripts/                # Utility scripts
├── docs/                   # Documentation
├── main.py                 # Main application entry
├── api_server.py          # API server
└── requirements.txt        # Python dependencies
```

## Configuration

Edit `config/config.yaml` to customize:

- Audio settings (sample rate, channels, buffer size)
- Model selections (STT, TTS, NLP)
- Latency optimization parameters
- Application-specific settings

## Performance

- **End-to-End Latency**: < 200ms (typical)
- **STT Latency**: < 50ms (streaming)
- **NLP Processing**: < 30ms
- **TTS Latency**: < 80ms (streaming start)
- **Turn-Taking**: < 100ms response initiation

## Use Cases

### 1. Language Practice Partner

Real-time conversation practice with instant feedback on pronunciation, grammar, and vocabulary.

### 2. Voice-Controlled Assistant

Hands-free control for multitasking professionals with instant command execution.

### 3. Accessibility Tool

Low-latency voice interface for users requiring assistive technology.

### 4. Interview Preparation

Practice interviews with realistic timing and immediate feedback.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
```

### Profiling

```bash
python scripts/profile_pipeline.py
```

## Technical Details

### Speech Recognition

- **Primary**: Faster Whisper (optimized Whisper model)
- **Fallback**: Lightweight on-device models
- **VAD**: WebRTC VAD for instant speech detection

### Natural Language Processing

- **Intent Classification**: Fine-tuned BERT variants
- **Entity Extraction**: SpaCy + custom models
- **Context Management**: Conversation state tracking

### Text-to-Speech

- **Primary**: Piper TTS (fast neural TTS)
- **Fallback**: pyttsx3 (offline TTS)
- **Streaming**: Sentence-level synthesis with immediate playback

### Optimization Techniques

- Concurrent processing pipelines
- Predictive response preparation
- Audio buffering and streaming
- Model quantization and pruning
- Caching layer for common queries

## Troubleshooting

### High Latency

- Check CPU/GPU usage
- Reduce buffer sizes in config
- Use smaller models
- Disable unnecessary features

### Audio Issues

- Verify microphone permissions
- Check audio device settings
- Adjust sample rate and channels
- Test with different audio backends

### Model Loading Errors

- Ensure models are downloaded
- Check available disk space
- Verify model compatibility

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- RunAnywhere Voice Pipeline team
- OpenAI Whisper project
- Piper TTS contributors
- Open-source NLP community

## Citation

If you use this project in your research, please cite:

```bibtex
@software{realtime_voice_assistant,
  title={Real-Time Voice Assistant: Zero-Latency Voice Interface},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/real-time-voice-assistant}
}
```

## Contact

For questions and support, please open an issue on GitHub or contact [your-email@example.com]

## Roadmap

- [ ] Multi-language support with code-switching
- [ ] Emotion detection and empathetic responses
- [ ] Mobile app (iOS/Android)
- [ ] Browser extension
- [ ] Voice cloning for personalization
- [ ] Advanced analytics dashboard
