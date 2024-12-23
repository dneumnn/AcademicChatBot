import os
from typing import List
from models.model import get_available_models
from graphstore.graphstore import ask_question_to_graphdb, ask_question_to_graphdb_OLD, mock_load_text_to_graphdb
from rag.rag import rag

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "mock", "chroma_db")
ALICE_PATH = os.path.join(os.path.dirname(__file__), "mock", "alice.txt")
COLLECTION_NAME = "alice"

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
    return get_available_models()
 
##########################################################

def main():
    #mock_load_text_to_vectordb_with_ollama_embeddings()
    #mock_load_text_to_graphdb(ALICE_PATH)
    #print(ask_question_to_graphdb("Which book is Lewis Carroll the author of? Go only by ids."))
    #print(ask_question_to_graphdb_OLD("Which book is Lewis Carroll the author of? Go only by ids."))
    rag(DATABASE_PATH, COLLECTION_NAME, "What is allices opinion on getting older?")
 
if __name__ == "__main__":
    main()