# services/memory_service.py
import asyncio
from typing import Dict, List

MEMORY_LIMIT = 6  # last 6 turns only

# session_id -> list of {"role": str, "content": str}
SESSION_MEMORY: Dict[str, List[Dict[str, str]]] = {}
SESSION_LOCKS: Dict[str, asyncio.Lock] = {}


def _get_lock(session_id: str) -> asyncio.Lock:
    if session_id not in SESSION_LOCKS:
        SESSION_LOCKS[session_id] = asyncio.Lock()
    return SESSION_LOCKS[session_id]


async def add_to_memory(session_id: str, role: str, content: str) -> int:
    """
    Stores a message for the session and trims to the last MEMORY_LIMIT turns.
    Returns the current memory size for logging.
    """
    lock = _get_lock(session_id)
    async with lock:
        if session_id not in SESSION_MEMORY:
            SESSION_MEMORY[session_id] = []

        SESSION_MEMORY[session_id].append({"role": role, "content": content})

        # Trim old messages
        if len(SESSION_MEMORY[session_id]) > MEMORY_LIMIT:
            SESSION_MEMORY[session_id] = SESSION_MEMORY[session_id][-MEMORY_LIMIT:]

        return len(SESSION_MEMORY[session_id])


async def get_memory(session_id: str) -> str:
    """
    Returns formatted conversation memory for the session.
    """
    lock = _get_lock(session_id)
    async with lock:
        messages = list(SESSION_MEMORY.get(session_id, []))

    if not messages:
        return "No previous conversation."

    formatted = ""
    for msg in messages:
        formatted += f"{msg['role']}: {msg['content']}\n"

    return formatted.strip()


async def get_memory_size(session_id: str) -> int:
    lock = _get_lock(session_id)
    async with lock:
        return len(SESSION_MEMORY.get(session_id, []))


async def clear_memory(session_id: str):
    lock = _get_lock(session_id)
    async with lock:
        SESSION_MEMORY.pop(session_id, None)
