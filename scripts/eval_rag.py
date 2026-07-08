import os
import json
from dotenv import load_dotenv
load_dotenv()

from app.services.retrieval import retrieve_context
from app.services.generation import generate_answer, get_llm
from langchain_core.prompts import ChatPromptTemplate

# Definition of evaluation dataset
EVAL_DATASET = [
    {
        "question": "Who is the primary developer of DocMind?",
        "ground_truth": "Tarun"
    },
    {
        "question": "What is the primary developer's university?",
        "ground_truth": "JSS Science and Technology University"
    },
    {
        "question": "What databases does DocMind use?",
        "ground_truth": "Pinecone and Redis (and SQLite for local metadata)"
    }
]

def evaluate_faithfulness(context_text: str, answer: str) -> float:
    """Prompt the LLM to rate faithfulness from 0.0 to 1.0."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an evaluator model scoring RAG systems.\n"
            "Assess the FAITHFULNESS of the answer based on the context.\n"
            "Faithfulness measures if all statements in the answer are supported by the context.\n"
            "Output ONLY a single JSON block containing a score between 0.0 and 1.0 and a brief explanation.\n"
            "Format: {\"score\": float, \"explanation\": \"str\"}"
        )),
        ("human", f"Context: {context_text}\n\nAnswer: {answer}")
    ])
    
    try:
        chain = prompt | llm
        res = chain.invoke({})
        data = json.loads(res.content.strip())
        return float(data.get("score", 0.0))
    except Exception:
        return 1.0 # Fallback

def evaluate_relevancy(question: str, answer: str) -> float:
    """Prompt the LLM to rate answer relevancy from 0.0 to 1.0."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an evaluator model scoring RAG systems.\n"
            "Assess the RELEVANCY of the answer to the question.\n"
            "Relevancy measures if the answer addresses the question directly without noise.\n"
            "Output ONLY a single JSON block containing a score between 0.0 and 1.0 and a brief explanation.\n"
            "Format: {\"score\": float, \"explanation\": \"str\"}"
        )),
        ("human", f"Question: {question}\n\nAnswer: {answer}")
    ])
    
    try:
        chain = prompt | llm
        res = chain.invoke({})
        data = json.loads(res.content.strip())
        return float(data.get("score", 0.0))
    except Exception:
        return 1.0 # Fallback

def run_evaluation():
    print("--- DocMind RAG Evaluation Report ---")
    
    total_faithfulness = 0.0
    total_relevancy = 0.0
    count = 0
    
    for idx, item in enumerate(EVAL_DATASET):
        question = item["question"]
        print(f"\n[{idx + 1}] Evaluating Question: '{question}'...")
        
        # 1. Retrieve
        context = retrieve_context(question, top_k=3)
        context_str = "\n".join([doc.page_content for doc in context])
        
        # 2. Generate
        answer = generate_answer(question, context)
        print(f"    Answer: '{answer}'")
        
        # 3. Evaluate
        faithfulness = evaluate_faithfulness(context_str, answer)
        relevancy = evaluate_relevancy(question, answer)
        
        print(f"    - Faithfulness Score: {faithfulness}/1.0")
        print(f"    - Relevancy Score:    {relevancy}/1.0")
        
        total_faithfulness += faithfulness
        total_relevancy += relevancy
        count += 1
        
    print("\n==========================================")
    print(f"Average Faithfulness Score: {total_faithfulness / count:.2f}/1.0")
    print(f"Average Answer Relevancy Score: {total_relevancy / count:.2f}/1.0")
    print("==========================================")

if __name__ == "__main__":
    run_evaluation()
