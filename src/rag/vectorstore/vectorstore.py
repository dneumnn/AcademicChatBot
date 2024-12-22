import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_index.core import Document

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
 
def get_persistent_chroma_db_directory():
    return os.path.join(os.path.dirname(__file__), "mock", "chroma_db")
 
def format_docs(docs):
    return "\n\n".join(f"{i}.) {doc.page_content}" for i, doc in enumerate(docs))