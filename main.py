from fastapi import FastAPI, HTTPException
import requests
import logging

from src.data_processing.app import download_pipeline_youtube

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
def analyze(video_input: str):
    url = "https://www.youtube.com/oembed?format=json&url=" + video_input
    response = requests.head(url, allow_redirects=True)
    if response.status_code in range(200, 300):
        status_code = download_pipeline_youtube(video_input)
        if status_code in range(200, 300):
            return {"message": "YouTube content processed successfully", "status_code": status_code}
        else:
            raise HTTPException(status_code=status_code, detail=f"YouTube content could not be processed")
    else:
        logging.error(f"YouTube URL does not exist: {response.status_code}")
        raise HTTPException(status_code=404, detail=f"YouTube URL does not exist")

# placeholder
@app.get("/support")
def support():
    pass
