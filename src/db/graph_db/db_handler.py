import ast
from neo4j import GraphDatabase
from src.db.graph_db.node_creation import *
from src.db.graph_db.relation_creation import *
from sklearn.metrics.pairwise import cosine_similarity

class GraphHandler:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # session functions for node creation
    def create_meta_data_session(self, meta_data):
        with self.driver.session() as session:
            session.execute_write(create_meta_data_node, meta_data)

    def create_transcript_chunk_session(self, chunks):
        with self.driver.session() as session:
            for chunk in chunks:
                session.execute_write(create_transcript_chunk_node, chunk)
    
    def create_frame_description_session(self, frames):
        with self.driver.session() as session:
            for frame in frames:
                session.execute_write(create_frame_description_node, frame)
    
    # sessions for relation creation
    def create_chunk_next_relation_session(self, chunks):
         with self.driver.session() as session:
            for i in range(len(chunks) - 1):
                session.execute_write(
                    create_next_relationship_transcript,
                    chunks[i]['node_id'],
                    chunks[i + 1]['node_id'])
                
    def create_chunk_metadata_relation_session(self, chunks, meta_data):
        with self.driver.session() as session:
            for chunk in chunks:
                session.execute_write(
                    create_meta_data_relationship_to_transcript,
                    chunk['node_id'],
                    meta_data['id']
                )
    
    def create_frameDescription_metadata_relation_session(self, frames, meta_data):
        with self.driver.session() as session:
            for frame in frames:
                session.execute_write(
                    create_meta_data_relationship_to_frame,
                    frame['frame_id'],
                    meta_data['id']
                )

    def create_frameDescription_transcript_relation_session(self, frames, chunks):
        with self.driver.session() as session:
            for frame in frames:
                matching_chunk = next(
                    (chunk for chunk in chunks if chunk["time"] == frame["time"]), None
                )
                if matching_chunk:
                    session.execute_write(
                        create_frame_relationship_to_transcript,
                        frame["frame_id"],
                        matching_chunk["node_id"]
                    )

    def create_chunk_similarity_relation_session(self, chunks, video_id):
        with self.driver.session() as session:
            
            # Get embeddings for current chunks in the db
            current_chunks = self.get_transcript_embeddings(video_id)
            current_chunks_formatted = {}
            for node_id, embedding_str in current_chunks.items():
                embedding = ast.literal_eval(embedding_str)  
                current_chunks_formatted[node_id] = [float(val) for val in embedding]
                
            # Get embeddings for new chunks
            new_embeddings = [ast.literal_eval(chunk["embedding"]) for chunk in chunks]
            
            # Set similarity threshold
            similarity_threshold = 0.8
            
            # Iterate through the new chunks
            for chunk, new_embedding in zip(chunks, new_embeddings):
                # Compare the new chunk to all current chunks
                for node_id, current_embedding in current_chunks_formatted.items():
                    similarity_score = cosine_similarity([new_embedding], [current_embedding])[0][0]
                    
                    # If similarity exceeds threshold, create the relationship
                    if similarity_score > similarity_threshold:
                        print(f"Comparing {chunk['node_id']} with {node_id} | Similarity: {similarity_score}")
                        session.execute_write(
                            create_chunk_similartity_relationship, 
                            chunk['node_id'], 
                            node_id  
                        )
                           
    def get_transcript_embeddings(self, video_id):
        with self.driver.session() as session:
            query = """
            MATCH (t:TranscriptChunk)
            WHERE NOT t.node_id STARTS WITH $exclude_id
            RETURN t.node_id AS node_id, t.embedding AS embedding
            """
            
            result = session.run(
                query,
                exclude_id=video_id)
            
            embedding_dict = {}
            
            result_list = list(result)
            
            for record in result_list:
                node_id = record["node_id"]
                embedding = record["embedding"]
                embedding_dict[node_id] = embedding 

            return embedding_dict
        
        
        