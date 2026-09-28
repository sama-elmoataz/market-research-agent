import json
from langchain_core.messages import ToolMessage
from datetime import date

from .state import ResearchState
from langgraph.types import interrupt
from .agent import llm

from .schemas import (
    ResearchPlan,
    SearchQueries,
    ReviewResult,
    ResearchQualityAssessment,
)

from .tools import search_web


def planner_node(
    state: ResearchState,
):
    """
    Convert the user's research objective
    into a focused market research plan.
    """

    topic = state["topic"]
    structured_planner = (
        llm.with_structured_output(
            ResearchPlan,
            method="function_calling",
        )
    )

    prompt = f"""
You are a senior market research planner.

Current date:
{date.today().isoformat()}

Research objective:
{topic}

Create a focused market research plan for this objective.

Break the objective into 4 to 6 research tasks.

The tasks should collectively cover the most relevant
areas for the specific market being researched.

Possible areas include:

- market size, growth, and outlook
- important market and consumer trends
- customer needs, behavior, and adoption
- key competitors and competitive positioning
- pricing and business models
- distribution or sales channels
- regulatory requirements
- operational barriers and risks
- market-entry opportunities

Rules:

- Keep every task specific to the research objective.
- Avoid duplicate or overlapping tasks.
- Do not perform the research.
- Do not invent market findings or statistics.
- Do not request primary interviews or surveys.
- Focus on questions that can realistically be
  investigated using public web research.
- Return only the structured research plan.
"""

    plan = structured_planner.invoke(
        prompt
    )

    if plan is None:

        raise ValueError(
            "Planner returned no structured "
            "research plan."
        )

    if not plan.tasks:

        raise ValueError(
            "Planner returned an empty "
            "research plan."
        )

    return {
        "research_plan": plan.tasks,
        "iteration": 0,
        "research_round": 0,
    }


def researcher_node(state: ResearchState):

    topic = state["topic"]
    research_plan = state["research_plan"]

    plan_text = "\n".join(
        f"{i}. {task}"
        for i, task in enumerate(
            research_plan,
            start=1,
        )
    )



    structured_query_planner = (
        llm.with_structured_output(
            SearchQueries,
            method="function_calling",
        )
    )


    query_prompt = f"""
You are planning web searches for a market
research project.

Research objective:

{topic}


Research plan:

{plan_text}


Create 3 to 6 focused web search queries.

Together, the queries should cover the most
important parts of the research plan.

Rules:

- Avoid duplicate queries.
- Prefer specific queries over broad queries.
- Include geography when relevant.
- Include recent/current terms when appropriate.
- Search only for information that can realistically
  be obtained from public web sources.
- Do not request interviews or primary surveys.
- Do not perform the research yourself.

Only produce the search-query plan.
"""


    query_plan = (
        structured_query_planner.invoke(
            query_prompt
        )
    )


    evidence = []

    for query in query_plan.queries:

        try:

            results = search_web(
                query=query,
                max_results=3,
            )

            evidence.extend(
                results
            )

        except Exception as exc:

            print(
                f"Search failed for "
                f"{query!r}: {exc}"
            )


    if not evidence:

        raise ValueError(
            "No usable research evidence "
            "was collected."
        )


    unique_evidence = {}

    for item in evidence:

        url = item.get(
            "url",
            "",
        )

        if (
            url
            and url not in unique_evidence
        ):
            unique_evidence[url] = item


    evidence = list(
        unique_evidence.values()
    )


    evidence_text = "\n\n".join(
        f"""
SOURCE {i}

Title:
{item.get("title", "")}

URL:
{item.get("url", "")}

Evidence:
{item.get("content", "")}
"""
        for i, item in enumerate(
            evidence,
            start=1,
        )
    )



    synthesis_prompt = f"""
You are a senior market researcher.

Research objective:

{topic}


Research plan:

{plan_text}


WEB EVIDENCE:

{evidence_text}


Create detailed research notes using ONLY
the evidence above.

Organize the notes around the research plan.

For each important finding:

- explain the finding
- include the source URL
- distinguish FACT from INTERPRETATION
- identify conflicting data when present
- identify missing or weak evidence

Rules:

- Do not invent statistics.
- Do not invent TAM, SAM, or SOM.
- Do not invent companies.
- Do not claim interviews or surveys occurred.
- Do not silently resolve conflicting market-size
  definitions.
- State uncertainty explicitly.
- Do not write the final polished report.

Return detailed research notes.
"""


    response = llm.invoke(
        synthesis_prompt
    )


    research_content = (
        response.content
    )


    if (
        not research_content
        or len(
            str(
                research_content
            ).strip()
        ) < 100
    ):

        raise ValueError(
            "Research synthesis returned "
            "insufficient notes."
        )


    return {
        "research_results": [
            research_content
        ]
    }


def research_quality_node(
    state: ResearchState
):

    topic = state["topic"]

    research_plan = state[
        "research_plan"
    ]

    research_results = state[
        "research_results"
    ]


    plan_text = "\n".join(
        f"{i}. {task}"
        for i, task in enumerate(
            research_plan,
            start=1,
        )
    )


    research_text = "\n\n".join(
        research_results
    )


    quality_llm = llm.with_structured_output(
        ResearchQualityAssessment,
        method="function_calling",
    )


    prompt = f"""
You are a research quality evaluator.

Your job is NOT to write the report.

Your job is to decide whether the collected
research evidence is sufficient for a useful,
evidence-based market analysis.


RESEARCH OBJECTIVE:

{topic}


RESEARCH PLAN:

{plan_text}


COLLECTED RESEARCH:

{research_text}


Evaluate the evidence based on:

1. Coverage of the research objective
2. Coverage of the important research-plan areas
3. Presence of factual evidence
4. Source diversity
5. Source relevance
6. Major unsupported gaps
7. Conflicting claims that need clarification


Do NOT demand perfect or exhaustive research.

The evidence is SUFFICIENT if it provides enough
credible material for a useful market analysis,
even if some minor gaps remain.


Return:

SUFFICIENT

when the research is good enough to proceed.


Return:

NEEDS_MORE_RESEARCH

only when an important evidence gap would materially
weaken the final report.


If more research is needed:

- identify the important missing areas
- generate at most 3 targeted search queries
- avoid repeating research already collected


Do not invent missing facts.
"""


    assessment = quality_llm.invoke(
        prompt
    )


    if assessment is None:

        raise ValueError(
            "Research quality evaluator "
            "returned no structured result."
        )


    return {
        "research_quality_status":
            assessment.status,

        "research_quality_reasoning":
            assessment.reasoning,

        "research_gaps":
            assessment.missing_areas,

        "additional_queries":
            assessment.additional_queries,
    }


def supplemental_research_node(
    state: ResearchState
):

    topic = state["topic"]

    queries = state[
        "additional_queries"
    ][:3]


    if not queries:

        return {
            "research_round":
                state["research_round"] + 1
        }


    evidence = []


    for query in queries:

        try:

            results = search_web(
                query=query,
                max_results=3,
            )

            evidence.extend(
                results
            )

        except Exception as exc:

            print(
                f"Supplemental search failed "
                f"for {query!r}: {exc}"
            )


    if not evidence:

        return {
            "research_results":
                state["research_results"]
                + [
                    (
                        "Supplemental research "
                        "returned no usable evidence."
                    )
                ],

            "research_round":
                state["research_round"] + 1,
        }



    unique_evidence = {}

    for item in evidence:

        url = item.get(
            "url",
            "",
        )

        if (
            url
            and url not in unique_evidence
        ):
            unique_evidence[url] = item


    evidence = list(
        unique_evidence.values()
    )


    evidence_text = "\n\n".join(
        f"""
SOURCE {i}

Title:
{item.get("title", "")}

URL:
{item.get("url", "")}

Evidence:
{item.get("content", "")}
"""
        for i, item in enumerate(
            evidence,
            start=1,
        )
    )


    gaps_text = "\n".join(
        f"- {gap}"
        for gap in state[
            "research_gaps"
        ]
    )


    synthesis_prompt = f"""
You are adding supplemental evidence to an
existing market research project.


Research objective:

{topic}


Important evidence gaps:

{gaps_text}


New web evidence:

{evidence_text}


Create concise supplemental research notes.

Focus only on filling the identified gaps.

Rules:

- Use only the evidence provided.
- Include source URLs.
- Separate facts from interpretations.
- Mention conflicting evidence.
- Do not invent missing statistics.
- Do not repeat unrelated research.
"""


    response = llm.invoke(
        synthesis_prompt
    )


    supplemental_notes = (
        response.content
    )


    return {
        "research_results":
            state["research_results"]
            + [
                supplemental_notes
            ],

        "research_round":
            state["research_round"] + 1,

        "additional_queries": [],
    }


def analyzer_node(state: ResearchState):

    topic = state["topic"]
     
    research_results = state.get(
    "research_results",
    []
    )

    if not research_results:
        raise ValueError(
        "Analyzer received no research results. "
        "Check the researcher node output."
    )

    research_text = "\n\n".join(
        research_results
    )

    prompt = f"""
You are a senior market research analyst.

Research objective:

{topic}

Collected research evidence:

{research_text}

Analyze the evidence.

Your job is NOT to search for new information.
Use only the evidence provided above.

Identify:

1. Key market trends
2. Competitive patterns
3. Customer or buyer needs
4. Market barriers and risks
5. Potential market gaps
6. Business opportunities
7. Important uncertainties or weak evidence

Clearly distinguish:

FACTS:
What is directly supported by the research evidence.

INTERPRETATIONS:
What can reasonably be inferred from those facts.

Do not invent statistics, companies, pricing,
or unsupported claims.

Return a structured analysis that can later
be used to write a market research report.
"""

    response = llm.invoke(prompt)

    return {
        "analysis": response.content
    }


def writer_node(state: ResearchState):

    topic = state["topic"]

    research_text = "\n\n".join(
        state["research_results"]
    )

    analysis = state["analysis"]

    current_draft = state["draft_report"]
    critique = state["critique"]

    is_revision = bool(
        current_draft and critique
    )

    if not is_revision:

        prompt = f"""
You are a professional market research writer.

Research objective:

{topic}


RESEARCH EVIDENCE:

{research_text}


MARKET ANALYSIS:

{analysis}


Write a professional draft market research report.

Structure:

# Executive Summary

# Market Overview

# Market Trends

# Competitive Landscape

# Customer Needs

# Risks and Barriers

# Market Opportunities

# Key Uncertainties

# Sources


Rules:

- Base factual claims on supplied evidence.
- Do not invent statistics.
- Do not invent companies.
- Distinguish facts from interpretations.
- Include source URLs when available.
- Explicitly mention weak or incomplete evidence.
"""

        response = llm.invoke(prompt)

        return {
            "draft_report": response.content
        }




    prompt = f"""
You are revising a market research report.

Research objective:

{topic}


ORIGINAL EVIDENCE:

{research_text}


ANALYSIS:

{analysis}


CURRENT REPORT:

{current_draft}


REVIEWER CRITIQUE:

{critique}


Revise the report to address the reviewer critique.

Rules:

- Preserve correct information.
- Remove unsupported claims.
- Remove irrelevant companies.
- Correct contradictions.
- Do not invent missing evidence.
- If evidence is insufficient, state that explicitly.
- Keep source URLs where possible.

Return the COMPLETE revised report.
"""

    response = llm.invoke(prompt)

    return {
        "draft_report": response.content,
        "iteration": state["iteration"] + 1,
        "critique": "",
    }

def reviewer_node(state: ResearchState):

    topic = state["topic"]

    research_results = "\n\n".join(
        state["research_results"]
    )

    analysis = state["analysis"]
    draft_report = state["draft_report"]

    structured_reviewer = llm.with_structured_output(
        ReviewResult,
        method="function_calling",
    )

    prompt = f"""
You are a strict market research reviewer.

Research objective:

{topic}


ORIGINAL RESEARCH EVIDENCE:

{research_results}


ANALYSIS:

{analysis}


DRAFT REPORT:

{draft_report}


Review the report for:

1. factual support
2. relevance
3. unsupported claims
4. hallucinated statistics
5. irrelevant competitors
6. contradictions
7. missing important findings
8. separation between facts and interpretations
9. source quality
10. clarity and usefulness


Choose:

PASS
if the report is sufficiently supported and useful.

REVISE
if important problems should be corrected.
"""

    review = structured_reviewer.invoke(
        prompt
    )

    return {
        "review_status": review.status,
        "critique": review.critique,
    }


MAX_REVISIONS = 2

def review_router(state: ResearchState):

    if state["review_status"] == "PASS":
        return "approved"

    if state["iteration"] >= MAX_REVISIONS:
        return "max_revisions"

    return "revise"

def max_revisions_node(state: ResearchState):

    return {
        "critique": (
            "Maximum revision limit reached. "
            "The report still has unresolved review issues. "
            + state["critique"]
        )
    }


def human_approval_node(state: ResearchState):

    decision = interrupt(
        {
            "message": "Please review the market research report.",
            "report": state["draft_report"],
            "options": [
                "approve",
                "reject",
            ],
        }
    )

    approved = (
        str(decision).lower() == "approve"
    )

    return {
        "approved": approved
    }

MAX_RESEARCH_ROUNDS = 2


def research_quality_router(
    state: ResearchState
):

    if (
        state["research_quality_status"]
        == "SUFFICIENT"
    ):
        return "analyze"


    if (
        state["research_round"]
        >= MAX_RESEARCH_ROUNDS
    ):
        return "analyze"


    return "research_more"