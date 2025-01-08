import json
import logging
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from routing.semantic_routing import get_base_template, semantic_routing
from rerankers.rerankers import rerank_passages_with_cross_encoder
from vectorstore.vectorstore import format_docs, retrieve_top_n_documents_chromadb, transform_string_list_to_string
from routing.logical_routing import route_query
from logger.logger import setup_logger
from constants.config import VECTORSTORE_TOP_K, RERANKING_TOP_K, DEFAULT_KNOWLEDGE_BASE

def contextualize_and_improve_query(question: str, llm: ChatOllama, logger: logging.Logger, message_history: list[dict] = None):
    logger.info("Improving query")
    if message_history is not None:
        logger.info("Contextualizing query with provided message history")

    contextualize_q_prompt_string = """
        You are an expert at reformulating questions to be more concise and only mention the most relevant information and adding relevant context.

        Given a optional chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history if provided. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is. \
        
        Also improve the standalone question as much as possible. \
        The question should be concise and only mention the most relevant information. \
        If the question is already concise and only mentions the most relevant information, \
        return it as is. Do not return a history, only a reformulated question. \
        Try to indentify what the user is trying to ask. Focus on the user messages. \
        The newly generated question should be good for a vector search and prompting GenAI.

        ==============================
        Question: {query}
        ==============================
        Chat History: {message_history}
        ==============================

        ONLY return the reformulated question, do not add any other text or explanation.
    """
    
    contextualize_q_prompt = PromptTemplate.from_template(contextualize_q_prompt_string)

    contextualize_q_chain = (
        {"message_history": RunnablePassthrough(), "query": RunnablePassthrough()}
        | contextualize_q_prompt
        | llm
        | StrOutputParser()
    )

    output = []
    for chunk in contextualize_q_chain.stream({"message_history": message_history, "query": question}):
        output.append(chunk)
        print(chunk, end="", flush=True)
    print()

    logger.info(f"Contextualized and improved user query: {''.join(output)}")

    return ''.join(output)

def get_vector_context(question: str, subject: str, logger: logging.Logger, vectorstore_top_k: int = 25, reranker_top_k: int = 5):
    vector_context = retrieve_top_n_documents_chromadb(
        question=question,
        subject=subject,
        logger=logger,
        top_k=vectorstore_top_k
    )
    passages = [doc["document"] for doc in vector_context]

    reranked_passages = rerank_passages_with_cross_encoder(
        question=question,
        passages=passages,
        logger=logger,
        top_k=reranker_top_k
    )

    # add metadata for reranked passage from original vector_context
    reranked_context = [next(orig_doc for orig_doc in vector_context if orig_doc["document"] == reranked_passage) for reranked_passage in reranked_passages]

    return reranked_context

def rag(question: str, model_id: str, model_parameters: dict, logger: logging.Logger | None = None, message_history: list[dict] = None, use_logical_routing: bool = False, knowledge_base: str | None = None, use_semantic_routing: bool = False, basic_return: bool = False):
    if logger is None:
        logger = setup_logger()

    llm = ChatOllama(
        model=model_id,
        temperature=model_parameters["temperature"],
        top_p=model_parameters["top_p"],
        top_k=model_parameters["top_k"]
    )

    question = contextualize_and_improve_query(question, llm, logger, message_history)

    if knowledge_base is None and use_logical_routing == False:
        logger.info(f"Knowledge base is not provided and logical routing is not enabled. Using default knowledge base: {DEFAULT_KNOWLEDGE_BASE}")
        knowledge_base = DEFAULT_KNOWLEDGE_BASE

    logger.info(f"Starting RAG with model: {model_id}")
    logger.info(f"Using top_k values in retrieval: VECTORSTORE_TOP_K={VECTORSTORE_TOP_K}, RERANKER_TOP_K={RERANKING_TOP_K}")

    prompt_template = get_base_template() if not use_semantic_routing else semantic_routing(question)
    logger.info(f"Using prompt template: {prompt_template.template}, use_semantic_routing={use_semantic_routing}")
    subject = route_query(question) if use_logical_routing else knowledge_base
    logger.info(f"Using subject: {subject}, use_logical_routing={use_logical_routing}")

    #docs = retriever_chain.invoke(question)
    #print(docs)
    #retriever_chain.get_graph().print_ascii()

    vector_context = get_vector_context(question, subject, logger, VECTORSTORE_TOP_K, RERANKING_TOP_K)
    vector_context_text = "\n".join([doc["document"] for doc in vector_context])
    vector_context_metadatas = [doc["metadata"] for doc in vector_context]

    rag_chain = (
        {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    output = []
    for chunk in rag_chain.stream({"context": vector_context_text, "question": question}):
        output.append(chunk)
        print(chunk, end="", flush=True)
    print()
    
    logger.info(f"RAG output: {''.join(output)}")

    if basic_return:
        return ''.join(output)
