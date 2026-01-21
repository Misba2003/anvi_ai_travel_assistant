import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("NASHIK_API_TOKEN", "").strip()
BASE_URL = "https://nashikguide.sapphiredigital.agency/api/search"

async def test():
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json"
    }
    params = {"query": "hotel"}

    async with httpx.AsyncClient() as client:
        res = await client.get(BASE_URL, params=params, headers=headers)
        print(res.status_code)
        print(res.text)

import asyncio
asyncio.run(test())
