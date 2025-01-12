import time
import os
import google.generativeai as genai
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

loader = TextLoader(file_path="dummytext.txt")
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=24)
documents = text_splitter.split_documents(documents=docs)




def parse_response_to_graph(response_text):
    """
    Verarbeitet die generierte Antwort von Gemini und extrahiert Knoten und Beziehungen.
    Diese Funktion muss an die genaue Antwortstruktur angepasst werden.
    """
    # Beispiel: Antwort in ein Wörterbuch mit Knoten und Kanten umwandeln
    graph_data = {
        "nodes": [],
        "edges": []
    }

    lines = response_text.strip().split("\n")
    for line in lines:
        if "Node:" in line:
            node = line.split(":")[1].strip()
            graph_data["nodes"].append(node)
        elif "Relationship:" in line:
            parts = line.split(":")[1].strip().split("->")
            if len(parts) == 2:
                graph_data["edges"].append((parts[0].strip(), parts[1].strip()))
                print(graph_data)

    return graph_data

def add_to_graphdb(graph_data, driver):
    """
    Fügt Knoten und Beziehungen in die Neo4j-Datenbank ein.
    """
    with driver.session() as session:
        for node in graph_data["nodes"]:
            session.run("MERGE (n:Entity {name: $name})", name=node)
        for edge in graph_data["edges"]:
            session.run("""
                MATCH (a:Entity {name: $source})
                MATCH (b:Entity {name: $target})
                MERGE (a)-[:RELATED_TO]->(b)
            """, source=edge[0], target=edge[1])

def load_csv_to_graphdb(documents) -> None:
    # Lade Umgebungsvariablen und konfiguriere Google Gemini
    load_dotenv()
    API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)

    # Verbindung zur Neo4j-Datenbank
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    # Verarbeite jeden Chunk und speichere die Daten in der Graph-Datenbank
    requests_made = 0
    for document in documents:
        # Prompt, um Entitäten und Beziehungen zu extrahieren
        prompt = f"""
        Extract all Entities and their relation from following text:
        {document}

        Return the output in the following format:
        Node: <Entity1>
        Node: <Entity2>
        Relationship: <Entity1> - <Relationship> -> <Entity2>
        """
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        if requests_made >= 14:
            time.sleep(60)
            requests_made = 0

        response = model.generate_content(contents=prompt)
        #print(response.text)

        requests_made += 1

        # Verarbeite die Antwort von Gemini
        graph_data = parse_response_to_graph(response.text)

        # Speichere Knoten und Beziehungen in der Graph-Datenbank
        add_to_graphdb(graph_data, driver)

    # Schließe den Neo4j-Driver
    driver.close()

load_csv_to_graphdb(documents)