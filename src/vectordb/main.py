import csv
import os
import chromadb
import time
import re
# from config import INPUT_DIR, DB_DIR
from sentence_transformers import SentenceTransformer

# Pfade für verschieden Directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # AcademicChatBot
INPUT_DIR = os.path.join(BASE_DIR, 'media') # AcademicChatBot/media
DB_DIR = os.path.join(BASE_DIR, 'db', 'chromadb') # AcademicChatBot/db/chromadb
model = SentenceTransformer("all-MiniLM-L6-v2") # Model für Sentence Embeddings


def create_embedding(text): # Erstellt die Vektor Embeddings
    try:
        return model.encode(text).tolist()
    except Exception as e:
        # Fallback, falls ein Fehler auftritt; es werden Nullvektoren zurückgegeben
        print("Fehler beim Generieren des Embeddings:", e)
        return [0.0] * 384

def remove_leading_non_alphabetic_characters(name):
    # Entfernt Zeichen am Anfang, bis ein Buchstabe (a-z oder A-Z) gefunden wird
    return re.sub(r'^[^a-zA-Z]+', '', name)

def remove_trailing_non_alphabetic_characters(name):
    # Entfernt Zeichen am Ende, bis ein Buchstabe (a-z oder A-Z) gefunden wird
    return re.sub(r'[^a-zA-Z]+$', '', name)

def generate_vector_db(video_id): # Liest die passende Csv Datei aus und erzeugt eine ChromaDB-Collection
    
    csv_path = os.path.join(INPUT_DIR, video_id, "transcripts_chunks", f"{video_id}.csv") # Pfad zur CSV-Datei für Transkript-Chunks
    
    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        first_row = next(reader, None)

        # Prüfen, ob video topic in der CSV vorhanden ist
        if not first_row or not first_row.get("video_topic"):
            print("Fehlende 'video_topic' in CSV.")
            return
        
        # Ersetzen der Sonderzeichen im Namen der Collection (auch Leerzeichen) und Generierung des Namens für die Collection
        collection_name = first_row["video_topic"].strip()
        print("Generiere Collection Name")
        collection_name = remove_leading_non_alphabetic_characters(collection_name)
        collection_name = remove_trailing_non_alphabetic_characters(collection_name)
        collection_name = re.sub(r'[^a-zA-Z0-9_-]', '_', collection_name)
        file.seek(0) # Zurücksetzen des Lesezeigers
        reader = csv.DictReader(file)

        # Verbindung zur ChromaDB
        client = chromadb.PersistentClient(path=DB_DIR)

        # Checkt, ob bereits eine Collection mit dem collection_name existiert oder erstellt eine neue
        all_collections = [c.name for c in client.list_collections()]
        if collection_name in all_collections:
            collection = client.get_collection(name=collection_name)
        else:
            collection = client.create_collection(name=collection_name)

        # Erstellung einer Fallback collection, falls RAG Team die spezifische Collection nicht finden kann
        fallback_name = "fallback"
        if fallback_name in all_collections:
            fallback_collection = client.get_collection(name=fallback_name)
        else:
            fallback_collection = client.create_collection(name=fallback_name)

        valid_entries = 0
        for i, row in enumerate(reader):
            
            if not row.get("time") or not row.get("chunks") or not row.get("length"):
                continue

            embedding = create_embedding(row["chunks"]) # Erzeugt Embeddings für die Chunks
            unique_id = f"row_{i}_{int(time.time())}" # Erzeugung einer Eindeutigen ID für jeden Chunk
            
            # Definition der Metadatenpunkte
            meta = {
                "time": row["time"],
                "length": row["length"],
                "video_id": row.get("video_id"),
                "video_topic": row.get("video_topic"),
                "video_title": row.get("video_title"),
                "video_uploaddate": row.get("video_uploaddate"),
                "video_duration": row.get("video_duration"),
                "channel_url": row.get("channel_url"),
                "is_image_description": False # Hier False da Textchunk (wird vom RAG Team für die Suche verwendet)
            }
            collection.add(
                # Hinzufügen zur Collection mit Namen aus der CSV
                embeddings=[embedding],
                documents=[row["chunks"]],
                metadatas=[meta],
                ids=[unique_id]
            )
            fallback_collection.add(
                # Hinzufügen zur Fallback Collection
                embeddings=[embedding],
                documents=[row["chunks"]],
                metadatas=[meta],
                ids=[unique_id]
            )
            valid_entries += 1
            if valid_entries % 50 == 0:
                # Zwischenausgabe für Statusfortschritt
                print(f"{valid_entries} Datensätze erfolgreich gespeichert.")


    # Verarbeitung der Frame Beschreibungen
    frames_csv_path = os.path.join(INPUT_DIR, video_id, "frames_description", "frame_descriptions.csv")
    
    # Prüfen, ob die Frames-CSV existiert
    if os.path.exists(frames_csv_path):
        # Falls eine Frames-CSV existiert, werden deren Beschreibungen ebenfalls hinzugefügt
        with open(frames_csv_path, mode="r", encoding="utf-8") as frames_file:
            frames_reader = csv.DictReader(frames_file)
            frame_entries = 0
            for row in frames_reader:
                if not row.get("description"):
                    continue
                description_embedding = create_embedding(row["description"])
                frame_unique_id = f"frame_{frame_entries}_{int(time.time())}"
                frame_meta = {
                    "video_id": row.get("video_id"),
                    "time": row.get("time_in_s"),
                    "is_image_description": True # Hier True da Bildbeschreibung (wird vom RAG Team für die Suche verwendet)
                }
                collection.add(
                    embeddings=[description_embedding],
                    documents=[row["description"]],
                    metadatas=[frame_meta],
                    ids=[frame_unique_id]
                )
                fallback_collection.add(
                    embeddings=[description_embedding],
                    documents=[row["description"]],
                    metadatas=[frame_meta],
                    ids=[frame_unique_id]
                )
                frame_entries += 1
            print(f"Fertig! {frame_entries} Frame-Beschreibungen in die Collection '{collection_name}' und 'fallback' gespeichert.")
    else:
        print("Keine 'frame_descriptions.csv' Datei gefunden; Überspringe Frames.")

    print(f"Fertig! Insgesamt {valid_entries} Chunks in der Vector Datenbank in der Collection '{collection_name}' und 'fallback' gespeichert.")