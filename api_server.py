"""
Real-Time Voice Assistant API Server
WebSocket-based API for voice interaction
"""

import asyncio
import json
import numpy as np
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.pipeline import VoicePipeline, PipelineConfig


# Create FastAPI app
app = FastAPI(
    title="Real-Time Voice Assistant API",
    description="Zero-latency voice interface API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active pipelines
active_pipelines: Dict[str, VoicePipeline] = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Real-Time Voice Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(active_pipelines)
    }


@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "stt_models": ["tiny.en", "base.en", "small.en", "medium.en"],
        "tts_engines": ["pyttsx3", "coqui"],
        "languages": ["en", "es", "fr", "de", "it"]
    }


@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """WebSocket endpoint for voice interaction"""
    await websocket.accept()
    session_id = f"session_{id(websocket)}"
    
    logger.info(f"WebSocket connection established: {session_id}")
    
    try:
        # Initialize pipeline
        config = PipelineConfig(
            sample_rate=16000,
            chunk_size=1024,
            enable_vad=True,
            enable_streaming=True
        )
        
        pipeline = VoicePipeline(config=config)
        active_pipelines[session_id] = pipeline
        
        # Setup callbacks
        async def send_transcription(text: str):
            await websocket.send_json({
                "type": "transcription",
                "text": text
            })
        
        async def send_response(response):
            await websocket.send_json({
                "type": "response",
                "text": response.text,
                "intent": response.intent,
                "confidence": response.confidence
            })
        
        pipeline.on_transcription = lambda text: asyncio.create_task(send_transcription(text))
        pipeline.on_response = lambda response: asyncio.create_task(send_response(response))
        
        # Initialize and start pipeline
        pipeline.initialize_components()
        
        # Send ready message
        await websocket.send_json({
            "type": "ready",
            "session_id": session_id
        })
        
        # Handle messages
        while True:
            data = await websocket.receive()
            
            if "text" in data:
                # Text message
                message = json.loads(data["text"])
                
                if message.get("type") == "config":
                    # Configuration message
                    logger.info(f"Received config: {message}")
                    
                elif message.get("type") == "command":
                    # Command message
                    command = message.get("command")
                    
                    if command == "start":
                        pipeline.start()
                        await websocket.send_json({"type": "status", "status": "started"})
                        
                    elif command == "stop":
                        pipeline.stop()
                        await websocket.send_json({"type": "status", "status": "stopped"})
                        
                    elif command == "metrics":
                        metrics = pipeline.get_metrics()
                        await websocket.send_json({
                            "type": "metrics",
                            "data": metrics
                        })
            
            elif "bytes" in data:
                # Audio data
                audio_bytes = data["bytes"]
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                
                # Process audio (would add to pipeline)
                logger.debug(f"Received audio: {len(audio_array)} samples")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        if session_id in active_pipelines:
            pipeline = active_pipelines[session_id]
            pipeline.stop()
            del active_pipelines[session_id]
        
        logger.info(f"WebSocket connection closed: {session_id}")


@app.post("/api/transcribe")
async def transcribe_audio(audio_data: Dict[str, Any]):
    """Transcribe audio data"""
    # This would process audio and return transcription
    return {
        "transcription": "Example transcription",
        "confidence": 0.95
    }


@app.post("/api/synthesize")
async def synthesize_speech(text_data: Dict[str, Any]):
    """Synthesize speech from text"""
    text = text_data.get("text", "")
    
    # This would generate audio
    return {
        "status": "success",
        "audio_length": 0
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Real-Time Voice Assistant API Server...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
