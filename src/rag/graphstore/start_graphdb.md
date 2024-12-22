# To start the Neo4j db run the followign commands:

Pull the image for docker:

´´´bash
docker pull neo4j
´´´

Start the container:

´´´bash
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -d \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS=\[\"apoc\"\]  \
    neo4j:latest
´´´

https://python.langchain.com/docs/integrations/graphs/neo4j_cypher/