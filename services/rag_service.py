# services/rag_service.py

import asyncio
from typing import List, Dict

from services.data_service import search_api

MAX_RESULTS = 8  # enforce 6-8 item window for LLM consumption


async def _format_item(item: Dict, index: int) -> str:
    name = item.get("vendor_name") or item.get("name") or "Unknown"
    category = item.get("category") or item.get("type") or ""
    area = item.get("area_name") or item.get("zone_name") or item.get("area") or ""
    rating = item.get("rating") or item.get("star_rating") or ""
    address = (
        item.get("address")
        or item.get("location")
        or item.get("area_name")
        or ""
    )
    desc = item.get("short_description") or item.get("description") or ""

    if desc and len(desc) > 200:
        desc = desc[:200].rstrip() + "..."

    return (
        f"[{index}]\n"
        f"Name: {name}\n"
        f"Category: {category}\n"
        f"Area: {area}\n"
        f"Rating: {rating}\n"
        f"Address: {address}\n"
        f"Description: {desc}\n"
        f"----"
    )


async def get_rag_context(keyword: str, session_id: str, intent: Dict) -> str:
    """
    Uses ONLY the canonical category keyword from intent.
    Fetch up to 30 API results → keep top MAX_RESULTS for RAG.
    """

    items = await search_api(keyword, intent, limit=30)

    if not items:
        print(f"[DEBUG] RAG: No items for keyword '{keyword}' | session={session_id}")
        return ""

    selected = items[:MAX_RESULTS]
    print(
        f"[DEBUG] RAG: final item count={len(selected)} "
        f"(raw={len(items)}) | session={session_id}"
    )

    formatted = await asyncio.gather(
        *[_format_item(item, i + 1) for i, item in enumerate(selected)]
    )

    return "\n".join(formatted).strip()


async def get_rag_items(keyword: str, intent: Dict) -> List[Dict]:
    items = await search_api(keyword, intent, limit=15)
    return items or []