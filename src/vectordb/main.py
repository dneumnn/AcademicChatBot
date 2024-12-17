import os
from config import INPUT_DIR, PROCESSED_DIR, MAX_SENTENCES_PER_CHUNK, OVERLAP_SENTENCES
from chunker.chunker import load_text, chunk_text_hf, save_chunks

if __name__ == "__main__":
    input_file = os.path.join(INPUT_DIR, "example_transcript.txt")
    output_file = os.path.join(PROCESSED_DIR, "vektor_chunks_example.txt")

    # Text laden
    text = load_text(input_file)
    # Chunks erstellen
    chunks = chunk_text_hf(text, MAX_SENTENCES_PER_CHUNK, OVERLAP_SENTENCES)
    # Chunks speichern
    save_chunks(chunks, output_file)

    print("Chunking erfolgreich abgeschlossen!")
    print(f"Anzahl Chunks: {len(chunks)}")
