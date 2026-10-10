import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from case_engine import known_requirement_ids, narrative
from config import get_llm
from mcp_client import call_tool_sync
from state import OnboardingState

OFF_TOPIC = (
    "poem",
    "japan",
    "flight",
    "weather forecast",
    "stock price",
    "write code",
    "ignore previous",
)

HINTS = (
    ("passport", "identity_proof"),
    ("photo", "identity_proof"),
    ("identity", "identity_proof"),
    ("conduct", "code_of_conduct"),
    ("benefit", "benefits_enrollment"),
    ("bank", "bank_details"),
    ("payroll", "bank_details"),
    ("tax", "tax_declaration"),
    ("laptop", "laptop_provision"),
    ("login", "sso_account"),
    ("sso", "sso_account"),
    ("badge", "badge_issued"),
    ("security", "security_training"),
    ("training", "security_training"),
    ("buddy", "buddy_coffee"),
)


def _llm():
    return get_llm()


def _llm_text(system: str, prompt: str) -> str:
    response = _llm().invoke([
        SystemMessage(content=system),
        HumanMessage(content=prompt),
    ])
    return response.content


def _json_from_llm(text: str) -> dict:
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])


def _bump(state: OnboardingState, extra: int = 1) -> int:
    return state.get("llm_calls", 0) + extra


def _fallback_route(query: str) -> dict:
    lowered = query.lower()
    if any(phrase in lowered for phrase in OFF_TOPIC):
        return {
            "allowed": False,
            "reason": "This companion only helps with joining the company.",
        }
    intent = "ask"
    if any(word in lowered for word in ("uploaded", "re-upload", "clearer", "submitted", "submit")):
        intent = "submit_update"
    elif any(word in lowered for word in ("remind", "nudge", "ping")):
        intent = "send_reminder"
    elif any(word in lowered for word in ("finished", "i've done", "ive done", "mark", "accept", "completed")):
        intent = "complete_task"
    hint = ""
    for word, requirement_id in HINTS:
        if word in lowered:
            hint = requirement_id
            break
    focus = ""
    if "rohan" in lowered:
        focus = "rohan"
    elif "maya" in lowered:
        focus = "maya"
    elif "everyone" in lowered or "who needs" in lowered or "portfolio" in lowered:
        focus = "all"
    return {
        "allowed": True,
        "intent": intent,
        "requirement_hint": hint,
        "focus_employee_id": focus,
        "selected_agents": ["case_agent", "policy_agent", "reminder_agent"],
        "reasoning": "Routed from the question without a model call.",
    }


def supervisor_agent(state: OnboardingState):
    query = state.get("user_query", "")
    role = state.get("viewer_role") or "employee"
    employee_id = state.get("employee_id") or "maya"
    forced_intent = (state.get("forced_intent") or "").strip()
    forced_requirement = (state.get("forced_requirement_id") or "").strip()

    if forced_intent:
        return {
            "guardrail_passed": True,
            "intent": forced_intent,
            "target_requirement_id": forced_requirement,
            "employee_id": employee_id,
            "viewer_role": role,
            "selected_agents": ["case_agent", "policy_agent", "reminder_agent"],
            "supervisor_reasoning": "The companion already chose this action, so it skipped free-text routing.",
            "messages": [AIMessage(content="Supervisor accepted a confirmed companion action.")],
            "trace": ["Supervisor: action came from the companion, not free text."],
            "llm_calls": state.get("llm_calls", 0),
        }

    catalog = known_requirement_ids(employee_id if employee_id != "all" else "all")
    parsed = None
    llm_calls = state.get("llm_calls", 0)
    if _llm() is not None:
        prompt = f"""
You are the supervisor and input guardrail for an employee onboarding companion.

Allow only requests about joining, documents, benefits, equipment, access, meetings, training, reminders, or what to do next for a new hire.
Reject travel, general coding, poems, and anything unrelated to onboarding.

Viewer role: {role}
Employee in context: {employee_id}
Known requirements: {json.dumps(catalog)}

Return only JSON:
{{
  "allowed": true,
  "reason": "",
  "intent": "ask",
  "requirement_hint": "",
  "focus_employee_id": "",
  "selected_agents": ["case_agent", "policy_agent", "reminder_agent"],
  "reasoning": ""
}}

intent is one of: ask, submit_update, send_reminder, complete_task.
requirement_hint must be an id from the known list, or empty.
focus_employee_id is maya, rohan, all, or empty to keep the current person.
Include policy_agent when a rule or explanation would help.
Include reminder_agent when someone may need a nudge. Both are usually right.

User request:
{query}
"""
        try:
            raw = _llm_text("Return strict JSON only.", prompt)
            parsed = _json_from_llm(raw)
            llm_calls += 1
        except Exception:
            parsed = None

    if parsed is None:
        parsed = _fallback_route(query)

    if not parsed.get("allowed", False):
        reason = parsed.get("reason") or "This companion only helps with joining the company."
        return {
            "guardrail_passed": False,
            "intent": "ask",
            "selected_agents": [],
            "supervisor_reasoning": reason,
            "final_response": reason,
            "employee_id": employee_id,
            "viewer_role": role,
            "messages": [AIMessage(content=reason)],
            "trace": [f"Guardrail stopped the request: {reason}"],
            "llm_calls": llm_calls,
        }

    focus = (parsed.get("focus_employee_id") or "").strip().lower()
    if focus in {"maya", "rohan", "all"}:
        employee_id = focus
    hint = (parsed.get("requirement_hint") or "").strip()
    known = {item["id"] for item in known_requirement_ids(employee_id if employee_id != "all" else "all")}
    if hint not in known:
        hint = ""

    selected = [name for name in ("case_agent", "policy_agent", "reminder_agent") if name in (parsed.get("selected_agents") or [])]
    if "case_agent" not in selected:
        selected.insert(0, "case_agent")

    return {
        "guardrail_passed": True,
        "intent": parsed.get("intent") or "ask",
        "target_requirement_id": hint,
        "employee_id": employee_id,
        "viewer_role": role,
        "selected_agents": selected,
        "supervisor_reasoning": parsed.get("reasoning") or "Reading the case before answering.",
        "messages": [AIMessage(content="Supervisor planned the onboarding agents.")],
        "trace": [f"Supervisor: {parsed.get('intent') or 'ask'} for {employee_id} as {role}."],
        "llm_calls": llm_calls,
    }


def case_agent(state: OnboardingState):
    employee_id = state.get("employee_id") or "maya"
    role = state.get("viewer_role") or "employee"
    snapshot = call_tool_sync("get_readiness", {"employee_id": employee_id, "viewer_role": role})
    if isinstance(snapshot, dict) and snapshot.get("ok") is False:
        raise RuntimeError(snapshot.get("error") or "Case file unavailable")
    label = snapshot.get("name") or "the onboarding portfolio"
    return {
        "case_snapshot": snapshot,
        "messages": [AIMessage(content=f"Case agent read {label}.")],
        "trace": [f"Case agent: loaded {label} from the HR case file."],
    }


def policy_agent(state: OnboardingState):
    snapshot = state.get("case_snapshot") or {}
    query = state.get("user_query") or ""
    topic = ""
    nxt = snapshot.get("next") or {}
    if nxt:
        topic = nxt.get("policy_topic") or ""
    if state.get("target_requirement_id") and snapshot.get("next") and snapshot["next"]["id"] != state["target_requirement_id"]:
        topic = state["target_requirement_id"].split("_")[0]
    hits = call_tool_sync("search_onboarding_policy", {"query": f"{topic} {query}".strip()})
    policies = hits.get("hits", []) if isinstance(hits, dict) else []
    title = policies[0]["title"] if policies else "no matching policy"
    return {
        "policy_context": policies,
        "messages": [AIMessage(content="Policy agent retrieved the relevant passage.")],
        "trace": [f"Policy agent: {title}."],
    }


def reminder_agent(state: OnboardingState):
    snapshot = state.get("case_snapshot") or {}
    plan = {"items": [], "note": "No reminder is due."}
    if snapshot.get("mode") == "portfolio":
        for person in snapshot.get("people") or []:
            action = person.get("action") or {}
            if action.get("type") == "send_reminder":
                plan["items"].append({
                    "employee_id": person["employee_id"],
                    "name": person["name"],
                    "requirement_id": action.get("requirement_id"),
                    "message": action.get("message") or action.get("title"),
                })
        plan["note"] = f"{len(plan['items'])} reminder(s) could be sent."
    else:
        action = snapshot.get("action") or {}
        if action.get("type") == "send_reminder":
            plan["items"].append({
                "employee_id": snapshot.get("employee_id"),
                "name": snapshot.get("name"),
                "requirement_id": action.get("requirement_id"),
                "message": action.get("message") or action.get("title"),
                "audience": action.get("audience"),
            })
            plan["note"] = "One reminder is ready for approval."
        elif snapshot.get("urgency") == "clear":
            plan["note"] = "Nobody needs a reminder right now."
        else:
            plan["note"] = "The next step is work, not a reminder."
    return {
        "reminder_plan": plan,
        "messages": [AIMessage(content="Reminder agent checked who is due a nudge.")],
        "trace": [f"Reminder agent: {plan['note']}"],
    }


def _proposed_from_intent(state: OnboardingState) -> dict:
    snapshot = state.get("case_snapshot") or {}
    intent = state.get("intent") or "ask"
    target = state.get("target_requirement_id") or ""
    if snapshot.get("mode") == "portfolio" or intent == "ask":
        return {"type": "none", "needs_approval": False}

    action = dict(snapshot.get("action") or {})
    if target and action.get("requirement_id") != target:
        # The person named a specific step. Carry it only when the intent matches
        # a write, and let the case file reject it if the dependency is not met.
        action = {
            "type": intent if intent in {"submit_update", "complete_task", "send_reminder"} else "none",
            "requirement_id": target,
            "title": target.replace("_", " "),
            "note": state.get("user_query") or "",
            "message": state.get("user_query") or "",
            "audience": "employee",
            "label": action.get("label") or "Confirm",
        }
    elif not action:
        return {"type": "none", "needs_approval": False}
    else:
        action = dict(action)

    if intent == "ask":
        return {"type": "none", "needs_approval": False}
    if action.get("type") != intent and not state.get("forced_intent"):
        # Trust the case file's next action when the words were vague.
        if intent in {"submit_update", "complete_task", "send_reminder"} and action.get("type") == intent:
            pass
        elif state.get("target_requirement_id"):
            action["type"] = intent
        else:
            action = dict(snapshot.get("action") or {})
            if action.get("type") != intent:
                return {"type": "none", "needs_approval": False}

    action["needs_approval"] = action.get("type") in {"submit_update", "complete_task", "send_reminder"}
    action["employee_id"] = snapshot.get("employee_id") or state.get("employee_id")
    action["actor_role"] = state.get("viewer_role") or "employee"
    return action


def companion_agent(state: OnboardingState):
    snapshot = state.get("case_snapshot") or {}
    policies = state.get("policy_context") or []
    draft = narrative(snapshot, policies)
    action = _proposed_from_intent(state)
    llm_calls = state.get("llm_calls", 0)

    if action.get("needs_approval"):
        message = (
            f"I can {action.get('title', 'update the case').lower()} "
            f"for {snapshot.get('preferred_name') or snapshot.get('name') or 'this person'}. "
            "Nothing is written until you confirm."
        )
    elif _llm() is None:
        message = draft
    else:
        prompt = f"""
Rewrite this onboarding brief as a calm note to the {state.get('viewer_role')} reader.
Use only the facts in the brief. Do not invent tasks, dates, owners, or systems.
Keep it under 140 words. Start with the one thing that matters.

Brief:
{draft}

Question:
{state.get('user_query')}
"""
        try:
            message = _llm_text("You write concise onboarding guidance from a trusted brief.", prompt)
            llm_calls += 1
        except Exception:
            message = draft

    approval_request = ""
    if action.get("needs_approval"):
        detail = action.get("message") or action.get("note") or action.get("title")
        approval_request = f"{action.get('title')}\n\n{detail}"

    return {
        "proposed_action": action,
        "companion_message": message,
        "approval_request": approval_request,
        "messages": [AIMessage(content="Companion prepared the next step.")],
        "trace": ["Companion: chose one next step from the case file."],
        "llm_calls": llm_calls,
    }


def human_approval_agent(state: OnboardingState):
    action = state.get("proposed_action") or {}
    feedback = interrupt(
        {
            "question": "Should I write this into the onboarding case?",
            "title": action.get("title") or "Confirm update",
            "detail": action.get("message") or action.get("note") or "",
            "action": action,
        }
    )
    approved = bool(feedback.get("approved"))
    note = feedback.get("feedback") or ""
    return {
        "approved": approved,
        "human_feedback": note,
        "messages": [AIMessage(content="A person reviewed the proposed update.")],
        "trace": ["Human approval: " + ("confirmed." if approved else "left the case unchanged.")],
    }


def apply_action_agent(state: OnboardingState):
    action = state.get("proposed_action") or {}
    if not state.get("approved"):
        return {
            "action_result": {"ok": False, "skipped": True, "error": "Not written."},
            "messages": [AIMessage(content="Update was not applied.")],
            "trace": ["Case file left unchanged."],
        }

    employee_id = action.get("employee_id") or state.get("employee_id")
    requirement_id = action.get("requirement_id") or ""
    kind = action.get("type")
    note = state.get("human_feedback") or action.get("note") or ""
    if kind == "submit_update":
        result = call_tool_sync("submit_requirement_update", {
            "employee_id": employee_id,
            "requirement_id": requirement_id,
            "note": note or action.get("note") or "Submitted from the companion.",
            "actor_role": action.get("actor_role") or state.get("viewer_role") or "employee",
        })
    elif kind == "complete_task":
        result = call_tool_sync("complete_onboarding_requirement", {
            "employee_id": employee_id,
            "requirement_id": requirement_id,
            "actor_role": action.get("actor_role") or state.get("viewer_role") or "hr",
            "note": note or action.get("note") or "",
        })
    elif kind == "send_reminder":
        result = call_tool_sync("log_onboarding_reminder", {
            "employee_id": employee_id,
            "requirement_id": requirement_id,
            "message": note or action.get("message") or action.get("title") or "Reminder",
            "audience": action.get("audience") or "employee",
        })
    else:
        result = {"ok": False, "error": "Nothing to write."}

    refreshed = call_tool_sync("get_readiness", {
        "employee_id": employee_id,
        "viewer_role": state.get("viewer_role") or "employee",
    })
    ok = isinstance(result, dict) and result.get("ok")
    return {
        "action_result": result if isinstance(result, dict) else {"ok": True, "raw": str(result)},
        "case_snapshot": refreshed if isinstance(refreshed, dict) else state.get("case_snapshot"),
        "messages": [AIMessage(content="Case file updated." if ok else "Case file refused the update.")],
        "trace": ["Apply: " + ("wrote the update." if ok else result.get("error", "refused."))],
    }


def final_response_agent(state: OnboardingState):
    if not state.get("guardrail_passed", False):
        text = state.get("final_response") or "This companion only helps with joining the company."
        return {
            "final_response": text,
            "messages": [AIMessage(content=text)],
            "trace": ["Final: guardrail message."],
        }

    result = state.get("action_result") or {}
    snapshot = state.get("case_snapshot") or {}
    if result:
        if result.get("skipped"):
            text = "Nothing was written. " + (state.get("human_feedback") or "The case is unchanged.")
        elif result.get("ok"):
            follow = narrative(snapshot, state.get("policy_context") or [])
            text = "That's recorded.\n\n" + follow
        else:
            text = result.get("error") or "The case file did not accept that update."
        return {
            "final_response": text,
            "messages": [AIMessage(content=text)],
            "trace": ["Final: told the person what the case file did."],
        }

    text = state.get("companion_message") or narrative(snapshot, state.get("policy_context") or [])
    return {
        "final_response": text,
        "messages": [AIMessage(content=text)],
        "trace": ["Final: companion note ready."],
    }
