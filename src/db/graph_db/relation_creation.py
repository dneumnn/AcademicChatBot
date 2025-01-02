# File for the node relations 
# Linear relationships: NEXT and PREVIOUS model the sequence and make navigation easier

def create_next_relationship(tx, node_id1, node_id2):
    query = """
    MATCH (c1:TranscriptChunk {node_id: $chunk_id1})
    MATCH (c2:TranscriptChunk {node_id: $chunk_id2})
    CREATE (c1)-[:NEXT]->(c2)
    """
    tx.run(query, chunk_id1=node_id1, chunk_id2=node_id2)



