import uuid

import streamlit as st

from case_engine import portfolio, readiness, reset_store
from runtime import ask, resume, waiting_for_approval

st.set_page_config(page_title="Employee Onboarding Companion", page_icon="✦", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,520;9..144,640&family=Outfit:wght@380;500;640&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
.stApp { background: #f3efe6; color: #1d1a16; }
h1, h2, h3, .serif { font-family: 'Fraunces', serif; letter-spacing: -0.03em; }
section[data-testid="stSidebar"] { background: #ebe4d6; border-right: 1px solid #ddd4c4; }
.kicker { color: #6d6458; font-size: 0.82rem; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.3rem; }
.hero-card { background: #fffdf8; border: 1px solid #e4dac8; border-radius: 18px; padding: 1.4rem 1.5rem 1.1rem; }
.quiet { color: #5e564c; }
.pill { display: inline-block; border-radius: 999px; padding: 0.2rem 0.7rem; font-size: 0.78rem; background: #efe7d8; color: #3d3428; margin-right: 0.4rem; }
.pill.now { background: #f3d7c4; color: #6d3518; }
.pill.clear { background: #dce8df; color: #1d4a38; }
.section-label { margin: 1.3rem 0 0.4rem; color: #6d6458; font-size: 0.78rem; letter-spacing: 0.12em; text-transform: uppercase; }
.reply { background: #1d1a16; color: #f6f1e7; border-radius: 18px; padding: 1.2rem 1.3rem; line-height: 1.55; }
.reply p, .reply li { color: #f6f1e7 !important; }
div[data-testid="stButton"] > button[kind="primary"], div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"] {
  background: #1d4a38; color: #f6f1e7; border: none; border-radius: 999px;
}
.block-container { padding-top: 1.4rem; max-width: 1080px; }
</style>
""",
    unsafe_allow_html=True,
)


def _init():
    st.session_state.setdefault("thread_id", uuid.uuid4().hex[:10])
    st.session_state.setdefault("role", "employee")
    st.session_state.setdefault("employee_id", "maya")
    st.session_state.setdefault("latest", None)
    st.session_state.setdefault("waiting", False)


def _new_thread():
    st.session_state.thread_id = uuid.uuid4().hex[:10]
    st.session_state.latest = None
    st.session_state.waiting = False


def _run(query: str, forced_intent: str = "", forced_requirement_id: str = ""):
    with st.spinner("Checking the case file…"):
        result, _config = ask(
            query,
            viewer_role=st.session_state.role,
            employee_id=st.session_state.employee_id,
            user_id=st.session_state.role,
            thread_id=st.session_state.thread_id,
            forced_intent=forced_intent,
            forced_requirement_id=forced_requirement_id,
        )
    st.session_state.latest = result
    st.session_state.waiting = waiting_for_approval(result)


_init()

with st.sidebar:
    st.markdown("<div class='serif' style='font-size:1.35rem'>Onboarding</div>", unsafe_allow_html=True)
    st.caption("One case file. One next step.")
    role = st.radio("I am", ["Joining", "Onboarding owner"], index=0 if st.session_state.role == "employee" else 1)
    new_role = "employee" if role == "Joining" else "hr"
    if new_role != st.session_state.role:
        st.session_state.role = new_role
        if new_role == "hr":
            st.session_state.employee_id = "all"
        elif st.session_state.employee_id == "all":
            st.session_state.employee_id = "maya"
        _new_thread()
        st.rerun()

    if st.session_state.role == "employee":
        person = st.selectbox(
            "Viewing as",
            ["maya", "rohan"],
            format_func=lambda value: "Maya Chen · before Day 1" if value == "maya" else "Rohan Iyer · first week",
            index=0 if st.session_state.employee_id != "rohan" else 1,
        )
        if person != st.session_state.employee_id:
            st.session_state.employee_id = person
            _new_thread()
            st.rerun()
    else:
        person = st.selectbox(
            "Case",
            ["all", "maya", "rohan"],
            format_func=lambda value: {"all": "Everyone", "maya": "Maya Chen", "rohan": "Rohan Iyer"}[value],
            index=["all", "maya", "rohan"].index(st.session_state.employee_id if st.session_state.employee_id in {"all", "maya", "rohan"} else "all"),
        )
        if person != st.session_state.employee_id:
            st.session_state.employee_id = person
            _new_thread()
            st.rerun()

    st.caption(f"Thread {st.session_state.thread_id}")
    if st.button("New conversation"):
        _new_thread()
        st.rerun()
    if st.button("Reset demo stories"):
        reset_store()
        _new_thread()
        st.rerun()
    st.markdown("<div class='section-label'>How it runs</div>", unsafe_allow_html=True)
    st.caption("Supervisor and guardrail, then the case, policy, and reminder agents. A write waits for a person before it touches the file.")


def _pill(urgency: str) -> str:
    label = {"now": "Needs you", "soon": "This week", "clear": "Clear"}.get(urgency, urgency)
    return f"<span class='pill {urgency}'>{label}</span>"


def _show_person(snap: dict):
    st.markdown(
        f"<div class='kicker'>{snap['when_label']} · {snap['location']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<h1 style='margin:0 0 0.2rem'>{snap['name']}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<p class='quiet' style='margin-top:0'>{snap['role_title']}, {snap['team']} · starts {snap['start_date']} · "
        f"manager {snap['manager']}</p>",
        unsafe_allow_html=True,
    )
    st.markdown(_pill(snap["urgency"]) + f"<span class='quiet'>{snap['settled']} of {snap['total']} settled</span>", unsafe_allow_html=True)

    nxt = snap.get("next")
    st.markdown("<div class='section-label'>Do this next</div>", unsafe_allow_html=True)
    if not nxt:
        st.markdown("<div class='hero-card'><h3>Nothing is waiting on you.</h3><p class='quiet'>The calendar already has the rest.</p></div>", unsafe_allow_html=True)
    else:
        unlock = ""
        if snap.get("unlocks"):
            unlock = "<p class='quiet'>Holding up " + ", ".join(snap["unlocks"]) + ".</p>"
        st.markdown(
            f"<div class='hero-card'><h3 style='margin-top:0'>{nxt['title']}</h3>"
            f"<p>{snap.get('next_reason') or ''}</p>{unlock}</div>",
            unsafe_allow_html=True,
        )
        action = snap.get("action")
        if action and not st.session_state.waiting:
            if st.button(action["label"], type="primary"):
                _run(
                    action.get("title") or action["label"],
                    forced_intent=action["type"],
                    forced_requirement_id=action["requirement_id"],
                )
                st.rerun()

    if snap.get("also_ready"):
        st.markdown("<div class='section-label'>When you have a moment</div>", unsafe_allow_html=True)
        for item in snap["also_ready"]:
            due = f" · by {item['due']}" if item.get("due") else ""
            st.markdown(f"- {item['title']}{due}")

    if snap.get("in_motion"):
        st.markdown("<div class='section-label'>Already in motion</div>", unsafe_allow_html=True)
        for item in snap["in_motion"]:
            note = f" — {item['note']}" if item.get("note") else ""
            st.markdown(f"- {item['short']} · {item['owner_label']}{note}")

    if snap.get("upcoming"):
        st.markdown("<div class='section-label'>Coming up</div>", unsafe_allow_html=True)
        for meeting in snap["upcoming"]:
            st.markdown(f"- {meeting['when']} · {meeting['title']} · {meeting['with']}")


def _show_portfolio(board: dict):
    st.markdown("<div class='kicker'>Onboarding owner · 10 Oct 2026</div>", unsafe_allow_html=True)
    st.markdown("<h1 style='margin-bottom:0.2rem'>Who needs you</h1>", unsafe_allow_html=True)
    st.markdown("<p class='quiet'>Two people, one list. Open a case only when the headline is not enough.</p>", unsafe_allow_html=True)
    for person in board["people"]:
        cols = st.columns([5, 1])
        with cols[0]:
            st.markdown(_pill(person["urgency"]) + f"**{person['name']}** · {person['when_label']}", unsafe_allow_html=True)
            st.markdown(person["headline"])
            if person.get("next"):
                st.caption(person["next"]["title"])
        with cols[1]:
            if st.button("Open", key=f"open_{person['employee_id']}"):
                st.session_state.employee_id = person["employee_id"]
                _new_thread()
                st.rerun()


if st.session_state.employee_id == "all":
    _show_portfolio(portfolio("hr"))
else:
    _show_person(readiness(st.session_state.employee_id, st.session_state.role))

st.markdown("<div class='section-label'>Ask</div>", unsafe_allow_html=True)
prompts = (
    ["What should I do before Monday?", "What is the laptop waiting on?", "When is induction?"]
    if st.session_state.role == "employee"
    else ["Who needs attention?", "Why is Maya blocked?", "What should IT be reminded about?"]
)
prompt_cols = st.columns(len(prompts))
for column, prompt in zip(prompt_cols, prompts):
    with column:
        if st.button(prompt, key=f"prompt_{prompt}", disabled=st.session_state.waiting):
            if st.session_state.role == "hr" and prompt.startswith("Who"):
                st.session_state.employee_id = "all"
            _run(prompt)
            st.rerun()

question = st.text_input("Ask the companion", placeholder="Ask about your joining, or about a person you own.", label_visibility="collapsed")
if st.button("Ask", disabled=st.session_state.waiting):
    if question.strip():
        _run(question.strip())
        st.rerun()
    else:
        st.warning("Ask something about joining first.")

latest = st.session_state.get("latest")
if latest and waiting_for_approval(latest):
    payload = latest["__interrupt__"][0].value
    st.markdown("<div class='section-label'>Confirm before anything is written</div>", unsafe_allow_html=True)
    st.markdown(f"**{payload.get('title', 'Update')}**")
    st.write(payload.get("detail") or "")
    note = st.text_input("Note to store", value="")
    yes, no = st.columns(2)
    with yes:
        if st.button("Write it", type="primary"):
            with st.spinner("Updating the case…"):
                final = resume(
                    {"approved": True, "feedback": note},
                    {"configurable": {"thread_id": st.session_state.thread_id}},
                )
            st.session_state.latest = final
            st.session_state.waiting = False
            st.rerun()
    with no:
        if st.button("Leave it"):
            with st.spinner("Leaving the case as it is…"):
                final = resume(
                    {"approved": False, "feedback": note},
                    {"configurable": {"thread_id": st.session_state.thread_id}},
                )
            st.session_state.latest = final
            st.session_state.waiting = False
            st.rerun()

if latest and latest.get("final_response"):
    st.markdown("<div class='section-label'>Companion</div>", unsafe_allow_html=True)
    st.markdown(latest["final_response"])
    with st.expander("How this was decided"):
        st.write(latest.get("supervisor_reasoning") or "")
        for line in latest.get("trace") or []:
            st.write("· " + line)
        st.caption(f"Model calls: {latest.get('llm_calls', 0)}")
