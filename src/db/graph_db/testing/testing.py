import json 
import os
import time
import ast
import re
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
import google.generativeai as genai
from sklearn.metrics import precision_score, recall_score, f1_score

file_pathV2 = "gold_standard_entities.json"
file_pathV3 = "gold_standard_entitiesV3.json"
sample_file = "sample_data.txt"

def processing_gold_datasetV2(file_path):
    with open(file_path, "r", encoding='utf8') as file:
        test_data = json.load(file)

    golden_standard_entities = test_data["entities"]

    return golden_standard_entities

def processing_gold_datasetV3(file_path):
    with open(file_path, "r", encoding='utf8') as file:
        test_data = json.load(file)

    golden_standard_entities = test_data["entities"]

    return golden_standard_entities

def to_camel_case(node):
    # Sonderfälle: Wörter wie BERT oder GPT unangetastet lassen
    if node.isupper():
        return node

    # Entferne Sonderzeichen und teile die Wörter
    words = re.split(r'[\s_-]+', node)
    # Wandle die Wörter in CamelCase um
    camel_case = ''.join(word.capitalize() for word in words)
    return camel_case


def llm_entities_extractionV2(chunks):
    requests_made = 0 
    load_dotenv()
    API_KEY_GOOGLE_GEMINI_GRAPHDB = os.getenv("API_KEY_GOOGLE_GEMINI")
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI_GRAPHDB)

    model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction="""
        You are an expert in Machine Learning (ML) and Natural Language Processing (NLP). 
        Your task is to extract entities and relationships specifically relevant to ML from text.
        Entities include:
        - ML methods, algorithms, datasets, tools, frameworks, performance metrics, and general concepts.
        Relationships are:
        - Domain-specific actions or associations (e.g., uses, trains, evaluates, is_based_on).
        Output should strictly follow this format:
        Node: <Entity1>
        Node: <Entity2>
        Relationship: <Entity1>, <Relationship>, <Entity2>""")
    
    llm_entities_list = []
    for chunk in chunks:
        user_prompt = f"""
            Extract all Entities and their relationships from the following text:
            {chunk}
            """
        if requests_made >= 14:
            print("Rate limit reached. Sleeping for 60 seconds.")
            time.sleep(60)
            requests_made = 0
        
        llm_response = model.generate_content(contents=user_prompt)
        requests_made += 1
        print(llm_response.text)
        try:
            nodes = re.findall(r"Node: (.+)", llm_response.text)
            nodes_camel_case = [to_camel_case(node) for node in nodes]
            llm_entities_list.extend(nodes_camel_case)
            #llm_entities = ast.literal_eval(llm_response.text.strip()) 
            #llm_entities_list.extend(llm_entities) 
        except(ValueError, SyntaxError):
            print("Fehler beim Parsen der LLM-Antwort.")
    
    return llm_entities_list


def llm_entities_extractionV3(chunks):
    requests_made = 0 
    load_dotenv()
    API_KEY_GOOGLE_GEMINI_GRAPHDB = os.getenv("API_KEY_GOOGLE_GEMINI")
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI_GRAPHDB)

    model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction="""
        You are an expert in Machine Learning (ML), Natural Language Processing (NLP), Artifical Intelligence and Neuronal Networks.
        Your task is to extract entities from a given text. Focus on extracting only meaningful entities from your expert field.
        Do not include generic or unrelated information.

        Entity examples:
        - machine learning, neuronal network, alogrithm, data, supervised learning, training data, layer, weight, clustering, feature, ...
    
        Rules:
        - Format entities that are in plural to an entity in singular.
        
        Write all entities found in a list as in the following example:
        ['artificial intelligence', 'algorithm', 'pattern', 'data']
        """)
    
    llm_entities_list = []
    for chunk in chunks:
        user_prompt = f"""
            Extract all Entities from the following text:
            {chunk}
            """
        if requests_made >= 14:
            print("Rate limit reached. Sleeping for 60 seconds.")
            time.sleep(60)
            requests_made = 0
        
        llm_response = model.generate_content(contents=user_prompt)
        requests_made += 1
        print(llm_response.text)
        try:
            llm_entities = ast.literal_eval(llm_response.text.strip())
            llm_entities_lowercase = [entity.lower() for entity in llm_entities]
            llm_entities_list.extend(llm_entities_lowercase)  
        except(ValueError, SyntaxError):
            print("Fehler beim Parsen der LLM-Antwort.")
    
    return llm_entities_list


def split_text_by_sentence_splitter(chunk_size=500, chunk_overlap=50):
    with open("sample_data.txt", "r", encoding="utf-8") as file:
        text = file.read()
    
    sentences = sent_tokenize(text)  # Split text into sentences
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # Check if adding the next sentence exceeds the chunk size
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence
        else:
            # Add the current chunk to the list and include overlap
            chunks.append(current_chunk.strip())
            current_chunk = " ".join(chunks[-1].split()[-chunk_overlap:]) + " " + sentence  # Add overlap
        
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def metrics_calculations(golden_standard_entities, llm_entities):
    
    gold_standard_set = set(golden_standard_entities)
    llm_entities_set = set(llm_entities)

    only_gold = gold_standard_set - llm_entities_set
    only_llm = llm_entities_set - gold_standard_set

    all_entities = list(gold_standard_set | llm_entities_set)

    print("\nNur im Gold-Standard:", only_gold)
    print("\nNur im LLM:", only_llm)
    print("\nAll entities:", all_entities)
    
    gold_labels = [1 if entity in gold_standard_set else 0 for entity in all_entities]
    llm_labels = [1 if entity in llm_entities_set else 0 for entity in all_entities]

    precision = precision_score(gold_labels, llm_labels)
    recall = recall_score(gold_labels, llm_labels)
    f1 = f1_score(gold_labels, llm_labels)

    print(f"\nPrecision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1-Score: {f1:.2f}")


if __name__ == "__main__":
    
    golden_standard_entitiesV2 = processing_gold_datasetV2(file_pathV2)
    #print("Golden-Standard-Entities:", golden_standard_entities)

    golden_standard_entitiesV3 = processing_gold_datasetV3(file_pathV3)
    
    chunks = ['Machine learning is a core component of artificial intelligence, where algorithms are developed to identify patterns in data and make predictions or decisions based on these patterns. The process begins with data collection, where large volumes of raw data are gathered from various sources such as databases, APIs, or sensors. Before it can be used, this data is processed in Data preparation involves several steps, including cleaning, where erroneous or irrelevant data is removed, and normalization, where values are transformed into a consistent range to improve training stability.','Another crucial step is feature engineering, where relevant properties are extracted from data to make them usable for the model. For example, in analyzing customer behavior, features like age, average order value, or purchase frequency might be extracted. The next step in machine learning is selecting an appropriate model. In supervised learning, one of the main categories of machine learning, models are trained on labeled data. This data consists of inputs and the corresponding desired outputs. An example would be predicting real estate prices, where input data such as square footage and location are used to predict the price.','Classification models such as decision trees or support vector machines are particularly suited for discrete outputs, while linear regression or neural networks are used for continuous values. A key concept in supervised learning is the cost function, which measures how well a model makes predictions. During the training process, the algorithm minimizes this cost function by adjusting the model parameters using an optimization method such as gradient descent. Gradient descent is an iterative process where parameters are adjusted in the direction of the steepest descent of the cost function until a local minimum or global minimum is reached.','Another critical aspect of machine learning is unsupervised learning, where no labels are provided, and the model must discover patterns or structures in the data. Typical tasks in this area include clustering and dimensionality reduction. Clustering algorithms like K-Means or DBSCAN group data points based on their similarity, while methods like Principal Component Analysis reduce the dimensions of a dataset to reveal hidden structures or make the data more manageable for visualization.','Reinforcement learning, another major category of machine learning, is based on a completely different approach. Here, an agent learns by interacting with an environment and receiving rewards or penalties for its actions. The goal is to develop a strategy that maximizes long-term rewards. This is often used in dynamic systems such as controlling autonomous vehicles or in games. Algorithms like Q-learning or policy gradient methods are particularly popular here.','Model validation assesses how well a model performs on unseen data. To do this, the dataset is often split into training data, validation data, and test data. Validation is used to evaluate the algorithm during training and prevent overfitting, which occurs when a model learns the training data too precisely and is no longer able to generalize to new data. Regularization techniques such as L1 norms and L2 norms or dropout in neural networks help address overfitting.','Neural networks play an outstanding role in machine learning, particularly in tasks such as image recognition and speech recognition. They consist of layers of neurons that process input data through multiple transformations. Each connection between the neurons has a weight that is adjusted during training. A neural network learns by processing inputs through forward propagation, calculating the error, and then updating the weights using backpropagation.','Modern architectures such as convolutional neural networks (CNNs) are specifically optimized for image data and use convolutional layers to recognize local features like edges or textures. For time dependent data such as speech series or time series, recurrent neural networks (RNNs) or their advancements, such as Long Short-Term Memory (LSTM) and Gated Recurrent Units (GRUs), are used. These models can process sequences by storing information from previous steps and using it in later processing stages.','Transformer models, as used in language models like GPT or BERT, enabled the efficient processing of data through mechanisms such as self-attention. In practical applications, machine learning models are often implemented using frameworks like TensorFlow, PyTorch, or scikit-learn. These libraries provide pre-built functions and modules that significantly simplify the development and training of models. After training a model, it is crucial to deploy it in a real-world environment. To do this, models are often embedded in APIs or directly integrated into applications.','Monitoring the model in operation is equally important, as data can change over time, a phenomenon known as data drift. Regular evaluations and, if necessary, retraining the model are essential to maintain accuracy and reliability. Machine learning is an iterative process that requires continuous improvement and adaptation to meet the demands of specific use cases.']
    
    #with open(sample_file, "r", encoding="utf-8") as file:
       # chunks = file.read()
    llm_entitiesV2 = llm_entities_extractionV2(chunks)
    print("\nLLM-extracted-Entities:", llm_entitiesV2)

    #llm_entitiesV3 = llm_entities_extractionV3(chunks)
    #print("\nLLM-extracted-Entities:", llm_entitiesV3)
    
    metrics_calculations(golden_standard_entitiesV2, llm_entitiesV2)
    