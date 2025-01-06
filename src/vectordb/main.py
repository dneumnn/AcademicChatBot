import csv
import os
import chromadb
import subprocess
import json
from config import INPUT_DIR

def create_embedding(text): # Ruft das ollama-CLI-Modell auf und gibt das Embedding zurück.
    try: # Versuche, das Embedding zu generieren
        command = ["ollama", "generate", "-m", "nomic-embed-text", text]
        result = subprocess.run(command, capture_output=True, text=True, check=True) 
        data = json.loads(result.stdout) 
        return data.get("embedding", [])
    except Exception as e:
        # Fallback, falls ein Fehler auftritt
        return [0.0] * 768 

def main():
    csv_path = os.path.join(INPUT_DIR, "Yq0QkCxoTHM.csv") # Pfad zur CSV-Datei
    client = chromadb.PersistentClient(path="AcademicChatBot/db/chromadb") # Verbindung zur Datenbank
    collection = client.get_or_create_collection(name="youtube_chunks") # Erstelle eine Sammlung TODO

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file) # Lese die CSV-Datei
        valid_entries = 0 # Zähler für gültige Einträge

        for i, row in enumerate(reader):
            if not row.get("time") or not row.get("chunks") or not row.get("length"): 
                continue  # Überspringt unvollständige Einträge

            embedding = create_embedding(row["chunks"]) # Generiere das Embedding
            collection.add( # Füge den Eintrag zur Datenbank hinzu
                embeddings=[embedding], 
                documents=[row["chunks"]],
                metadatas=[{"time": row["time"], "length": row["length"]}],
                ids=[f"row_{i}"]
            )
            valid_entries += 1
            if valid_entries % 50 == 0: # Alle 50 Einträge speichern
                print(f"{valid_entries} Datensätze erfolgreich gespeichert.")

    print(f"Fertig! Insgesamt {valid_entries} Datensätze gespeichert.") # Ausgabe der Anzahl der gespeicherten Datensätze

if __name__ == "__main__":
    main()