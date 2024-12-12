import os

def load_text(file_path: str) -> str:
    """Lädt den gesamten Inhalt einer Textdatei und gibt ihn als String zurück."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def chunk_text(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    """
    Teilt den Text in Chunks der Länge 'chunk_size' auf.
    Ein optionaler Overlap sorgt dafür, dass sich die Chunks inhaltlich überlappen.
    """
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        chunks.append(chunk)

        # Beim nächsten Chunk etwas zurückgehen, um Overlap zu erzeugen
        step = chunk_size - overlap if chunk_size > overlap else chunk_size
        start += step

    return chunks

def save_chunks(chunks: list[str], output_file: str):
    """Speichert die Chunks in einer Ausgabedatei. Hier einfach alle Chunks hintereinander mit Trenner."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, c in enumerate(chunks):
            f.write(f"--- Chunk {i} ---\n{c}\n\n")
