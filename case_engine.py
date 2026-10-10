"""Deterministic onboarding case file.

Agents phrase and route. This module decides what is true: which documents
are in, which requirements are satisfied, what is blocked, who owns the next
step, and whether a reminder is due. HR, IT, and document systems are mocked
behind this store.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICY_DIR = ROOT / "data" / "policies"

OWNER_LABELS = {
    "employee": "Employee",
    "hr": "HR",
    "it": "IT",
    "manager": "Manager",
}

DONE = {"done", "waived"}


def store_path() -> Path:
    override = os.environ.get("ONBOARDING_STORE_PATH")
    if override:
        return Path(override)
    return ROOT / "data" / "case_store.json"


def _date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def _iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")


def _req(spec: dict) -> dict:
    base = {
        "depends_on": [],
        "due": None,
        "policy_topic": "",
        "note": "",
        "document": None,
    }
    base.update(spec)
    return base


def _meeting(spec: dict) -> dict:
    return spec


def seed() -> dict:
    return {
        "as_of": "2026-10-10",
        "employees": {
            "maya": {
                "id": "maya",
                "name": "Maya Chen",
                "preferred_name": "Maya",
                "role_title": "Product Designer",
                "team": "Design",
                "location": "Bengaluru studio",
                "start_date": "2026-10-20",
                "manager": "Arun Mehta",
                "hr_partner": "Priya Shah",
                "it_partner": "Dev Anand",
                "requirements": [
                    _req({
                        "id": "offer_accepted",
                        "title": "Offer accepted",
                        "short": "Offer",
                        "owner": "hr",
                        "status": "done",
                        "note": "Signed 28 Sep.",
                    }),
                    _req({
                        "id": "personal_details",
                        "title": "Personal details confirmed",
                        "short": "Personal details",
                        "owner": "employee",
                        "status": "done",
                        "note": "Name, address, and emergency contact are on file.",
                    }),
                    _req({
                        "id": "identity_proof",
                        "title": "Re-upload the passport bio page",
                        "short": "Passport photo",
                        "owner": "employee",
                        "status": "needs_clarification",
                        "due": "2026-10-16",
                        "policy_topic": "identity",
                        "review": True,
                        "note": "The scan is cropped, so payroll and access cannot use it yet.",
                        "document": {
                            "filename": "passport_scan.jpg",
                            "received_on": "2026-10-08",
                            "review_note": "All four corners of the bio page need to be visible.",
                        },
                    }),
                    _req({
                        "id": "code_of_conduct",
                        "title": "Acknowledge the code of conduct",
                        "short": "Code of conduct",
                        "owner": "employee",
                        "status": "not_started",
                        "due": "2026-10-16",
                        "policy_topic": "conduct",
                        "note": "A short acknowledgement. Nothing else depends on it.",
                    }),
                    _req({
                        "id": "benefits_enrollment",
                        "title": "Choose your benefits",
                        "short": "Benefits",
                        "owner": "employee",
                        "status": "not_started",
                        "due": "2026-10-17",
                        "policy_topic": "benefits",
                        "note": "Worth doing before Wednesday's walkthrough, or during it.",
                    }),
                    _req({
                        "id": "bank_details",
                        "title": "Add bank details for payroll",
                        "short": "Bank details",
                        "owner": "employee",
                        "status": "not_started",
                        "due": "2026-10-18",
                        "depends_on": ["identity_proof"],
                        "policy_topic": "payroll",
                        "review": True,
                    }),
                    _req({
                        "id": "tax_declaration",
                        "title": "Submit the tax declaration",
                        "short": "Tax declaration",
                        "owner": "employee",
                        "status": "not_started",
                        "due": "2026-10-18",
                        "depends_on": ["identity_proof"],
                        "policy_topic": "payroll",
                        "review": True,
                    }),
                    _req({
                        "id": "laptop_provision",
                        "title": "Laptop for Maya",
                        "short": "Laptop",
                        "owner": "it",
                        "status": "in_progress",
                        "due": "2026-10-16",
                        "depends_on": ["offer_accepted"],
                        "policy_topic": "equipment",
                        "note": "Ordered. Expected at the studio on 16 Oct.",
                    }),
                    _req({
                        "id": "sso_account",
                        "title": "Create Maya's login",
                        "short": "Login",
                        "owner": "it",
                        "status": "not_started",
                        "due": "2026-10-17",
                        "depends_on": ["identity_proof"],
                        "policy_topic": "equipment",
                        "note": "Legal name has to match the identity document.",
                    }),
                    _req({
                        "id": "badge_issued",
                        "title": "Issue the studio badge",
                        "short": "Badge",
                        "owner": "hr",
                        "status": "not_started",
                        "due": "2026-10-18",
                        "depends_on": ["identity_proof"],
                        "policy_topic": "equipment",
                    }),
                    _req({
                        "id": "collect_equipment",
                        "title": "Collect laptop and badge",
                        "short": "Collection",
                        "owner": "employee",
                        "status": "not_started",
                        "due": "2026-10-20",
                        "depends_on": ["laptop_provision", "badge_issued"],
                        "policy_topic": "equipment",
                        "note": "Reception, Day 1 morning.",
                    }),
                    _req({
                        "id": "security_training",
                        "title": "Finish security training",
                        "short": "Security training",
                        "owner": "employee",
                        "status": "not_started",
                        "due": "2026-10-24",
                        "depends_on": ["sso_account"],
                        "policy_topic": "security",
                    }),
                    _req({
                        "id": "manager_welcome",
                        "title": "Welcome conversation with Arun",
                        "short": "Welcome",
                        "owner": "manager",
                        "status": "in_progress",
                        "due": "2026-10-20",
                        "policy_topic": "first_week",
                        "note": "Monday 20 Oct, 10:00, Bengaluru studio.",
                    }),
                    _req({
                        "id": "team_intro",
                        "title": "Meet the design team",
                        "short": "Team intro",
                        "owner": "manager",
                        "status": "not_started",
                        "due": "2026-10-21",
                        "depends_on": ["manager_welcome"],
                        "policy_topic": "first_week",
                    }),
                ],
                "meetings": [
                    _meeting({
                        "id": "benefits_call",
                        "title": "Benefits walkthrough",
                        "when": "2026-10-14 11:00",
                        "with": "Priya Shah",
                        "where": "Video call",
                    }),
                    _meeting({
                        "id": "welcome",
                        "title": "Welcome with Arun",
                        "when": "2026-10-20 10:00",
                        "with": "Arun Mehta",
                        "where": "Bengaluru studio",
                    }),
                    _meeting({
                        "id": "induction",
                        "title": "Studio induction",
                        "when": "2026-10-20 14:00",
                        "with": "People team",
                        "where": "Bengaluru studio",
                    }),
                    _meeting({
                        "id": "team",
                        "title": "Design team introduction",
                        "when": "2026-10-21 11:00",
                        "with": "Design team",
                        "where": "Bengaluru studio",
                    }),
                ],
                "reminders": [],
                "events": [
                    {"at": "2026-09-28", "text": "Offer signed."},
                    {"at": "2026-10-08", "text": "Passport scan received and sent back for a clearer photo."},
                ],
            },
            "rohan": {
                "id": "rohan",
                "name": "Rohan Iyer",
                "preferred_name": "Rohan",
                "role_title": "Backend Engineer",
                "team": "Platform",
                "location": "Bengaluru studio",
                "start_date": "2026-10-06",
                "manager": "Leela Nair",
                "hr_partner": "Priya Shah",
                "it_partner": "Dev Anand",
                "requirements": [
                    _req({"id": "offer_accepted", "title": "Offer accepted", "short": "Offer", "owner": "hr", "status": "done"}),
                    _req({"id": "personal_details", "title": "Personal details confirmed", "short": "Personal details", "owner": "employee", "status": "done"}),
                    _req({
                        "id": "identity_proof",
                        "title": "Identity document",
                        "short": "Identity",
                        "owner": "employee",
                        "status": "done",
                        "policy_topic": "identity",
                        "document": {"filename": "passport_rohan.pdf", "received_on": "2026-09-30", "review_note": ""},
                    }),
                    _req({"id": "code_of_conduct", "title": "Code of conduct", "short": "Code of conduct", "owner": "employee", "status": "done", "policy_topic": "conduct"}),
                    _req({"id": "benefits_enrollment", "title": "Benefits", "short": "Benefits", "owner": "employee", "status": "done", "policy_topic": "benefits"}),
                    _req({"id": "bank_details", "title": "Bank details", "short": "Bank details", "owner": "employee", "status": "done", "depends_on": ["identity_proof"], "policy_topic": "payroll"}),
                    _req({"id": "tax_declaration", "title": "Tax declaration", "short": "Tax declaration", "owner": "employee", "status": "done", "depends_on": ["identity_proof"], "policy_topic": "payroll"}),
                    _req({"id": "laptop_provision", "title": "Laptop", "short": "Laptop", "owner": "it", "status": "done", "policy_topic": "equipment", "note": "Collected on Day 1."}),
                    _req({"id": "sso_account", "title": "Login", "short": "Login", "owner": "it", "status": "done", "depends_on": ["identity_proof"], "policy_topic": "equipment"}),
                    _req({"id": "badge_issued", "title": "Badge", "short": "Badge", "owner": "hr", "status": "done", "depends_on": ["identity_proof"]}),
                    _req({"id": "collect_equipment", "title": "Collect laptop and badge", "short": "Collection", "owner": "employee", "status": "done", "depends_on": ["laptop_provision", "badge_issued"]}),
                    _req({
                        "id": "security_training",
                        "title": "Finish security training",
                        "short": "Security training",
                        "owner": "employee",
                        "status": "not_started",
                        "due": "2026-10-13",
                        "depends_on": ["sso_account"],
                        "policy_topic": "security",
                        "note": "About 20 minutes. The link is already on the login home page.",
                    }),
                    _req({"id": "manager_welcome", "title": "Welcome with Leela", "short": "Welcome", "owner": "manager", "status": "done", "policy_topic": "first_week"}),
                    _req({"id": "team_intro", "title": "Platform team introduction", "short": "Team intro", "owner": "manager", "status": "done", "depends_on": ["manager_welcome"]}),
                    _req({
                        "id": "buddy_coffee",
                        "title": "Buddy coffee with Neel",
                        "short": "Buddy coffee",
                        "owner": "manager",
                        "status": "in_progress",
                        "due": "2026-10-15",
                        "policy_topic": "first_week",
                        "note": "Wednesday 15 Oct, 16:00. Neel will walk over.",
                    }),
                ],
                "meetings": [
                    _meeting({
                        "id": "buddy",
                        "title": "Buddy coffee with Neel",
                        "when": "2026-10-15 16:00",
                        "with": "Neel Kapoor",
                        "where": "Studio cafe",
                    }),
                ],
                "reminders": [],
                "events": [
                    {"at": "2026-10-06", "text": "Day 1 complete. Laptop, badge, and team intro done."},
                ],
            },
        },
    }


def _database_url() -> str:
    if os.environ.get("ONBOARDING_STORE_PATH"):
        return ""
    return os.environ.get("ONBOARDING_DATABASE_URL") or ""


_SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    preferred_name TEXT NOT NULL,
    role_title TEXT NOT NULL,
    team TEXT NOT NULL,
    location TEXT NOT NULL,
    start_date DATE NOT NULL,
    manager TEXT NOT NULL,
    hr_partner TEXT NOT NULL,
    it_partner TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS app_settings (
    id INT PRIMARY KEY,
    as_of DATE NOT NULL
);
CREATE TABLE IF NOT EXISTS requirements (
    employee_id TEXT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    id TEXT NOT NULL,
    position INT NOT NULL,
    title TEXT NOT NULL,
    short TEXT NOT NULL,
    owner TEXT NOT NULL,
    status TEXT NOT NULL,
    due DATE,
    policy_topic TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    review BOOLEAN NOT NULL DEFAULT FALSE,
    depends_on TEXT[] NOT NULL DEFAULT '{}',
    document JSONB,
    PRIMARY KEY (employee_id, id)
);
CREATE TABLE IF NOT EXISTS meetings (
    employee_id TEXT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    id TEXT NOT NULL,
    position INT NOT NULL,
    title TEXT NOT NULL,
    when_at TEXT NOT NULL,
    with_person TEXT NOT NULL,
    place TEXT NOT NULL,
    PRIMARY KEY (employee_id, id)
);
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    at DATE NOT NULL,
    requirement_id TEXT NOT NULL,
    audience TEXT NOT NULL,
    message TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    at DATE NOT NULL,
    text TEXT NOT NULL
);
"""


def _iso(value) -> str | None:
    if value is None or value == "":
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _save_json(data: dict) -> None:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(path)


def _load_json() -> dict:
    path = store_path()
    if not path.exists():
        data = seed()
        _save_json(data)
        return data
    return json.loads(path.read_text(encoding="utf-8"))


def _connect():
    import psycopg

    return psycopg.connect(_database_url())


def _json_doc(document):
    from psycopg.types.json import Json

    return Json(document) if document else None


def _ensure_schema(connection) -> None:
    connection.execute(_SCHEMA)


def _write_postgres(data: dict) -> None:
    with _connect() as connection:
        _ensure_schema(connection)
        connection.execute("DELETE FROM events")
        connection.execute("DELETE FROM reminders")
        connection.execute("DELETE FROM meetings")
        connection.execute("DELETE FROM requirements")
        connection.execute("DELETE FROM employees")
        connection.execute("DELETE FROM app_settings")
        connection.execute(
            "INSERT INTO app_settings (id, as_of) VALUES (1, %s)",
            (data["as_of"],),
        )
        for case in data["employees"].values():
            connection.execute(
                """
                INSERT INTO employees (
                    id, name, preferred_name, role_title, team, location,
                    start_date, manager, hr_partner, it_partner
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    case["id"],
                    case["name"],
                    case["preferred_name"],
                    case["role_title"],
                    case["team"],
                    case["location"],
                    case["start_date"],
                    case["manager"],
                    case["hr_partner"],
                    case["it_partner"],
                ),
            )
            for position, req in enumerate(case["requirements"]):
                connection.execute(
                    """
                    INSERT INTO requirements (
                        employee_id, id, position, title, short, owner, status,
                        due, policy_topic, note, review, depends_on, document
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        case["id"],
                        req["id"],
                        position,
                        req["title"],
                        req["short"],
                        req["owner"],
                        req["status"],
                        req.get("due") or None,
                        req.get("policy_topic") or "",
                        req.get("note") or "",
                        bool(req.get("review")),
                        req.get("depends_on") or [],
                        _json_doc(req.get("document")),
                    ),
                )
            for position, meeting in enumerate(case.get("meetings") or []):
                connection.execute(
                    """
                    INSERT INTO meetings (
                        employee_id, id, position, title, when_at, with_person, place
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        case["id"],
                        meeting["id"],
                        position,
                        meeting["title"],
                        meeting["when"],
                        meeting["with"],
                        meeting["where"],
                    ),
                )
            for reminder in case.get("reminders") or []:
                connection.execute(
                    """
                    INSERT INTO reminders (employee_id, at, requirement_id, audience, message)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        case["id"],
                        reminder["at"],
                        reminder["requirement_id"],
                        reminder["audience"],
                        reminder["message"],
                    ),
                )
            for event in case.get("events") or []:
                connection.execute(
                    "INSERT INTO events (employee_id, at, text) VALUES (%s, %s, %s)",
                    (case["id"], event["at"], event["text"]),
                )
        connection.commit()


def _read_postgres() -> dict | None:
    with _connect() as connection:
        _ensure_schema(connection)
        connection.commit()
        count = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if count == 0:
            return None
        as_of = connection.execute("SELECT as_of FROM app_settings WHERE id = 1").fetchone()
        employees = {}
        for row in connection.execute(
            """
            SELECT id, name, preferred_name, role_title, team, location,
                   start_date, manager, hr_partner, it_partner
            FROM employees ORDER BY name
            """
        ).fetchall():
            employees[row[0]] = {
                "id": row[0],
                "name": row[1],
                "preferred_name": row[2],
                "role_title": row[3],
                "team": row[4],
                "location": row[5],
                "start_date": _iso(row[6]),
                "manager": row[7],
                "hr_partner": row[8],
                "it_partner": row[9],
                "requirements": [],
                "meetings": [],
                "reminders": [],
                "events": [],
            }
        for row in connection.execute(
            """
            SELECT employee_id, id, title, short, owner, status, due, policy_topic,
                   note, review, depends_on, document
            FROM requirements ORDER BY employee_id, position
            """
        ).fetchall():
            employees[row[0]]["requirements"].append({
                "id": row[1],
                "title": row[2],
                "short": row[3],
                "owner": row[4],
                "status": row[5],
                "due": _iso(row[6]),
                "policy_topic": row[7] or "",
                "note": row[8] or "",
                "review": bool(row[9]),
                "depends_on": list(row[10] or []),
                "document": row[11],
            })
        for row in connection.execute(
            """
            SELECT employee_id, id, title, when_at, with_person, place
            FROM meetings ORDER BY employee_id, position
            """
        ).fetchall():
            employees[row[0]]["meetings"].append({
                "id": row[1],
                "title": row[2],
                "when": row[3],
                "with": row[4],
                "where": row[5],
            })
        for row in connection.execute(
            "SELECT employee_id, at, requirement_id, audience, message FROM reminders ORDER BY id"
        ).fetchall():
            employees[row[0]]["reminders"].append({
                "at": _iso(row[1]),
                "requirement_id": row[2],
                "audience": row[3],
                "message": row[4],
            })
        for row in connection.execute(
            "SELECT employee_id, at, text FROM events ORDER BY id"
        ).fetchall():
            employees[row[0]]["events"].append({"at": _iso(row[1]), "text": row[2]})
        return {"as_of": _iso(as_of[0]) if as_of else "2026-10-10", "employees": employees}


def load_store() -> dict:
    if not _database_url():
        return _load_json()
    data = _read_postgres()
    if data is None:
        data = seed()
        _write_postgres(data)
    return data


def save_store(data: dict) -> None:
    if not _database_url():
        _save_json(data)
        return
    _write_postgres(data)


def reset_store() -> dict:
    data = seed()
    save_store(data)
    return data


def _case(store: dict, employee_id: str) -> dict:
    key = (employee_id or "").strip().lower()
    aliases = {
        "maya chen": "maya",
        "rohan iyer": "rohan",
    }
    key = aliases.get(key, key)
    case = store["employees"].get(key)
    if case is None:
        known = ", ".join(store["employees"])
        raise KeyError(f"Unknown employee '{employee_id}'. Known ids: {known}")
    return case


def get_case(employee_id: str) -> dict:
    store = load_store()
    return copy.deepcopy(_case(store, employee_id))


def list_cases() -> list[dict]:
    store = load_store()
    rows = []
    for case in store["employees"].values():
        snap = readiness(case["id"], "hr", store)
        rows.append({
            "employee_id": case["id"],
            "name": case["name"],
            "role_title": case["role_title"],
            "team": case["team"],
            "start_date": case["start_date"],
            "phase": snap["phase"],
            "urgency": snap["urgency"],
            "headline": snap["headline"],
            "settled": snap["settled"],
            "total": snap["total"],
        })
    rank = {"now": 0, "soon": 1, "clear": 2}
    rows.sort(key=lambda row: (rank.get(row["urgency"], 9), row["name"]))
    return rows


def _by_id(requirements: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in requirements}


def _satisfied(req: dict) -> bool:
    return req["status"] in DONE


def _blockers(req: dict, lookup: dict[str, dict]) -> list[dict]:
    blocked = []
    for dep_id in req.get("depends_on") or []:
        dep = lookup.get(dep_id)
        if dep and not _satisfied(dep):
            blocked.append(dep)
    return blocked


def _ready(req: dict, lookup: dict[str, dict]) -> bool:
    if req["status"] in DONE or req["status"] in {"submitted", "in_progress"}:
        return False
    return not _blockers(req, lookup)


def _direct_unlocks(req_id: str, requirements: list[dict]) -> list[dict]:
    return [
        item for item in requirements
        if req_id in (item.get("depends_on") or []) and not _satisfied(item)
    ]


def _reminded_on(case: dict, requirement_id: str, day: str) -> bool:
    return any(
        item.get("requirement_id") == requirement_id and item.get("at") == day
        for item in case.get("reminders") or []
    )


def _phase(case: dict, as_of: str) -> str:
    start = _date(case["start_date"])
    today = _date(as_of)
    if today < start:
        return "pre_joining"
    if (today - start).days < 7:
        return "week_1"
    return "first_weeks"


def _days_label(case: dict, as_of: str) -> str:
    delta = (_date(case["start_date"]) - _date(as_of)).days
    if delta > 1:
        return f"{delta} days before Day 1"
    if delta == 1:
        return "Tomorrow is Day 1"
    if delta == 0:
        return "Today is Day 1"
    if delta == -1:
        return "Day 2"
    return f"Day {abs(delta) + 1}"


def _upcoming(case: dict, as_of: str) -> list[dict]:
    upcoming = []
    for meeting in case.get("meetings") or []:
        if meeting["when"][:10] >= as_of:
            upcoming.append(meeting)
    upcoming.sort(key=lambda item: item["when"])
    return upcoming


def _sort_ready(items: list[dict]) -> list[dict]:
    def key(item: dict):
        clarification = 0 if item["status"] == "needs_clarification" else 1
        return (clarification, item.get("due") or "9999-12-31", item["title"])
    return sorted(items, key=key)


def _action_for(req: dict, viewer_role: str, case: dict, as_of: str) -> dict | None:
    if viewer_role == "employee" and req["owner"] == "employee" and req["status"] == "needs_clarification":
        return {
            "type": "submit_update",
            "requirement_id": req["id"],
            "label": "I've uploaded a clearer photo",
            "title": req["title"],
            "note": "Employee uploaded a clearer full bio page.",
        }
    if viewer_role == "employee" and req["owner"] == "employee" and req["status"] == "not_started":
        if req.get("review"):
            return {
                "type": "submit_update",
                "requirement_id": req["id"],
                "label": f"Submit {req['short'].lower()}",
                "title": req["title"],
                "note": f"{case['preferred_name']} submitted {req['short'].lower()} for review.",
            }
        return {
            "type": "complete_task",
            "requirement_id": req["id"],
            "label": f"I've done this: {req['short']}",
            "title": req["title"],
            "note": f"{case['preferred_name']} marked {req['short'].lower()} complete.",
        }
    if viewer_role == "hr" and req["status"] == "submitted":
        return {
            "type": "complete_task",
            "requirement_id": req["id"],
            "label": f"Accept {req['short'].lower()}",
            "title": f"Accept {req['short'].lower()}",
            "note": "HR accepted the document.",
        }
    if viewer_role == "hr" and req["status"] == "needs_clarification":
        if _reminded_on(case, req["id"], as_of):
            return None
        return {
            "type": "send_reminder",
            "requirement_id": req["id"],
            "audience": req["owner"],
            "label": f"Remind {case['preferred_name']}",
            "title": f"Remind {case['preferred_name']} about {req['short'].lower()}",
            "message": (
                f"{case['preferred_name']}, {req['note'] or req['title']} "
                "This is the step other access is waiting on."
            ),
        }
    if viewer_role == "hr" and req["owner"] == "hr" and _ready(req, _by_id(case["requirements"])):
        return {
            "type": "complete_task",
            "requirement_id": req["id"],
            "label": f"Mark {req['short'].lower()} done",
            "title": req["title"],
            "note": "HR completed this step.",
        }
    if viewer_role == "hr" and req["owner"] != "hr" and not _reminded_on(case, req["id"], as_of):
        return {
            "type": "send_reminder",
            "requirement_id": req["id"],
            "audience": req["owner"],
            "label": f"Remind {OWNER_LABELS.get(req['owner'], req['owner'])}",
            "title": f"Nudge {OWNER_LABELS.get(req['owner'], req['owner']).lower()} about {req['short'].lower()}",
            "message": f"{req['title']} is coming due and is still open.",
        }
    return None


def _candidate_queue(case: dict, viewer_role: str, as_of: str) -> list[tuple[int, dict]]:
    lookup = _by_id(case["requirements"])
    today = _date(as_of)
    soon_limit = today + timedelta(days=3)
    queued: list[tuple[int, dict]] = []

    for req in case["requirements"]:
        if _satisfied(req):
            continue
        due = _date(req["due"]) if req.get("due") else None
        overdue = bool(due and due < today and req["status"] != "in_progress")
        due_soon = bool(due and today <= due <= soon_limit)

        if viewer_role == "employee":
            if req["owner"] != "employee":
                continue
            if req["status"] == "needs_clarification":
                queued.append((0, req))
            elif _ready(req, lookup):
                queued.append((1, req))
            continue

        if req["status"] == "submitted":
            queued.append((0, req))
        elif req["status"] == "needs_clarification":
            queued.append((1, req))
        elif overdue and not _reminded_on(case, req["id"], as_of):
            queued.append((2, req))
        elif req["owner"] == "hr" and _ready(req, lookup):
            queued.append((3, req))
        elif due_soon and req["owner"] != "hr" and req["status"] in {"not_started", "needs_clarification"}:
            if not _reminded_on(case, req["id"], as_of):
                queued.append((4, req))

    queued.sort(key=lambda pair: (
        pair[0],
        pair[1].get("due") or "9999-12-31",
        -len(_direct_unlocks(pair[1]["id"], case["requirements"])),
    ))
    return queued


def readiness(employee_id: str, viewer_role: str = "employee", store: dict | None = None) -> dict:
    store = store or load_store()
    case = _case(store, employee_id)
    as_of = store["as_of"]
    lookup = _by_id(case["requirements"])
    role = viewer_role if viewer_role in {"employee", "hr", "it", "manager"} else "employee"

    settled = [item for item in case["requirements"] if _satisfied(item)]
    in_motion = [
        item for item in case["requirements"]
        if item["status"] == "in_progress" and item["owner"] != role
    ]
    waiting_review = [item for item in case["requirements"] if item["status"] == "submitted"]
    later = []
    for item in case["requirements"]:
        if _satisfied(item) or item["status"] in {"in_progress", "submitted"}:
            continue
        blockers = _blockers(item, lookup)
        if blockers and not (role == "employee" and item["owner"] == "employee" and item["status"] == "needs_clarification"):
            later.append({
                "id": item["id"],
                "title": item["title"],
                "owner": item["owner"],
                "waiting_on": [blocker["short"] for blocker in blockers],
            })

    queue = _candidate_queue(case, role, as_of)
    focus = queue[0][1] if queue else None
    urgency = "clear"
    if queue:
        urgency = "now" if queue[0][0] <= 1 else "soon" if queue[0][0] <= 3 else "soon"
        if role == "hr" and queue[0][0] >= 4:
            urgency = "soon"
        if role == "employee" and focus and focus["status"] != "needs_clarification":
            due = _date(focus["due"]) if focus.get("due") else None
            if due and due > _date(as_of) + timedelta(days=3):
                urgency = "soon"

    action = _action_for(focus, role, case, as_of) if focus else None
    unlocks = _direct_unlocks(focus["id"], case["requirements"]) if focus else []
    reason = ""
    if focus:
        if focus["status"] == "needs_clarification":
            reason = focus["note"] or "This needs a clearer submission before anything that depends on it."
        elif focus["status"] == "submitted":
            reason = "It is in the file and waiting for a person to accept it."
        elif unlocks:
            names = ", ".join(item["short"].lower() for item in unlocks[:4])
            reason = f"This is the step that opens {names}."
        else:
            reason = focus["note"] or "This is the next open step that is actually yours."

    if role == "hr" and focus and focus["status"] == "needs_clarification":
        review_note = ((focus.get("document") or {}).get("review_note") or "").strip()
        reminded = _reminded_on(case, focus["id"], as_of)
        reason = f"{case['preferred_name']} already sent this, and it was sent back."
        if review_note:
            reason = f"{reason} {review_note}"
        if reminded:
            reason = f"A reminder is already logged for today. {reason}"

    reminded_focus = bool(focus and _reminded_on(case, focus["id"], as_of))
    headline = _headline(case, role, focus, urgency, reminded_focus)
    also = []
    if role == "employee":
        ready_rest = _sort_ready([
            item for item in case["requirements"]
            if item["owner"] == "employee" and _ready(item, lookup) and (not focus or item["id"] != focus["id"])
        ])
        also = [_public_req(item, lookup, case) for item in ready_rest[:3]]

    snapshot = {
        "employee_id": case["id"],
        "name": case["name"],
        "preferred_name": case["preferred_name"],
        "role_title": case["role_title"],
        "team": case["team"],
        "location": case["location"],
        "start_date": case["start_date"],
        "manager": case["manager"],
        "hr_partner": case["hr_partner"],
        "it_partner": case["it_partner"],
        "as_of": as_of,
        "phase": _phase(case, as_of),
        "when_label": _days_label(case, as_of),
        "viewer_role": role,
        "settled": len(settled),
        "total": len(case["requirements"]),
        "urgency": urgency,
        "headline": headline,
        "next": _public_req(focus, lookup, case) if focus else None,
        "next_reason": reason,
        "unlocks": [item["short"] for item in unlocks],
        "action": action,
        "also_ready": also,
        "in_motion": [_public_req(item, lookup, case) for item in in_motion],
        "waiting_review": [_public_req(item, lookup, case) for item in waiting_review],
        "later": later,
        "upcoming": _upcoming(case, as_of)[:3],
        "reminders": list(case.get("reminders") or []),
        "events": list(case.get("events") or [])[-5:],
    }
    return snapshot


def _public_req(req: dict | None, lookup: dict[str, dict], case: dict) -> dict | None:
    if req is None:
        return None
    blockers = _blockers(req, lookup)
    return {
        "id": req["id"],
        "title": req["title"],
        "short": req["short"],
        "owner": req["owner"],
        "owner_label": OWNER_LABELS.get(req["owner"], req["owner"]),
        "status": req["status"],
        "due": req.get("due"),
        "note": req.get("note") or "",
        "policy_topic": req.get("policy_topic") or "",
        "document": req.get("document"),
        "blocked_by": [item["short"] for item in blockers],
        "unlocks": [item["short"] for item in _direct_unlocks(req["id"], case["requirements"])],
    }


def _headline(case: dict, role: str, focus: dict | None, urgency: str, reminded: bool) -> str:
    name = case["preferred_name"]
    if role == "employee":
        if focus is None:
            return "Nothing is waiting on you. The next thing is already on the calendar."
        if focus["status"] == "needs_clarification":
            return "One document needs a clearer photo. Everything else can wait."
        if urgency == "clear":
            return "You're in. The rest of this week is light."
        return focus["title"]
    if focus is None:
        return f"{name} is not stuck on anyone."
    if focus["status"] == "submitted":
        return f"{name} is waiting on a review."
    if focus["status"] == "needs_clarification" and reminded:
        return f"You already reminded {name} today. The document is still open."
    if focus["status"] == "needs_clarification":
        return f"{name} is paused on one document."
    if focus["owner"] == "hr":
        return f"You can move {focus['short'].lower()} for {name}."
    if urgency == "soon":
        return f"Nothing is blocked for {name}. One reminder is optional."
    return f"{name} needs a nudge on {focus['short'].lower()}."


def portfolio(viewer_role: str = "hr") -> dict:
    store = load_store()
    people = []
    for case in store["employees"].values():
        snap = readiness(case["id"], viewer_role, store)
        people.append({
            "employee_id": snap["employee_id"],
            "name": snap["name"],
            "role_title": snap["role_title"],
            "team": snap["team"],
            "when_label": snap["when_label"],
            "urgency": snap["urgency"],
            "headline": snap["headline"],
            "next": snap["next"],
            "action": snap["action"],
            "settled": snap["settled"],
            "total": snap["total"],
        })
    rank = {"now": 0, "soon": 1, "clear": 2}
    people.sort(key=lambda row: (rank[row["urgency"]], row["name"]))
    return {
        "mode": "portfolio",
        "as_of": store["as_of"],
        "viewer_role": viewer_role,
        "people": people,
    }


def search_policy(query: str, limit: int = 2) -> list[dict]:
    terms = {token for token in _tokens(query) if len(token) > 2}
    hits = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        topic = ""
        title = path.stem
        body_start = 0
        for index, line in enumerate(lines):
            if line.lower().startswith("topic:"):
                topic = line.split(":", 1)[1].strip()
            elif line.lower().startswith("title:"):
                title = line.split(":", 1)[1].strip()
            elif line.strip() == "":
                body_start = index + 1
                break
        body = "\n".join(lines[body_start:]).strip()
        haystack = _tokens(f"{title} {topic} {body}")
        score = len(terms & set(haystack))
        if topic and topic in query.lower():
            score += 5
        if score <= 0:
            continue
        excerpt = body.split("\n\n")[0][:320]
        hits.append({
            "title": title,
            "topic": topic,
            "excerpt": excerpt,
            "body": body[:1200],
            "score": score,
        })
    hits.sort(key=lambda item: (-item["score"], item["title"]))
    return hits[:limit]


def _tokens(text: str) -> list[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [part for part in cleaned.split() if part]


def _mutate(employee_id: str, mutator):
    store = load_store()
    case = _case(store, employee_id)
    result = mutator(store, case)
    save_store(store)
    return result


def _find_req(case: dict, requirement_id: str) -> dict:
    for req in case["requirements"]:
        if req["id"] == requirement_id:
            return req
    raise KeyError(f"Unknown requirement '{requirement_id}' for {case['name']}")


def submit_update(employee_id: str, requirement_id: str, note: str, actor_role: str = "employee") -> dict:
    def mutate(store, case):
        if actor_role not in {"employee", "hr"}:
            return {"ok": False, "error": "Only the employee or HR can submit a document."}
        req = _find_req(case, requirement_id)
        if req["status"] in DONE:
            return {"ok": False, "error": f"{req['short']} is already settled."}
        if actor_role == "employee" and req["owner"] != "employee":
            return {"ok": False, "error": f"{req['short']} belongs to {OWNER_LABELS[req['owner']]}, not the employee."}
        req["status"] = "submitted"
        req["document"] = {
            "filename": (req.get("document") or {}).get("filename") or f"{requirement_id}.pdf",
            "received_on": store["as_of"],
            "review_note": "",
        }
        req["note"] = note or "Submitted and waiting for review."
        case["events"].append({"at": store["as_of"], "text": f"{req['short']} submitted for review."})
        return {"ok": True, "requirement_id": requirement_id, "status": "submitted"}

    try:
        return _mutate(employee_id, mutate)
    except KeyError as exc:
        return {"ok": False, "error": str(exc)}


def complete_requirement(employee_id: str, requirement_id: str, actor_role: str, note: str = "") -> dict:
    def mutate(store, case):
        req = _find_req(case, requirement_id)
        lookup = _by_id(case["requirements"])
        if req["status"] in DONE:
            return {"ok": False, "error": f"{req['short']} is already settled."}
        if req.get("review") and actor_role != "hr" and req["status"] != "in_progress":
            return {
                "ok": False,
                "error": f"HR still needs to accept {req['short']}. Submit it instead of marking it done.",
            }
        blockers = _blockers(req, lookup)
        if blockers and req["status"] != "submitted":
            names = ", ".join(item["short"] for item in blockers)
            return {"ok": False, "error": f"Still waiting on {names}."}
        allowed = actor_role == "hr" or actor_role == req["owner"]
        if req["status"] == "submitted" and actor_role != "hr":
            allowed = False
        if not allowed:
            return {"ok": False, "error": f"{OWNER_LABELS.get(actor_role, actor_role)} cannot close {req['short']}."}
        req["status"] = "done"
        if note:
            req["note"] = note
        case["events"].append({"at": store["as_of"], "text": f"{req['short']} marked done by {OWNER_LABELS.get(actor_role, actor_role)}."})
        return {"ok": True, "requirement_id": requirement_id, "status": "done"}

    try:
        return _mutate(employee_id, mutate)
    except KeyError as exc:
        return {"ok": False, "error": str(exc)}


def log_reminder(employee_id: str, requirement_id: str, message: str, audience: str) -> dict:
    def mutate(store, case):
        req = _find_req(case, requirement_id)
        if req["status"] in DONE:
            return {"ok": False, "error": f"{req['short']} is already settled, so no reminder is needed."}
        entry = {
            "at": store["as_of"],
            "requirement_id": requirement_id,
            "audience": audience or req["owner"],
            "message": message,
        }
        case.setdefault("reminders", []).append(entry)
        case["events"].append({
            "at": store["as_of"],
            "text": f"Reminder logged for {OWNER_LABELS.get(entry['audience'], entry['audience'])}: {req['short']}.",
        })
        return {"ok": True, "reminder": entry}

    try:
        return _mutate(employee_id, mutate)
    except KeyError as exc:
        return {"ok": False, "error": str(exc)}


def known_requirement_ids(employee_id: str) -> list[dict]:
    if employee_id in {"", "all", "portfolio"}:
        seen = {}
        for case in seed()["employees"].values():
            for req in case["requirements"]:
                seen[req["id"]] = req["short"]
        return [{"id": key, "short": value} for key, value in seen.items()]
    case = get_case(employee_id)
    return [{"id": req["id"], "short": req["short"]} for req in case["requirements"]]


def narrative(snapshot: dict, policy_hits: list[dict] | None = None) -> str:
    if snapshot.get("mode") == "portfolio":
        lines = ["Who needs you today:"]
        for person in snapshot["people"]:
            nxt = person["next"]["short"] if person.get("next") else "nothing open"
            lines.append(f"- {person['name']} ({person['when_label']}): {person['headline']} Focus: {nxt}.")
        return "\n".join(lines)

    name = snapshot["preferred_name"]
    lines = [snapshot["headline"]]
    nxt = snapshot.get("next")
    if nxt:
        lines.append(f"The step that matters: {nxt['title']}. {snapshot.get('next_reason', '')}".strip())
        if snapshot.get("unlocks"):
            lines.append("It is holding up " + ", ".join(snapshot["unlocks"]) + ".")
    if snapshot.get("also_ready"):
        extras = "; ".join(item["title"] for item in snapshot["also_ready"])
        lines.append(f"When you have a spare moment: {extras}.")
    if snapshot.get("in_motion"):
        moving = "; ".join(f"{item['short']} ({item['owner_label']})" for item in snapshot["in_motion"])
        lines.append(f"Already moving without you: {moving}.")
    if snapshot.get("upcoming"):
        meet = snapshot["upcoming"][0]
        lines.append(f"Next on the calendar: {meet['title']} on {meet['when']} with {meet['with']}.")
    if policy_hits:
        lines.append(policy_hits[0]["excerpt"])
    if snapshot["viewer_role"] == "employee" and snapshot["phase"] == "pre_joining":
        lines.append(f"{name}, you do not need to chase IT or your manager. They already have their pieces.")
    return "\n\n".join(line for line in lines if line)
