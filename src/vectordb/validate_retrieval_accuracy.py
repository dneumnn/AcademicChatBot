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
    """List collections and let the user pick one by number."""
    collections = client.list_collections()
    if not collections:
        print("No collections found in the Chroma Database.")
        return None
    print("Collections in the Chroma Database:")
    for idx, name in enumerate(collections):
        print(f"{idx+1}. {name}")
    try:
        choice = int(input("Choose a collection by number: ")) - 1
        if choice < 0 or choice >= len(collections):
            print("Invalid choice.")
            return None
        return collections[choice]
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
            "query": "What's the difference between artificial intelligence and machine learning?",
            "relevant_ids": [
                "row_0_1737028307",  # Discusses AI vs. ML distinctions
                "row_3_1737028307",  # Explains ML as a capability within AI
                "row_12_1737028308", # Mentions the Venn diagram (ML as a subset of AI)
                "row_13_1737028308"  # Concludes ML is indeed a subset of AI
            ]
        },
        {
            "query": "How are deep learning and neural networks related?",
            "relevant_ids": [
                "row_6_1737028307",  # Introduces deep learning as a subfield of ML
                "row_7_1737028307"   # Explains neural networks and their layers in deep learning
            ]
        },
            {
        "query": "What's the difference between supervised and unsupervised machine learning?",
        "relevant_ids": [
            "row_5_1737028307",  # Mentions supervised vs. unsupervised ML
            "row_6_1737028307"   # Continues discussing the difference
        ]
    },
    {
        "query": "What does robotics have to do with AI?",
        "relevant_ids": [
            "row_9_1737028307",  # Mentions AI systems being able to see/hear (human-like capabilities)
            "row_11_1737028307"  # Explicitly references robotics as a subset of AI
        ]
    }
    ]


    precision_values = []
    recall_values = []

    for i, test_query in enumerate(test_queries):
        if i == 0:
            k = 4
        else:
            k = 2

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