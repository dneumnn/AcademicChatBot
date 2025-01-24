import os
from dotenv import load_dotenv

from .config import NEO4J_FALLBACK

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI") or NEO4J_FALLBACK.get("uri")
NEO4J_USER = os.getenv("NEO4J_USER") or NEO4J_FALLBACK.get("user")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or NEO4J_FALLBACK.get("password")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

proper_gemini_key = os.getenv("GOOGLE_API_KEY")
funny_gemini_key = os.getenv("API_KEY_GOOGLE_GEMINI")
GEMINI_API_KEY = proper_gemini_key or funny_gemini_key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
