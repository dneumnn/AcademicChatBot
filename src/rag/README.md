# RAG (Retrieval Augmented Generation) System

A modular RAG system that supports both vector and graph-based retrieval with multiple LLM options.

## Core Functions

### Get Available Models

Returns a list of all available LLM models from the local Ollama server. Use these model IDs when calling the chat function.

```python
from rag.app import models

available_models = models() # e.g. ["llama3.2:latest", "mistral:latest"]
```

### RAG Function - Direct Access to RAG Pipeline

```python
from rag.rag import rag

response = rag(
    question="What is machine learning?",
    message_history=[
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ],
    model_id="llama3.2:latest",
    model_parameters={
        "temperature": 0.8,
        "top_p": 0.9,
        "top_k": 40
    },
    knowledge_base="youtube_chunks",
    use_logical_routing=false,
    use_semantic_routing=false,
)
```

Parameters:

- `question`: Your query
- `model_id`: LLM model ID (e.g., "llama3.2:latest")
- `model_parameters`: Dictionary containing:
  - `temperature`: Controls randomness (0.0-1.0)
  - `top_p`: Nucleus sampling parameter (0.0-1.0)
  - `top_k`: Number of tokens to consider
- `message_history`: Optional list of previous messages for context
- `knowledge_base`: Specify knowledge base (defaults to "all")
- `use_logical_routing`: Enable rule-based routing (default: False)
- `use_semantic_routing`: Enable semantic-based routing (default: False)
- `basic_return`: Return only response text without metadata (default: False)

### Chat Function - High-Level Interface

```python
from rag.app import chat

response = chat(
    prompt="What is machine learning?"
)
```

Parameters:

- `prompt`: Your query
- `model_id`: Optional model ID (defaults to latest available)
- `message_history`: Previous conversation history
- `knowledge_base`: Specific knowledge base to query
- `model_parameters`: Model configuration parameters
- `database`: Database type to use ("vector", "graph", or "all")
- `playlist_id`: Optional YouTube playlist ID for context
- `video_id`: Optional YouTube video ID for context

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start Ollama server with required models

3. (Optional) Start Neo4j for graph database support:

```bash
MSYS_NO_PATHCONV=1 bash ./src/rag/mock/create_graph_store.sh
```

4. Configure settings in config.yml:

```yaml
config:
  default_database: vector
  default_model: llama3.2:latest
  default_model_parameters:
    temperature: 0.8
    top_p: 0.9
    top_k: 40
  default_knowledge_base: youtube_chunks
  use_semantic_routing: false
  use_logical_routing: false
  retrieval_embedding_model: all-MiniLM-L6-v2
  reranking_cross_encoder_model: BAAI/bge-reranker-large
  vectorstore_top_k: 10
  reranking_top_k: 3
```

Key Configuration Options:

- `default_database`: Type of database to use ("vector", "graph", "all")
- `default_model`: Default LLM model ID
- `default_model_parameters`: Model inference settings
- `default_knowledge_base`: Default knowledge base to query
- `retrieval_embedding_model`: Model used for text embeddings
- `reranking_cross_encoder_model`: Model used for reranking results
- `vectorstore_top_k`: Number of initial vector results to retrieve
- `reranking_top_k`: Number of results to keep after reranking

## Database Options

### Vector Store (ChromaDB)

- Default option
- Embedded database, no setup required

### Graph Store (Neo4j)

- Optional for relationship-based queries
- Requires Docker
- Web interface: `localhost:7474` (neo4j/password)

## Model Parameters Guide

- `temperature`:
  - 0.8: More creative responses
  - 0.2: More focused, factual responses
- `top_p`: Filter for token sampling (0.9 recommended)
- `top_k`: Number of tokens to consider (40 recommended)

Note: The system includes built-in logging (stored in `logger/logs/`) and error handling for invalid parameters, connection issues, etc.
