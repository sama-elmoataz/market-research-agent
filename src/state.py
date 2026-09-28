from typing import TypedDict


class ResearchState(TypedDict):

    topic: str
    research_plan: list[str]
    research_results: list[str]
    research_quality_status: str
    research_quality_reasoning: str
    research_gaps: list[str]
    additional_queries: list[str]
    research_round: int
    analysis: str
    draft_report: str
    critique: str
    review_status: str
    iteration: int
    approved: bool