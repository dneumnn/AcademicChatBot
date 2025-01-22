import chromadb
from config import DB_DIR

def compute_precision_at_k(actual_ids, retrieved_ids, k):
    """Gibt die Precision@K zurück (relevante Treffer in Top-K / K)."""
    if k == 0 or not retrieved_ids:
        return 0.0
    relevant_count = sum(1 for rid in retrieved_ids[:k] if rid in actual_ids)
    return relevant_count / float(k)

def compute_recall_at_k(actual_ids, retrieved_ids, k):
    """Gibt die Recall@K zurück (relevante Treffer in Top-K / Gesamtzahl relevanter IDs)."""
    if not actual_ids:
        return 0.0
    relevant_count = sum(1 for rid in retrieved_ids[:k] if rid in actual_ids)
    return relevant_count / float(len(actual_ids))

def choose_collection(client):
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
    # Verbindung zur bestehenden DB
    try:
        client = chromadb.PersistentClient(path=DB_DIR)
    except Exception as e:
        print(f"Fehler bei der DB-Verbindung: {e}")
        return

    collection_name = choose_collection(client)
    if not collection_name:
        return
    try:
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        print(f"Fehler beim Zugriff auf die Collection '{collection_name}': {e}")
        return

    # Test-Queries mit relevanten IDs
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
    recall_values = []

    for i, test_query in enumerate(test_queries):
        if i == 0:
            k = 5
        else:
            k = 5

        query_text = test_query["query"]
        actual_ids = test_query["relevant_ids"]

        # Hole Top-K Ergebnisse
        try:
            results = collection.query(query_texts=[query_text], n_results=k)
            retrieved_ids = results.get("ids", [[]])[0] if "ids" in results else []
            # Print document content for each retrieved ID
        except Exception as e:
            print(f"Fehler bei der Abfrage '{query_text}': {e}")
            continue

        # Berechne Precision@K und Recall@K
        precision = compute_precision_at_k(actual_ids, retrieved_ids, k)
        recall = compute_recall_at_k(actual_ids, retrieved_ids, k)

        print(f"Query: {query_text}")
        print(f"  Relevant IDs: {actual_ids}")
        print(f"  Retrieved IDs (Top-{k}): {retrieved_ids}")
        print(f"  → Precision@{k}: {precision:.2f}")
        print(f"  → Recall@{k}: {recall:.2f}")
        print("")

        precision_values.append(precision)
        recall_values.append(recall)

    if precision_values and recall_values:
        avg_precision = sum(precision_values) / len(precision_values)
        avg_recall = sum(recall_values) / len(recall_values)
        print(f"Durchschnittliche Precision@{k}: {avg_precision:.2f}")
        print(f"Durchschnittliche Recall@{k}: {avg_recall:.2f}")
    else:
        print("Keine validen Testergebnisse gefunden.")

if __name__ == "__main__":
    main()