from typing import List
from sentence_transformers import CrossEncoder, SentenceTransformer
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import Document
import Stemmer
from torch import cosine_similarity
from vectorstore.legacy.vectorstore import query_vectordb

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

def rerank_passages_with_cross_encoder_bge(question: str, passages: List[str], top_k: int = 3) -> List[str]:
    """
    Rerank passages using cross-encoder model for semantic similarity scoring
   
    Args:
        question: Question to search for
        passages: List of passages to rerank
        top_k: Number of top passages to return
   
    Returns:
        List of reranked passages sorted by semantic similarity to question
    """
    cross_encoder_model = CrossEncoder('BAAI/bge-reranker-large')
    sentence_pairs = [(question, passage) for passage in passages]
    similarity_scores = cross_encoder_model.predict(sentence_pairs)
    ranked_passages = [p for _, p in sorted(zip(similarity_scores, passages), reverse=True)]
    return ranked_passages[:top_k]

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