import os
from langchain_ollama import ChatOllama
import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from ..rag.rag import rag

compliance_prompt = """
You are comparing a submitted answer to an expert answer on a given question. Here is the data:
[BEGIN DATA]
************
[Question]: {input}
************
[Expert]: {expected}
************
[Submission]: {output}
************
[END DATA]

Compare the compliance of the facts of the submitted answer with the expert answer.

Ignore any differences in style, grammar, or punctuation. Also, ignore any missing information in the submission; we only care if there is new or contradictory information.

Select one of the following options:
(A) All facts in the submitted answer are consistent with the expert answer.
(B) The submitted answer contains new information not present in the expert answer.
(C) There is a disagreement between the submitted answer and the expert answer.
"""

completeness_prompt = """
You are comparing a submitted answer to an expert answer on a given question. Here is the data:
[BEGIN DATA]
************
[Question]: {input}
************
[Expert]: {expected}
************
[Submission]: {output}
************
[END DATA]

Compare the completeness of the submitted answer and the expert answer to the question.

Ignore any differences in style, grammar, or punctuation. Also, ignore any extra information in the submission; we only care that the submission completely answers the question.

Select one of the following options:
(A) The submitted answer completely answers the question in a way that is consistent with the expert answer.
(B) The submitted answer is missing information present in the expert answer, but this does not matter for completeness.
(C) The submitted answer is missing information present in the expert answer, which reduces the completeness of the response.
(D) There is a disagreement between the submitted answer and the expert answer.
"""

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(CURRENT_DIR, "test_data.csv")

def load_test_data():
    df = pd.read_csv(CSV_PATH)
    return df

def save_test_data(df: pd.DataFrame):
    df.to_csv(CSV_PATH, index=False)

def rag_test_data(database_path: str):
    df = load_test_data()
    for index, row in df.iterrows():
        question = row["question"]
        output = rag(database_path=database_path, question=question, basic_return=True)
        output = output.replace(",", "").replace("\n", " ")
        df.loc[index, "output"] = output

    save_test_data(df)

def judge_with_ai(prompt_template: PromptTemplate, input: str, expected: str, output: str):
    llm = ChatOllama(model="llama3.2")
    prompt_chain = (
        {"input": RunnablePassthrough(), "expected": RunnablePassthrough(), "output": RunnablePassthrough()} 
        | prompt_template 
        | llm 
        | StrOutputParser()
    )

    output = []
    for chunk in prompt_chain.stream({"input": input, "expected": expected, "output": output}):
        output.append(chunk)
    return ''.join(output).replace(",", "").replace("\n", " ")

def test_compliance():
    df = load_test_data()
    prompt_template = PromptTemplate.from_template(compliance_prompt)

    for index, row in df.iterrows():
        question = row["question"]
        expected = row["expected"]
        output = row["output"]

        result = judge_with_ai(prompt_template, question, expected, output)
        df.loc[index, "compliance"] = result

        print(f"Question: {question}")
        print(f"Expected: {expected}")
        print(f"Output: {output}")
        print(f"Compliance: {result}")
        print()

    save_test_data(df)

def test_completeness():
    df = load_test_data()
    prompt_template = PromptTemplate.from_template(completeness_prompt)

    for index, row in df.iterrows():
        question = row["question"]
        expected = row["expected"]
        output = row["output"]

        result = judge_with_ai(prompt_template, question, expected, output)
        df.loc[index, "completeness"] = result

        print(f"Question: {question}")
        print(f"Expected: {expected}")
        print(f"Output: {output}")
        print(f"Completeness: {result}")
        print()
    
    save_test_data(df)

def test_complete_generation(database_path: str, generate_output_first: bool = False):
    if generate_output_first:
        rag_test_data(database_path)
    test_compliance()
    test_completeness()
