import time
import os
import google.generativeai as genai
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from itertools import chain
from src.data_processing.logger import log
from src.db.graph_db.utilities import *


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
            

    return graph_data

def add_nodes_to_graphdb(graph_data, driver, chunk, meta_data):
    """
    Fügt Knoten und Beziehungen in die Neo4j-Datenbank ein.
    """
    with driver.session() as session:
        for node in graph_data["nodes"]:
            query = """
            MERGE (n:Entity {name: $name})
            SET n.time = coalesce(n.time, []) + $time,     
                n.text = coalesce(n.text, []) + $sentence,     
                n.url_id = coalesce(n.url_id, []) + $url_id,
                n.title = coalesce(n.title, []) + $title,
                n.description = coalesce(n.description, []) + $description,
                n.duration = coalesce(n.duration, []) + $duration,
                n.view_count = coalesce(n.view_count, []) + $view_count,
                n.uploader = coalesce(n.uploader, []) + $uploader,
                n.tags = coalesce(n.tags, []) + $tags,
                n.thumbnail = coalesce(n.thumbnail, []) + $thumbnail,
                n.uploader_url = coalesce(n.uploader_url, []) + $uploader_url,
                n.age_limit = coalesce(n.age_limit, []) + $age_limit,
                n.categories = coalesce(n.categories, []) + $categories,
                n.like_count = coalesce(n.like_count, []) + $like_count,
                n.upload_date = coalesce(n.upload_date, []) + $upload_date
            """

            session.run(query, parameters={
                "time": chunk['time'],
                "sentence": chunk['sentence'],
                "name": node,
                "url_id": chunk['node_id'],
                "title": meta_data.get('title'),
                "description": meta_data.get('description'),
                "duration": meta_data.get('duration'),
                "view_count": meta_data.get('view_count'),
                "uploader": meta_data.get('uploader'),
                "tags": meta_data.get('tags'),
                "thumbnail": meta_data.get('thumbnail'),
                "uploader_url": meta_data.get('uploader_url'),
                "age_limit": meta_data.get('age_limit'),
                "categories": meta_data.get('categories'),
                "like_count": meta_data.get('like_count'),
                "upload_date": meta_data.get('upload_date')
            })


                
        for relationship in graph_data["relationships"]:
            source, relation, target = relationship
            sanitized_relation = relation.replace(" ", "_").replace("-", "_").upper()
            #print(f"relationship:{sanitized_relation}")
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

def add_attributes_to_nodes(driver, meta_data, frames):
    with driver.session() as session:
        # Insert Frame information to respective nodes
        if frames:
            query = """
            MATCH (n:Entity)
            WITH n, n.url_id AS urlIdArray
            UNWIND urlIdArray AS urlIdElement
            WITH n, urlIdElement, 
                REDUCE(i = -1, idx IN RANGE(0, SIZE(urlIdArray) - 1) 
                    | CASE WHEN urlIdArray[idx] = urlIdElement THEN idx ELSE i END) AS index
            MATCH (n:Entity)
            WHERE urlIdElement = $id
            WITH n, index, ABS(n.time[index] - $time) AS difference
            ORDER BY difference ASC
            LIMIT 1
            WITH index, n.time[index] AS closestTime
            MATCH (n:Entity)
            WHERE $id IN n.url_id AND n.time[index] = closestTime
            SET n.frame_names = coalesce(n.frame_names, []) + [$frame_name],
                n.frame_descriptions = coalesce(n.frame_descriptions, []) + [$description]
            RETURN n
            """
            for frame in frames:
                session.run(query, parameters={
                 "id": meta_data.get('id'),
                 "time": frame['time'],
                 "frame_name": frame['file_name'],
                 "description": frame['description']
                }) 
        else:
            log.error("download_pipeline_youtube: Node frames could not be inserted into graph_db: %s")
            return 500, "Internal error when trying Insert frames to nodes in graph_db. Please contact a developer."
        
def load_csv_to_graphdb(meta_data, video_id) -> None:

    load_dotenv()
    API_KEY_GOOGLE_GEMINI_GRAPHDB = os.getenv("API_KEY_GOOGLE_GEMINI_GRAPHDB")
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI_GRAPHDB)

    # Connection to neo4j database
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    try:
        chunks = read_csv_chunks(video_id, meta_data)
    except Exception as e:
        log.error("download_pipeline_youtube: Transcript CSV could not be read: %s", e)
        return 500, "Internal error when trying to read Transcript CSV File. Please contact a developer."
    try:
        frames = read_csv_frames(video_id)
    except Exception as e:
        log.error("download_pipeline_youtube: Frame description CSV could not be read: %s", e)
        return 500, "Internal error when trying to read Frame description CSV File. Please contact a developer."
    
    requests_made = 0
    
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction="""
        You are an expert in Machine Learning (ML) and Natural Language Processing (NLP). 
        Your task is to extract entities and relationships specifically relevant to ML from text.

        Entities include:
        - ML methods, algorithms, datasets, tools, frameworks, performance metrics, and general concepts.

        Relationships are:
        - Domain-specific actions or associations (e.g., uses, trains, evaluates, is_based_on).

        Output should strictly follow this format:
        Node: <Entity1>
        Node: <Entity2>
        Relationship: <Entity1>, <Relationship>, <Entity2>

        Focus on extracting only meaningful ML-related entities and relationships.
        Do not include generic or unrelated information. Adhere to all formatting rules.
        """)

    for chunk in chunks:
        user_prompt = f"""
            Extract all Entities and their relationships from the following text:
            {chunk}
            """
      
        if requests_made >= 14:
            log.info("Rate limit reached. Sleeping for 50 seconds.")
            time.sleep(50)
            requests_made = 0

        # Extract entities and relation from transcript chunks
        try:
            response = model.generate_content(contents=user_prompt)
            print(response.text)
            requests_made += 1
        except Exception as e:
            log.error("load_csv_to_graphdb: API Call failed: %s", e)
            return 500, "Internal error when trying get response from API Call for graph_db Entity extraction. Please contact a developer."
               
        # Prepare LLM-answer for graph_db
        try:
            graph_data = parse_response_to_graph(response.text)
        except Exception as e:
            log.error("load_csv_to_graphdb: Data preparation for graph_db failed: %s", e)
            return 500, "Internal error when trying prepare LLM response for graph_db. Please contact a developer."
        
        # Insert Nodes and Relations to graph_db
        try:
            add_nodes_to_graphdb(graph_data, driver, chunk, meta_data)
        except Exception as e:
            log.error("load_csv_to_graphdb: Node/relation insertion failed: %s", e)
            return 500, "Internal error when trying to insert nodes and relations into graph_db. Please contact a developer."
    try:
        add_attributes_to_nodes(driver, meta_data, frames)
    except Exception as e:
        log.error("load_csv_to_graphdb: Node attribute insertion failed: %s", e)
        return 500, "Internal error when trying to insert nodes attributes. Please contact a developer."
    
    driver.close()