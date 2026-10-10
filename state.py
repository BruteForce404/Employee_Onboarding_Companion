import operator
from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from typing_extensions import TypedDict


class OnboardingState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], operator.add]
    trace: Annotated[list[str], operator.add]

    user_id: str
    user_query: str
    viewer_role: str
    employee_id: str

    forced_intent: str
    forced_requirement_id: str

    guardrail_passed: bool
    intent: str
    target_requirement_id: str
    selected_agents: list[str]
    supervisor_reasoning: str

    case_snapshot: dict[str, Any]
    policy_context: list[dict[str, Any]]
    reminder_plan: dict[str, Any]
    proposed_action: dict[str, Any]
    companion_message: str

    approval_request: str
    human_feedback: str
    approved: bool
    action_result: dict[str, Any]

    final_response: str
    llm_calls: int
