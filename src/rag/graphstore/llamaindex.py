from llama_index.core.retrievers import KnowledgeGraphRAGRetriever
from llama_index.core import get_response_synthesizer, StorageContext
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from llama_index.graph_stores.neo4j import Neo4jGraphStore
import os
from dotenv import load_dotenv

def mock_load_text_to_graphdb(file_path: str) -> None:
    pass

def ask_question_to_graphdb(question: str) -> str:
    graph_store = Neo4jGraphStore(
        url="bolt://localhost:7687", 
        username="neo4j", 
        password="password",
    )

    llm = Ollama(model="llama3.2")
    #load_dotenv()
    #OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    #llm = IndexOpenAI(api_key=OPENAI_API_KEY)

    storage_context = StorageContext.from_defaults(graph_store=graph_store)
    graph_rag_retriever = KnowledgeGraphRAGRetriever(llm=llm, storage_context=storage_context, verbose=True)
    query_engine = RetrieverQueryEngine.from_args(llm=llm, retriever=graph_rag_retriever)
    retrieved_context = query_engine.query(question)

    response_synthesizer = get_response_synthesizer(llm=llm, response_mode="compact", verbose=True)
    response = response_synthesizer.synthesize(question, retrieved_context.source_nodes)

    return (retrieved_context, response)