from typing import Literal

from pydantic import BaseModel, Field


class ResearchPlan(BaseModel):
    tasks: list[str] = Field(
        description="A list of 4 to 6 focused market research tasks."
    )


class SearchQueries(BaseModel):
    queries: list[str] = Field(
        min_length=3,
        max_length=6,
        description=(
            "A list of 3 to 6 focused web search queries "
            "that together cover the research plan."
        ),
    )


class ReviewResult(BaseModel):
    status: Literal["PASS", "REVISE"]

    critique: str = Field(
        description="Explanation of the review decision."
    )


class ResearchQualityAssessment(BaseModel):

    status: Literal[
        "SUFFICIENT",
        "NEEDS_MORE_RESEARCH",
    ]

    reasoning: str = Field(
        description=(
            "Short explanation of why the "
            "research is sufficient or insufficient."
        )
    )

    missing_areas: list[str] = Field(
        default_factory=list,
        description=(
            "Important research areas that are "
            "still weak or missing."
        ),
    )

    additional_queries: list[str] = Field(
        default_factory=list,
        max_length=3,
        description=(
            "Up to 3 targeted web search queries "
            "needed to close important evidence gaps."
        ),
    )    