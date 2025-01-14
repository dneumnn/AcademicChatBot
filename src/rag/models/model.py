from typing import List
import requests
from openai import OpenAI
import google.generativeai as gemini

from ..constants.env import GEMINI_API_KEY, OPENAI_API_KEY

def get_available_models():
    return get_local_ollama_models() + get_openai_models() + get_gemini_models()

def get_local_ollama_models() -> List[str]:
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
            models = [model["name"].replace(":latest", "") for model in response.json()["models"]]
            return models
        return []
    except Exception as e:
        print(f"Error getting local ollama models: {e}")
        return []
    
def get_openai_models():
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        return [model.id for model in client.models.list()]
    except Exception as e:
        print(f"Error getting OpenAI models: {e}")
        return []

def get_gemini_models():
    try:
        gemini.configure(api_key=GEMINI_API_KEY)
        return [model.name.replace("models/", "") for model in gemini.list_models()]
    except Exception as e:
        print(f"Error getting Gemini models: {e}")
        return []