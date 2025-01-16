from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_ollama import ChatOllama
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_openai import OpenAI, ChatOpenAI
from dotenv import load_dotenv
import os

from ..constants.env import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

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
        url=NEO4J_URI, 
        username=NEO4J_USER, 
        password=NEO4J_PASSWORD,
    )
    graph_store.add_graph_documents(graph_documents)

def ask_question_to_graphdb(question: str) -> str:
    graph_store = Neo4jGraph(
        url=NEO4J_URI, 
        username=NEO4J_USER, 
        password=NEO4J_PASSWORD,
    )

    llm = ChatOllama(model="llama3.2")
    #llm = ChatOpenAI(model="gpt-4o")
    qa_chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph_store,
        verbose=True,
        allow_dangerous_requests=True
    )
    result = qa_chain.invoke(question)

    return result

def main():
    print(ask_question_to_graphdb("Wehre was the ehibition?"))

if __name__ == "__main__":
    main()

