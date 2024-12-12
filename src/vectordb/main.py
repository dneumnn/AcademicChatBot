import os
from src.vectordb.config import INPUT_DIR, PROCESSED_DIR, CHUNK_SIZE, OVERLAP
from src.vectordb.chunker.chunker import load_text, chunk_text, save_chunks

if __name__ == "__main__":
    input_file = os.path.join(INPUT_DIR, "example_transcript.txt")
    output_file = os.path.join(PROCESSED_DIR, "chunks_example.txt")

    # Text laden
    text = load_text(input_file)
    # Chunks erstellen
    chunks = chunk_text(text, CHUNK_SIZE, OVERLAP)
    # Chunks speichern
    save_chunks(chunks, output_file)

    print("Chunking erfolgreich abgeschlossen!")
    print(f"Anzahl Chunks: {len(chunks)}")