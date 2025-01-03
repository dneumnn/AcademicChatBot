import csv
import random
import os
import chromadb
from ollama import OllamaClient  # Importiere das Ollama SDK
from config import INPUT_DIR

# Initialisiere Ollama Client
ollama_client = OllamaClient(model="nomic-embed-text")

def create_embedding_with_ollama(text):
    """
    Erzeugt ein echtes Embedding für den übergebenen Text
    mit dem Ollama-Modell 'nomic-embed-text'.
    """
    try:
        response = ollama_client.embed(text)
        if response and "embedding" in response:
            return response["embedding"]
        else:
            raise ValueError("Embedding konnte nicht erstellt werden.")
    except Exception as e:
        print(f"Fehler beim Erstellen des Embeddings: {e}")
        return None

def main():
    csv_path = os.path.join(INPUT_DIR, "Yq0QkCxoTHM.csv")
    client = chromadb.PersistentClient(path="AcademicChatBot/db/chromadb")
    collection = client.get_collection(name="youtube_chunks")

    # 1. Anzahl der Einträge vergleichen
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    csv_count = len(rows)
    db_count = collection.count()
    print(f"CSV-Einträge: {csv_count}, ChromaDB-Einträge: {db_count}")

    # 2. Stichprobenartige Metadatenprüfung
    sample_size = 3
    if db_count > 0:
        for _ in range(min(sample_size, csv_count)):
            index = random.randint(0, csv_count - 1)
            row = rows[index]
            doc_id = f"row_{index}"
            db_result = collection.get(ids=[doc_id])
            if db_result and db_result["documents"]:
                db_doc = db_result["documents"][0]
                meta = db_result["metadatas"][0]
                if (db_doc == row["chunks"] and
                        meta.get("time") == row["time"] and
                        meta.get("length") == row["length"]):
                    print(f"Stichprobe ID {doc_id}: Metadaten stimmen überein.")
                else:
                    print(f"Stichprobe ID {doc_id}: Metadaten weichen ab!")
            else:
                print(f"Stichprobe ID {doc_id}: Keine Daten in ChromaDB gefunden.")

    # 3. Beispielsuche mit Ollama-Embedding
    test_text = "What is the topic of the video segment about machine learning?"
    embedding = create_embedding_with_ollama(test_text)
    if embedding:
        try:
            results = collection.query(query_embeddings=[embedding], n_results=3)
            print("Beispielsuche erfolgreich, gefundene Dokumente:")
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                print(f"  Dokument: {doc[:60]}... | time={meta.get('time')} | length={meta.get('length')}")
        except Exception as e:
            print(f"Fehler bei der Embedding-Suche: {e}")
    else:
        print("Fehler: Embedding für die Suche konnte nicht erstellt werden.")

if __name__ == "__main__":
    main()
