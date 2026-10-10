# Employee Onboarding Companion

An onboarding companion for the person joining and for the internal owner. A LangGraph supervisor routes specialist agents, an MCP server stands in for HR and access systems, and a human approval step runs before anything is written.

The case file is the source of truth. The model may phrase a reply. It does not invent tasks, owners, or dates.

## What the system knows

Two seeded stories, both dated 10 Oct 2026:

- **Maya Chen** is ten days from Day 1. Her passport scan was cropped, so payroll, tax, login, and the badge are still closed. IT has already ordered the laptop. Her manager already has Monday's welcome.
- **Rohan Iyer** is in week one. Documents, laptop, and introductions are done. The only open task that is his is a 20-minute security module, before a buddy coffee on Wednesday.

For either person the companion keeps:

- documents received, and which ones need a clearer copy
- requirements that are satisfied, in review, or blocked
- dependencies and the owner (employee, HR, IT, manager)
- meetings
- whether a reminder was already logged today
- the policy passage that matters for the current step

The screen shows one next action, not a wall of tickets. Other ready items sit under "when you have a moment." Work owned by someone else is marked as already in motion.

## Agents

```text
supervisor (guardrail + route)
    -> case agent          MCP: HR case file
    -> policy agent        MCP: onboarding handbook
    -> reminder agent      who should be nudged, and whether that already happened
    -> companion           one next step, phrased from the case brief
    -> human approval      only when the step would write to the case
    -> apply action        MCP: submit, complete, or log a reminder
    -> final response
```

Off-topic requests stop at the guardrail. A write (new document, completed task, reminder) pauses until a person confirms it. Declining leaves the file unchanged.

HR, document storage, IT access, and the handbook are mocked. They are tools on `servers/onboarding_mcp_server.py`, backed by `case_engine.py`.

## Run

```bash
cd Employee_Onboarding_Companion
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run frontend.py
```

Use the sidebar to switch between Maya, Rohan, and the onboarding owner. The primary button proposes one case update and asks you to confirm. The ask box is for questions.

Free-text replies use Groq (`openai/gpt-oss-120b`) when `GROQ_API_KEY` is set in `.env`. Without a key, routing falls back to the question itself and the reply is the case brief, unchanged.

```bash
python main.py --role employee --employee maya "What should I do before Monday?"
python -m unittest tests.test_case_engine tests.test_graph
```

Cases and conversation checkpoints are stored in Postgres on port 5432:

`postgresql://gulshan37.kumar@localhost:5432/onboarding_companion`

```bash
psql -h localhost -p 5432 -U gulshan37.kumar -d onboarding_companion
```

```sql
SELECT name, role_title, start_date FROM employees;
SELECT e.name, r.short, r.owner, r.status, r.due
FROM requirements r
JOIN employees e ON e.id = r.employee_id
ORDER BY e.name, r.position;
```

If Postgres is down, conversation memory falls back to the current process, and the case file stays in `data/case_store.json`.
