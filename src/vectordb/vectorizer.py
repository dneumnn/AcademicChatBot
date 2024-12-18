from openai import OpenAI
import os
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)
from config import EMBEDDING_MODEL


def vectorize_chunks(chunks):
    vectors = []
    for chunk in chunks:
        response = client.embeddings.create(input=chunk,
        model=EMBEDDING_MODEL)
        vector = response.data[0].embedding
        vectors.append(vector)
    return vectors
