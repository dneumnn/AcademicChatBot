from typing import List
import requests
import chromadb
from chromadb.utils import embedding_functions
import os
from sentence_transformers import CrossEncoder, SentenceTransformer
from llama_index.core import Document
from llama_index.retrievers.bm25 import BM25Retriever
import Stemmer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
# pip install llama-index-retrievers-bm25
# pip install sentence_transformers
# pip install chromadb
# pip install langchain_core
# pip install langchain_chroma
# pip install langchain_ollama
 
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
   
def mock_load_text_to_vectordb(file_path: str = os.path.join(os.path.dirname(__file__), "mock", "alice.txt"), collection_name: str = "alice") -> None:
    """
    Load text file into ChromaDB, splitting by paragraphs
   
    Args:
        file_path: Path to text file
        collection_name: Name for ChromaDB collection
    """
    database_path = os.path.join(os.path.dirname(__file__), "mock", "chroma_db")
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

def mock_load_text_to_vectordb_with_ollama_embeddings(file_path: str = os.path.join(os.path.dirname(__file__), "mock", "alice.txt"), collection_name: str = "alice") -> None:
    """
    Load text file into ChromaDB, splitting by paragraphs
   
    Args:
        file_path: Path to text file
        collection_name: Name for ChromaDB collection
    """
    database_path = os.path.join(os.path.dirname(__file__), "mock", "chroma_db")
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
 
# Inpired by class notebook
def rerank_passages_with_cross_encoder(question: str, passages: List[str], top_k: int = 3) -> List[str]:
    """
    Rerank passages using cross-encoder model for semantic similarity scoring
   
    Args:
        question: Question to search for
        passages: List of passages to rerank
        top_k: Number of top passages to return
   
    Returns:
        List of reranked passages sorted by semantic similarity to question
    """
    cross_encoder_model = CrossEncoder('cross-encoder/stsb-roberta-base')
    sentence_pairs = [(question, passage) for passage in passages]
    similarity_scores = cross_encoder_model.predict(sentence_pairs)
    ranked_passages = [p for _, p in sorted(zip(similarity_scores, passages), reverse=True)]
    return ranked_passages[:top_k]
 
# Inpired by class notebook
def rerank_passages_with_bm25(question: str, passages: List[str], top_k: int = 3) -> List[str]:
    """
    Rerank passages using BM25 algorithm for keyword-based relevance scoring
   
    Args:
        question: Question to search for
        passages: List of passages to rerank
        top_k: Number of top passages to return
   
    Returns:
        List of reranked passages sorted by BM25 relevance score
    """
    documents = [Document(text=passage) for passage in passages]
    bm25_retriever = BM25Retriever.from_defaults(
        nodes=documents,
        similarity_top_k=top_k,
        stemmer=Stemmer.Stemmer("english"),
        language="english"
    )
    return bm25_retriever.retrieve(question)
 
def rerank_passages_with_cosine(question: str, passages: List[str], top_k: int = 3) -> List[str]:
    """
    Rerank passages using cosine similarity with sentence embeddings
   
    Args:
        question: Question to search for
        passages: List of passages to rerank
        top_k: Number of top passages to return
   
    Returns:
        List of reranked passages sorted by cosine similarity score
    """
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
   
    question_embedding = model.encode([question])
    passage_embeddings = model.encode(passages)
 
    similarities = cosine_similarity(question_embedding, passage_embeddings)[0]
    ranked_passages = [p for _, p in sorted(zip(similarities, passages), reverse=True)]
    return ranked_passages[:top_k]
 
def get_persistent_chroma_db_directory():
    return os.path.join(os.path.dirname(__file__), "mock", "chroma_db")
 
def format_docs(docs):
    return "\n\n".join(f"{i}.) {doc.page_content}" for i, doc in enumerate(docs))
 
def rag():
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma(
        persist_directory=get_persistent_chroma_db_directory(),
        embedding_function=embeddings,
        collection_name="alice",
        collection_metadata={"hnsw:space": "cosine"}
    )
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
 
    llm = ChatOllama(model="llama3.2")
 
    prompt = """
        You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
        Question: {question}
        Context: {context}
        Answer:
    """
 
    prompt_template = PromptTemplate.from_template(prompt)
 
    question = "Why did allice fall down the rabbit hole?"
 
    retriever_chain = retriever | format_docs
    docs = retriever_chain.invoke(question)
    print(docs)

    rag_chain = (
        {"context": retriever_chain, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )
    rag_chain.get_graph().print_ascii()

    for chunk in rag_chain.stream("Why did allice fall down the rabbit hole?"):
        print(chunk, end="", flush=True)
 
def __test__reranking():
    passages = query_vectordb("Why did allice fall down the rabbit hole?")
    print("\nRelevant passages about Alice:")
    for r in passages:
        print(f"\n- {r}")
 
    reranked_passages = rerank_passages_with_cross_encoder("Why did allice fall down the rabbit hole?", passages, top_k=3)
    print("\nReranked passages about Alice with cross-encoder:")
    for r in reranked_passages:
        print(f"\n- {r}")
 
    reranked_passages = rerank_passages_with_bm25("Why did allice fall down the rabbit hole?", passages, top_k=3)
    print("\nReranked passages about Alice with BM25:")
    for r in reranked_passages:
        print(f"\n- {r}")
 
    reranked_passages = rerank_passages_with_cosine("Why did allice fall down the rabbit hole?", passages, top_k=3)
    print("\nReranked passages about Alice with cosine similarity:")
    for r in reranked_passages:
        print(f"\n- {r}")

def main():
    #mock_load_text_to_vectordb()
    #__test__reranking()
    #mock_load_text_to_vectordb_with_ollama_embeddings()
    rag()
 
if __name__ == "__main__":
    main()