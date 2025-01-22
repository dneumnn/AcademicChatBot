import os
import pandas as pd
from langchain_ollama import OllamaEmbeddings
import logging

from .logger import log, clean_up_logger

def embed_text_chunks(video_id: str, embedding_model: str="nomic-embed-text"):
    """
    Create embeddings for each text chunk.
    """
    log.info("embed_text_chunks: Start embedding for video with ID %s.", video_id)
    embeddings = OllamaEmbeddings(model=embedding_model)

    df = pd.read_csv(f"./media/{video_id}/transcripts_chunks/{video_id}.csv")

    embeddings_list = [embeddings.embed_query(chunk) for chunk in df["chunks"]]

    df["chunks_embedded"] = embeddings_list

    df.to_csv(f"./media/{video_id}/transcripts_chunks/{video_id}.csv", index=False)
    clean_up_logger()
    log.info("embed_text_chunks: Saved embeddings for video with ID %s to %s", video_id, f"./media/{video_id}/transcripts_chunks/{video_id}.csv")
