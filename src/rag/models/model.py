from typing import List
import requests
from openai import OpenAI
import google.generativeai as gemini

from ..constants.env import GEMINI_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY

combined_cache = None
ollama_model_cache = None
deepseek_model_cache = None
openai_model_cache = None
gemini_model_cache = None


def get_available_models():
    global combined_cache
    if combined_cache is None:
        combined_cache = get_local_ollama_models() + get_openai_models() + get_gemini_models() + get_deepseek_models()
        return combined_cache
    return combined_cache


def get_local_ollama_models() -> List[str]:
    """
    Query local Llama server for available models with caching.

    Returns:
        List[str]: List of available model IDs.
    """
    global ollama_model_cache
    if ollama_model_cache is None:
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                ollama_model_cache = [
                    model["name"].replace(":latest", "") for model in response.json().get("models", [])
                ]
            else:
                ollama_model_cache = []
        except Exception as e:
            print(f"Error getting local Ollama models: {e}")
            ollama_model_cache = []
    return ollama_model_cache


def get_deepseek_models() -> List[str]:
    """
    Query DeepSeek for available models with caching.

    Returns:
        List[str]: List of available model IDs.
    """
    global deepseek_model_cache
    if deepseek_model_cache is None:
        try:
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            deepseek_model_cache = [model.id for model in client.models.list()]
        except Exception as e:
            print(f"Error getting DeepSeek models: {e}")
            deepseek_model_cache = []
    return deepseek_model_cache


def get_gemini_models() -> List[str]:
    """
    Query Gemini for available models with caching.

    Returns:
        List[str]: List of available model IDs.
    """
    global gemini_model_cache
    if gemini_model_cache is None:
        try:
            gemini.configure(api_key=GEMINI_API_KEY)
            gemini_model_cache = [model.name.replace("models/", "") for model in gemini.list_models()]
        except Exception as e:
            print(f"Error getting Gemini models: {e}")
            gemini_model_cache = []
    return gemini_model_cache


def get_openai_models() -> List[str]:
    """
    Query OpenAI for available models with caching.

    Returns:
        List[str]: List of available model IDs.
    """
    global openai_model_cache
    if openai_model_cache is None:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            openai_model_cache = [model.id for model in client.models.list()]
        except Exception as e:
            print(f"Error getting OpenAI models: {e}")
            openai_model_cache = []
    return openai_model_cache
