from typing import List
import requests
from openai import OpenAI
import google.generativeai as gemini

from ..constants.env import GEMINI_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY

ollama_cache = []
openai_cache = []
gemini_cache = []
deepseek_cache = []

def get_available_models():
    return get_local_ollama_models() + get_openai_models() + get_gemini_models() + get_deepseek_models()

def get_local_ollama_models() -> List[str]:
    """
    Query local Llama server for available models
   
    Returns:
        List[str]: List of available model IDs
   
    Raises:
        ConnectionError: If can't connect to Llama server
    """
    global ollama_cache

    if ollama_cache and len(ollama_cache) > 0:
        return ollama_cache
    
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            ollama_cache = [model["name"].replace(":latest", "") for model in response.json()["models"]]
            return ollama_cache
        return []
    except Exception as e:
        print(f"Error getting local ollama models: {e}")
        return []
    
def get_openai_models() -> List[str]:
    global openai_cache

    if openai_cache and len(openai_cache) > 0:
        return openai_cache
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        openai_cache = [model.id for model in client.models.list()]
        return openai_cache
    except Exception as e:
        print(f"Error getting OpenAI models: {e}")
        return []

def get_gemini_models() -> List[str]:
    global gemini_cache

    if gemini_cache and len(gemini_cache) > 0:
        return gemini_cache

    try:
        gemini.configure(api_key=GEMINI_API_KEY)
        gemini_cache = [model.name.replace("models/", "") for model in gemini.list_models()]
        return gemini_cache
    except Exception as e:
        print(f"Error getting Gemini models: {e}")
        return []

def get_deepseek_models() -> List[str]:
    """
    Query DeepSeek for available models with caching.

    Returns:
        List[str]: List of available model IDs.
    """
    global deepseek_cache

    if deepseek_cache and len(deepseek_cache) > 0:
        return deepseek_cache

    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        deepseek_cache = [model.id for model in client.models.list()]
        return deepseek_cache
    except Exception as e:
        print(f"Error getting DeepSeek models: {e}")
        return []