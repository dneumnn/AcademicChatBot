from openai import OpenAI

client = OpenAI(api_key='your-api-key')
from config import EMBEDDING_MODEL


def vectorize_chunks(chunks):
    vectors = []
    for chunk in chunks:
        response = client.embeddings.create(input=chunk,
        model=EMBEDDING_MODEL)
        vector = response.data[0].embedding
        vectors.append(vector)
    return vectors
