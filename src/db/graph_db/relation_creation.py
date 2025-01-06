# File for the node relations 
# Linear relationships: NEXT and PREVIOUS model the sequence and make navigation easier

def create_next_relationship(tx, chunk_id1, chunk_id2):
    query = """
    MATCH (c1:TranscriptChunk {id: $chunk_id1})
    MATCH (c2:TranscriptChunk {id: $chunk_id2})
    CREATE (c1)-[:NEXT]->(c2)
    """
    tx.run(query, chunk_id1=chunk_id1, chunk_id2=chunk_id2)

# Liste von Chunks
chunks = [
    {'chunk_id': 'chunk_001', 'text': 'Hallo, wie geht es dir?', 'embedding': [0.1, 0.2, 0.3]},
    {'chunk_id': 'chunk_002', 'text': 'Mir geht es gut, danke!', 'embedding': [0.2, 0.3, 0.4]},
    {'chunk_id': 'chunk_003', 'text': 'Was machst du heute?', 'embedding': [0.1, 0.1, 0.2]},
]
"""""
with driver.session() as session:
    for i in range(len(chunks) - 1):
        session.write_transaction(
            create_next_relationship,
            chunks[i]['chunk_id'],
            chunks[i + 1]['chunk_id']
        )
"""