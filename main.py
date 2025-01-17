from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import requests
import logging
from pydantic import BaseModel

from src.data_processing.data_pipeline import download_pipeline_youtube
from src.rag.app import chat_internal, models_internal

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO) # default=INFO (DEBUG, INFO, WARNING, ERROR, CRITICAL)

app = FastAPI()

# placeholder
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/model")
def model():
    return {
        "models": models_internal(),
        "status_code": 200
    }

class ChatRequest(BaseModel):
    prompt: str
    message_history: Optional[List[Dict[str, str]]] = None
    model_id: Optional[str] = None
    database: Optional[str] = None
    model_parameters: Optional[Dict[str, float]] = None
    playlist_id: Optional[str] = None
    video_id: Optional[str] = None
    knowledge_base: Optional[str] = None


class AnalyzeRequest(BaseModel):
    video_input: str
    chunk_max_length: Optional[int] = 550
    chunk_overlap_length: Optional[int] = 50
    embedding_model: Optional[str] = "nomic-embed-text"


@app.post("/chat", response_class=StreamingResponse)
def chat(request: ChatRequest):
    return StreamingResponse(
        chat_internal(
            prompt=request.prompt,
            message_history=request.message_history,
            model_id=request.model_id,
            database=request.database,
            model_parameters=request.model_parameters,
            playlist_id=request.playlist_id,
            video_id=request.video_id,
            knowledge_base=request.knowledge_base
        ),
        media_type="text/event-stream"
    )

# placeholder
@app.get("/chathistory")
def chat_history():
    pass

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    video_input = request.video_input
    chunk_max_length = request.chunk_max_length
    chunk_overlap_length = request.chunk_overlap_length
    embedding_model = request.embedding_model
    

    logging.info(f"Video {video_input}")
    # Check if the passed URL is a valid YouTube URL.
    url = "https://www.youtube.com/oembed?format=json&url=" + video_input
    response = requests.head(url, allow_redirects=True)
    if response.status_code in range(200, 300):
        # Valid YouTube URL
        status_code, status_message = download_pipeline_youtube(video_input, chunk_max_length, chunk_overlap_length, embedding_model)
        if status_code in range(200, 300):
            # Pre-Processing was successfull
            return {"message": status_message, "status_code": status_code}
        else:
            # Pre-Processing failed
            raise HTTPException(status_code=status_code, detail=f"YouTube content could not be processed: {status_message}")
    else:
        # No valid YouTube URL
        logging.error(f"YouTube URL does not exist: {response.status_code}")
        raise HTTPException(status_code=404, detail=f"YouTube content could not be processed: YouTube URL does not exist.")

# placeholder
@app.get("/support")
def support():
    pass
