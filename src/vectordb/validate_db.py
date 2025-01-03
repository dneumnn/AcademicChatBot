import csv
import random
import os
import chromadb
from config import INPUT_DIR

def create_dummy_embedding(text):
    """
    Platzhalter: Gibt ein Dummy-Embedding zurück.
    Für echte Tests sollte hier ein richtiges Embedding erzeugt werden.
    """
    return [0.0] * 768

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

    # 3. Beispielsuche mit Dummy-Embedding
    test_text = "Gay Cake"
    embedding = create_dummy_embedding(test_text)
    try:
        results = collection.query(query_embeddings=[embedding], n_results=3)
        print("Beispielsuche erfolgreich, gefundene Dokumente:")
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            print(f"  Dokument: {doc[:60]}... | time={meta.get('time')} length={meta.get('length')}")
    except Exception as e:
        print(f"Fehler bei der Embedding-Suche: {e}")

if __name__ == "__main__":
    main()