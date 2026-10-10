import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["ONBOARDING_STORE_PATH"] = str(Path(tempfile.mkdtemp()) / "case_store.json")

import sys
sys.path.insert(0, str(ROOT))

from case_engine import (  # noqa: E402
    complete_requirement,
    log_reminder,
    portfolio,
    readiness,
    reset_store,
    search_policy,
    submit_update,
)


class CaseEngineTests(unittest.TestCase):
    def setUp(self):
        reset_store()

    def test_maya_employee_is_blocked_on_the_passport(self):
        snap = readiness("maya", "employee")
        self.assertEqual(snap["next"]["id"], "identity_proof")
        self.assertEqual(snap["urgency"], "now")
        self.assertIn("Bank details", snap["unlocks"])
        self.assertIn("Login", snap["unlocks"])
        self.assertEqual(snap["action"]["type"], "submit_update")
        later_ids = {item["id"] for item in snap["later"]}
        self.assertIn("bank_details", later_ids)
        self.assertTrue(any(item["id"] == "code_of_conduct" for item in snap["also_ready"]))

    def test_submitting_the_photo_moves_the_next_step(self):
        result = submit_update("maya", "identity_proof", "Clearer bio page uploaded.")
        self.assertTrue(result["ok"])
        employee = readiness("maya", "employee")
        self.assertEqual(employee["next"]["id"], "code_of_conduct")
        self.assertTrue(any(item["id"] == "identity_proof" for item in employee["waiting_review"]))
        hr = readiness("maya", "hr")
        self.assertEqual(hr["next"]["id"], "identity_proof")
        self.assertEqual(hr["action"]["type"], "complete_task")

    def test_hr_can_accept_identity_and_unlock_their_own_badge_work(self):
        submit_update("maya", "identity_proof", "Clearer bio page uploaded.")
        accepted = complete_requirement("maya", "identity_proof", "hr", "Photo accepted.")
        self.assertTrue(accepted["ok"])
        hr = readiness("maya", "hr")
        self.assertEqual(hr["next"]["id"], "badge_issued")
        employee = readiness("maya", "employee")
        self.assertNotEqual(employee["next"]["id"], "identity_proof")
        self.assertNotIn("bank_details", {item["id"] for item in employee["later"]})

    def test_employee_cannot_close_a_document_hr_must_review(self):
        refused = complete_requirement("maya", "identity_proof", "employee", "I say it's fine.")
        self.assertFalse(refused["ok"])

    def test_employee_cannot_finish_it_work(self):
        refused = complete_requirement("maya", "laptop_provision", "employee", "I have it.")
        self.assertFalse(refused["ok"])

    def test_reminder_is_logged_once_for_the_day(self):
        before = readiness("maya", "hr")
        self.assertEqual(before["action"]["type"], "send_reminder")
        logged = log_reminder("maya", "identity_proof", "Please resend the photo.", "employee")
        self.assertTrue(logged["ok"])
        after = readiness("maya", "hr")
        self.assertEqual(after["next"]["id"], "identity_proof")
        self.assertIsNone(after["action"])
        self.assertIn("already reminded", after["headline"].lower())

    def test_rohan_only_has_security_training_left(self):
        snap = readiness("rohan", "employee")
        self.assertEqual(snap["phase"], "week_1")
        self.assertEqual(snap["next"]["id"], "security_training")
        done = complete_requirement("rohan", "security_training", "employee", "Module finished.")
        self.assertTrue(done["ok"])
        clear = readiness("rohan", "employee")
        self.assertIsNone(clear["next"])
        self.assertEqual(clear["urgency"], "clear")

    def test_portfolio_puts_maya_ahead_of_rohan(self):
        board = portfolio("hr")
        self.assertEqual(board["people"][0]["employee_id"], "maya")
        self.assertEqual(board["people"][0]["urgency"], "now")

    def test_policy_search_finds_the_passport_rule(self):
        hits = search_policy("passport photo cropped")
        self.assertTrue(hits)
        self.assertEqual(hits[0]["topic"], "identity")
        self.assertIn("four corners", hits[0]["excerpt"].lower())


if __name__ == "__main__":
    unittest.main()
