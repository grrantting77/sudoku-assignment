"""UI state regressions. Fault injection tests error handling, not inference.

Run with the runtime requirements installed:
    python -m unittest discover -s tests -v
"""

from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "sudoku_app.py"


class AppStateRegressionTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(APP, default_timeout=30).run()
        self.assertFalse(self.app.exception)

    def markup(self):
        return "\n".join(item.proto.body for item in self.app.get("html"))

    def solve(self, result=None, error=None):
        with patch("sudoku_solver.solve_full_grid_fc", return_value=result,
                   side_effect=error):
            self.app.button(key="solve_button").click().run()
        self.assertFalse(self.app.exception)

    def test_failed_retry_removes_previous_grid_and_timing(self):
        # R1C1 is empty in puzzle 1. An earlier inferred value must disappear.
        self.solve(result={(1, 1): 1})
        self.assertIn('class="derived" data-cell="1_1"', self.markup())
        self.solve(error=RuntimeError("injected failure"))
        self.assertIn("injected failure", self.app.error[0].value)
        self.assertNotIn("Cells established", self.markup())
        self.assertNotIn('class="derived" data-cell="1_1"', self.markup())
        self.assertNotIn("solve_record", self.app.session_state)
        # A normal retry must clear the error, including its visible message.
        self.solve(result={(1, 1): 1})
        self.assertEqual(len(self.app.error), 0)
        self.assertNotIn("solve_error", self.app.session_state)

    def test_settings_change_clears_error(self):
        self.solve(error=RuntimeError("injected failure"))
        self.app.selectbox(key="algorithm").set_value("Backward Chaining").run()
        self.assertEqual(len(self.app.error), 0)
        self.app.session_state["solve_error"] = "old puzzle error"
        self.app.selectbox(key="puzzle_index").set_value(1).run()
        self.assertNotIn("solve_error", self.app.session_state)

    def test_partial_grid_and_accessible_cell_roles(self):
        self.solve(result={(1, 1): 1})
        self.assertIn("a partial solution", self.markup())
        self.assertNotIn("The grid is fully solved", self.markup())
        self.assertIn("Row 1, column 1: 1; derived", self.markup())
        self.assertIn("query target", self.markup())
        self.assertIn('class="cell-role" aria-hidden="true">Q', self.markup())

    def test_query_error_does_not_leave_a_verdict_or_tutor_trace(self):
        # A real given requires a one-fact proof and is inexpensive to check.
        self.app.number_input(key="query_col").set_value(2)
        self.app.number_input(key="query_value").set_value(3)
        self.app.run()
        self.app.button(key="query_button").click().run()
        self.assertTrue(self.app.session_state["query_record"]["result"])
        with patch("sudoku_solver.pl_bc_entails", side_effect=RuntimeError("query failure")):
            self.app.button(key="query_button").click().run()
        self.assertFalse(self.app.exception)
        self.assertIn("query failure", self.app.error[0].value)
        self.assertNotIn("query_record", self.app.session_state)
        self.assertNotIn('class="verdict', self.markup())
        self.assertIn("Start in Cell Query", self.markup())

    def test_elimination_target_keeps_its_marker_and_real_proof(self):
        from sudoku_solver import build_definite_kb
        from logic_ import parse_definite_clause
        import json

        self.app.button(key="query_button").click().run()
        record = self.app.session_state["query_record"]
        self.assertTrue(record["result"])
        pool = json.loads(APP.with_name("puzzles.json").read_text())
        givens = {tuple(map(int, k.split("_"))): v
                  for k, v in pool["puzzles"][0]["givens"].items()}
        kb = build_definite_kb(pool["n"], pool["box_h"], pool["box_w"], givens)
        facts = {c for c in kb.clauses if c.op != "==>"}
        rules = {(frozenset(ps), q) for c in kb.clauses if c.op == "==>"
                 for ps, q in [parse_definite_clause(c)]}
        proven = set()
        for step in record["trace"]:
            goal = step["conclusion"]
            if step["type"] == "fact":
                self.assertIn(goal, facts)
            else:
                premises = frozenset(step["premises"])
                self.assertTrue(premises <= proven)
                self.assertIn((premises, goal), rules)
            proven.add(goal)
        # Find an elimination whose target has not yet received a proved value.
        index = next(i for i, step in enumerate(record["trace"], 1)
                     if step["conclusion"].op.startswith("Not1_1_"))
        self.app.number_input(key="proof_step").set_value(index).run()
        self.assertIn('class="elimination"', self.markup())
        self.assertIn('class="cell-role" aria-hidden="true">T', self.markup())
        self.assertIn('class="cell-role" aria-hidden="true">S', self.markup())
        self.assertFalse(self.app.exception)


if __name__ == "__main__":
    unittest.main()
