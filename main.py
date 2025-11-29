"""
Real-Time Voice Assistant - Main Application
Zero-latency voice interface implementation
"""

import argparse
import sys
import time
import yaml
from pathlib import Path
from loguru import logger

from src.pipeline import VoicePipeline, PipelineConfig
from src.applications.language_learning import LanguageLearningApp


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level
    )
    logger.add(
        "logs/voice_assistant.log",
        rotation="1 day",
        retention="7 days",
        level=log_level
    )


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return {}
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded configuration from {config_path}")
    return config


def run_general_assistant(config: dict) -> None:
    """Run general voice assistant mode"""
    logger.info("Starting General Voice Assistant")
    
    # Create pipeline configuration
    pipeline_config = PipelineConfig(
        sample_rate=config.get('audio', {}).get('input', {}).get('sample_rate', 16000),
        chunk_size=config.get('audio', {}).get('input', {}).get('chunk_size', 1024),
        enable_vad=config.get('vad', {}).get('enabled', True),
        enable_streaming=config.get('stt', {}).get('streaming', True),
        max_latency_ms=config.get('pipeline', {}).get('processing', {}).get('max_latency_ms', 200),
        enable_interruption=config.get('pipeline', {}).get('interruption', {}).get('enabled', True)
    )
    
    # Initialize pipeline
    pipeline = VoicePipeline(config=pipeline_config)
    
    # Setup callbacks
    def on_transcription(text: str):
        logger.info(f"[USER]: {text}")
    
    def on_response(response):
        logger.info(f"[ASSISTANT]: {response.text}")
    
    pipeline.on_transcription = on_transcription
    pipeline.on_response = on_response
    
    # Initialize components
    stt_model = config.get('stt', {}).get('model', 'base.en')
    tts_engine = config.get('tts', {}).get('engine', 'pyttsx3')
    
    pipeline.initialize_components(
        stt_model=stt_model,
        tts_engine=tts_engine,
        language="en"
    )
    
    # Start pipeline
    pipeline.start()
    
    logger.info("Voice assistant is ready. Start speaking...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
            
            # Print metrics every 30 seconds
            if int(time.time()) % 30 == 0:
                metrics = pipeline.get_metrics()
                logger.info(f"Metrics: {metrics}")
                
    except KeyboardInterrupt:
        logger.info("Stopping voice assistant...")
    finally:
        pipeline.stop()
        logger.info("Voice assistant stopped")


def run_language_learning(config: dict, language: str, level: str) -> None:
    """Run language learning mode"""
    logger.info(f"Starting Language Learning Assistant - {language} ({level})")
    
    # Create language learning application
    app = LanguageLearningApp(
        target_language=language,
        proficiency_level=level,
        config=config
    )
    
    # Initialize and run
    app.initialize()
    app.run()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Real-Time Voice Assistant - Zero-latency voice interface"
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        default='general',
        choices=['general', 'language-learning', 'interview-prep'],
        help='Application mode'
    )
    
    parser.add_argument(
        '--language',
        type=str,
        default='spanish',
        help='Target language for learning mode'
    )
    
    parser.add_argument(
        '--level',
        type=str,
        default='intermediate',
        choices=['beginner', 'intermediate', 'advanced'],
        help='Proficiency level for learning mode'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Configuration file path'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    parser.add_argument(
        '--stt-model',
        type=str,
        default='base.en',
        help='Speech recognition model'
    )
    
    parser.add_argument(
        '--tts-engine',
        type=str,
        default='pyttsx3',
        choices=['pyttsx3', 'coqui', 'piper'],
        help='Text-to-speech engine'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command line arguments
    if args.stt_model:
        config.setdefault('stt', {})['model'] = args.stt_model
    if args.tts_engine:
        config.setdefault('tts', {})['engine'] = args.tts_engine
    
    # Display banner
    print("\n" + "="*60)
    print("  Real-Time Voice Assistant")
    print("  Zero-Latency Voice Interface")
    print("="*60 + "\n")
    
    # Run application based on mode
    try:
        if args.mode == 'general':
            run_general_assistant(config)
        elif args.mode == 'language-learning':
            run_language_learning(config, args.language, args.level)
        elif args.mode == 'interview-prep':
            logger.error("Interview prep mode not yet implemented")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
