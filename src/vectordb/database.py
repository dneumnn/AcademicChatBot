
import chromadb

def store_vectors(chunks, vectors, collection_name='my_collection'):
    # Use the PersistentClient for a local persistent database
    client = chromadb.PersistentClient(path="chromadb_data")
    collection = client.get_or_create_collection(name=collection_name)

    ids = [f"doc_{i}" for i in range(len(chunks))]
    collection.add(
        embeddings=vectors,
        documents=chunks,
        ids=ids
    )
