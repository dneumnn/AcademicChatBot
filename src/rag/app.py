from typing import List
import requests
import chromadb
import os

"""
VectorDB -> ChromaDB
GraphDB -> neo4j
"""

##########################################################
# Final functions
##########################################################

# POST /chat
def chat(
        prompt: str,
        model_id: str = None,
        message_history: List[dict] = None,
        playlist_id: str = None,
        video_id: str = None,
        knowledge_base: str = None,
        model_parameters: dict = None
    ):
    """
    Respond to the user's prompt

    Args:
    prompt (str): The user's prompt
    model_id (str, optional): ID of the model to use
    message_history (List[dict], optional): History of messages in the conversation
    playlist_id (str, optional): ID of the YouTube playlist
    video_id (str, optional): ID of the YouTube video
    knowledge_base (str, optional): Knowledge base to use for the response
    model_parameters (dict, optional): Parameters for the model

    Returns:
    str: The response to the user's prompt

    Example:
    chat("Tell me about the video", "llama3.2", [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}], "PL12345", "VID67890", "physics", {"temperature": 0.7})
    """
    return "Chatting with the user"

# GET /models
def models() -> List[str]:
    """
    List all available models

    Returns:
        List[str]: List of model IDs
    """
    return get_local_llama_models()

##########################################################

def get_local_llama_models() -> List[str]:
    """
    Query local Llama server for available models
    
    Returns:
        List[str]: List of available model IDs
    
    Raises:
        ConnectionError: If can't connect to Llama server
    """
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = [model["name"] for model in response.json()["models"]]
            return models
        return []
    except requests.exceptions.RequestException:
        raise ConnectionError("Cannot connect to local Llama server")
    
def mock_load_text_to_vectordb(file_path: str, collection_name: str = "alice") -> None:
    """
    Load text file into ChromaDB, splitting by paragraphs
    
    Args:
        file_path: Path to text file
        collection_name: Name for ChromaDB collection
    """
    database_path = os.path.join(os.path.dirname(__file__), "mock", "chroma_db")
    client = chromadb.PersistentClient(path=database_path)
    
    collection = client.get_or_create_collection(name=collection_name)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    collection.add(
        documents=paragraphs,
        ids=[f"para_{i}" for i in range(len(paragraphs))]
    )

def query_vectordb(question: str, collection_name: str = "alice", n_results: int = 3) -> List[str]:
    """
    Query ChromaDB for relevant text passages based on a question
    
    Args:
        question: Question to search for
        collection_name: Name of ChromaDB collection
        n_results: Number of results to return
    
    Returns:
        List of relevant text passages
    """
    database_path = os.path.join(os.path.dirname(__file__), "mock", "chroma_db")
    client = chromadb.PersistentClient(path=database_path)
    
    collection = client.get_collection(name=collection_name)
    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )
    
    return results['documents'][0]

if __name__ == "__main__":
    #alice_path = os.path.join(os.path.dirname(__file__), "mock", "alice.txt")
    #mock_load_text_to_vectordb(alice_path)
    results = query_vectordb("Why did allice fall down the rabbit hole?")
    print("\nRelevant passages about Alice:")
    for r in results:
        print(f"\n- {r}")