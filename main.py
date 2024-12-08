from fastapi import FastAPI
import requests

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
    print(response.status_code)

# placeholder
@app.get("/support")
def support():
    pass
