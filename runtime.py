import uuid

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import app


def thread_config(thread_id: str | None = None) -> dict:
    return {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}


def ask(
    query: str,
    *,
    viewer_role: str,
    employee_id: str,
    user_id: str = "demo",
    thread_id: str | None = None,
    forced_intent: str = "",
    forced_requirement_id: str = "",
):
    config = thread_config(thread_id)
    result = app.invoke(
        {
            "messages": [HumanMessage(content=query)],
            "trace": [],
            "user_id": user_id,
            "user_query": query,
            "viewer_role": viewer_role,
            "employee_id": employee_id,
            "forced_intent": forced_intent,
            "forced_requirement_id": forced_requirement_id,
            "guardrail_passed": False,
            "selected_agents": [],
            "case_snapshot": {},
            "policy_context": [],
            "proposed_action": {},
            "final_response": "",
            "llm_calls": 0,
        },
        config=config,
    )
    return result, config


def resume(decision: dict, config: dict):
    return app.invoke(Command(resume=decision), config=config)


def waiting_for_approval(result: dict) -> bool:
    return bool(result and result.get("__interrupt__"))
