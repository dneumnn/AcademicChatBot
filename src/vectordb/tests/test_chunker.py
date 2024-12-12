import os
import pytest
from src.vectordb.config import INPUT_DIR, CHUNK_SIZE, OVERLAP
from src.vectordb.chunker.chunker import load_text, chunk_text

def test_load_text():
    # Überprüfe, ob der Text tatsächlich geladen wird.
    # Stelle sicher, dass die Datei example_transcript.txt unter data/input liegt.
    input_file = os.path.join(INPUT_DIR, "example_transcript.txt")
    text = load_text(input_file)
    assert len(text) > 0, "Der geladene Text sollte nicht leer sein."

def test_chunk_text():
    # Test mit einem kurzen Testtext, um die Chunk-Funktion zu überprüfen.
    text = "Dies ist ein kurzer Testtext. Er dient zum Testen des Chunkings."
    test_chunk_size = 20
    test_overlap = 5

    chunks = chunk_text(text, test_chunk_size, test_overlap)

    # Es sollte mindestens ein Chunk erstellt werden.
    assert len(chunks) > 0, "Es sollte mindestens einen Chunk geben."
    
    # Wenn es mehrere Chunks gibt, prüfen wir, ob der Overlap korrekt angewendet wurde.
    if len(chunks) > 1:
        first_chunk = chunks[0]
        second_chunk = chunks[1]
        overlap_region_first = first_chunk[-test_overlap:]
        assert overlap_region_first in second_chunk, "Der Overlap des ersten Chunks sollte im zweiten Chunk vorkommen."
