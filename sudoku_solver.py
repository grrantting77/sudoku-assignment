"""IT5005 Assignment 1: student implementation file.

Implement the functions marked below. Do not modify utils.py or logic_.py.
"""

from utils import *
from logic_ import *


# Do not change this function; it is used to create atomic propositions.
def atom(prefix, r, c, v):
    """prefix is 'Is' or 'Not'. Returns the Expr for e.g. Is3_2_4."""
    return expr(f'{prefix}{r}_{c}_{v}')


def build_general_kb(n, box_h, box_w, givens):
    """Return a PropKB encoding this n x n Sudoku's constraints plus
    the given cells, as general propositional clauses.

    Parameters
    ----------
    n, box_h, box_w : int
    givens : dict[(int, int), int]

    Returns
    -------
    PropKB
    """

    kb = PropKB()

    # -----------------------------------------------------
    # 1. Every cell must contain at least one value.
    #
    # Example for a 9x9 Sudoku:
    # Is1_1_1 OR Is1_1_2 OR ... OR Is1_1_9
    # -----------------------------------------------------
    for r in range(1, n + 1):
        for c in range(1, n + 1):

            clause = atom('Is', r, c, 1)

            for v in range(2, n + 1):
                clause = clause | atom('Is', r, c, v)

            kb.tell(clause)

    # -----------------------------------------------------
    # 2. Every cell can contain at most one value.
    #
    # A cell cannot be both v1 and v2.
    # -----------------------------------------------------
    for r in range(1, n + 1):
        for c in range(1, n + 1):

            for v1 in range(1, n + 1):
                for v2 in range(v1 + 1, n + 1):

                    kb.tell(
                        ~atom('Is', r, c, v1)
                        | ~atom('Is', r, c, v2)
                    )

    # -----------------------------------------------------
    # 3. The same value cannot appear twice in one row.
    # -----------------------------------------------------
    for r in range(1, n + 1):
        for v in range(1, n + 1):

            for c1 in range(1, n + 1):
                for c2 in range(c1 + 1, n + 1):

                    kb.tell(
                        ~atom('Is', r, c1, v)
                        | ~atom('Is', r, c2, v)
                    )

    # -----------------------------------------------------
    # 4. The same value cannot appear twice in one column.
    # -----------------------------------------------------
    for c in range(1, n + 1):
        for v in range(1, n + 1):

            for r1 in range(1, n + 1):
                for r2 in range(r1 + 1, n + 1):

                    kb.tell(
                        ~atom('Is', r1, c, v)
                        | ~atom('Is', r2, c, v)
                    )

    # -----------------------------------------------------
    # 5. The same value cannot appear twice in one box.
    # -----------------------------------------------------
    for box_r in range(1, n + 1, box_h):
        for box_c in range(1, n + 1, box_w):

            cells = []

            # Collect all cells in this box.
            for dr in range(box_h):
                for dc in range(box_w):
                    cells.append(
                        (box_r + dr, box_c + dc)
                    )

            # For every value, no two cells in this box
            # may both contain that value.
            for v in range(1, n + 1):

                for i in range(len(cells)):
                    for j in range(i + 1, len(cells)):

                        r1, c1 = cells[i]
                        r2, c2 = cells[j]

                        kb.tell(
                            ~atom('Is', r1, c1, v)
                            | ~atom('Is', r2, c2, v)
                        )

    # -----------------------------------------------------
    # 6. Add all given cells as facts.
    # -----------------------------------------------------
    for (r, c), v in givens.items():
        kb.tell(
            atom('Is', r, c, v)
        )

    return kb


def build_definite_kb(n, box_h, box_w, givens):
    """Return a PropDefiniteKB encoding this n x n Sudoku's constraints
    plus the given cells, using elimination + last-candidate reasoning.

    Parameters
    ----------
    n, box_h, box_w : int
    givens : dict[(int, int), int]

    Returns
    -------
    PropDefiniteKB
    """

    kb = PropDefiniteKB()

    # -----------------------------------------------------
    # 1. Add all givens as known facts.
    # -----------------------------------------------------
    for (r, c), v in givens.items():
        kb.tell(
            atom('Is', r, c, v)
        )

    # -----------------------------------------------------
    # 2. Elimination rules.
    #
    # If cell (r, c) is known to contain v:
    #
    # - the same cell cannot contain another value;
    # - another cell in the same row cannot contain v;
    # - another cell in the same column cannot contain v;
    # - another cell in the same box cannot contain v.
    # -----------------------------------------------------
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v in range(1, n + 1):

                current = atom('Is', r, c, v)

                # Same cell: eliminate every other value.
                for other_v in range(1, n + 1):

                    if other_v != v:

                        kb.tell(
                            current
                            | '==>'
                            | atom(
                                'Not',
                                r,
                                c,
                                other_v
                            )
                        )

                # Collect all peer cells:
                # same row, column, or box.
                peers = []

                # Same row.
                for other_c in range(1, n + 1):

                    if other_c != c:
                        peers.append(
                            (r, other_c)
                        )

                # Same column.
                for other_r in range(1, n + 1):

                    if (
                        other_r != r
                        and (other_r, c) not in peers
                    ):
                        peers.append(
                            (other_r, c)
                        )

                # Find the top-left corner of the box.
                box_start_r = (
                    ((r - 1) // box_h) * box_h
                    + 1
                )

                box_start_c = (
                    ((c - 1) // box_w) * box_w
                    + 1
                )

                # Same box.
                for rr in range(
                    box_start_r,
                    box_start_r + box_h
                ):
                    for cc in range(
                        box_start_c,
                        box_start_c + box_w
                    ):

                        if (
                            (rr, cc) != (r, c)
                            and (rr, cc) not in peers
                        ):
                            peers.append(
                                (rr, cc)
                            )

                # If the current cell is v,
                # all its peers cannot also be v.
                for rr, cc in peers:

                    kb.tell(
                        current
                        | '==>'
                        | atom(
                            'Not',
                            rr,
                            cc,
                            v
                        )
                    )

    # -----------------------------------------------------
    # 3. Last-candidate rules.
    #
    # If every other value has been eliminated from
    # a cell, the remaining value must be correct.
    #
    # Example:
    # Not1 & Not2 & ... & Not8 ==> Is9
    # -----------------------------------------------------
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v in range(1, n + 1):

                premises = []

                for other_v in range(1, n + 1):

                    if other_v != v:

                        premises.append(
                            atom(
                                'Not',
                                r,
                                c,
                                other_v
                            )
                        )

                # This case is mainly included to keep
                # the function general for n = 1.
                if len(premises) == 0:

                    kb.tell(
                        atom('Is', r, c, v)
                    )

                    continue

                antecedent = premises[0]

                for premise in premises[1:]:
                    antecedent = (
                        antecedent & premise
                    )

                kb.tell(
                    antecedent
                    | '==>'
                    | atom('Is', r, c, v)
                )

    return kb


def solve_full_grid_fc(n, box_h, box_w, givens):
    """Solve the whole puzzle using build_definite_kb + pl_fc_entails.

    Returns
    -------
    dict[(int, int), int]
        {(row, col): value} for every solved cell
    """

    kb = build_definite_kb(
        n,
        box_h,
        box_w,
        givens
    )

    # -----------------------------------------------------
    # Cache rules by premise.
    #
    # The provided pl_fc_entails() repeatedly calls
    # clauses_with_premise(). Building this small index
    # avoids repeatedly scanning the entire KB while still
    # using the provided forward-chaining algorithm.
    # -----------------------------------------------------
    premise_index = {}

    for clause in kb.clauses:

        if clause.op == '==>':

            premises, _ = parse_definite_clause(
                clause
            )

            for premise in premises:

                if premise not in premise_index:
                    premise_index[premise] = []

                premise_index[premise].append(
                    clause
                )

    def cached_clauses_with_premise(p):
        return premise_index.get(p, [])

    # Replace only this KB instance's lookup method.
    # logic_.py itself is not modified.
    kb.clauses_with_premise = (
        cached_clauses_with_premise
    )

    solved = {}

    # -----------------------------------------------------
    # Try candidate values for every cell.
    # -----------------------------------------------------
    for r in range(1, n + 1):
        for c in range(1, n + 1):

            for v in range(1, n + 1):

                query = atom(
                    'Is',
                    r,
                    c,
                    v
                )

                if pl_fc_entails(
                    kb,
                    query
                ):
                    solved[(r, c)] = v
                    break

    return solved


def pl_bc_entails(kb, query, trace=None):
    """Backward chaining for a PropDefiniteKB.

    Parameters
    ----------
    kb : PropDefiniteKB

    query : Expr

    trace : list or None
        Optional list used to record the successful
        proof path for Tutor Mode.

        If trace is None, the function behaves exactly
        like a normal True/False entailment query.

    Returns
    -------
    bool
    """

    # -----------------------------------------------------
    # Build lookup structures only once for each KB.
    # -----------------------------------------------------
    if not hasattr(kb, '_bc_facts'):

        # Single positive symbols are known facts.
        kb._bc_facts = {
            clause
            for clause in kb.clauses
            if is_prop_symbol(clause.op)
        }

        # Map:
        # conclusion -> list of possible premise lists
        kb._bc_rules = {}

        for clause in kb.clauses:

            if clause.op == '==>':

                premises, conclusion = (
                    parse_definite_clause(
                        clause
                    )
                )

                if conclusion not in kb._bc_rules:
                    kb._bc_rules[
                        conclusion
                    ] = []

                kb._bc_rules[
                    conclusion
                ].append(
                    premises
                )

    proven = set(
        kb._bc_facts
    )

    rules_by_conclusion = (
        kb._bc_rules
    )

    # Remember which successful rule was used
    # to prove each derived proposition.
    proof_rule = {}

    def prove(goal, visiting, memo):
        """Try to prove one goal recursively."""

        # Already known or previously proved.
        if goal in proven:
            return True

        # Reuse a result from the current attempt.
        if goal in memo:
            return memo[goal]

        # Avoid cyclic proof paths.
        if goal in visiting:
            return False

        visiting.add(goal)

        # -------------------------------------------------
        # OR:
        # Several different rules may conclude the goal.
        # Proving any one of them is enough.
        # -------------------------------------------------
        for premises in rules_by_conclusion.get(
            goal,
            []
        ):

            all_proved = True

            # ---------------------------------------------
            # AND:
            # Every premise of one chosen rule
            # must be proved.
            # ---------------------------------------------
            for premise in premises:

                if not prove(
                    premise,
                    visiting,
                    memo
                ):
                    all_proved = False
                    break

            if all_proved:

                visiting.remove(goal)

                proven.add(goal)

                memo[goal] = True

                # Store the successful rule so that
                # Tutor Mode can later reconstruct
                # the proof path.
                proof_rule[goal] = list(
                    premises
                )

                return True

        visiting.remove(goal)

        memo[goal] = False

        return False

    def build_trace(goal, seen):
        """Reconstruct the successful proof path."""

        if goal in seen:
            return []

        seen.add(goal)

        # Initial KB fact.
        # For this Sudoku representation,
        # these correspond to givens.
        if goal in kb._bc_facts:

            return [
                {
                    'type': 'fact',
                    'conclusion': goal
                }
            ]

        premises = proof_rule.get(
            goal
        )

        if premises is None:
            return []

        steps = []

        # First explain how all premises
        # were established.
        for premise in premises:

            steps.extend(
                build_trace(
                    premise,
                    seen
                )
            )

        # Then record the rule that derives
        # the current goal.
        steps.append(
            {
                'type': 'rule',
                'premises': list(premises),
                'conclusion': goal
            }
        )

        return steps

    # -----------------------------------------------------
    # Because cyclic dependencies are possible,
    # an unsuccessful attempt may still prove new facts.
    #
    # Retry only if progress was made.
    # If no new fact was proved, another attempt
    # cannot change the result.
    # -----------------------------------------------------
    while True:

        before = len(proven)

        memo = {}

        if prove(
            query,
            set(),
            memo
        ):

            if trace is not None:

                trace.clear()

                trace.extend(
                    build_trace(
                        query,
                        set()
                    )
                )

            return True

        # No new facts were added:
        # the query cannot be proved.
        if len(proven) == before:

            if trace is not None:
                trace.clear()

            return False


def solve_full_grid_bc(n, box_h, box_w, givens):
    """Solve the whole puzzle using build_definite_kb
    and the backward-chaining implementation.

    For every cell, candidate values are tried until
    pl_bc_entails confirms one.

    Returns
    -------
    dict[(int, int), int]
        {(row, col): value} for every solved cell
    """

    kb = build_definite_kb(
        n,
        box_h,
        box_w,
        givens
    )

    solved = {}

    for r in range(1, n + 1):
        for c in range(1, n + 1):

            for v in range(1, n + 1):

                query = atom(
                    'Is',
                    r,
                    c,
                    v
                )

                if pl_bc_entails(
                    kb,
                    query
                ):

                    solved[(r, c)] = v
                    break

    return solved