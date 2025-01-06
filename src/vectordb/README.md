# AcademicChatBot Vektordatenbank

Dieses Projekt nutzt [Chromadb](https://docs.trychroma.com/) zum Speichern und Abfragen von Vektoren. Neben der Datenbank enthält es Skripte zum Einlesen, Embedding, Validieren und Abfragen der Vektordatenbank.

---

## Dateien und Funktionen

### 1. config.py
Enthält globale Einstellungen:
- `INPUT_DIR`: Verzeichnis, in dem die CSV-Dateien abgelegt sind.  
- `DB_DIR`: Verzeichnis, in dem die chromadb abgelegt ist.  

Das Skript dient ausschließlich als Konfigurationsquelle, auf die andere Module zugreifen.

### 2. main.py
Hauptskript zum Einlesen und Speichern von YouTube-Video-Chunks in die Vektordatenbank:
- Liest eine CSV-Datei ein, die Informationen zu YouTube-Video-Chunks enthält.
- Generiert Embeddings für die Text-Chunks mithilfe von SentenceTransformer.
- Speichert die Embeddings zusammen mit den zugehörigen Metadaten in der Chromadb-Datenbank.

#### Funktionen:
- `create_embedding(text)`: Erstellt ein Embedding für den gegebenen Text mithilfe von SentenceTransformer.
- `main()`: Liest eine CSV-Datei ein, generiert Embeddings für die Text-Chunks und speichert diese in der Chromadb-Datenbank.

### 3. validate_db.py
- Bietet zwei Hauptfunktionen:  
  1. `validate_db()`: Wählt ein zufälliges Dokument aus der Vektordatenbank (Collection "youtube_chunks"), gibt sein Embedding aus und führt eine Ähnlichkeitsabfrage durch.  
  2. `find_most_similar(question)`: Fragt die Collection "youtube_chunks" nach dem am stärksten ähnlichen Dokument zum eingegebenen Text ab.
- Nutzt SentenceTransformer, um Texte in Embeddings zu verwandeln.

#### Funktionen:
- `validate_db()`: Validiert die gespeicherten Embeddings in der Datenbank.
- `find_most_similar(question)`: Findet das ähnlichste Dokument zu einer gegebenen Frage.

---

## Zugriff auf die Datenbank

- Die Chromadb-Datenbank wird in den Skripten über `chromadb.PersistentClient(...)` initialisiert.  
- Jede Collection kann über `create_collection` oder `get_collection` bezogen werden.  
- Neue Einträge (Vektoren und zugehörige Metadaten) werden über `collection.add(...)` mit einer Unique_ID (über Zeitstempel) hinzugefügt.  
- Abfragen erfolgen mit `collection.query(...)`.

---

## Installation und Ausführung

1. **Vorbereitung**  
   - Stellen Sie sicher, dass Python 3.10+ installiert ist.  
   - Installieren Sie die benötigten Bibliotheken, z.B. mit `pip install -r requirements.txt`.

2. **Validierung**  
   - Starten Sie `python validate_db.py`, um die Vektordatenbank zu prüfen und Test-Abfragen durchzuführen.  

---

## Wichtige Hinweise

- Das Projekt nutzt SentenceTransformer für Embeddings.
- Im Ordner `data/input` sollten die CSV-Dateien liegen, die in die Datenbank importiert werden.  
- Achten Sie darauf, dass Chromadb schreib- und leseberechtigt ist (Pfad `AcademicChatBot/db/chromadb`).
