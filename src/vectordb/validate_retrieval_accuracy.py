
import chromadb

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

def main():
    # Verbindung zur bestehenden DB (analog zu main.py)
    try:
        client = chromadb.PersistentClient(path="AcademicChatBot/db/chromadb")
        collection = client.get_collection(name="youtube_chunks")
    except Exception as e:
        print(f"Fehler bei der DB-Verbindung: {e}")
        return

    # Test-Queries mit relevanten IDs
    test_queries = [
        {"query": "Wie installiere ich Python?", "relevant_ids": ["row_10_...", "row_25_..."]},
        # ...weitere Test-Queries...
    ]

    k = 5
    precision_values = []
    recall_values = []

    for test_query in test_queries:
        query_text = test_query["query"]
        actual_ids = test_query["relevant_ids"]

        # Hole Top-K Ergebnisse
        try:
            results = collection.query(query_texts=[query_text], n_results=k)
            retrieved_ids = results.get("ids", [[]])[0] if "ids" in results else []
        except Exception as e:
            print(f"Fehler bei der Abfrage '{query_text}': {e}")
            continue

        # Berechne Precision@K und Recall@K
        precision = compute_precision_at_k(actual_ids, retrieved_ids, k)
        recall = compute_recall_at_k(actual_ids, retrieved_ids, k)
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