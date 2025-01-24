import json
import traceback

import google.generativeai as genai
import os
import dotenv
import requests

dotenv.load_dotenv()

genai.configure(api_key=os.getenv("API_KEY_GOOGLE_GEMINI"))

questions = [
    {
        "question": "What is the price of the new RTX 5070?",
        "answer": "$549",
        "difficulty": "easy"
    },
    {
        "question": "Which architecture does the new GeForce RTX 50 Series use?",
        "answer": "The Blackwell architecture",
        "difficulty": "easy"
    },
    {
        "question": "How does the RTX 5070 compare in performance to the RTX 4090?",
        "answer": "It matches the performance of the RTX 4090",
        "difficulty": "easy"
    },
    {
        "question": "What is the approximate retail price for a laptop featuring the RTX 5070?",
        "answer": "$1,299",
        "difficulty": "easy"
    },
    {
        "question": "How many additional frames can the latest generation of DLSS predict for each rendered frame?",
        "answer": "It can predict three additional frames for every frame rendered",
        "difficulty": "easy"
    },
    {
        "question": "What is the memory bandwidth of the GeForce RTX 50 Series GPUs’ G7 memory?",
        "answer": "1.8 terabytes per second",
        "difficulty": "easy"
    },
    {
        "question": "Name one of the AI models mentioned that can generate 3D images from textual prompts.",
        "answer": "Flux (an image generation NeMo)",
        "difficulty": "easy"
    },
    {
        "question": "Which NVIDIA platform is used to help develop domain-specific AI agents for enterprise use?",
        "answer": "NVIDIA NeMo",
        "difficulty": "easy"
    },
    {
        "question": "What major change did Google's Transformer bring to AI according to the keynote?",
        "answer": "It completely changed the landscape for artificial intelligence and computing",
        "difficulty": "easy"
    },
    {
        "question": "What is the code name of NVIDIA’s new world foundation model for physical AI?",
        "answer": "NVIDIA Cosmos",
        "difficulty": "easy"
    },
    {
        "question": "Which technology helps reduce the computational load by generating unrendered pixels using AI?",
        "answer": "DLSS (Deep Learning Super Sampling)",
        "difficulty": "easy"
    },
    {
        "question": "How many transistors does the Blackwell GPU in the RTX 50 Series have?",
        "answer": "92 billion transistors",
        "difficulty": "medium"
    },
    {
        "question": "What is the name of NVIDIA’s next-generation robotics computer announced in the keynote?",
        "answer": "Thor",
        "difficulty": "medium"
    },
    {
        "question": "What is the function of post-training scaling mentioned in the keynote?",
        "answer": "It involves techniques like reinforcement learning and human feedback to refine AI after its initial training",
        "difficulty": "medium"
    },
    {
        "question": "Which automotive company did Jensen mention as a new partner for developing next-generation AVs with NVIDIA?",
        "answer": "Toyota",
        "difficulty": "medium"
    },
    {
        "question": "What is the main focus of NVIDIA Isaac GrOot in robotics development?",
        "answer": "It provides tools and workflows for synthetic data generation, imitation learning, and policy training for humanoid robots",
        "difficulty": "medium"
    },
    {
        "question": "What are the three computers that NVIDIA says every robotics company will need?",
        "answer": "A DGX for training AI models, Omniverse/Cosmos for simulation, and an AGX (like Thor) in the robot or autonomous system",
        "difficulty": "medium"
    },
    {
        "question": "Why is synthetic data so crucial for training autonomous vehicles according to the keynote?",
        "answer": "Real-world data is limited and costly to capture; synthetic data can amplify edge cases and help train at massive scale",
        "difficulty": "medium"
    },
    {
        "question": "What kind of new AI era does Jensen predict is approaching for enterprise applications?",
        "answer": "Agentic AI, where multiple AI models collaborate, plan, and take actions on behalf of users",
        "difficulty": "medium"
    },
    {
        "question": "Which core idea makes Omniverse critical for physically accurate simulation?",
        "answer": "It is a physics-principled simulation platform, grounded in real-world principles like friction, lighting, and object permanence",
        "difficulty": "medium"
    },
    {
        "question": "What is NVIDIA’s stated reason for making Llama 2 NeoTron models available?",
        "answer": "To provide enterprise-focused models with improved fine-tuning and performance for domains like chat, instruction, and retrieval",
        "difficulty": "hard"
    },
    {
        "question": "Name two techniques mentioned that allow AI models to refine themselves after initial training.",
        "answer": "Reinforcement learning with human feedback and synthetic data generation",
        "difficulty": "hard"
    },
    {
        "question": "How much performance gain, in terms of perf per watt, does the Blackwell-based datacenter system have over the previous generation?",
        "answer": "It is roughly four times more performance per watt than the previous generation",
        "difficulty": "hard"
    },
    {
        "question": "Approximately how large is the total memory in NVIDIA’s ‘giant chip’ multi-GPU configuration described in the keynote?",
        "answer": "About 14 terabytes of memory",
        "difficulty": "hard"
    },
    {
        "question": "Which industry does Jensen predict will be the first multi-trillion-dollar robotics market?",
        "answer": "Autonomous vehicles (AVs)",
        "difficulty": "hard"
    },
    {
        "question": "What does test-time scaling in AI primarily involve?",
        "answer": "Allocating more or different amounts of compute during inference, often for multi-step reasoning or chain-of-thought processes",
        "difficulty": "hard"
    },
    {
        "question": "What is the significance of NVIDIA’s Drive OS reaching ASIL D certification?",
        "answer": "It is the highest functional safety standard, making NVIDIA’s AI computer software-defined yet safety-certified for cars",
        "difficulty": "hard"
    },
    {
        "question": "Which specific memory technology is used in the Grace Hopper-based ‘smallest chip’ for the newly unveiled Project Digits system?",
        "answer": "HBM (High Bandwidth Memory), connected with chip-to-chip NVLink",
        "difficulty": "hard"
    },
    {
        "question": "How many hours of video was Cosmos trained on to understand physical dynamics?",
        "answer": "20 million hours of video",
        "difficulty": "hard"
    },
    {
        "question": "Why is WSL2 (Windows Subsystem for Linux 2) important for AI on Windows PCs according to the keynote?",
        "answer": "It gives direct access to CUDA out of the box, enabling cloud-native AI workflows and NVIDIA's entire AI software stack on Windows",
        "difficulty": "hard"
    }
]

test_data = []
model = genai.GenerativeModel(model_name='gemini-1.5-flash')

test_runs = 5
max_questions = 100_000_000
target_models = [
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'llama3.2',
    'gpt-4o',
    'gpt-4o-mini',
]

q_counter = 0

try:
    for t_model in target_models:
        for q_data in questions:

            if q_counter >= max_questions:
                break

            q_counter += 1
            q = q_data["question"]
            level = q_data["difficulty"]
            a = q_data["answer"]

            scores = []
            best_answer = ""
            worst_answer = ""

            for i in range(0, test_runs):
                print(f'Testing: q={q} Run {i + 1}/{test_runs}')

                p_data = {
                    'prompt': q,
                    'database': 'vector',
                    'stream': False,
                    'plaintext': True,
                    "model_id": t_model
                }

                response = requests.post('http://localhost:8000/chat', json=p_data)

                print(f"Got response: {response.text}")

                actual_answer = response.text

                validate_prompt = f"""
                    Validate if the answer matches the expected answer, the score should be 100
                    if it satisfies the question/expected answer, below 60 means that some parts are missing
                    below 20 means it is not acceptable at all. If the question is generally answered the
                    score should be at least 80. Scores between 80 and 100 are reserved by the quality of the
                    answer. If the answer contains too much information but the correct information is in it, it
                    should stay above 80.
                    
                    question = {q}
                    expected answer = {a}
                    actual answer = {actual_answer}
                    
                    ONLY ANSWER WITH AN INTEGER BETWEEN 1 - 100, no text at all
                    """

                validate_response = model.generate_content(validate_prompt).text
                score = int(validate_response.strip())

                if len(scores) == 0:
                    best_answer = actual_answer
                    worst_answer = actual_answer
                elif score > max(scores):
                    best_answer = actual_answer
                elif score < min(scores):
                    worst_answer = actual_answer

                scores.append(score)

            avg_result = sum(scores) / len(scores)
            best_result = max(scores)
            worst_result = min(scores)

            acceptable_count = len([score for score in scores if score >= 80])

            print(
                f"Validated with avg = {avg_result} worst = {worst_result} acceptable = {((100 * acceptable_count) / len(scores)):.2f}% best_answer = {best_answer}")
            print('all scores are', scores)
            test_obj = q_data.copy()
            test_obj['avg_score'] = str(avg_result)
            test_obj['worst_score'] = str(worst_result)
            test_obj['acceptable_score'] = f"{((100 * acceptable_count) / len(scores)):.2f}%"
            test_obj['best_answer'] = best_answer
            test_obj['model'] = t_model
            test_data.append(test_obj)
except BaseException:
    traceback.print_exc()

with open('results.json', 'w') as f:
    json.dump(test_data, f)

print('Successfully saved testing results')
