import csv
import os
import chromadb
import subprocess
import json
import time
from config import INPUT_DIR
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def create_embedding(text):
    try:
        return model.encode(text).tolist()
    except Exception as e:
        print("Fehler beim Generieren des Embeddings:", e)
        return [0.0] * 384

def main():
    csv_path = os.path.join(INPUT_DIR, "Yq0QkCxoTHM.csv") # Pfad zur CSV-Datei
    client = chromadb.PersistentClient(path="AcademicChatBot/db/chromadb") # Verbindung zur Datenbank
    collection = client.create_collection(
        name="youtube_chunks"
    )

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file) # Lese die CSV-Datei
        valid_entries = 0 # Zähler für gültige Einträge

        for i, row in enumerate(reader):
            if not row.get("time") or not row.get("chunks") or not row.get("length"): 
                continue  # Überspringt unvollständige Einträge

            embedding = create_embedding(row["chunks"]) # Generiere das Embedding
            unique_id = f"row_{i}_{int(time.time())}" # Erzeuge eine eindeutige ID
            collection.add( # Füge den Eintrag zur Datenbank hinzu
                embeddings=[embedding], 
                documents=[row["chunks"]],
                metadatas=[{"time": row["time"], "length": row["length"]}],
                ids=[unique_id]
            )
            valid_entries += 1
            if valid_entries % 50 == 0: # Alle 50 Einträge speichern
                print(f"{valid_entries} Datensätze erfolgreich gespeichert.")

    print(f"Fertig! Insgesamt {valid_entries} Datensätze gespeichert.") # Ausgabe der Anzahl der gespeicherten Datensätze

if __name__ == "__main__":
    main()