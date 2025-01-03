import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_DIR = os.path.join(BASE_DIR, 'data', 'input')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

MAX_SENTENCES_PER_CHUNK = 5  # Maximale Anzahl Sätze pro Chunk
OVERLAP_SENTENCES = 1        # Anzahl der Sätze für Overlap

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Ensure this environment variable is set
EMBEDDING_MODEL = 'text-embedding-ada-002'