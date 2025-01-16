import chromadb
from config import DB_DIR

def list_collections(client):
    collections = client.list_collections()
    if collections:
        print("Collections in the Chroma Database:")
        for idx, collection_name in enumerate(collections):
            print(f"{idx + 1}. {collection_name}")
        return collections
    else:
        print("No collections found in the Chroma Database.")
        return []

def main():
    client = chromadb.PersistentClient(path=DB_DIR)
    collections = list_collections(client)
    if not collections:
        return

    try:
        choice = int(input("Choose a collection by number: ")) - 1
        if choice < 0 or choice >= len(collections):
            print("Invalid choice.")
            return
        collection_name = collections[choice]
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        print(f"Error accessing the collection: {e}")
        return

    # Retrieve the entire collection (can be paginated if desired)
    data = collection.get()
    ids = data.get("ids", [])
    documents = data.get("documents", [])
    metadatas = data.get("metadatas", [])

    for idx, doc_id in enumerate(ids):
        print(f"ID: {doc_id}")
        print(f"  Document: {documents[idx]}...")  # Show only part of the document
        print(f"  Metadata: {metadatas[idx]}")
        print("---")

if __name__ == "__main__":
    main()