# AcademicChatBot Vektordatenbank

Dieses Projekt nutzt [Chromadb](https://docs.trychroma.com/) zum Speichern und Abfragen von Vektoren. Neben der Datenbank enthält es Skripte zum Einlesen, Embedding, Validieren und Abfragen von YouTube-Inhalten.

---

## Dateien und Funktionen

### 1. config.py
Enthält globale Einstellungen:
- `INPUT_DIR`: Verzeichnis, in dem die CSV-Dateien abgelegt sind.  
- `OPENAI_API_KEY`: Automatisch aus den Umgebungsvariablen gelesen.  

Das Skript dient ausschließlich als Konfigurationsquelle, auf die andere Module zugreifen.

### 2. main.py
Haupt-Entry-Point für die FastAPI-App:
- Stellt verschiedene Endpunkte bereit:  
  - "/" liefert eine einfache JSON-Antwort.  
  - "/analyze" überprüft, ob ein YouTube-Video existiert und startet dann die Verarbeitung (inklusive Download und Embedding).  
- Nutzt `download_pipeline_youtube(video_input)`, um den Video-Content zu verarbeiten.  
- Bei Erfolg wird der Inhalt als Vektoren in der Datenbank gespeichert.

#### Funktionen:
- `create_embedding(text)`: Erstellt ein Embedding für den gegebenen Text mithilfe von SentenceTransformer.
- `main()`: Liest eine CSV-Datei ein, generiert Embeddings für die Text-Chunks und speichert diese in der Chromadb-Datenbank.

### 3. validate_db.py
- Bietet zwei Hauptfunktionen:  
  1. `validate_db()`: Wählt ein zufälliges Dokument aus der Vektordatenbank (Collection "youtube_chunks"), gibt sein Embedding aus und führt eine Ähnlichkeitsabfrage durch.  
  2. `find_most_similar(question)`: Fragt die Collection "youtube_chunks2" nach dem am stärksten ähnlichen Dokument zum eingegebenen Text ab.  
- Nutzt SentenceTransformer, um Texte in Embeddings zu verwandeln.

#### Funktionen:
- `validate_db()`: Validiert die gespeicherten Embeddings in der Datenbank.
- `find_most_similar(question)`: Findet das ähnlichste Dokument zu einer gegebenen Frage.

---

## Zugriff auf die Datenbank

- Die Chromadb-Datenbank wird in den Skripten über `chromadb.PersistentClient(...)` initialisiert.  
- Jede Collection kann über `create_collection` oder `get_collection` bezogen werden.  
- Neue Einträge (Vektoren und zugehörige Metadaten) werden über `collection.add(...)` hinzugefügt.  
- Abfragen erfolgen mit `collection.query(...)`.

---

## Installation und Ausführung

1. **Vorbereitung**  
   - Stellen Sie sicher, dass Python 3.10+ installiert ist.  
   - Installieren Sie die benötigten Bibliotheken, z.B. mit `pip install -r requirements.txt`.

2. **Konfiguration**  
   - Passen Sie Pfade in `config.py` an, falls nötig.

3. **Validierung**  
   - Starten Sie `python validate_db.py`, um die Vektordatenbank zu prüfen und Test-Abfragen durchzuführen.  

---

## Wichtige Hinweise

- Das Projekt nutzt SentenceTransformer für Embeddings.
- Im Ordner `data/input` sollten die CSV-Dateien liegen, die in die Datenbank importiert werden.  
- Achten Sie darauf, dass Chromadb schreib- und leseberechtigt ist (Pfad `AcademicChatBot/db/chromadb`).
