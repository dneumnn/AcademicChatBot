from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_ollama import ChatOllama
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from llama_index.core.retrievers import KnowledgeGraphRAGRetriever
from llama_index.core import get_response_synthesizer, StorageContext
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI as IndexOpenAI
from llama_index.graph_stores.neo4j import Neo4jGraphStore
import os
from langchain_openai import OpenAI
from dotenv import load_dotenv

def mock_load_text_to_graphdb(file_path: str) -> None:
    # load and preprocess text data
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=8000, chunk_overlap=400)
    texts = text_splitter.split_documents(documents)

    # init language model and extract knowledge graph
    #llm = ChatOllama(model="llama3.2") llama 3.2 is too bad for this, the output is unusable
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    llm = OpenAI(api_key=OPENAI_API_KEY)
    llm_transformer = LLMGraphTransformer(llm=llm)
    graph_documents = llm_transformer.convert_to_graph_documents(texts) # costs about 9 cent :^)
    
    # store in database
    graph_store = Neo4jGraph(
        url="bolt://localhost:7687", 
        username="neo4j", 
        password="password",
    )
    graph_store.add_graph_documents(graph_documents)

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

    response_synthesizer = get_response_synthesizer(llm=llm, response_mode="compact")
    response = response_synthesizer.synthesize(question, retrieved_context.source_nodes)

    return (retrieved_context, response)

def ask_question_to_graphdb_OLD(question: str) -> str:
    graph_store = Neo4jGraph(
        url="bolt://localhost:7687", 
        username="neo4j", 
        password="password",
    )

    llm = ChatOllama(model="llama3.2")
    qa_chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph_store,
        verbose=True,
        allow_dangerous_requests=True
    )
    result = qa_chain.invoke(question)

    return result