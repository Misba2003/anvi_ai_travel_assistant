# services/llm_service.py

import os
from typing import Dict
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ✅ VERIFIED WORKING MODEL
MODEL_NAME = "llama-3.3-70b-versatile"

# ✅ Initialize Groq client once
client = Groq(api_key=GROQ_API_KEY)


async def answer_with_ai(
    query: str,
    context: str,
    intent: Dict,
    memory: str
) -> str:
    """
    Final LLM call using Groq (cloud).
    Fully replaces Ollama.
    """

    # ✅ HARD SAFETY: No hallucinations when data is empty
    if not context or context.strip() == "":
        return "No matching data found for your request. Please try a different search."

    system_msg = f"""
You are Anvi AI, a Nashik-based travel assistant.

STRICT RULES:
- Use ONLY the items provided in the CONTEXT.
- DO NOT hallucinate or invent places.
- Show ONLY the TOP 6–8 most relevant items.
- If a field is missing, write "Not provided".
- Format cleanly for mobile UI.
- End with ONE short follow-up question.
"""

    user_msg = f"""
PREVIOUS CONVERSATION:
{memory}

USER QUERY:
{query}

CONTEXT:
{context}
"""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.2,
            top_p=0.9
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        print("[ERROR] GROQ FAILURE:", e)
        return "LLM is temporarily unavailable. Please try again."
