import logging
import os
from typing import List
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_index.core import Document
import chromadb
from sentence_transformers import SentenceTransformer

from ..rerankers.rerankers import rerank_passages_with_cross_encoder
from ..constants.config import RETRIEVAL_EMBEDDING_MODEL, DEFAULT_KNOWLEDGE_BASE

open_default_collection = None

def mock_load_text_to_vectordb_with_ollama_embeddings(database_path: str, file_path: str, collection_name: str) -> None:
    """
    Load text file into ChromaDB, splitting by paragraphs
   
    Args:
        database_path: Path to ChromaDB database
        file_path: Path to text file
        collection_name: Name for ChromaDB collection
    """
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma(
        persist_directory=database_path,
        embedding_function=embeddings,
        collection_name=collection_name,
        collection_metadata={"hnsw:space": "cosine"}
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
        separators=["\n\n\n","\n\n", "\n"]
    )
    
    # Split text into chunks
    texts = text_splitter.split_text(text)
    
    # Add documents to vectorstore with proper Document class
    documents = [
        Document(
            page_content=t,
            metadata={"chunk_index": i, "source": file_path}
        ) for i, t in enumerate(texts)
    ]
    vectorstore.add_documents(documents)
 
def get_persistent_mock_chroma_db_directory():
    return os.path.join(os.path.dirname(__file__), "..", "mock", "chroma_db")

def get_persistent_chroma_db_directory():
    return os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "chromadb")
 
def format_docs(docs: List[Document]) -> List[str]:
    return [doc.page_content for doc in docs]

def transform_string_list_to_string(docs: List[str]) -> str:
    return "\n\n".join(docs)

def retrieve_top_n_documents_chromadb_mock(logger: logging.Logger, question: str, subject: str):
    EMBEDDING_MODEL_ID = "nomic-embed-text"
    VECTORSTORE_TOP_K = 25
    RERANKER_TOP_K = 5

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_ID)
    logger.info(f"Using embeddings model: {EMBEDDING_MODEL_ID}")
    vectorstore = Chroma(
        persist_directory=get_persistent_mock_chroma_db_directory(),
        embedding_function=embeddings,
        collection_name=subject,
        collection_metadata={"hnsw:space": "cosine"}
    )
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": VECTORSTORE_TOP_K})
    
    retriever_chain = (
        retriever 
        | format_docs 
        | (lambda docs: rerank_passages_with_cross_encoder(question=question, passages=docs, logger=logger, top_k=RERANKER_TOP_K))
        | transform_string_list_to_string
    )

def tidy_vectorstore_results(results):
    """
    Original:
    {
    'ids': [[...]],
    'distances': [[...]],
    'metadatas': [[...]],
    'documents': [[...]]
    }

    Tidied:
    [
        {document, metadata}
    ]
    """
    results = [
        {
            "document": doc,
            "metadata": meta
        } for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]
    return results

def generate_vector_filter(logger: logging.Logger, video_id: str | None = None, playlist_id: str | None = None, include_image_descriptions: bool | None = None):
    filters = []

    # If video_id is provided, use it for the filter, otherwise if playlist_id is provided, use it for the filter
    if video_id is not None:
        logger.info(f"Using video_id: {video_id} for vector filter")
        filters.append({"video_id": video_id})
    elif playlist_id is not None:
        logger.info(f"Using playlist_id: {playlist_id} for vector filter")
        filters.append({"playlist_id": playlist_id})

    # Do not include image descriptions if explicitly set to False
    if include_image_descriptions is not None and include_image_descriptions == False:
        filters.append({"is_image_description": False})

    if len(filters) == 0:
        logger.warning("No filters provided. Not using vector filter.")
        return None

    # Combine filters into a single filter
    filter = {"$and": filters} if len(filters) > 1 else filters[0]

    logger.info(f"Using filter: {filter} for vector filter")

    return filter

def retrieve_top_n_documents_chromadb(question: str, subject: str, logger: logging.Logger, top_k: int = 25, filter: dict | None = None):
    global open_default_collection

    logger.info(f"Using embeddings model: {RETRIEVAL_EMBEDDING_MODEL}")
    client = chromadb.PersistentClient(path=get_persistent_chroma_db_directory())

    collections = client.list_collections()

    if DEFAULT_KNOWLEDGE_BASE in [collection.name for collection in collections] and open_default_collection is None:
        open_default_collection = client.get_collection(DEFAULT_KNOWLEDGE_BASE)

    for collection in collections:
        logger.info(f"Collection exists: {collection.name}, meta {collection.metadata}")

    if subject == DEFAULT_KNOWLEDGE_BASE:
        collection = open_default_collection
    else:
        collection = client.get_collection(subject)

    model = SentenceTransformer(RETRIEVAL_EMBEDDING_MODEL)
    question_embedding = model.encode(question).tolist()

    result = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
        where=filter
    )

    clean_result = tidy_vectorstore_results(result)

    return clean_result

def get_vector_collections():
    client = chromadb.PersistentClient(path=get_persistent_chroma_db_directory())
    collections = [collection.name for collection in client.list_collections()]
    return collections
