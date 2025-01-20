from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
import requests
import logging
from pydantic import BaseModel

from src.data_processing.data_pipeline import download_pipeline_youtube
from src.rag.app import chat_internal, models_internal, collections_internal

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO) # default=INFO (DEBUG, INFO, WARNING, ERROR, CRITICAL)

app = FastAPI()

# placeholder
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/model")
def model():
    models = models_internal()
    return JSONResponse(content=models, status_code=200)

@app.get("/collection")
def collection():
    collections = collections_internal()
    return JSONResponse(content=collections, status_code=200)

class ChatRequest(BaseModel):
    prompt: str
    message_history: Optional[List[Dict[str, str]]] = None
    model_id: Optional[str] = None
    database: Optional[str] = None
    model_parameters: Optional[Dict[str, float]] = None
    playlist_id: Optional[str] = None
    video_id: Optional[str] = None
    knowledge_base: Optional[str] = None
    stream: Optional[bool] = True
    plaintext: Optional[bool] = False
    mode: Optional[str] = None
    use_logical_routing: Optional[bool] = None
    use_semantic_routing: Optional[bool] = None


class AnalyzeRequest(BaseModel):
    video_input: str
    chunk_max_length: Optional[int] = 550
    chunk_overlap_length: Optional[int] = 50
    embedding_model: Optional[str] = "nomic-embed-text"
    seconds_between_frames: Optional[int] = 30
    local_model: Optional[bool] = False
    enabled_detailed_chunking: Optional[bool] = False


@app.post("/chat", response_class=StreamingResponse)
def chat(request: ChatRequest):
    use_stream = request.stream
    if use_stream is None:
        use_stream = True

    use_plaintext = request.plaintext
    if use_plaintext is None:
        use_plaintext = False

    if use_stream is False:
        response = chat_internal(
            prompt=request.prompt,
            message_history=request.message_history,
            model_id=request.model_id,
            database=request.database,
            model_parameters=request.model_parameters,
            playlist_id=request.playlist_id,
            video_id=request.video_id,
            knowledge_base=request.knowledge_base,
            stream=request.stream,
            plaintext=request.plaintext,
            mode=request.mode,
            use_logical_routing=request.use_logical_routing,
            use_semantic_routing=request.use_semantic_routing
        )

        if use_plaintext:
            return PlainTextResponse(content=response, status_code=200)
        else:
            return JSONResponse(content=response, status_code=200)
    else:
        return StreamingResponse(
            content=chat_internal(
                prompt=request.prompt,
                message_history=request.message_history,
                model_id=request.model_id,
                database=request.database,
                model_parameters=request.model_parameters,
                playlist_id=request.playlist_id,
                video_id=request.video_id,
                knowledge_base=request.knowledge_base,
                stream=request.stream,
                plaintext=request.plaintext,
                mode=request.mode,
                use_logical_routing=request.use_logical_routing,
                use_semantic_routing=request.use_semantic_routing
            ),
            media_type="text/event-stream",
            status_code=200
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
    seconds_between_frames = request.seconds_between_frames
    local_model  = request.local_model
    enabled_detailed_chunking = request.enabled_detailed_chunking
    

    logging.info(f"Video {video_input}")
    # Check if the passed URL is a valid YouTube URL.
    # url = "https://www.youtube.com/oembed?format=json&url=" + video_input # ! Deprecated
    response = requests.head(video_input, allow_redirects=True)
    if response.status_code in range(200, 300) and "youtube" in video_input:
        # Valid YouTube URL
        status_code, status_message = download_pipeline_youtube(video_input, chunk_max_length, chunk_overlap_length, seconds_between_frames, local_model, enabled_detailed_chunking)
        if status_code in range(200, 300):
            # Pre-Processing was successfull
            return {"message": status_message, "status_code": status_code}
        else:
            # Pre-Processing failed
            raise HTTPException(status_code=status_code, detail=f"YouTube content could not be processed: {status_message}")
    else:
        # No valid YouTube URL
        logging.warning(f"YouTube URL does not exist: Status code = {response.status_code}")
        raise HTTPException(status_code=404, detail=f"YouTube content could not be processed: This is not a valid YouTube URL.")

# placeholder
@app.get("/support")
def support():
    pass
