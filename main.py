from fastapi import FastAPI
import requests
from src.data_processing.app import download_pipeline_youtube

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
    if(response.status_code in range(200, 300)):
        download_pipeline_youtube(video_input)
    else:
        print(f"error: {response.status_code}")

# placeholder
@app.get("/support")
def support():
    pass
