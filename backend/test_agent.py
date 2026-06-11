import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# ADK reads GOOGLE_API_KEY — map it from GEMINI_API_KEY if needed
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

async def main():
    gemini_key = os.getenv("GOOGLE_API_KEY")
    exa_key = os.getenv("EXA_API_KEY")
    search_key = os.getenv("GOOGLE_SEARCH_API_KEY")

    print(f"GOOGLE_API_KEY: {'SET' if gemini_key else 'MISSING'}")
    print(f"EXA_API_KEY:    {'SET' if exa_key else 'MISSING'}")
    print(f"SEARCH_API_KEY: {'SET' if search_key else 'MISSING'}")
    print()

    if not gemini_key:
        print("ERROR: GEMINI_API_KEY is missing from .env")
        return

    print("Running research for Linear (linear.app)...")
    print("This will take 30-60 seconds.\n")

    from agent.orchestrator import run_research
    result = await run_research(
        company_name="Linear",
        domain="linear.app",
        meeting_title="Demo call with Linear",
        attendees=["john@linear.app"],
    )

    if result:
        print("SUCCESS — BriefOutput:")
        print(f"  Company:      {result.company_name}")
        print(f"  What they do: {result.what_they_do}")
        print(f"  Stage:        {result.company_stage}")
        print(f"  Confidence:   {result.confidence}")
        print(f"  News items:   {len(result.recent_news)}")
        print(f"  Pain points:  {len(result.pain_points)}")
        print(f"  Talking pts:  {len(result.talking_points)}")
        if result.talking_points:
            print(f"\n  Talking points:")
            for tp in result.talking_points:
                print(f"    - {tp.point}")
    else:
        print("FAILED — run_research returned None. Check logs above.")

asyncio.run(main())
