import time
import os
import ast
import google.generativeai as genai
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from itertools import chain
from src.data_processing.logger import log
from src.db.graph_db.utilities import *



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

def add_relations_to_graphdb(graph_data, driver):
    """
    Fügt Knoten und Beziehungen in die Neo4j-Datenbank ein.
    """
    with driver.session() as session:                
        for relationship in graph_data["relationships"]:
            source, relation, target = relationship
            sanitized_relation = relation.replace(" ", "_").replace("-", "_").upper()
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

def add_attributes_to_nodes(driver, meta_data, frames, chunks):
    chunks_times = [chunk['time'] for chunk in chunks]
    frame_times, frame_file_names, frame_descriptions = zip(*[(frame['time'], frame['file_name'], frame['description']) for frame in frames])

    frame_times = list(frame_times)
    frame_file_names = list(frame_file_names)
    frame_descriptions = list(frame_descriptions)

    closest_matches = {}

    for chunk_time in chunks_times:
        closest_frame_index = min(range(len(frame_times)), key=lambda i: abs(frame_times[i] - chunk_time))
        closest_matches[chunk_time] = closest_frame_index  # Store the index of the closest frame time

    with driver.session() as session:

        for chunk_time, closest_frame_index in closest_matches.items():
            query = """
            MATCH (n:Entity)
            WHERE 
            ANY(i IN RANGE(0, SIZE(n.url_id) - 1) 
                WHERE n.url_id[i] = $id AND n.time[i] = $time)
            SET n.frame_name = coalesce(n.frame_name, []) + $frame_name, 
                n.frame_description = coalesce(n.frame_description, []) + $description
            """
        
            session.run(query, parameters={
            "id": meta_data.get('id'),
            "time": chunk_time,
            "frame_name": frame_file_names[closest_frame_index],
            "description": frame_descriptions[closest_frame_index]
            }) 
        
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
    try:
        entities = extract_entities(driver, chunks, meta_data)
    except Exception as e:
        log.error("download_pipeline_youtube: Entities could not be extracted: %s", e)
        return 500, "Internal error when trying to extract Entities from chunks. Please contact a developer."
    try:
        relations = create_relations(entities, chunks)
    except Exception as e:
        log.error("download_pipeline_youtube: Relations could not be created: %s", e)
        return 500, "Internal error when trying to create relations. Please contact a developer."
    try:
        add_relations_to_graphdb(relations, driver)
    except Exception as e:
        log.error("download_pipeline_youtube: Relations could not be inserted to graph_db: %s", e)
        return 500, "Internal error when trying to insert relations into graph_db. Please contact a developer."
    try:
        add_attributes_to_nodes(driver, meta_data, frames, chunks)
    except Exception as e:
        log.error("load_csv_to_graphdb: Node attribute insertion failed: %s", e)
        return 500, "Internal error when trying to insert nodes attributes. Please contact a developer."
    
    driver.close()

def extract_entities(driver, chunks, meta_data):
    requests_made = 0
    
    entity_model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction="""
        You are an expert in Machine Learning (ML), Natural Language Processing (NLP), Artifical Intelligence and Neuronal Networks.
        Your task is to extract entities from a given text. Focus on extracting only meaningful entities from your expert field.
        Do not include generic or unrelated information.

        Entity examples:
        - machine learning, neuronal network, alogrithm, data, supervised learning, training data, layer, weight, clustering, feature, ...
    
        Rules:
        - Format entities that are in plural to an entity in singular.
        
        Write all entities found in a list as in the following example:
        ['artificial intelligence', 'algorithm', 'pattern', 'data']""")
    
    entities_list = []

    for chunk in chunks:
        user_prompt = f"""
            Extract all Entities from the following text:
            {chunk}
            """
        if requests_made >= 14:
            log.info("Rate limit reached. Sleeping for 60 seconds.")
            time.sleep(60)
            requests_made = 0  

        # Extract entities from transcript chunks
        response = entity_model.generate_content(contents=user_prompt)
        requests_made += 1 
        entities = ast.literal_eval(response.text.strip())
        node_data = {"nodes": entities}
        print(node_data)
        entities_list.extend(entities) 
        cleaned_entities = list(dict.fromkeys(entities_list))

        add_nodes_to_graphdb(node_data, driver, chunk, meta_data)

           
    return cleaned_entities

def create_relations(entities, chunks):
    
    relation_model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction="""
        You are an expert in Machine Learning (ML), Natural Language Processing (NLP), Artifical Intelligence and Neuronal Networks.
        Your task is to create relations between entities based on information from a given text.

        Relation examples:
        - is_part_of, makes, based_on, extracts, is, from, uses, has, consists_of, maximizes, ...
            
        Output should strictly follow this format:
        Entity1, Relationship, Entity2.
                                           
        """)
    
    #for chunk in chunks:
    user_prompt = f"""
        Create reasonable relations for these entities: {entities}
        Use the information from this text to find relations between the entities: {chunks}
        """
    relationships = {
        "relationships": []
    }
    # Extract entities from transcript chunks
    response = relation_model.generate_content(contents=user_prompt)
    lines = response.text.strip().split("\n")
    for line in lines:
        parts = line.split(",")
        source = parts[0].strip()
        relation = parts[1].strip()
        target = parts[2].strip()
        relationships["relationships"].append((source, relation, target))

    return relationships
    