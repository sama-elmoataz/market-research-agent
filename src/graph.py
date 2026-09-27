from langgraph.graph import (
    StateGraph,
    START,
    END,
)

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from .state import ResearchState

from .nodes import (
    planner_node,
    researcher_node,
    research_quality_node,
    supplemental_research_node,
    analyzer_node,
    writer_node,
    reviewer_node,
    max_revisions_node,
    human_approval_node,
    research_quality_router,
    review_router,
)


builder = StateGraph(
    ResearchState
)


# -------------------------------------------
# Nodes
# -------------------------------------------

builder.add_node(
    "planner",
    planner_node,
)

builder.add_node(
    "researcher",
    researcher_node,
)

builder.add_node(
    "analyzer",
    analyzer_node,
)

builder.add_node(
    "writer",
    writer_node,
)

builder.add_node(
    "reviewer",
    reviewer_node,
)

builder.add_node(
    "human_approval",
    human_approval_node,
)

builder.add_node(
    "max_revisions",
    max_revisions_node,
)

builder.add_node(
    "research_quality",
    research_quality_node,
)

builder.add_node(
    "supplemental_research",
    supplemental_research_node,
)


# -------------------------------------------
# Normal edges
# -------------------------------------------

builder.add_edge(
    START,
    "planner",
)

builder.add_edge(
    "planner",
    "researcher",
)

builder.add_edge(
    "researcher",
    "research_quality",
)

builder.add_conditional_edges(
    "research_quality",
    research_quality_router,
    {
        "analyze": "analyzer",
        "research_more":
            "supplemental_research",
    },
)

builder.add_edge(
    "supplemental_research",
    "research_quality",
)

builder.add_edge(
    "analyzer",
    "writer",
)

builder.add_edge(
    "writer",
    "reviewer",
)


# -------------------------------------------
# Conditional edge
# -------------------------------------------

builder.add_conditional_edges(
    "reviewer",
    review_router,
    {
        "approved": "human_approval",
        "revise": "writer",
        "max_revisions": "max_revisions",
    },
)


builder.add_edge(
    "human_approval",
    END,
)

builder.add_edge(
    "max_revisions",
    "human_approval",
)

# -------------------------------------------
# Persistent checkpointing
# -------------------------------------------

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "research_checkpoints.sqlite"
)

checkpoint_connection = sqlite3.connect(
    DB_PATH,
    check_same_thread=False,
)

checkpointer = SqliteSaver(
    checkpoint_connection
)


research_graph = builder.compile(
    checkpointer=checkpointer
)

