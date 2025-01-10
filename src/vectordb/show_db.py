
import chromadb

def main():
    client = chromadb.PersistentClient(path="AcademicChatBot/db/chromadb")
    try:
        collection = client.get_collection(name="youtube_chunks")
    except Exception as e:
        print(f"Fehler beim Zugriff auf die Sammlung: {e}")
        return

    # Gesamte Sammlung abrufen (kann paginiert werden, falls gewünscht)
    data = collection.get()
    ids = data.get("ids", [])
    documents = data.get("documents", [])
    metadatas = data.get("metadatas", [])

    for idx, doc_id in enumerate(ids):
        print(f"ID: {doc_id}")
        print(f"  Dokument: {documents[idx][:80]}...")  # Zeige nur einen Teil des Dokuments
        print(f"  Metadaten: {metadatas[idx]}")
        print("---")

if __name__ == "__main__":
    main()