import pandas as pd
from ollama import OllamaEmbeddings 

def embed_text_chunks(videoid: str, embedding_model: str="nomic-embed-text"):
    """
    Create embeddings for each text chunk.
    """
    embeddings = OllamaEmbeddings(model=embedding_model)

    df = pd.read_csv(f"./media/{videoid}/transcripts_chunks/{videoid}.csv")

    embeddings_list = [embeddings.embed_query(chunk) for chunk in df["chunks"]]

    df["chunks_embedded"] = embeddings_list

    df.to_csv(f"./media/{videoid}/transcripts_chunks/{videoid}.csv", index=False)
