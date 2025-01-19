import csv
import os
import chromadb
import time
import re
# from config import INPUT_DIR, DB_DIR
from sentence_transformers import SentenceTransformer
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # AcademicChatBot
INPUT_DIR = os.path.join(BASE_DIR, 'media') # AcademicChatBot/media
DB_DIR = os.path.join(BASE_DIR, 'db', 'chromadb') # AcademicChatBot/db/chromadb
model = SentenceTransformer("all-MiniLM-L6-v2")

def create_embedding(text):
    try:
        return model.encode(text).tolist()
    except Exception as e:
        print("Fehler beim Generieren des Embeddings:", e)
        return [0.0] * 384

def generate_vector_db(video_id):
    csv_path = os.path.join(INPUT_DIR, video_id, "transcripts_chunks", f"{video_id}.csv") # Pfad zur CSV-Datei
    
    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        first_row = next(reader, None)
        if not first_row or not first_row.get("video_topic"):
            print("Fehlende 'video_topic' in CSV.")
            return
        collection_name = first_row["video_topic"].strip()
        collection_name = re.sub(r'[^a-zA-Z0-9_-]', '_', collection_name)
        file.seek(0)
        reader = csv.DictReader(file)

        client = chromadb.PersistentClient(path=DB_DIR)
        all_collections = [c.name for c in client.list_collections()]
        if collection_name in all_collections:
            collection = client.get_collection(name=collection_name)
        else:
            collection = client.create_collection(name=collection_name)

        valid_entries = 0
        for i, row in enumerate(reader):
            if not row.get("time") or not row.get("chunks") or not row.get("length"):
                continue
            embedding = create_embedding(row["chunks"])
            unique_id = f"row_{i}_{int(time.time())}"
            meta = {
                "time": row["time"],
                "length": row["length"],
                "video_id": row.get("video_id"),
                "video_topic": row.get("video_topic"),
                "video_title": row.get("video_title"),
                "video_uploaddate": row.get("video_uploaddate"),
                "video_duration": row.get("video_duration"),
                "channel_url": row.get("channel_url"),
            }
            collection.add(
                embeddings=[embedding],
                documents=[row["chunks"]],
                metadatas=[meta],
                ids=[unique_id]
            )
            valid_entries += 1
            if valid_entries % 50 == 0:
                print(f"{valid_entries} Datensätze erfolgreich gespeichert.")

    print(f"Fertig! Insgesamt {valid_entries} Datensätze in der Vector Datenbank gespeichert.")
