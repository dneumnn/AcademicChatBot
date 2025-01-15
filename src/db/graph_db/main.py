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
        "relationships": []
    }

    lines = response_text.strip().split("\n")
    for line in lines:
        if line.startswith("Node:"):
            node = line.split(":", 1)[1].strip()
            if node not in graph_data["nodes"]:
                graph_data["nodes"].append(node)
        elif line.startswith("Relationship:"):
            relationship_data = line.split(":", 1)[1].strip()
            parts = relationship_data.split(",")
            if len(parts) == 3:
                source = parts[0].strip()
                relation = parts[1].strip()
                target = parts[2].strip()
                graph_data["relationships"].append((source, relation, target))
                print(graph_data)
            

    return graph_data

def add_to_graphdb(graph_data, driver, meta_data=None):
    """
    Fügt Knoten und Beziehungen in die Neo4j-Datenbank ein.
    """
    with driver.session() as session:
        for node in graph_data["nodes"]:
            session.run("MERGE (n:Entity {name: $name})", name=node)
        
        if meta_data:
            # Überprüfen, welche Knoten keine Metadaten haben (hier mit `upload_date`)
            query = """
                MATCH (n:Entity)
                WHERE n.uploader IS NULL
                SET n += {
                    title: $title,
                    description: $description,
                    duration: $duration,
                    view_count: $view_count,
                    uploader: $uploader,
                    tags: $tags,
                    thumbnail: $thumbnail,
                    uploader_url: $uploader_url
                }
            """ 
            session.run(query, parameters={
                "title": meta_data.get('title'),
                "description": meta_data.get('description'),
                "duration": meta_data.get('duration'),
                "view_count": meta_data.get('view_count'),
                "uploader": meta_data.get('uploader'),
                "tags": meta_data.get('tags'),
                "thumbnail": meta_data.get('thumbnail'),
                "uploader_url": meta_data.get('uploader_url')
            })
        
        for relationship in graph_data["relationships"]:
            source, relation, target = relationship
            sanitized_relation = relation.replace(" ", "_").replace("-", "_").upper()
            print(f"relationship:{sanitized_relation}")
            query = f"""
                MATCH (a:Entity {{name: $source}})
                MATCH (b:Entity {{name: $target}})
                MERGE (a)-[:{sanitized_relation}]->(b)
            """
            session.run(query, source=source, target=target)
        
        # Lösche Knoten ohne Beziehungen (isolierte Knoten)
        session.run("""
            MATCH (n:Entity)
            WHERE NOT (n)--()  // Knoten ohne Beziehungen
            DELETE n
        """)

def load_csv_to_graphdb(documents, meta_data) -> None:
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
        {document}. Entities can be people, places, organizations, concepts, or other meaningful items. Relationships represent how these entities are connected.

        Return the output in the following format:
        Node: <Entity1>
        Node: <Entity2>
        Relationship: <Entity1> , <Relationship> , <Entity2>

        Follow these rules strictly:

        1. If Relationships consist of more than one word use _ to separate them. If two entities have more than one relation to one another make to separate relationships.
        2. Relationships and nodes may only contain letters, numbers and underscores.
        3. If a relationship includes multiple actions (e.g., `own/created`), split it into separate relationships for each action. For example:
            - Instead of `own/created`, create `own` and `created` as two distinct relationships.
        """
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        if requests_made >= 12:
            time.sleep(60)
            requests_made = 0

        response = model.generate_content(contents=prompt)

        requests_made += 1

        # Verarbeite die Antwort von Gemini
        graph_data = parse_response_to_graph(response.text)

        # Speichere Knoten und Beziehungen in der Graph-Datenbank
        add_to_graphdb(graph_data, driver, meta_data)

    # Schließe den Neo4j-Driver
    driver.close()


meta_data = {
    'id': 'dQw4w9WgXcQ',
    'title': 'Never Gonna Give You Up',
    'description': 'Never gonna give you up... (Textbeschreibung)',
    'upload_date': '2021-10-01',
    'duration': 213,
    'view_count': 1000000,
    'uploader_url': 'https://www.youtube.com/channel/UC1234567890',
    'uploader_id': 'UC1234567890',
    'channel_id': None,
    'uploader': 'Bob dylan',
    'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
    'like_count': None,
    'tags': ['rick', 'astley', 'never gonna give you up'],
    'categories': None,
    'age_limit': None,
}


load_csv_to_graphdb(documents, meta_data)

# Lösche alle Knoten und Beziehungen 
# MATCH (n)
# DETACH DELETE n