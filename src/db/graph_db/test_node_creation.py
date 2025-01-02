 

import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)
import csv
from src.db.graph_db.db_handler import GraphHandler


def read_csv_chunks(file_path):
    chunks = []
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            node_id = f"TextChunk{index:02d}"
            chunks.append({
                "node_id": node_id,
                "sentence": row["sentence"],
                "time": row["start_time"],
                "length": int(row["length"])
            })
    return chunks

def main():

    csv_file_path = "test_chunks.csv"

    uri = "bolt://localhost:7687"  
    user = "neo4j"  
    password = "this_pw_is_a_test25218###1119jj" 

    graph_handler = GraphHandler(uri, user, password) 

    try:
        chunks = read_csv_chunks(csv_file_path)

        graph_handler.create_transcript_chunk_session(chunks)
        print("Nodes successfully created!")
        graph_handler.create_chunk_next_relation_session(chunks)
        print("Relations successfully created!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        graph_handler.close()

    
if __name__ == "__main__":
    main()