# File for the node relations 

# Linear relationship for transcript chunks
def create_next_relationship_transcript(tx, node_id1, node_id2):
    query = """
    MATCH (c1:TranscriptChunk {node_id: $chunk_id1})
    MATCH (c2:TranscriptChunk {node_id: $chunk_id2})
    MERGE (c1)-[:NEXT]->(c2)
    """
    tx.run(query, chunk_id1=node_id1, chunk_id2=node_id2)

# Linear relationship between meta_data nodes and transcript chunk nodes
def create_meta_data_relationship_to_transcript(tx, node_id, metadata_id):
    query = """
    MATCH (t:TranscriptChunk {node_id: $chunk_id})
    MATCH (m:MetaData {url_id: $metadata_id})
    MERGE (t)-[:HAS_METADATA]->(m)
    """
    tx.run(query, chunk_id=node_id, metadata_id=metadata_id)

# Linear relationship between meta_data nodes and frame description chunk nodes
def create_meta_data_relationship_to_frame(tx, frame_id, metadata_id):
    query = """
    MATCH (f:FrameDescription {frame_id: $frame_id})
    MATCH (m:MetaData {url_id: $metadata_id})
    MERGE (t)-[:HAS_METADATA]->(m)
    """
    tx.run(query, frame_id=frame_id, metadata_id=metadata_id)

# Linear relationship between frame nodes and transcript chunk nodes
def create_frame_relationship_to_transcript(tx, frame_id, node_id):
    query = """"
    MATCH (f:FrameDescription {frame_id: $frame_id})
    MATCH (c:TranscriptChunk {node_id: $chunk_id})
    MERGE (f)-[:DESCRIBES]->(c)
    """
    tx.run(query, frame_id=frame_id, chunk_id=node_id)

# Bi-linear relationship for similar transcript chunk nodes
def create_chunk_similartity_relationship(tx, node_id1, node_id2):
    print(node_id1)
    print(node_id2)
    query = """
    MATCH (c1:TranscriptChunk {node_id: $chunk_id1})
    MATCH (c2:TranscriptChunk {node_id: $chunk_id2})
    MERGE (c1)-[:SIMILAR_TO]->(c2)
    MERGE (c2)-[:SIMILAR_TO]->(c1)
    """
    tx.run(query, chunk_id1=node_id1, chunk_id2=node_id2) 