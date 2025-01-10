# To start the Neo4j db run the followign commands:

Start Neo4j (Docker required):

´´´bash
MSYS_NO_PATHCONV=1 bash ./src/rag/mock/create_graph_store.sh
´´´

Web interface can be accessed via:

[localhost:7474](http://localhost:7474/)

Standard Login is:

- Username: neo4j
- Password: password

Further reading:

https://python.langchain.com/docs/integrations/graphs/neo4j_cypher/
