import uuid
from langgraph.types import Command
from .graph import research_graph


def get_run_mode():
    mode = input(
        "Start new research or resume? "
        "(new/resume): "
    ).strip().lower()

    if mode == "resume":
        thread_id = input(
            "Enter thread ID: "
        ).strip()

        return "resume", thread_id

    thread_id = str(
        uuid.uuid4()
    )

    print(
        "\nThread ID:",
        thread_id,
    )

    print(
        "Save this ID if you want "
        "to resume this research later.\n"
    )

    return "new", thread_id


def print_final_result(result):
    print(
        "\n" + "=" * 80
    )

    print(
        "FINAL RESULT"
    )

    print(
        "=" * 80
    )

    print(
        result["draft_report"]
    )

    print(
        "\nApproved:",
        result["approved"],
    )

    print(
        "Research quality:",
        result["research_quality_status"],
    )

    print(
        "Extra research rounds:",
        result["research_round"],
    )

    print(
        "Revision count:",
        result["iteration"],
    )


def handle_human_approval(
    result,
    config,
):
    if "__interrupt__" not in result:
        return result

    print(
        "\n" + "=" * 80
    )

    print(
        "HUMAN APPROVAL REQUIRED"
    )

    print(
        "=" * 80
    )

    interrupt_data = (
        result["__interrupt__"][0].value
    )

    print(
        interrupt_data["report"]
    )

    decision = input(
        "\nApprove report? "
        "(approve/reject): "
    ).strip().lower()

    result = research_graph.invoke(
        Command(
            resume=decision
        ),
        config=config,
    )

    return result


def main():
    mode, thread_id = get_run_mode()

    config = {
    "configurable": {
        "thread_id": thread_id
    },

    "tags": [
        "market-research",
        "agentic-ai",
    ],

    "metadata": {
        "thread_id": thread_id,
        "run_mode": mode,
    },
}

    if mode == "new":
        topic = input(
            "Enter a market research objective: "
        )

        initial_state = {
            "topic": topic,

            "research_plan": [],

            "research_results": [],

            "research_quality_status": "",

            "research_quality_reasoning": "",

            "research_gaps": [],

            "additional_queries": [],

            "research_round": 0,

            "analysis": "",

            "draft_report": "",

            "critique": "",

            "review_status": "",

            "iteration": 0,

            "approved": False,
        }

        result = research_graph.invoke(
            initial_state,
            config=config,
        )

        result = handle_human_approval(
            result=result,
            config=config,
        )

        print_final_result(
            result
        )

        return


    snapshot = research_graph.get_state(
        config
    )

    if not snapshot.values:
        print(
            "\nNo checkpoint was found "
            "for this thread ID."
        )

        return

    print(
        "\nCheckpoint loaded."
    )

    print(
        "Next node(s):",
        snapshot.next,
    )


    if not snapshot.next:
        print(
            "\nThis research run "
            "is already complete."
        )

        print_final_result(
            snapshot.values
        )

        return


    if "human_approval" in snapshot.next:
        print(
            "\n" + "=" * 80
        )

        print(
            "HUMAN APPROVAL REQUIRED"
        )

        print(
            "=" * 80
        )

        print(
            snapshot.values[
                "draft_report"
            ]
        )

        decision = input(
            "\nApprove report? "
            "(approve/reject): "
        ).strip().lower()

        result = research_graph.invoke(
            Command(
                resume=decision
            ),
            config=config,
        )

        result = handle_human_approval(
            result=result,
            config=config,
        )

        print_final_result(
            result
        )

        return


    print(
        "\nResuming workflow from "
        "the saved checkpoint..."
    )

    result = research_graph.invoke(
        None,
        config=config,
    )

    result = handle_human_approval(
        result=result,
        config=config,
    )

    print_final_result(
        result
    )


if __name__ == "__main__":
    main()