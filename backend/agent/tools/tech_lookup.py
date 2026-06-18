import os
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

EXA_API_KEY = os.getenv("EXA_API_KEY")


async def tech_lookup_tool(company_name: str, domain: str) -> Dict[str, Any]:
    """
    Look up what a company does, their products, services, and customers using Exa search.

    Args:
        company_name: The company name e.g. Linear
        domain: The company domain e.g. linear.app

    Returns:
        Dict with results list containing title, url, and text for each result
    """
    if not EXA_API_KEY:
        logger.warning("EXA_API_KEY not configured")
        return {"results": [], "error": "EXA_API_KEY not configured"}

    try:
        from exa_py import Exa
        exa = Exa(api_key=EXA_API_KEY)
    except ImportError:
        return {"results": [], "error": "exa-py not installed"}

    all_results = []
    loop = asyncio.get_event_loop()

    # Search 1 — what the company does, offers, and what industry/domain they're in
    try:
        search1 = await loop.run_in_executor(
            None,
            lambda: exa.search_and_contents(
                f"{company_name} what industry domain space do they operate in product overview",
                num_results=5,
                use_autoprompt=True,
                text=True,
            )
        )
        for r in search1.results:
            all_results.append({
                "title": getattr(r, "title", ""),
                "url": getattr(r, "url", ""),
                "text": getattr(r, "text", "")[:2000],  # cap per result
            })
    except Exception as e:
        logger.warning(f"Exa search 1 failed for {company_name}: {e}")

    # Search 2 — their own website
    try:
        search2 = await loop.run_in_executor(
            None,
            lambda: exa.search_and_contents(
                f"site:{domain}",
                num_results=3,
                use_autoprompt=True,
                text=True,
            )
        )
        for r in search2.results:
            all_results.append({
                "title": getattr(r, "title", ""),
                "url": getattr(r, "url", ""),
                "text": getattr(r, "text", "")[:2000],
            })
    except Exception as e:
        logger.warning(f"Exa search 2 failed for {domain}: {e}")

    # Search 3 — explicit industry classification (Crunchbase/Wikipedia-style "about" sources
    # tend to state industry/sector directly, which generic product pages often don't)
    try:
        search3 = await loop.run_in_executor(
            None,
            lambda: exa.search_and_contents(
                f"{company_name} {domain} industry sector category overview",
                num_results=4,
                use_autoprompt=True,
                text=True,
            )
        )
        for r in search3.results:
            all_results.append({
                "title": getattr(r, "title", ""),
                "url": getattr(r, "url", ""),
                "text": getattr(r, "text", "")[:2000],
            })
    except Exception as e:
        logger.warning(f"Exa search 3 (industry) failed for {company_name}: {e}")

    return {"results": all_results}