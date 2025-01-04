from neo4j import GraphDatabase
from src.db.graph_db.node_creation import *
from src.db.graph_db.relation_creation import *
from sklearn.metrics.pairwise import cosine_similarity

class GraphHandler:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_meta_data_session(self, meta_data):
        with self.driver.session() as session:
            session.execute_write(create_meta_data_node, meta_data)

    def create_transcript_chunk_session(self, chunks):
        with self.driver.session() as session:
            for chunk in chunks:
                session.execute_write(create_transcript_chunk_node, chunk)
    
    def create_chunk_next_relation_session(self, chunks):
         with self.driver.session() as session:
            for i in range(len(chunks) - 1):
                session.execute_write(
                    create_next_relationship,
                    chunks[i]['node_id'],
                    chunks[i + 1]['node_id'])
                
    def create_chunk_metadata_relation_session(self, chunks, meta_data):
        with self.driver.session() as session:
            for chunk in chunks:
                session.execute_write(
                    create_meta_data_relationship,
                    chunk['node_id'],
                    meta_data['id']
                )
                
    def create_chunk_similarity_relation_session(self, chunks):
        current_chunks = self.get_transcript_embeddings()            
            
    def get_transcript_embeddings(self):
        with self.driver.session() as session:
            query = """
            MATCH (t:TextChunk)
            RETURN t.node_id AS node_id, t.embedding AS embedding
            """
            
            # Initialize an empty dictionary to store the results
            chunks_dict = {}
            
            try:
                # Execute the query and process the results
                result = session.run(query)
                
                # Iterate through the result and store each node's information in the dictionary
                for record in result:
                    node_id = record["node_id"]
                    embedding = record["embedding"]
                    
                    # If the embedding is a list or array, ensure it’s stored correctly
                    if embedding:
                        chunks_dict[node_id] = embedding
                    else:
                        print(f"Warning: No embedding found for node {node_id}.")
            except Exception as e:
                print(f"Error retrieving embeddings: {e}")
        
        return chunks_dict