"""Terminal companion. The Streamlit app is the main experience."""

import argparse

from case_engine import readiness
from runtime import ask, resume, waiting_for_approval


def main():
    parser = argparse.ArgumentParser(description="Employee Onboarding Companion")
    parser.add_argument("query", help="Question or instruction")
    parser.add_argument("--role", choices=["employee", "hr"], default="employee")
    parser.add_argument("--employee", default="maya")
    args = parser.parse_args()

    result, config = ask(args.query, viewer_role=args.role, employee_id=args.employee)
    if waiting_for_approval(result):
        interrupt_value = result["__interrupt__"][0].value
        print("\nApproval needed")
        print(interrupt_value.get("title", ""))
        print(interrupt_value.get("detail", ""))
        answer = input("Write this to the case? [y/N] ").strip().lower()
        result = resume({"approved": answer in {"y", "yes"}, "feedback": ""}, config)

    print("\n" + (result.get("final_response") or "No response."))
    snap = readiness(args.employee, args.role)
    nxt = (snap.get("next") or {}).get("title")
    if nxt:
        print(f"\nNext in the case file: {nxt}")


if __name__ == "__main__":
    main()
