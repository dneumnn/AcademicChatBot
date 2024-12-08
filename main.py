from fastapi import FastAPI

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

# placeholder
@app.post("/analyze")
def analyze():
    pass

# placeholder
@app.get("/support")
def support():
    pass
