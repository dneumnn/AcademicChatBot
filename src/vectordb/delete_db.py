import chromadb
def delete_existing_collection():
    client = chromadb.PersistentClient(path="AcademicChatBot/db/chromadb")
    collection_name = "youtube_chunks"
    try:
        client.delete_collection(name=collection_name)
        print(f"Collection '{collection_name}' erfolgreich gelöscht.")
    except Exception as e:
        print(f"Fehler beim Löschen der Collection '{collection_name}': {e}")

delete_existing_collection()
