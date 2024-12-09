from typing import List

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

    Example:
        models()
    """
    return ["model1", "model2"]

##########################################################