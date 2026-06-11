import os
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

SERPER_API_KEY = os.getenv("SERPER_API_KEY")


async def web_search_tool(query: str) -> Dict[str, Any]:
    """
    Search the web using Serper.dev API (Google Search results).

    Args:
        query: The search query string

    Returns:
        Dict with "results" list and optional "error" field
    """
    if not SERPER_API_KEY:
        logger.warning("SERPER_API_KEY not configured")
        return {"results": [], "error": "SERPER_API_KEY not configured"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "q": query,
                    "num": 5,
                    "tbs": "qdr:m3",  # last 3 months
                },
            )
            response.raise_for_status()
            data = response.json()

            # Normalize to same shape as before so agent prompts don't change
            items = []
            for r in data.get("organic", []):
                items.append({
                    "title": r.get("title", ""),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                })

            return {"results": items}

    except Exception as e:
        logger.warning(f"Serper search failed for query '{query}': {e}")
        return {"results": [], "error": str(e)}
