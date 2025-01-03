import csv
import os
import chromadb
import openai
from config import INPUT_DIR

# Setze den OpenAI API-Schlüssel
openai.api_key = os.getenv("OPENAI_API_KEY")

def create_embedding(text):
    """
    Erzeugt ein Embedding für den übergebenen Text mit dem OpenAI-Modell 'text-embedding-ada-002'.
    """
    try:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response["data"][0]["embedding"]
    except Exception as e:
        print(f"Fehler beim Erstellen des Embeddings: {e}")
        return [0.0] * 1536

def main():
    csv_path = os.path.join(INPUT_DIR, "Yq0QkCxoTHM.csv")
    client = chromadb.PersistentClient(path="AcademicChatBot/db/chromadb")

    # Collection prüfen oder erstellen
    collection_name = "youtube_chunks"
    try:
        existing_collection = client.get_collection(name=collection_name)
        # Überprüfe die Dimension
        dimension = existing_collection.metadata.get("dimension") if existing_collection.metadata else None
        if dimension != 1536:
            # Falsche Dimension: Lösche und erstelle neu
            client.delete_collection(name=collection_name)
            collection = client.create_collection(
                name=collection_name,
                metadata={"dimension": 1536}
            )
        else:
            # Collection hat die korrekte Dimension
            collection = existing_collection
    except chromadb.errors.InvalidCollectionException:
        # Collection existiert nicht: Neu erstellen
        collection = client.create_collection(
            name=collection_name,
            metadata={"dimension": 1536}
        )

    # Daten aus der CSV-Datei verarbeiten und in die Collection einfügen
    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        valid_entries = 0

        for i, row in enumerate(reader):
            if not row.get("time") or not row.get("chunks") or not row.get("length"):
                continue  # Überspringt unvollständige Einträge

            embedding = create_embedding(row["chunks"])
            collection.add(
                embeddings=[embedding],
                documents=[row["chunks"]],
                metadatas=[{"time": row["time"], "length": row["length"]}],
                ids=[f"row_{i}"]
            )
            valid_entries += 1
            if valid_entries % 50 == 0:
                print(f"{valid_entries} Datensätze erfolgreich gespeichert.")

    print(f"Fertig! Insgesamt {valid_entries} Datensätze gespeichert.")




if __name__ == "__main__":
    main()