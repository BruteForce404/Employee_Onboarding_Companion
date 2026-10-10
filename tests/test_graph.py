import os
import sys
import tempfile
import unittest
from pathlib import Path

STORE = Path(tempfile.mkdtemp()) / "case_store.json"
os.environ["ONBOARDING_STORE_PATH"] = str(STORE)
os.environ["ONBOARDING_DATABASE_URL"] = ""

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from case_engine import readiness, reset_store  # noqa: E402
from runtime import ask, resume, waiting_for_approval  # noqa: E402


class GraphTests(unittest.TestCase):
    def setUp(self):
        reset_store()

    def test_button_action_waits_for_a_person_then_writes(self):
        result, config = ask(
            "Record a clearer passport photo",
            viewer_role="employee",
            employee_id="maya",
            thread_id="maya-submit",
            forced_intent="submit_update",
            forced_requirement_id="identity_proof",
        )
        self.assertTrue(waiting_for_approval(result))
        self.assertEqual(readiness("maya", "employee")["next"]["id"], "identity_proof")

        declined = resume({"approved": False, "feedback": "Not yet"}, config)
        self.assertIn("Nothing was written", declined["final_response"])
        self.assertEqual(readiness("maya", "employee")["next"]["status"], "needs_clarification")

        again, config = ask(
            "Record a clearer passport photo",
            viewer_role="employee",
            employee_id="maya",
            thread_id="maya-submit-2",
            forced_intent="submit_update",
            forced_requirement_id="identity_proof",
        )
        self.assertTrue(waiting_for_approval(again))
        accepted = resume({"approved": True, "feedback": "Full bio page attached."}, config)
        self.assertIn("recorded", accepted["final_response"].lower())
        snap = readiness("maya", "employee")
        self.assertEqual(snap["next"]["id"], "code_of_conduct")
        self.assertTrue(any("Case agent" in line for line in accepted.get("trace") or []))

    def test_off_topic_never_opens_the_case_tools(self):
        result, _config = ask(
            "Plan a 7 day Japan trip with flights",
            viewer_role="employee",
            employee_id="maya",
            thread_id="off-topic",
        )
        self.assertFalse(waiting_for_approval(result))
        self.assertFalse(result.get("guardrail_passed", True))
        self.assertIn("joining", result.get("final_response", "").lower())


if __name__ == "__main__":
    unittest.main()
