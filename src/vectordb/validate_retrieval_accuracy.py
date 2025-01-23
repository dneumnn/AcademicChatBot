import chromadb
from config import DB_DIR

def compute_precision_at_k(actual_ids, retrieved_ids, k):
    # Berechnung, wie viele der abgerufenen Dokumente tatsächlich relevant sind (Quotient relevanter Treffer durch k)
    if k == 0 or not retrieved_ids:
        return 0.0
    relevant_count = sum(1 for rid in retrieved_ids[:k] if rid in actual_ids)
    return relevant_count / float(k)

def choose_collection(client):
    # Auflistung aller Collections und Auswahl einer Collection aus der Chroma-Datenbank (für test Query: Finance)
    collections = client.list_collections()
    if not collections:
        print("No collections found in the Chroma Database.")
        return None
    print("Collections in the Chroma Database:")
    for idx, col in enumerate(collections):
        print(f"{idx+1}. {col.name}")
    try:
        choice = int(input("Choose a collection by number: ")) - 1
        if choice < 0 or choice >= len(collections):
            print("Invalid choice.")
            return None
        return collections[choice].name
    except ValueError:
        print("Invalid input.")
        return None

def main():
    # Verbindung zur Datenbank
    try:
        client = chromadb.PersistentClient(path=DB_DIR)
    except Exception as e:
        print(f"Fehler bei der DB-Verbindung: {e}")
        return

    # Verbindung zur Collection
    collection_name = choose_collection(client)
    if not collection_name:
        return
    try:
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        print(f"Fehler beim Zugriff auf die Collection '{collection_name}': {e}")
        return

    # Test Queries mit relevanten IDs (Basisvideo: But how does Bitcoin actually work?)
    test_queries = [
        {
            "query": "How do digital signatures work in Bitcoin?",
            "relevant_ids": [
                "row_9_1737477365",
                "row_10_1737477366",
                "row_11_1737477366",
                "row_12_1737477366",
                "row_13_1737477366",
                "row_17_1737477366",
                "frame_17_1737477368",
                "frame_19_1737477368",
                "frame_37_1737477369",
                "frame_44_1737477370"
            ]
        },
        {
            "query": "How does proof-of-work secure the Bitcoin blockchain?",
            "relevant_ids": [
                "row_28_1737477366",
                "row_33_1737477367",
                "row_34_1737477367",
                "row_35_1737477367",
                "row_36_1737477367",
                "row_38_1737477367",
                "row_51_1737477367",
                "frame_2_1737477368",
                "frame_20_1737477369",
                "frame_36_1737477369"
            ]
        }
    ]

    precision_values = []

    # Iteration über alle Test-Queries
    for i, test_query in enumerate(test_queries):
        k = 5 # Parameter zum Einstellen der Top-K Ergebnisse

        query_text = test_query["query"]
        actual_ids = test_query["relevant_ids"]

        # Extrahieren der top K Ergebnisse für die aktuelle Abfrage
        try:
            results = collection.query(query_texts=[query_text], n_results=k)
            retrieved_ids = results.get("ids", [[]])[0] if "ids" in results else []
        except Exception as e:
            print(f"Fehler bei der Abfrage '{query_text}': {e}")
            continue

        # Ermittlung der Precision@k für die aktuelle Abfrage
        precision = compute_precision_at_k(actual_ids, retrieved_ids, k)

        print(f"Query: {query_text}")
        print(f"  Relevant IDs: {actual_ids}")
        print(f"  Retrieved IDs (Top-{k}): {retrieved_ids}")
        print(f"  → Precision@{k}: {precision:.2f}")
        print("")

        precision_values.append(precision)

    # Zusammenfassung des Durchschnitss der Precision über alle Test-Queries.
    if precision_values:
        avg_precision = sum(precision_values) / len(precision_values)
        print(f"Durchschnittliche Precision@{k}: {avg_precision:.2f}")
    else:
        print("Keine validen Testergebnisse gefunden.")

if __name__ == "__main__":
    main()