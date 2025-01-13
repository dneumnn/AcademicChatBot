from typing import List
import requests

def get_available_models():
    return get_local_llama_models() + get_openai_models() + get_gemini_models()

def get_local_llama_models() -> List[str]:
    """
    Query local Llama server for available models
   
    Returns:
        List[str]: List of available model IDs
   
    Raises:
        ConnectionError: If can't connect to Llama server
    """
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = [model["name"] for model in response.json()["models"]]
            return models
        return []
    except requests.exceptions.RequestException:
        raise ConnectionError("Cannot connect to local Llama server")
    
def get_openai_models():
    return ["gpt-4o"]

def get_gemini_models():
    return ["gemini-1.5-flash"]