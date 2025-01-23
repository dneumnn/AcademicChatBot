import requests
import json
from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness
from langchain_ollama import ChatOllama

BASE_URL = "http://localhost:8000"

llm = ChatOllama(
    model="llama3.2",
    temperature=0.8,
    top_p=0.9,
    top_k=40
)

sample_queries = [
    "Who introduced the theory of relativity?",
    "Who was the first computer programmer?"
]

expected_responses = [
    "Albert Einstein proposed the theory of relativity, which transformed our understanding of time, space, and gravity.",
    "Ada Lovelace is regarded as the first computer programmer for her work on Charles Babbage's early mechanical computer, the Analytical Engine."
]

dataset = []

for query, reference in zip(sample_queries, expected_responses):
    
    response = requests.post(f"{BASE_URL}/chat", json={"prompt": query, "model_id": "llama3.2", "stream": False})
    lines = response.iter_lines()
    response_content = ""

    for line in lines:
        if line:
            word = line.decode('utf-8')
            response_content += word + " "
    dict_response = json.loads(response_content)

    dataset.append({
        "user_input": query,
        "retrieved_contexts": relevant_docs,
        "response": dict_response['content'],
        "reference": reference
    })

eval_dataset = EvaluationDataset.from_list(dataset)

evaluator_llm = LangchainLLMWrapper(llm)
result = evaluate(eval_dataset, [LLMContextRecall(), Faithfulness(), FactualCorrectness()], llm=evaluator_llm)
print(result)