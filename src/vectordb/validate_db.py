import csv
import random
import os
import chromadb
from config import INPUT_DIR
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def validate_db():
    client = chromadb.PersistentClient(path="AcademicChatBot/db/chromadb")
    collection = client.get_collection("youtube_chunks")
    all_docs = collection.get(include=["embeddings", "documents"])
    if not all_docs["documents"]:
        print("Keine Dokumente in der Sammlung.")
        return

    import random
    idx = random.randint(0, len(all_docs["documents"]) - 1)
    doc_text = all_docs["documents"][idx]
    doc_embedding = all_docs["embeddings"][idx]
    result = collection.query(
        query_embeddings=[doc_embedding],
        n_results=3,
        include=["documents", "distances"]
    )
    print(f"Überprüfe Embedding für zufällig ausgewähltes Dokument {idx}:")
    print(doc_text)
    print("Ähnlichkeiten:")
    for i, dist in enumerate(result["distances"][0]):
        similarity = 1 - dist
        print(f"  - {result['documents'][0][i]} => Similarity: {similarity}")

def find_most_similar(question):
    client = chromadb.PersistentClient(path="AcademicChatBot/db/chromadb")
    collection = client.get_collection("youtube_chunks")
    question_embedding = model.encode(question).tolist()
    result = collection.query(
        query_embeddings=[question_embedding],
        n_results=1,
        include=["documents", "distances"]
    )
    most_similar_doc = result["documents"][0][0]
    similarity = 1 - result["distances"][0][0]
    return most_similar_doc, similarity

if __name__ == '__main__':
    validate_db()
    question = "what is artificial  intelligence?"
    doc, sim = find_most_similar(question)
    print(f"Die ähnlichste Antwort auf die Frage '{question}' ist:")
    print(f"  Dokument: {doc}")
    print(f"  Ähnlichkeit: {sim}")





