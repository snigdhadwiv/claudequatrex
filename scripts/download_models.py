"""
Download and setup required models for the voice assistant
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def download_whisper_models():
    """Download Whisper models"""
    logger.info("Downloading Whisper models...")
    
    try:
        import whisper
        
        models = ["tiny.en", "base.en", "small.en"]
        
        for model_name in models:
            logger.info(f"Downloading {model_name}...")
            whisper.load_model(model_name)
            logger.info(f"✓ {model_name} downloaded")
        
        logger.info("Whisper models downloaded successfully")
        
    except ImportError:
        logger.warning("Whisper not installed, skipping")
    except Exception as e:
        logger.error(f"Error downloading Whisper models: {e}")


def download_spacy_models():
    """Download spaCy models"""
    logger.info("Downloading spaCy models...")
    
    try:
        import subprocess
        
        models = ["en_core_web_sm", "es_core_news_sm"]
        
        for model_name in models:
            logger.info(f"Downloading {model_name}...")
            subprocess.run([sys.executable, "-m", "spacy", "download", model_name], 
                         check=True, capture_output=True)
            logger.info(f"✓ {model_name} downloaded")
        
        logger.info("spaCy models downloaded successfully")
        
    except ImportError:
        logger.warning("spaCy not installed, skipping")
    except Exception as e:
        logger.error(f"Error downloading spaCy models: {e}")


def setup_directories():
    """Create necessary directories"""
    logger.info("Setting up directories...")
    
    directories = [
        "models",
        "logs",
        "data",
        "cache"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"✓ Created directory: {directory}")


def main():
    """Main setup function"""
    logger.info("Starting model download and setup...")
    
    print("\n" + "="*60)
    print("  Real-Time Voice Assistant - Model Setup")
    print("="*60 + "\n")
    
    # Setup directories
    setup_directories()
    
    # Download models
    download_whisper_models()
    download_spacy_models()
    
    print("\n" + "="*60)
    print("  Setup complete!")
    print("="*60 + "\n")
    
    logger.info("All models downloaded and setup complete")


if __name__ == "__main__":
    main()
