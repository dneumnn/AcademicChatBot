import os
from config import INPUT_DIR, PROCESSED_DIR, MAX_SENTENCES_PER_CHUNK, OVERLAP_SENTENCES
from chunker.chunker import load_text, chunk_text_nltk, save_chunks
from vectorizer import vectorize_chunks
from database import store_vectors

if __name__ == "__main__":
    input_file = os.path.join(INPUT_DIR, "example_transcript.txt")
    output_file = os.path.join(PROCESSED_DIR, "vector_chunks_example.txt")

    # Text laden
    text = load_text(input_file)
    # Chunks erstellen
    chunks = chunk_text_nltk(text, MAX_SENTENCES_PER_CHUNK, OVERLAP_SENTENCES)
    # Chunks speichern
    save_chunks(chunks, output_file)

    # Chunks vectorisieren
    vectors = vectorize_chunks(chunks)

    # Vektoren in die Datenbank speichern
    store_vectors(chunks, vectors)

    print("Vectorisierung und Speicherung erfolgreich abgeschlossen!")
    print(f"Anzahl Chunks: {len(chunks)}")
