import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_DIR = os.path.join(BASE_DIR, 'data', 'input')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Ensure this environment variable is set
# EMBEDDING_MODEL = 'nomic-embed-text'
