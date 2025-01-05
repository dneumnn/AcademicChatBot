# File for the node relations 
# Linear relationships: NEXT and PREVIOUS model the sequence and make navigation easier
# Linear relationship for transcript chunks
def create_next_relationship_transcript(tx, node_id1, node_id2):
    query = """
    MATCH (c1:TranscriptChunk {node_id: $chunk_id1})
    MATCH (c2:TranscriptChunk {node_id: $chunk_id2})
    MERGE (c1)-[:NEXT]->(c2)
    """
    tx.run(query, chunk_id1=node_id1, chunk_id2=node_id2)

# Linear relationship for frame description 
def create_next_relationship_frame(tx, frame_id1, frame_id2):
    query = """
    MATCH (f1:FrameDescription {frame_id: $chunk_id1})
    MATCH (f2:FrameDescription {frame_id: $chunk_id2})
    MERGE (f1)-[:NEXT]->(f2)
    """
    tx.run(query, chunk_id1=frame_id1, chunk_id2=frame_id2)

# Linear relationship between meta_data chunks and transcript chunks
def create_meta_data_relationship_to_transcript(tx, node_id, metadata_id):
    query = """
    MATCH (t:TranscriptChunk {node_id: $chunk_id})
    MATCH (m:MetaData {url_id: $metadata_id})
    MERGE (t)-[:HAS_METADATA]->(m)
    """
    tx.run(query, chunk_id=node_id, metadata_id=metadata_id)

# Linear relationship between meta_data chunks and frame description chunks
def create_meta_data_relationship_to_frame(tx, frame_id, metadata_id):
    query = """
    MATCH (f:FrameDescription {frame_id: $frame_id})
    MATCH (m:MetaData {url_id: $metadata_id})
    MERGE (t)-[:HAS_METADATA]->(m)
    """
    tx.run(query, frame_id=frame_id, metadata_id=metadata_id)

def create_frame_relationship_to_transcript(tx, frame_id, node_id):
    query = """"
    MATCH (f:FrameDescription {frame_id: $frame_id})
    MATCH (c:TranscriptChunk {node_id: $chunk_id})
    MERGE (f)-[:DESCRIBES]->(c)
    """
    tx.run(query, frame_id=frame_id, chunk_id=node_id)


def create_chunk_similartity_relationship(tx, node_id1, node_id2):
    query = """
    MATCH (c1:TranscriptChunk {node_id: $chunk_id1})
    MATCH (c2:TranscriptChunk {node_id: $chunk_id2})
    MERGE (t1)-[:SIMILAR_TO]->(t2)
    MERGE (t2)-[:SIMILAR_TO]->(t1)
    """
    tx.run(query, chunk_id1=node_id1, chunk_id2=node_id2) 