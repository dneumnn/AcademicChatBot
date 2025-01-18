import chromadb
from config import DB_DIR

def list_collections():
    client = chromadb.PersistentClient(path=DB_DIR)
    collections = client.list_collections()
    if collections:
        print("Collections in the Chroma Database:")
        for collection_name in collections:
            print(collection_name)
    else:
        print("No collections found in the Chroma Database.")

if __name__ == "__main__":
    list_collections()
