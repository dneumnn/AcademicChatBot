from typing import List
import json

from .constants.config import DEFAULT_DATABASE, DEFAULT_MODEL, DEFAULT_MODEL_PARAMETER_TEMPERATURE, \
    DEFAULT_MODEL_PARAMETER_TOP_P, DEFAULT_MODEL_PARAMETER_TOP_K, USE_SEMANTIC_ROUTING, USE_LOGICAL_ROUTING, DEFAULT_MODE
from .models.model import get_available_models
from .graphstore.langchain_version import ask_question_to_graphdb, mock_load_text_to_graphdb
from .logger.logger import setup_logger
from .rag.rag import rag
from .__tests__.generation import test_complete_generation
from .graphstore.graphstore import get_full_graph_information

"""
VectorDB -> ChromaDB
GraphDB -> neo4j
"""


##########################################################
# Final functions
##########################################################

# POST /chat
def chat_internal(
        prompt: str,
        model_id: str | None = None,
        message_history: List[dict] | None = None,
        playlist_id: str | None = None,
        video_id: str | None = None,
        knowledge_base: str | None = None,
        model_parameters: dict | None = None,
        database: str | None = None,
        stream: bool | None = None,
        plaintext: bool | None = None,
        mode: str | None = None
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

    if mode is None:
        logger.warning(f"Mode is not provided. Using default mode: {DEFAULT_MODE}")
        mode = DEFAULT_MODE

    if prompt is None or prompt == "":
        logger.error("Prompt is empty. Throwing error.")
        raise ValueError("Prompt is empty")

    logger.info(f"Chatting with the user: {prompt}")

    if database is None or (database != "vector" and database != "graph" and database != "all"):
        logger.warning(f"Invalid database type: {database}. Using vector.")
        database = DEFAULT_DATABASE

    logger.info(f"Using database: {database}")

    if model_id is None or model_id not in get_available_models():
        logger.warning(
            f"Invalid model ID: {model_id}. Available models: {get_available_models()}. Using default model.")
        model_id = DEFAULT_MODEL

    logger.info(f"Using model: {model_id}")

    if model_parameters is None:
        logger.warning(f"No model parameters provided. Using default model parameters.")
        model_parameters = {
            "temperature": DEFAULT_MODEL_PARAMETER_TEMPERATURE,
            "top_p": DEFAULT_MODEL_PARAMETER_TOP_P,
            "top_k": DEFAULT_MODEL_PARAMETER_TOP_K
        }
    elif "temperature" not in model_parameters or model_parameters["temperature"] < 0 or model_parameters[
        "temperature"] > 1:
        logger.warning(f"Invalid temperature: {model_parameters.get('temperature')}. Using default temperature.")
        model_parameters["temperature"] = DEFAULT_MODEL_PARAMETER_TEMPERATURE
    elif "top_p" not in model_parameters or model_parameters["top_p"] < 0 or model_parameters["top_p"] > 1:
        logger.warning(f"Invalid top_p: {model_parameters.get('top_p')}. Using default top_p.")
        model_parameters["top_p"] = DEFAULT_MODEL_PARAMETER_TOP_P
    elif "top_k" not in model_parameters or model_parameters["top_k"] < 0:
        logger.warning(f"Invalid top_k: {model_parameters.get('top_k')}. Using default top_k.")
        model_parameters["top_k"] = DEFAULT_MODEL_PARAMETER_TOP_K

    logger.info(f"Using model parameters: {model_parameters}")

    if stream is None:
        logger.warning("Stream is not provided. Using default value.")
        stream = True

    if plaintext is None:
        logger.warning("Plaintext is not provided. Using default value.")
        plaintext = False

    if stream:
        return rag(
            question=prompt,
            message_history=message_history,
            model_id=model_id,
            knowledge_base=knowledge_base,
            model_parameters=model_parameters,
            use_logical_routing=USE_LOGICAL_ROUTING,
            use_semantic_routing=USE_SEMANTIC_ROUTING,
            logger=logger,
            video_id=video_id,
            playlist_id=playlist_id,
            plaintext=plaintext,
            database=database,
            mode=mode
        )
    else:
        output = []
        for chunk in rag(
                question=prompt,
                message_history=message_history,
                model_id=model_id,
                knowledge_base=knowledge_base,
                model_parameters=model_parameters,
                use_logical_routing=USE_LOGICAL_ROUTING,
                use_semantic_routing=USE_SEMANTIC_ROUTING,
                logger=logger,
                video_id=video_id,
                playlist_id=playlist_id,
                plaintext=plaintext,
                database=database,
                mode=mode
        ):
            output.append(chunk)
        if plaintext:
            return ''.join(output)
        else:
            return {
                "content:": ''.join([json.loads(chunk)["content"] for chunk in output]),
                "sources": json.loads(output[-1])["sources"]
            }


# GET /models
def models_internal() -> List[str]:
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
    print(chat_internal(
        prompt="Whats the price of the new cards?",
        model_id="gemini-1.5-flash",
        database="all",
        stream=False,
        plaintext=True,
        mode="smart"
    ))
    #get_full_graph_information()


if __name__ == "__main__":
    main()
