import os
from typing import List
from models.model import get_available_models
from graphstore.langchain import ask_question_to_graphdb, mock_load_text_to_graphdb
from logger.logger import setup_logger
from rag.rag import rag
from __tests__.generation import test_complete_generation

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
        model_parameters: dict = {
            "temperature": 0.8,
            "top_p": 0.9,
            "top_k": 40
        },
        database: str = "vector"
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
    chat("Tell me about the video", "llama3.2", [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}], "PL12345", "VID67890", "physics", {"temperature": 0.8, "top_p": 0.9, "top_k": 40})
    """
    logger = setup_logger()

    if prompt is None or prompt == "":
        logger.error("Prompt is empty. Throwing error.")
        raise ValueError("Prompt is empty")

    logger.info(f"Chatting with the user: {prompt}")

    if database != "vector" and database != "graph" and database != "all":
        logger.warning(f"Invalid database type: {database}. Using vector.")
        database = "vector"

    logger.info(f"Using database: {database}")

    if model_id is None or model_id not in get_available_models():
        logger.warning(f"Invalid model ID: {model_id}. Available models: {get_available_models()}. Using default model.")
        model_id = "llama3.2:latest"

    logger.info(f"Using model: {model_id}")

    if "temperature" not in model_parameters or model_parameters["temperature"] < 0 or model_parameters["temperature"] > 1:
        logger.warning(f"Invalid temperature: {model_parameters.get('temperature')}. Using default temperature.")
        model_parameters["temperature"] = 0.8
    elif "top_p" not in model_parameters or model_parameters["top_p"] < 0 or model_parameters["top_p"] > 1:
        logger.warning(f"Invalid top_p: {model_parameters.get('top_p')}. Using default top_p.")
        model_parameters["top_p"] = 0.9
    elif "top_k" not in model_parameters or model_parameters["top_k"] < 0:
        logger.warning(f"Invalid top_k: {model_parameters.get('top_k')}. Using default top_k.")
        model_parameters["top_k"] = 40
    
    logger.info(f"Using model parameters: {model_parameters}")

    rag(
        database_path=DATABASE_PATH,
        question=prompt,
        model_id=model_id,
        knowledge_base=knowledge_base,
        model_parameters=model_parameters,
        logger=logger,
        use_logical_routing=False,
        use_semantic_routing=False,
        basic_return=False
    )

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
    #print(ask_question_to_graphdb("Which book is Lewis Carroll the author of?"))
    #rag(database_path=DATABASE_PATH, question="What is allices opinion on getting older?")
    #test_complete_generation(DATABASE_PATH, generate_output_first=False)
    chat(prompt="What are supervised and unsupervised learning models?", model_id="llama3.2:latest", database="vector", model_parameters={"temperature": 0.8, "top_p": 0.9, "top_k": 40}, knowledge_base="youtube_chunks")
 
if __name__ == "__main__":
    main()