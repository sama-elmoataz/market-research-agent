from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from langchain.agents.middleware import (
    ToolCallLimitMiddleware,
    ModelCallLimitMiddleware,
)

from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)

from .tools import tools

llm = ChatOpenAI(
    model="google/gemma-4-26b-a4b-it:free",

    api_key=OPENROUTER_API_KEY,

    base_url="https://openrouter.ai/api/v1",

    temperature=0,

    use_responses_api=False,

    extra_body={
        "models": [
            "nvidia/nemotron-3-super-120b-a12b:free",
            "google/gemma-4-31b-it:free",
        ]
    },
)

SYSTEM_PROMPT = """
You are an autonomous market research agent.

Your job is to research markets, industries, competitors,
customers, pricing, trends, and business opportunities.

You have access to a web search tool.

When a user gives you a research topic:

1. Understand the research objective.
2. Identify what information is needed.
3. Use web search whenever current or external information is required.
4. You may search multiple times using different queries.
5. Do not rely on unsupported assumptions.
6. Compare information from multiple sources when possible.
7. Keep track of the source URLs used.
8. Stop searching when you have enough information to answer the request.
9. Produce a clear research summary based on the evidence you found.

Do not invent market statistics, company information,
pricing, or sources.
"""

research_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        ToolCallLimitMiddleware(
            tool_name="web_search",
            run_limit=6,
            exit_behavior="end",
        ),
        ModelCallLimitMiddleware(
            run_limit=8,
            exit_behavior="end",
        ),
    ],

)