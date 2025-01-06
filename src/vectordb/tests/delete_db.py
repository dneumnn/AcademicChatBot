import chromadb
from config import DB_DIR

def delete_existing_collection():
    client = chromadb.PersistentClient(path=DB_DIR)
    collection_name = "youtube_chunks"
    try:
        client.delete_collection(name=collection_name)
        print(f"Collection '{collection_name}' erfolgreich gelöscht.")
    except Exception as e:
        print(f"Fehler beim Löschen der Collection '{collection_name}': {e}")
delete_existing_collection()