from typing import Optional
from fastapi import FastAPI, HTTPException
import requests
import logging

from src.data_processing.data_pipeline import download_pipeline_youtube

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO) # default=INFO (DEBUG, INFO, WARNING, ERROR, CRITICAL)

app = FastAPI()

# placeholder
@app.get("/")
def read_root():
    return {"Hello": "World"}

# placeholder
@app.get("/model")
def model():
    pass

# placeholder
@app.post("/chat")
def chat():
    pass

# placeholder
@app.get("/chathistory")
def chat_history():
    pass

@app.post("/analyze")
def analyze(video_input: str, chunk_max_length: Optional[int] = 550, chunk_overlap_length: Optional[int] = 50, embedding_model: Optional[str] = "nomic-embed-text"):

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
