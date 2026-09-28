"""Regression checks for backward-chaining cache invalidation and proof paths.

Run from the repository root: python -m unittest discover -s tests -v
The assignment's support modules are used without modification.
"""

import unittest

from logic_ import PropDefiniteKB, expr, pl_fc_entails
from sudoku_solver import pl_bc_entails


def knowledge_base(*sentences):
    kb = PropDefiniteKB()
    for sentence in sentences:
        kb.tell(expr(sentence))
    return kb


class BackwardChainingRegressionTests(unittest.TestCase):
    def assert_agreement(self, kb, query, expected):
        symbol = expr(query)
        self.assertEqual(pl_bc_entails(kb, symbol), expected)
        self.assertEqual(pl_fc_entails(kb, symbol), expected)

    def test_new_fact_invalidates_cached_failure(self):
        kb = knowledge_base('A ==> B')
        self.assert_agreement(kb, 'B', False)
        kb.tell(expr('A'))
        self.assert_agreement(kb, 'B', True)

    def test_retracted_fact_invalidates_cached_success(self):
        kb = knowledge_base('A', 'A ==> B')
        self.assert_agreement(kb, 'B', True)
        kb.retract(expr('A'))
        self.assert_agreement(kb, 'B', False)

    def test_same_length_replacement_refreshes_rule_index(self):
        kb = knowledge_base('A', 'A ==> B')
        self.assert_agreement(kb, 'B', True)
        kb.retract(expr('A ==> B'))
        kb.tell(expr('C ==> B'))
        self.assert_agreement(kb, 'B', False)

    def test_trace_uses_new_fact_after_same_length_replacement(self):
        kb = knowledge_base('A', 'A ==> Q', 'B ==> Q')
        trace = []
        self.assertTrue(pl_bc_entails(kb, expr('Q'), trace))
        kb.retract(expr('A'))
        kb.tell(expr('B'))
        self.assertTrue(pl_bc_entails(kb, expr('Q'), trace))
        self.assertEqual(trace, [
            {'type': 'fact', 'conclusion': expr('B')},
            {'type': 'rule', 'premises': [expr('B')], 'conclusion': expr('Q')},
        ])

    def test_unsupported_cycle_is_not_a_proof(self):
        kb = knowledge_base('A ==> B', 'B ==> A')
        self.assert_agreement(kb, 'A', False)
        self.assert_agreement(kb, 'B', False)

    def test_fact_supported_alternative_and_shared_premises(self):
        kb = knowledge_base(
            'A ==> B', 'B ==> A', 'C ==> A', 'C', '(A & B) ==> Q'
        )
        self.assert_agreement(kb, 'Q', True)


if __name__ == '__main__':
    unittest.main()
