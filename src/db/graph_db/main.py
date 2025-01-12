from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph
import google.generativeai as genai
from dotenv import load_dotenv
import os


def load_csv_to_gaphdb(chunks) -> None:
    load_dotenv()
    API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    llm = genai.GenerativeModel('gemini-1.5-flash')
    llm_transformer = LLMGraphTransformer(llm=llm)
    graph_documents = llm_transformer.convert_to_graph_documents(chunks)

    graph_store = Neo4jGraph(
        url="bolt://localhost:7687", 
        username="neo4j", 
        password="this_pw_is_a_test25218###1119jj",
    )

    graph_store.add_graph_documents(graph_documents)