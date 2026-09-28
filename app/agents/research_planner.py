from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.agents.models import ResearchPlan
from app.llm.client import llm


class ResearchPlannerInputState(TypedDict):
    user_query: str


class ResearchPlannerState(TypedDict):
    user_query: str
    research_plan: ResearchPlan | None
    planning_error: str


class ResearchPlannerOutputState(TypedDict):
    research_plan: ResearchPlan | None
    planning_error: str


research_planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Research Planner for an investment research system. "
            "Your responsibility is only to determine which research areas "
            "are needed to answer the user's request. "
            "Available research areas are: company, financial, market, "
            "and industry_macro. "
            "Select only the relevant research areas."
            "Provide a concise rationale explaining why the selected"
            "research areas are required."
            "Do not execute any research agent. "
            "Do not perform valuation. "
            "Do not assess investment risk. "
            "Do not make an investment recommendation. "
            "Do not produce research findings or invent data.",
        ),
        (
            "human",
            "Create a research plan for the following user request.\n\n"
            "User request: {user_query}",
        ),
    ]

)


structured_research_planner_llm = (
    llm.with_structured_output(ResearchPlan)
)


def research_planner(
    state: ResearchPlannerState,
) -> ResearchPlannerState:

    prompt_value = research_planner_prompt.invoke(
        {
            "user_query": state["user_query"],
        }
    )

    try:
        research_plan = structured_research_planner_llm.invoke(
            prompt_value
        )
    except Exception as exc:
        return {
            "research_plan": None,
            "planning_error": str(exc),
        }

    return {
        "research_plan": research_plan,
        "planning_error": "",
    }


def build_research_planner_graph():
    builder = StateGraph(
        ResearchPlannerState,
        input_schema=ResearchPlannerInputState,
        output_schema=ResearchPlannerOutputState,
    )

    builder.add_node(
        "research_planner",
        research_planner,
    )

    builder.add_edge(
        START,
        "research_planner",
    )

    builder.add_edge(
        "research_planner",
        END,
    )

    return builder.compile()


research_planner_graph = build_research_planner_graph()