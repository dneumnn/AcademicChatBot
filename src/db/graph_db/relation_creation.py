# File for the node relations 
# Linear relationships: NEXT and PREVIOUS model the sequence and make navigation easier
# Linear relationship for transcript chunks
def create_next_relationship(tx, node_id1, node_id2):
    query = """
    MATCH (c1:TranscriptChunk {node_id: $chunk_id1})
    MATCH (c2:TranscriptChunk {node_id: $chunk_id2})
    MERGE (c1)-[:NEXT]->(c2)
    """
    tx.run(query, chunk_id1=node_id1, chunk_id2=node_id2)

# Linear relationship for frame description 

def create_next_relationship_frame(tx, frame_id1, frame_id2):
    query = """
    MATCH (f1:FrameChunk {frame_id: $chunk_id1})
    MATCH (f2:FrameChunk {frame_id: $chunk_id2})
    CREATE (f1)-[:NEXT]->(f2)
    """
    tx.run(query, chunk_id1=frame_id1, chunk_id2=frame_id2)

# Linear relationship between meta_data chunks and transcript chunks
def create_meta_data_relationship(tx, node_id, metadata_id):
    query = """
    MATCH (t:TranscriptChunk {node_id: $chunk_id})
    MATCH (m:MetaData {url_id: $metadata_id})
    MERGE (t)-[:HAS_METADATA]->(m)
    """
    tx.run(query, chunk_id=node_id, metadata_id=metadata_id)