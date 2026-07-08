import logging
from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)

def generate_answer(question: str, context: List[Document]) -> str:
    if not context:
        return "not found in context"

    formatted_context = ""
    for idx, doc in enumerate(context):
        filename = doc.metadata.get("filename", "Unknown")
        page = doc.metadata.get("page", "Unknown")
        formatted_context += f"Source [{idx+1}] - File: {filename}, Page: {page}\nContent: {doc.page_content}\n\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a helpful, precise document Q&A assistant.\n"
            "Your task is to answer the user's question using ONLY the provided context blocks.\n"
            "If the information required to answer the question is not found in the context, you MUST reply with: 'not found in context'.\n"
            "Do not try to make up an answer, and do not use any outside knowledge.\n"
            "Cite the source number (e.g. [1], [2]) for facts in your answer."
        )),
        ("human", "Context:\n{context}\n\nQuestion: {question}")
    ])

    logger.info(f"Generating answer using model {settings.GEMINI_MODEL}...")
    
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.0
    )

    chain = prompt | llm
    response = chain.invoke({"context": formatted_context, "question": question})
    
    answer_text = response.content.strip()
    logger.info("Answer generation complete.")
    return answer_text
