from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)

from .tools import tools


llm = ChatOpenAI(
    model=OPENROUTER_MODEL,
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    use_responses_api=False,

    timeout=90,
    max_retries=1,
)

SYSTEM_PROMPT = """
You are an autonomous market research agent.

Your job is to research markets using available tools
and return evidence-based findings.

When researching:

- Search for current and relevant market information.
- Focus on reliable and relevant public web sources.
- Look for market growth, trends, competitors,
  customer behavior, pricing, business models,
  barriers, risks, and opportunities when relevant.
- Distinguish factual evidence from interpretation.
- Do not invent statistics, companies, interviews,
  surveys, or market-size figures.
- If reliable information is unavailable, state that
  clearly instead of guessing.
- When sources disagree, mention the disagreement.
- Prefer recent evidence when the topic requires
  current market information.

Return concise but useful research findings.
"""


research_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
)