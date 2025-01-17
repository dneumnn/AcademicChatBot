import chromadb
from typing import List
from chromadb.utils import embedding_functions

def query_vectordb(database_path: str, question: str, collection_name: str, n_results: int = 3) -> List[str]:
    """
    Query ChromaDB for relevant text passages based on a question
   
    Args:
        database_path: Path to ChromaDB database
        question: Question to search for
        collection_name: Name of ChromaDB collection
        n_results: Number of results to return
   
    Returns:
        List of relevant text passages
    """
    client = chromadb.PersistentClient(path=database_path)
   
    collection = client.get_collection(name=collection_name)
    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )
   
    return results['documents'][0]

def mock_load_text_to_vectordb(database_path: str, file_path: str, collection_name: str) -> None:
    """
    Load text file into ChromaDB, splitting by paragraphs
   
    Args:
        database_path: Path to ChromaDB database
        file_path: Path to text file
        collection_name: Name for ChromaDB collection
    """
    embeddings = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.PersistentClient(path=database_path)

    try:
        client.delete_collection(
            name=collection_name
        )
    except Exception as e:
        print(e)
   
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embeddings,
        metadata={"hnsw:space": "cosine"} # l2 is the default, use cosine similarity
        )
   
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
   
    collection.add(
        documents=paragraphs,
        ids=[f"para_{i}" for i in range(len(paragraphs))]
    )