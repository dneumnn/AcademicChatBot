import logging
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from routing.semantic_routing import get_base_template, semantic_routing
from rerankers.rerankers import rerank_passages_with_cross_encoder_bge
from vectorstore.vectorstore import format_docs, transform_string_list_to_string
from routing.logical_routing import route_query

def rag(database_path: str, question: str, model_id: str, model_parameters: dict, logger: logging.Logger, use_logical_routing: bool = False, knowledge_base: str = None, use_semantic_routing: bool = False, basic_return: bool = False):
    VECTORSTORE_TOP_K = 25
    RERANKER_TOP_K = 5
    EMBEDDING_MODEL_ID = "nomic-embed-text"

    if knowledge_base is None and use_logical_routing == False:
        logger.warning("Knowledge base is not provided and logical routing is not enabled. Using default subject.")
        knowledge_base = "all"

    logger.info(f"Starting RAG with model: {model_id}")
    logger.info(f"Using top_k values: VECTORSTORE_TOP_K={VECTORSTORE_TOP_K}, RERANKER_TOP_K={RERANKER_TOP_K}")

    llm = ChatOllama(
        model=model_id,
        temperature=model_parameters["temperature"],
        top_p=model_parameters["top_p"],
        top_k=model_parameters["top_k"]
    )
    prompt_template = get_base_template() if not use_semantic_routing else semantic_routing(question)
    logger.info(f"Using prompt template: {prompt_template.template}, use_semantic_routing={use_semantic_routing}")
    subject = route_query(question) if use_logical_routing else knowledge_base
    logger.info(f"Using subject: {subject}, use_logical_routing={use_logical_routing}")

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_ID)
    logger.info(f"Using embeddings model: {EMBEDDING_MODEL_ID}")
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
        | (lambda docs: rerank_passages_with_cross_encoder_bge(question=question, passages=docs, logger=logger, top_k=RERANKER_TOP_K))
        | transform_string_list_to_string
    )

    #docs = retriever_chain.invoke(question)
    #print(docs)
    #retriever_chain.get_graph().print_ascii()

    rag_chain = (
        {"context": retriever_chain, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    output = []
    for chunk in rag_chain.stream(question):
        output.append(chunk)
        print(chunk, end="", flush=True)
    print()
    
    logger.info(f"RAG output: {''.join(output)}")

    if basic_return:
        return ''.join(output)
