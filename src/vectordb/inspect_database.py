import chromadb
from chromadb.config import Settings

def inspect_database():
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="chromadb_data"  # Same directory as in database.py
    ))

    # List all collections in the database
    collections = client.list_collections()
    print("Collections in the database:")
    for collection in collections:
        print(f"- {collection.name}")

    # Specify the collection name
    collection_name = 'my_collection'

    # Get the collection
    collection = client.get_collection(name=collection_name)

    # Retrieve all items from the collection
    results = collection.get()

    # Display the documents and their IDs
    print(f"\nDocuments in collection '{collection_name}':")
    for doc_id, document in zip(results['ids'], results['documents']):
        print(f"ID: {doc_id}")
        print(f"Document: {document}\n")

if __name__ == "__main__":
    inspect_database()