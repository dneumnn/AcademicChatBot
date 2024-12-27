from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from routing.semantic_routing import get_base_template, semantic_routing
from rerankers.rerankers import rerank_passages_with_cross_encoder_bge
from vectorstore.vectorstore import format_docs, transform_string_list_to_string
from routing.logical_routing import route_query

def rag(database_path: str, question: str, use_logical_routing: bool = False, use_semantic_routing: bool = False, knowledge_base_type: str = "vector"):
    VECTORSTORE_TOP_K = 25
    RERANKER_TOP_K = 5
    MODEL_ID = "llama3.2"
    EMBEDDING_MODEL_ID = "nomic-embed-text"

    if knowledge_base_type != "vector" and knowledge_base_type != "graph" and knowledge_base_type != "both":
        print("Invalid knowledge base type. Using vector.")
        knowledge_base_type = "vector"

    llm = ChatOllama(model=MODEL_ID)
    prompt_template = get_base_template() if not use_semantic_routing else semantic_routing(question)
    subject = route_query(question) if use_logical_routing else "alice"

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_ID)
    vectorstore = Chroma(
        persist_directory=database_path,
        embedding_function=embeddings,
        collection_name=subject,
        collection_metadata={"hnsw:space": "cosine"}
    )
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": VECTORSTORE_TOP_K})
 
    retriever_chain = (
        retriever 
        | format_docs 
        | (lambda docs: rerank_passages_with_cross_encoder_bge(question=question, passages=docs, top_k=RERANKER_TOP_K))
        | transform_string_list_to_string
    )

    #docs = retriever_chain.invoke(question)
    #print(docs)

    rag_chain = (
        {"context": retriever_chain, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    #rag_chain.get_graph().print_ascii()

    for chunk in rag_chain.stream(question):
        print(chunk, end="", flush=True)