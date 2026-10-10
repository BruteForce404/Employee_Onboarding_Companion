from langgraph.checkpoint.memory import MemorySaver

import config
from langgraph.graph import END, START, StateGraph

from agents import (
    apply_action_agent,
    case_agent,
    companion_agent,
    final_response_agent,
    human_approval_agent,
    policy_agent,
    reminder_agent,
    supervisor_agent,
)
from state import OnboardingState


def route_from_supervisor(state: OnboardingState) -> str:
    if not state.get("guardrail_passed", False):
        return "final_response"
    return "case_agent"


def route_after_case(state: OnboardingState) -> str:
    selected = state.get("selected_agents") or []
    if "policy_agent" in selected:
        return "policy_agent"
    if "reminder_agent" in selected:
        return "reminder_agent"
    return "companion_agent"


def route_after_policy(state: OnboardingState) -> str:
    selected = state.get("selected_agents") or []
    if "reminder_agent" in selected:
        return "reminder_agent"
    return "companion_agent"


def route_after_companion(state: OnboardingState) -> str:
    action = state.get("proposed_action") or {}
    if action.get("needs_approval"):
        return "human_approval"
    return "final_response"


def build_graph():
    graph = StateGraph(OnboardingState)
    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("case_agent", case_agent)
    graph.add_node("policy_agent", policy_agent)
    graph.add_node("reminder_agent", reminder_agent)
    graph.add_node("companion_agent", companion_agent)
    graph.add_node("human_approval", human_approval_agent)
    graph.add_node("apply_action", apply_action_agent)
    graph.add_node("final_response", final_response_agent)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", route_from_supervisor, ["case_agent", "final_response"])
    graph.add_conditional_edges("case_agent", route_after_case, ["policy_agent", "reminder_agent", "companion_agent"])
    graph.add_conditional_edges("policy_agent", route_after_policy, ["reminder_agent", "companion_agent"])
    graph.add_edge("reminder_agent", "companion_agent")
    graph.add_conditional_edges("companion_agent", route_after_companion, ["human_approval", "final_response"])
    graph.add_edge("human_approval", "apply_action")
    graph.add_edge("apply_action", "final_response")
    graph.add_edge("final_response", END)

    checkpointer = _checkpointer()
    return graph.compile(checkpointer=checkpointer)


def _checkpointer():
    database_url = config.ONBOARDING_DATABASE_URL
    # Postgres is used when ONBOARDING_DATABASE_URL is set, so a missing server cannot block startup.
    if database_url:
        try:
            import psycopg
            from langgraph.checkpoint.postgres import PostgresSaver

            connection = psycopg.connect(database_url, autocommit=True)
            saver = PostgresSaver(connection)
            saver.setup()
            print("Using Postgres checkpointer.")
            return saver
        except Exception as exc:
            print(f"Postgres unavailable ({exc}). Using in-memory checkpoints.")
    return MemorySaver()


app = build_graph()
