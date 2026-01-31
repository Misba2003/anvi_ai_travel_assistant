import os
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from services.intent_service import extract_intent, detect_attribute
from services.rag_service import get_rag_context, get_rag_items
from services.llm_service import answer_with_ai
from services.memory_service import get_recent_messages, save_message
from services.data_service import resolve_entity, format_attribute_answer, normalize_name

from jose import jwt, JWTError

# ------------------------
# Load environment variables
# ------------------------
project_root = Path(__file__).resolve().parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path)

# ------------------------
# FastAPI App Setup
# ------------------------
app = FastAPI(title="ANVI AI Backend")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# Request Model
# ------------------------
class AskRequest(BaseModel):
    query: str
    session_id: str | None = None

# ------------------------
# MAIN ENDPOINT
# ------------------------
@app.post("/ask")
async def ask_ai(
    req: AskRequest,
    authorization: str = Header(None),
):
    try:
        # ------------------------
        # AUTH (JWT)
        # ------------------------
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Unauthorized")

        token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        JWT_SECRET = os.getenv("JWT_SECRET")
        JWT_ALGORITHM = "HS256"

        if not JWT_SECRET:
            raise HTTPException(status_code=500, detail="JWT_SECRET not configured")

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                options={
                    "require": ["exp", "user_id"],
                    "verify_exp": True,
                    "verify_signature": True,
                },
            )
            app_user_id = str(payload["user_id"])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        # ------------------------
        # REQUEST DATA
        # ------------------------
        query = req.query.strip()
        session_id = (req.session_id or "").strip()

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        print(f"[DEBUG] /ask → {query} | session: {session_id}")

        # ------------------------
        # STORE USER MESSAGE
        # ------------------------
        await save_message(app_user_id, "user", query)
        print("[DEBUG] Stored user message in PostgreSQL memory")

        # ------------------------
        # CONVERSATIONAL SHORT-CIRCUIT
        # ------------------------
        q_lower = query.lower()

        CONVERSATIONAL_KEYWORDS = {
            "hi", "hello", "hey",
            "good morning", "good evening", "good afternoon",
            "what can you help me with", "what can you do",
            "how can you help me", "what do you do"
        }

        DOMAIN_KEYWORDS = {
            "hotel", "hotels", "stay", "resort", "villa",
            "price", "budget", "luxury", "rating", "address",
            "amenities", "location", "near", "in"
        }

        is_conversational = (
            any(k in q_lower for k in CONVERSATIONAL_KEYWORDS)
            and not any(d in q_lower for d in DOMAIN_KEYWORDS)
            and len(q_lower.split()) <= 8
        )

        if is_conversational:
            greeting_answer = (
                "Hey! 👋 I'm Anvi, I can help you with hotel searches, place details, "
                "and travel-related questions based on our available data.\n\n"
                "Just tell me what you're looking for 🙂"
            )

            await save_message(app_user_id, "assistant", greeting_answer)

            return {
                "answer": greeting_answer,
                "cards": []
            }

        # ------------------------
        # INTENT
        # ------------------------
        intent = extract_intent(query)
        category_keyword = intent["category"]

        # ------------------------
        # ENTITY + ATTRIBUTE BYPASS
        # ------------------------
        if intent.get("type") == "entity_lookup":
            detected_attribute = detect_attribute(query)

            if detected_attribute:
                entity_name = intent.get("entity_name", "")
                entity_data = await resolve_entity(entity_name, intent, token=token)

                if entity_data:
                    value = entity_data.get(detected_attribute)
                    answer = format_attribute_answer(entity_data, detected_attribute, value)

                    await save_message(app_user_id, "assistant", answer)

                    return {
                        "answer": answer,
                        "cards": []
                    }

        # ------------------------
        # RAG CONTEXT
        # ------------------------
        context = await get_rag_context(category_keyword, session_id, intent)

        history = await get_recent_messages(app_user_id)
        memory = "\n".join([f"{m['role']}: {m['content']}" for m in history])

        # ------------------------
        # LLM
        # ------------------------
        answer = await answer_with_ai(
            query=query,
            context=context or "",
            intent=intent,
            memory=memory
        )

        # ------------------------
        # CARDS
        # ------------------------
        items = await get_rag_items(category_keyword, intent)

        cards = []
        for item in items[:8]:
            cards.append({
                "title": item.get("vendor_name"),
                "subtitle": item.get("area_name"),
                "rating": item.get("star_rating"),
                "address": item.get("address"),
                "description": item.get("description"),
                "image": item.get("image_url")
            })

        await save_message(app_user_id, "assistant", answer)

        return {
            "answer": answer,
            "cards": cards
        }

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR]", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
