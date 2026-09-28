"""Sudoku interface. Keep this file beside the existing solver and puzzles.json.

Run:
    python -m streamlit run sudoku_app.py

Core inference remains in sudoku_solver.py.
"""

from html import escape
from pathlib import Path

import json
import re
import time

import streamlit as st

from sudoku_solver import (
    atom,
    build_definite_kb,
    build_general_kb,
    solve_full_grid_fc,
    solve_full_grid_bc,
    pl_bc_entails,
)


# =========================================================
# Page configuration
# =========================================================

st.set_page_config(
    page_title="Sudoku Logic Solver",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="auto",
)


# =========================================================
# HTML helper
# =========================================================

def html(markup):
    """Render HTML consistently without Markdown code-block issues."""

    if hasattr(st, "html"):
        st.html(markup)

    else:
        st.markdown(
            "\n".join(
                line.strip()
                for line in markup.splitlines()
            ),
            unsafe_allow_html=True,
        )


# =========================================================
# Styling
# =========================================================

CSS = """
<style>

:root {
    --navy: #16364f;
    --blue: #24618a;
    --teal: #137a78;

    --ink: #213e53;
    --muted: #597083;

    --line: #d5e1e9;

    --pale: #e7f2fa;

    --source-bg: #cce7f8;
    --source-border: #2f83b5;
    --source-text: #0d527e;

    --target-bg: #fff0c9;
    --target-border: #dfa63a;
    --target-text: #855b00;

    --primary-color: #24618a;
}


/* ======================================================
   MAIN PAGE
   ====================================================== */

.stApp {
    background: #f3f7fa;
    color: var(--ink);
}


[data-testid="stHeader"] {
    background: #f3f7fa;
}


[data-testid="stMainBlockContainer"],
.main .block-container {
    max-width: 1420px;
    padding: 5.25rem 2.5rem 4rem;
}


/* ======================================================
   SIDEBAR
   ====================================================== */

[data-testid="stSidebar"] {
    background: #fbfdff;

    border-right:
        1px solid #cbdbe6;

    box-shadow:
        6px 0 22px rgba(22, 54, 79, 0.04);
}


[data-testid="stSidebar"]
[data-testid="stSidebarContent"] {
    padding-top: 1rem;
}


[data-testid="stSidebar"] h2 {
    font-size: 1.35rem;
    color: var(--navy);
}


[data-testid="stSidebar"] h3 {
    font-size: 1rem;
    color: var(--navy);
}


[data-testid="stWidgetLabel"] p {
    font-size: .94rem;
    font-weight: 600;
    color: var(--ink);
}


[data-testid="stCaptionContainer"] p {
    color: var(--muted);
    line-height: 1.6;
}


/* ======================================================
   HERO
   ====================================================== */

.hero {
    position: relative;
    overflow: hidden;

    border-radius: 20px;

    padding:
        27px
        32px;

    background:
        linear-gradient(
            110deg,
            #132f49 0%,
            #1b4864 70%,
            #23677b 100%
        );

    box-shadow:
        0 10px 24px #16364f12;

    margin-bottom: 5px;
}


.hero h1 {
    color: #ffffff;

    font-size:
        clamp(
            1.65rem,
            2.5vw,
            2.2rem
        );

    letter-spacing: -.035em;

    font-weight: 750;

    padding: 0;

    margin:
        0
        0
        9px;

    line-height: 1.2;
}


.hero p {
    color: #d7e8f2;

    font-size: 1rem;

    line-height: 1.6;

    margin: 0;

    max-width: none;

    text-wrap: pretty;
}


.hero-meta {
    display: flex;

    gap: 9px;

    flex-wrap: wrap;

    margin-top: 17px;
}


.hero-meta span {
    color: #d5e7f1;

    font-size: .77rem;

    padding:
        4px
        10px;

    border:
        1px solid #ffffff28;

    border-radius: 6px;
}


/* ======================================================
   MAIN MODE TABS
   ====================================================== */

[data-baseweb="tab-list"] {
    display: grid;

    grid-template-columns:
        repeat(
            3,
            minmax(0, 1fr)
        );

    gap: 14px;

    overflow: visible;

    padding:
        8px
        0
        12px;

    background: transparent;
}


button[data-baseweb="tab"] {
    position: relative;

    width: 100%;

    height: 116px;

    min-width: 0;

    display: flex;

    flex-direction: column;

    align-items: flex-start;

    justify-content: center;

    gap: 9px;

    padding:
        20px
        23px;

    margin: 0;

    white-space: normal;

    background:
        #ffffff
        !important;

    border:
        2px solid #d6e2eb
        !important;

    border-radius: 15px;

    color:
        var(--navy)
        !important;

    box-shadow:
        0 5px 16px #16364f07;

    transition:
        background .15s,
        border-color .15s;
}


button[data-baseweb="tab"] p {
    font-size:
        1.4rem
        !important;

    font-weight:
        730
        !important;

    letter-spacing:
        -.025em;

    line-height:
        1.2;

    color:
        inherit
        !important;

    margin: 0;
}


button[data-baseweb="tab"]::before {
    position: absolute;

    right: 17px;
    top: 13px;

    color: #7193a9;

    font-size: .7rem;

    font-weight: 700;

    letter-spacing: .05em;
}


button[data-baseweb="tab"]::after {
    font-size: .87rem;

    font-weight: 450;

    color: #5a7589;
}


button[data-baseweb="tab"]:nth-of-type(1)::before {
    content: "01";
}


button[data-baseweb="tab"]:nth-of-type(2)::before {
    content: "02";
}


button[data-baseweb="tab"]:nth-of-type(3)::before {
    content: "03";
}


button[data-baseweb="tab"]:nth-of-type(1)::after {
    content: "Solve the grid";
}


button[data-baseweb="tab"]:nth-of-type(2)::after {
    content: "Test a proposition";
}


button[data-baseweb="tab"]:nth-of-type(3)::after {
    content: "Follow the proof";
}


button[data-baseweb="tab"]:hover {
    background:
        #edf6fc
        !important;

    border-color:
        #8cb6d0
        !important;
}


button[data-baseweb="tab"][aria-selected="true"] {
    background:
        #deedf8
        !important;

    border-color:
        #35769e
        !important;

    box-shadow:
        inset 0 4px 0 #137a78,
        0 7px 18px #24618a12;

    color:
        #103d5c
        !important;
}


button[data-baseweb="tab"][aria-selected="true"]::after {
    color: #315f7c;
}


[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] {
    display: none;
}


[data-baseweb="tab-panel"] {
    padding-top: 13px;
}


/* ======================================================
   SECTION HEADINGS
   ====================================================== */

.section-head {
    margin:
        0
        0
        6px;
}


.section-head h2 {
    padding: 0;

    margin:
        0
        0
        7px;

    color:
        var(--navy);

    font-size:
        1.5rem;

    font-weight:
        720;

    letter-spacing:
        -.025em;

    line-height:
        1.3;
}


.section-head p {
    margin: 0;

    color:
        var(--muted);

    font-size:
        .94rem;

    line-height:
        1.6;

    max-width: none;

    text-wrap: pretty;
}


.subhead {
    font-size:
        1.12rem;

    font-weight:
        720;

    color:
        var(--navy);

    margin:
        6px
        0
        8px;
}


.key-reasoning-head {
    display:
        flex;

    align-items:
        center;

    gap:
        10px;

    font-size:
        1.55rem;

    letter-spacing:
        -.025em;

    margin:
        12px
        0
        7px;
}


.key-reasoning-head::before {
    content: "";

    width:
        4px;

    height:
        1.45rem;

    flex:
        0 0 4px;

    border-radius:
        999px;

    background:
        var(--teal);
}


.key-reasoning-caption {
    margin:
        0
        0
        17px;

    color:
        var(--muted);

    font-size:
        .94rem;

    line-height:
        1.6;
}


/* ======================================================
   STREAMLIT CONTAINERS
   ====================================================== */

[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-color:
        var(--line)
        !important;

    border-radius:
        15px;
}


.st-key-solver_panel {
    background: #ffffff;

    border-radius: 15px;
}


/* ======================================================
   BUTTONS / FORM ELEMENTS
   ====================================================== */

button[kind],
[data-testid="stDownloadButton"] button {
    min-height: 44px;

    border-radius: 9px;

    font-weight: 650;

    color:
        var(--navy);

    background:
        #ffffff;

    border-color:
        #b9cedd;
}


button[kind="primary"] {
    background:
        var(--navy)
        !important;

    border-color:
        var(--navy)
        !important;

    color:
        #ffffff
        !important;

    box-shadow:
        0 4px 10px #16364f12;
}


button[kind="primary"]:hover {
    background:
        #245577
        !important;
}


.st-key-next_step button[kind="primary"] {
    background:
        #173f5e
        !important;

    border-color:
        #173f5e
        !important;

    box-shadow:
        0 5px 12px #173f5e24;
}


.st-key-next_step button[kind="primary"]:hover {
    background:
        #245b7e
        !important;

    border-color:
        #245b7e
        !important;
}


.st-key-previous_step button {
    background:
        transparent
        !important;

    border-color:
        #ccdae4
        !important;

    color:
        #35556c
        !important;

    box-shadow:
        none
        !important;
}


.st-key-previous_step button:hover {
    background:
        #edf4f8
        !important;

    border-color:
        #9eb9ca
        !important;
}


button[kind="secondary"]:hover,
[data-testid="stDownloadButton"] button:hover {
    color:
        var(--blue)
        !important;

    border-color:
        var(--blue)
        !important;

    background:
        #edf6fc
        !important;
}


button:focus-visible,
[data-baseweb="tab"]:focus-visible {
    outline:
        3px solid #74b7df
        !important;

    outline-offset:
        3px;

    box-shadow:
        none
        !important;
}


button[kind]:disabled {
    opacity: .4;
}


[data-baseweb="input"],
[data-baseweb="select"] > div {
    background:
        #ffffff;

    border-color:
        #b9cedd
        !important;

    border-radius:
        9px;

    color:
        var(--ink);
}


[data-baseweb="input"]:focus-within,
[data-baseweb="select"] > div:focus-within {
    border-color:
        var(--blue)
        !important;

    box-shadow:
        0 0 0 2px #b8d9ee
        !important;
}


[data-testid="stNumberInputContainer"] {
    border:
        1px solid #b9cedd
        !important;

    border-radius:
        9px;

    background:
        #ffffff
        !important;
}


[data-testid="stNumberInputContainer"].focused,
[data-testid="stNumberInputContainer"]:focus-within {
    border-color:
        var(--blue)
        !important;

    box-shadow:
        0 0 0 2px #b8d9ee
        !important;
}


[data-testid="stNumberInputContainer"]
[data-baseweb="input"] {
    box-shadow:
        none
        !important;
}


[data-testid="stNumberInputContainer"]
[data-baseweb="base-input"] {
    background:
        #ffffff
        !important;
}


[data-testid="stNumberInput"] button {
    color:
        var(--blue);

    background:
        #f0f6fa;
}


[data-testid="stNumberInput"] button:hover {
    background:
        #d8edf9
        !important;

    color:
        var(--navy)
        !important;
}


[role="option"][aria-selected="true"] {
    background:
        #deedf8
        !important;

    color:
        var(--navy)
        !important;
}


[role="option"]:hover {
    background:
        #edf6fc
        !important;

    color:
        var(--navy)
        !important;
}


/* ======================================================
   SUDOKU BOARD
   ====================================================== */

.board-wrap {
    width: 100%;

    max-width: 520px;

    margin:
        4px
        auto
        10px;
}


.sudoku-board {
    border-collapse:
        collapse;

    table-layout:
        fixed;

    width:
        100%;
}


.sudoku-board th {
    padding: 0;

    border: none;

    height: 26px;

    font-size: .67rem;

    font-weight: 650;

    color:
        #637d90;

    text-align:
        center;

    background:
        transparent;
}


.sudoku-board .axis {
    width: 27px;
}


.sudoku-board td {
    padding: 0;

    border:
        1px solid #b9cbd8;

    background:
        #ffffff;

    color:
        var(--navy);

    text-align:
        center;

    position:
        relative;
}


.sudoku-board .cell-inner {
    aspect-ratio: 1;

    display: flex;

    align-items:
        center;

    justify-content:
        center;

    position:
        relative;

    font-size:
        clamp(
            1rem,
            1.9vw,
            1.55rem
        );

    line-height:
        1;
}


/* Given values */

.sudoku-board td.given {
    background:
        #eaf0f5;

    font-weight:
        740;
}


/*
Inferred values:
slightly stronger / more saturated teal-green
without becoming visually harsh.
*/

.sudoku-board td.derived {
    background:
        #d9f1e9;

    color:
        #08736b;

    font-weight:
        680;
}


/* The underline and letter markers also work without color. */
.sudoku-board td.derived .cell-inner {
    text-decoration: underline;
    text-underline-offset: .16em;
}
.sudoku-board .cell-role {
    position: absolute;
    left: 3px;
    top: 3px;
    font-size: max(8px, .45em);
    font-weight: 750;
    line-height: 1;
    text-decoration: none;
}

/* Supporting cell */

.sudoku-board td.source {
    background:
        #cce7f8;

    color:
        #0d527e;

    box-shadow:
        inset 0 0 0 3px
        #2f83b5;
}


/* Reasoning target */

.sudoku-board td.target {
    background:
        #fff0c9;

    color:
        #855b00;

    box-shadow:
        inset 0 0 0 3px
        #dfa63a;
}


/* Cell Query target */

.sudoku-board td.query-target {
    background:
        #dceefa;

    box-shadow:
        inset 0 0 0 2px #327ca9;
}


/* ×3, ×8, etc. */

.sudoku-board .elimination {
    font-weight:
        780;

    font-size:
        .92em;

    letter-spacing:
        -.05em;

    color:
        #8a5b00;
}


.sudoku-board .cell-note {
    position:
        absolute;

    right:
        3px;

    bottom:
        3px;

    font-size:
        .48em;

    border-radius:
        4px;

    background:
        #ffe0a0;

    padding:
        2px
        3px;

    color:
        #815400;
}


/* ======================================================
   LEGENDS
   ====================================================== */

.legend {
    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        14px
        22px;

    color:
        var(--muted);

    font-size:
        .84rem;

    margin:
        10px
        0;
}


.legend span {
    display:
        inline-flex;

    align-items:
        center;

    gap:
        7px;
}


/*
Make the horizontal board legend use the same
maximum width and centering as the Sudoku board.
*/

.legend:not(.vertical) {
    width:
        100%;

    max-width:
        520px;

    margin:
        12px
        auto
        8px;

    justify-content:
        flex-start;
}


/*
Horizontal legend swatches are slightly larger
than before.
*/

.legend:not(.vertical) .swatch {
    width:
        20px;

    height:
        20px;

    border-radius:
        5px;
}


/*
Sidebar legend swatches.
*/

.swatch {
    width:
        18px;

    height:
        18px;

    display:
        inline-block;

    border:
        1.5px solid #9eb8ca;

    border-radius:
        4px;

    flex-shrink:
        0;
}


.legend.vertical {
    flex-direction:
        column;

    gap:
        14px;
}


.legend.vertical span {
    gap:
        10px;

    font-size:
        .88rem;
}


/* ======================================================
   INFORMATION BOXES
   ====================================================== */

.note {
    border:
        1px solid #cfe0ec;

    border-radius:
        12px;

    background:
        #eaf3fa;

    padding:
        17px
        19px;

    color:
        #345b75;

    font-size:
        .92rem;

    line-height:
        1.6;
}


.note strong {
    color:
        var(--navy);
}


.meta-label {
    font-size:
        .78rem;

    color:
        var(--muted);

    margin-bottom:
        6px;
}


.method-name {
    font-size:
        1.24rem;

    color:
        var(--navy);

    font-weight:
        700;

    margin-bottom:
        9px;
}


.stat-pair {
    display:
        flex;

    gap:
        28px;

    flex-wrap:
        wrap;

    margin:
        13px
        0
        7px;
}


.stat-pair strong {
    display:
        block;

    font-size:
        1.8rem;

    color:
        var(--navy);

    letter-spacing:
        -.04em;
}


.stat-pair span {
    font-size:
        .8rem;

    color:
        var(--muted);
}


/* ======================================================
   QUERY
   ====================================================== */

.query-claim {
    border:
        1px solid #cadde9;

    border-radius:
        12px;

    background:
        #f0f7fc;

    padding:
        16px
        20px;

    margin:
        1px
        0
        4px;
}


.query-claim strong {
    color:
        var(--navy);

    font-size:
        1.15rem;
}


/* ======================================================
   TRUE / FALSE VERDICT
   ====================================================== */

.verdict {
    display:
        flex;

    align-items:
        center;

    gap:
        22px;

    padding:
        20px
        23px;

    border:
        1px solid #bedfd9;

    border-left:
        5px solid var(--teal);

    border-radius:
        12px;

    background:
        #edf8f5;

    margin:
        5px
        0;
}


.verdict.false {
    border-color:
        #c4d9e9;

    border-left-color:
        var(--blue);

    background:
        #edf4fa;
}


.verdict-bool {
    font-size:
        2.25rem;

    line-height:
        1.1;

    font-weight:
        780;

    color:
        #0a6a67;

    letter-spacing:
        -.04em;
}


.verdict.false .verdict-bool {
    color:
        var(--blue);
}


.verdict-title {
    color:
        var(--navy);

    font-size:
        1rem;

    font-weight:
        700;
}


.verdict-desc {
    color:
        #4a6b79;

    font-size:
        .89rem;

    line-height:
        1.5;

    margin-top:
        5px;
}


/* ======================================================
   PROOF SUMMARY
   ====================================================== */

.proof-summary {
    display:
        flex;

    gap:
        12px;

    align-items:
        center;

    flex-wrap:
        wrap;

    color:
        var(--muted);

    padding:
        4px
        0;

    font-size:
        .85rem;
}


.pill {
    display:
        inline-block;

    padding:
        5px
        10px;

    border-radius:
        7px;

    font-size:
        .77rem;

    font-weight:
        650;

    background:
        #e5f1f8;

    color:
        #2d6385;
}


.pill.teal {
    color:
        #126c68;

    background:
        #def1eb;
}


/* ======================================================
   KEY REASONING
   ====================================================== */

.reasoning-list {
    border:
        1px solid var(--line);

    border-radius:
        13px;

    overflow:
        hidden;

    background:
        #ffffff;
}


.reason-row {
    display:
        grid;

    grid-template-columns:
        44px
        75px
        minmax(0, 1fr);

    align-items:
        start;

    gap:
        12px;

    padding:
        15px
        18px;
}


.reason-row + .reason-row {
    border-top:
        1px solid #e4edf3;
}


.value-badge {
    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    width:
        37px;

    height:
        34px;

    background:
        #eaf3fa;

    color:
        #285d7e;

    border-radius:
        8px;

    font-size:
        .95rem;

    font-weight:
        750;
}


.source-badge {
    display:
        inline-block;

    padding:
        5px
        8px;

    border-radius:
        6px;

    font-size:
        .73rem;

    font-weight:
        650;

    margin-top:
        3px;
}


.source-given {
    color:
        #4e677a;

    background:
        #edf2f6;
}


.source-derived {
    color:
        #126e69;

    background:
        #e1f3ed;
}


.reason-text {
    font-size:
        .91rem;

    color:
        #37546a;

    line-height:
        1.65;

    overflow-wrap:
        anywhere;
}


/* ======================================================
   FINAL INFERENCE
   ====================================================== */

.conclusion {
    background:
        #eaf7f3;

    border:
        1px solid #c2e3da;

    border-left:
        4px solid var(--teal);

    padding:
        20px
        23px;

    border-radius:
        12px;

    font-size:
        .95rem;

    line-height:
        1.75;

    color:
        #315b60;
}


.conclusion h3 {
    color:
        #116965;

    font-size:
        1.1rem;

    padding:
        0;

    margin:
        0
        0
        8px;
}


.conclusion p {
    margin: 0;
}


/* ======================================================
   STEP EXPLANATION CARD
   ====================================================== */

.step-card {
    background:
        #ffffff;

    border:
        1px solid var(--line);

    border-radius:
        14px;

    overflow:
        hidden;

    margin:
        7px
        0
        15px;
}


.step-card h4 {
    padding:
        15px
        18px;

    margin:
        0;

    background:
        #e9f3fa;

    color:
        #1c526f;

    font-size:
        1rem;
}


.step-field {
    padding:
        13px
        18px;

    border-top:
        1px solid #e3edf3;
}


.step-field strong {
    display:
        block;

    color:
        var(--navy);

    font-size:
        .95rem;

    line-height:
        1.5;
}


.step-explanation {
    font-size:
        .95rem;

    line-height:
        1.75;

    color:
        #37546a;
}


/* ======================================================
   PROOF PROGRESS
   ====================================================== */

.progress-track {
    height:
        5px;

    border-radius:
        5px;

    overflow:
        hidden;

    background:
        #dce8f0;

    margin:
        8px
        0
        12px;
}


.progress-fill {
    height:
        100%;

    background:
        linear-gradient(
            90deg,
            #3885b2,
            #188a82
        );
}


/* ======================================================
   FOOTER
   ====================================================== */

.footer-note {
    color:
        #7390a2;

    font-size:
        .75rem;

    border-top:
        1px solid #d9e5ed;

    padding-top:
        17px;

    margin-top:
        24px;
}


/* ======================================================
   RESPONSIVE
   ====================================================== */

@media (max-width: 1100px) {

    [data-testid="stMainBlockContainer"],
    .main .block-container {
        padding-left:
            1.5rem;

        padding-right:
            1.5rem;
    }


    button[data-baseweb="tab"] {
        padding:
            18px
            15px;
    }


    button[data-baseweb="tab"] p {
        font-size:
            1.17rem
            !important;
    }
}


@media (max-width: 740px) {

    [data-testid="stMainBlockContainer"],
    .main .block-container {
        padding:
            4.75rem
            1rem
            3rem;
    }


    .hero {
        padding:
            23px;

        border-radius:
            15px;
    }


    .hero-meta {
        gap:
            6px;
    }


    [data-baseweb="tab-list"] {
        gap:
            8px;

        grid-template-columns:
            1fr;
    }


    button[data-baseweb="tab"] {
        height:
            76px;

        gap:
            5px;

        padding:
            12px
            18px;
    }


    button[data-baseweb="tab"] p {
        font-size:
            1.22rem
            !important;
    }


    button[data-baseweb="tab"]::before {
        top:
            17px;
    }


    button[data-baseweb="tab"]::after {
        font-size:
            .82rem;
    }


    .reason-row {
        grid-template-columns:
            42px
            minmax(0, 1fr);

        gap:
            9px;

        padding:
            14px;
    }


    .reason-text {
        grid-column:
            1 / -1;
    }


    .sudoku-board .cell-inner {
        font-size:
            1.15rem;
    }


    .verdict {
        align-items:
            flex-start;

        gap:
            15px;

        padding:
            17px;
    }


    .verdict-bool {
        font-size:
            1.85rem;
    }
}

</style>
"""

html(CSS)


# =========================================================
# Small UI helpers
# =========================================================

def section(title, description=""):
    html(
        f'<div class="section-head">'
        f'<h2>{escape(title)}</h2>'
        f'<p>{escape(description)}</p>'
        f'</div>'
    )


def note(message):
    html(
        f'<div class="note" role="status">'
        f'{escape(message)}'
        f'</div>'
    )


# =========================================================
# Load puzzles
# =========================================================

def convert_cells(cells):
    return {
        tuple(
            map(
                int,
                key.split("_"),
            )
        ): int(value)

        for key, value
        in cells.items()
    }


try:

    pool = json.loads(
        Path(__file__)
        .with_name("puzzles.json")
        .read_text(
            encoding="utf-8"
        )
    )

    n = int(
        pool["n"]
    )

    box_h = int(
        pool["box_h"]
    )

    box_w = int(
        pool["box_w"]
    )

    puzzles = pool[
        "puzzles"
    ]

    if (
        not puzzles
        or box_h * box_w != n
        or n < 1
    ):

        raise ValueError(
            "Invalid board dimensions "
            "or empty puzzle list."
        )


except (
    OSError,
    ValueError,
    KeyError,
    TypeError,
) as exc:

    note(
        "Unable to load puzzles.json. "
        "Keep it in the same folder as "
        f"sudoku_app.py. {exc}"
    )

    st.stop()


# =========================================================
# Proposition parsing
# =========================================================

def parse_atom(proposition):

    match = re.fullmatch(
        r"(Is|Not)(\d+)_(\d+)_(\d+)",
        str(proposition),
    )

    return (
        (
            match[1],
            int(match[2]),
            int(match[3]),
            int(match[4]),
        )

        if match
        else None
    )


def describe_atom(proposition):

    parsed = parse_atom(
        proposition
    )

    if parsed is None:

        return str(
            proposition
        )

    prefix, r, c, value = (
        parsed
    )

    if prefix == "Is":

        return (
            f"cell ({r}, {c}) "
            f"= {value}"
        )

    return (
        f"value {value} is ruled out "
        f"for cell ({r}, {c})"
    )


# =========================================================
# Sudoku relations
# =========================================================

def relation_between(
    r1,
    c1,
    r2,
    c2,
):

    if (
        (r1, c1)
        == (r2, c2)
    ):

        return (
            "cell",
            "the same cell",
        )


    if r1 == r2:

        return (
            "row",
            f"row {r1}",
        )


    if c1 == c2:

        return (
            "column",
            f"column {c1}",
        )


    if (
        (
            (r1 - 1) // box_h,
            (c1 - 1) // box_w,
        )
        ==
        (
            (r2 - 1) // box_h,
            (c2 - 1) // box_w,
        )
    ):

        return (
            "box",
            f"the same "
            f"{box_h}×{box_w} box",
        )


    return (
        "constraint",
        "a Sudoku constraint",
    )


def is_given(
    proposition,
    trace,
):

    return any(
        step["type"] == "fact"
        and step["conclusion"]
        == proposition

        for step
        in trace
    )


def values_text(values):

    values = sorted(
        set(values)
    )

    if not values:

        return ""


    if (
        len(values) > 2
        and values
        == list(
            range(
                values[0],
                values[-1] + 1,
            )
        )
    ):

        return (
            f"{values[0]} "
            f"through "
            f"{values[-1]}"
        )


    if len(values) == 1:

        return str(
            values[0]
        )


    return (
        ", ".join(
            map(
                str,
                values[:-1],
            )
        )
        + f" and {values[-1]}"
    )


# =========================================================
# Human-readable proof explanation
# =========================================================

def explain_step(
    step,
    trace,
):

    parsed = parse_atom(
        step["conclusion"]
    )

    if not parsed:

        return (
            "The recorded rule establishes "
            f"{describe_atom(step['conclusion'])}."
        )


    prefix, r, c, value = (
        parsed
    )


    if step["type"] == "fact":

        return (
            "The puzzle directly gives "
            f"cell ({r}, {c}) = {value}."
        )


    premises = step.get(
        "premises",
        [],
    )


    if (
        prefix == "Not"
        and len(premises) == 1
    ):

        support = parse_atom(
            premises[0]
        )

        if (
            support
            and support[0] == "Is"
        ):

            _, sr, sc, sv = (
                support
            )


            if is_given(
                premises[0],
                trace,
            ):

                origin = (
                    "The puzzle gives"
                )

            else:

                origin = (
                    "Earlier reasoning establishes"
                )


            intro = (
                f"{origin} cell "
                f"({sr}, {sc}) = {sv}."
            )


            relation, label = (
                relation_between(
                    sr,
                    sc,
                    r,
                    c,
                )
            )


            if relation == "cell":

                return (
                    f"{intro} A cell has only one value, "
                    f"so {value} is ruled out "
                    f"for this cell."
                )


            return (
                f"{intro} The two cells share "
                f"{label}, where a value cannot repeat. "
                f"Therefore, {value} is ruled out "
                f"for cell ({r}, {c})."
            )


    alternatives = []


    for premise in premises:

        info = parse_atom(
            premise
        )

        if (
            info
            and info[0] == "Not"
            and info[1:3]
            == (r, c)
        ):

            alternatives.append(
                info[3]
            )


    if (
        prefix == "Is"
        and set(alternatives)
        ==
        set(
            range(
                1,
                n + 1,
            )
        )
        - {value}
    ):

        return (
            f"Values "
            f"{values_text(alternatives)} "
            f"have been ruled out "
            f"for cell ({r}, {c}). "
            f"Every cell must have one value "
            f"from 1 to {n}, so {value} is "
            f"the only remaining value."
        )


    return (
        "The recorded premises establish "
        f"that {describe_atom(step['conclusion'])}."
    )


# =========================================================
# Key reasoning
# =========================================================

def key_reasoning(
    trace,
    query,
):

    index = {
        step["conclusion"]:
            step

        for step
        in trace
    }


    final_step = index.get(
        query
    )


    if final_step is None:

        return (
            [],
            "No final proof step was recorded "
            "for this query.",
        )


    if final_step["type"] == "fact":

        return (
            [],
            explain_step(
                final_step,
                trace,
            )
            + " No additional inference "
              "is required.",
        )


    _, r, c, value = (
        parse_atom(
            query
        )
    )


    rows = []


    for premise in final_step.get(
        "premises",
        [],
    ):

        parsed = parse_atom(
            premise
        )


        if (
            not parsed
            or parsed[0] != "Not"
            or parsed[1:3]
            != (r, c)
        ):

            continue


        producer = index.get(
            premise
        )


        supports = (
            producer.get(
                "premises",
                [],
            )
            if producer
            else []
        )


        source = (
            "Given"

            if (
                len(supports) == 1
                and is_given(
                    supports[0],
                    trace,
                )
            )

            else "Derived"
        )


        rows.append(
            {
                "value":
                    parsed[3],

                "source":
                    source,

                "reason":
                    (
                        explain_step(
                            producer,
                            trace,
                        )

                        if producer
                        else describe_atom(
                            premise
                        )
                    ),
            }
        )


    rows.sort(
        key=lambda row:
            row["value"]
    )


    eliminated = {
        row["value"]
        for row
        in rows
    }


    if (
        eliminated
        ==
        set(
            range(
                1,
                n + 1,
            )
        )
        - {value}
    ):

        origins = {
            row["source"]
            for row
            in rows
        }


        support_text = {
            frozenset(
                {"Given"}
            ):
                (
                    "These exclusions follow directly "
                    "from the original givens."
                ),

            frozenset(
                {"Derived"}
            ):
                (
                    "These exclusions use values "
                    "established earlier in the proof."
                ),
        }.get(
            frozenset(
                origins
            ),
            (
                "Some exclusions follow directly from "
                "the original givens; others use values "
                "established earlier in the proof."
            ),
        )


        conclusion = (
            f"The reasoning above rules out values "
            f"{values_text(eliminated)} "
            f"for cell ({r}, {c}). "
            f"{support_text} "
            f"Since this cell must contain one value "
            f"from 1 to {n}, only {value} remains. "
            f"The knowledge base therefore entails "
            f"cell ({r}, {c}) = {value}: True."
        )


    else:

        conclusion = explain_step(
            final_step,
            trace,
        )


    return (
        rows,
        conclusion,
    )


# =========================================================
# Replay proof board
# =========================================================

def board_state(
    givens,
    trace,
    step_number,
):

    values = dict(
        givens
    )


    for step in trace[
        :step_number
    ]:

        parsed = parse_atom(
            step["conclusion"]
        )


        if (
            parsed
            and parsed[0] == "Is"
        ):

            _, r, c, value = (
                parsed
            )

            values[
                r,
                c,
            ] = value


    return values


# =========================================================
# Visual reasoning metadata
# =========================================================

def visual_details(
    step,
    trace,
):

    parsed = parse_atom(
        step["conclusion"]
    )


    details = dict(
        kind="Inference",
        source=None,
        target=None,
        note=None,
        support="Recorded premises",
        rule="Logical inference",
        result=describe_atom(
            step["conclusion"]
        ),
    )


    if parsed is None:

        return details


    prefix, r, c, value = (
        parsed
    )


    details["target"] = (
        r,
        c,
    )


    if step["type"] == "fact":

        details.update(
            kind="Given fact",

            support=(
                "Original puzzle"
            ),

            rule=(
                "Initial puzzle fact"
            ),
        )


    elif prefix == "Not":

        details.update(
            kind="Elimination",
            note=f"×{value}",
        )


        premises = step.get(
            "premises",
            [],
        )


        info = (
            parse_atom(
                premises[0]
            )

            if len(premises) == 1
            else None
        )


        if (
            info
            and info[0] == "Is"
        ):

            _, sr, sc, sv = (
                info
            )


            details["source"] = (
                sr,
                sc,
            )


            origin = (
                "Given"

                if is_given(
                    premises[0],
                    trace,
                )

                else "Derived"
            )


            relation, _ = (
                relation_between(
                    sr,
                    sc,
                    r,
                    c,
                )
            )


            rules = {
                "cell":
                    "One value per cell",

                "row":
                    "Row uniqueness",

                "column":
                    "Column uniqueness",

                "box":
                    (
                        f"{box_h}×{box_w} "
                        f"box uniqueness"
                    ),
            }


            details.update(
                support=(
                    f"Cell ({sr}, {sc}) = {sv} "
                    f"· {origin}"
                ),

                rule=rules.get(
                    relation,
                    "Sudoku constraint",
                ),
            )


    else:

        details.update(
            kind="Last candidate",

            support=(
                "All other values "
                "have been ruled out"
            ),

            rule=(
                "Last-candidate rule"
            ),
        )


    return details


# =========================================================
# Sudoku board HTML
# =========================================================

def board_html(
    values,
    givens,
    source=None,
    target=None,
    target_note=None,
    query_target=None,
):

    parts = [
        (
            '<div class="board-wrap">'
            '<table class="sudoku-board" '
            'aria-label="Sudoku board">'
        ),

        (
            '<thead>'
            '<tr>'
            '<th class="axis" '
            'aria-label="Row and column coordinates">'
            '</th>'
        ),
    ]


    parts.extend(
        f'<th scope="col">C{c}</th>'

        for c
        in range(
            1,
            n + 1,
        )
    )


    parts.append(
        '</tr>'
        '</thead>'
        '<tbody>'
    )


    for r in range(
        1,
        n + 1,
    ):

        parts.append(
            f'<tr>'
            f'<th class="axis" '
            f'scope="row">'
            f'R{r}'
            f'</th>'
        )


        for c in range(
            1,
            n + 1,
        ):

            cell = (
                r,
                c,
            )


            value = values.get(
                cell,
                "",
            )


            classes = [
                (
                    "given"

                    if cell in givens

                    else (
                        "derived"

                        if value != ""

                        else "empty"
                    )
                )
            ]


            if cell == source:
                classes.append(
                    "source"
                )


            if cell == target:
                classes.append(
                    "target"
                )


            if cell == query_target:
                classes.append(
                    "query-target"
                )


            display = escape(
                str(value)
            )


            label = (
                f"Row {r}, column {c}: "
                f"{value if value != '' else 'empty'}; {classes[0]}"
            )



            if (
                cell == target
                and target_note
            ):

                if value == "":

                    display = (
                        '<span class="elimination">'
                        f'{escape(target_note)}'
                        '</span>'
                    )

                else:

                    display += (
                        '<span class="cell-note">'
                        f'{escape(target_note)}'
                        '</span>'
                    )


                label += (
                    f"; eliminate "
                    f"{target_note[1:]}"
                )


            roles = []
            for highlighted, marker, description in (
                (source, "S", "supporting cell"),
                (target, "T", "reasoning target"),
                (query_target, "Q", "query target"),
            ):
                if cell == highlighted:
                    roles.append(marker)
                    label += f"; {description}"
            if roles:
                display += (
                    '<span class="cell-role" aria-hidden="true">'
                    f'{"/".join(roles)}</span>'
                )


            borders = []


            for edge, thick in (
                (
                    "top",
                    (r - 1) % box_h == 0,
                ),
                (
                    "left",
                    (c - 1) % box_w == 0,
                ),
                (
                    "bottom",
                    r == n,
                ),
                (
                    "right",
                    c == n,
                ),
            ):

                if thick:

                    borders.append(
                        f"border-{edge}:"
                        f"2px solid #47677f"
                    )


            parts.append(
                f'<td '
                f'class="{" ".join(classes)}" '
                f'data-cell="{r}_{c}" '
                f'aria-label="'
                f'{escape(label, quote=True)}" '
                f'style="{";".join(borders)}">'
                f'<div class="cell-inner">'
                f'{display}'
                f'</div>'
                f'</td>'
            )


        parts.append(
            '</tr>'
        )


    parts.append(
        '</tbody>'
        '</table>'
        '</div>'
    )


    return "".join(
        parts
    )


# =========================================================
# Board legend
# =========================================================

def board_legend(
    visual=False,
    vertical=False,
):

    entries = [
        (
            "#eaf0f5",
            "Given",
        ),

        (
            "#d9f1e9",
            "Inferred (underlined)",
        ),
    ]


    if visual:

        entries += [
            (
                "#cce7f8",
                "Supporting cell (S)",
            ),

            (
                "#fff0c9",
                "Reasoning target (T)",
            ),
        ]


    else:

        entries += [
            (
                "#ffffff",
                "Empty",
            )
        ]


    html(
        f'<div class="legend'
        f'{" vertical" if vertical else ""}'
        f'">'
        +
        "".join(
            (
                '<span>'
                f'<i class="swatch" '
                f'style="background:{color}">'
                '</i>'
                f'{label}'
                '</span>'
            )

            for color, label
            in entries
        )
        +
        '</div>'
    )


# =========================================================
# Session-state helpers
# =========================================================

def clear_query():

    st.session_state.pop(
        "query_record",
        None,
    )

    st.session_state[
        "proof_step"
    ] = 1

    st.session_state[
        "show_full_trace"
    ] = False


def change_puzzle():

    clear_query()
    clear_solve()


def clear_solve():

    st.session_state.pop("solve_error", None)
    st.session_state.pop(
        "solve_record",
        None,
    )


def move_step(
    delta,
    total,
):

    st.session_state[
        "proof_step"
    ] = max(
        1,
        min(
            total,
            st.session_state.get(
                "proof_step",
                1,
            )
            + delta,
        ),
    )


def toggle_trace():

    st.session_state[
        "show_full_trace"
    ] = (
        not st.session_state.get(
            "show_full_trace",
            False,
        )
    )


# =========================================================
# Verdict UI
# =========================================================

def render_verdict(
    record,
):

    result = record[
        "result"
    ]

    r, c, value = record[
        "query"
    ]


    title = (
        "Entailed by the knowledge base"

        if result

        else (
            "Not entailed by "
            "the knowledge base"
        )
    )


    explanation = (
        (
            f"The proof establishes "
            f"cell ({r}, {c}) = {value}."
        )

        if result

        else (
            "No proof was found under the "
            "current rules. This does not by "
            "itself prove the opposite proposition."
        )
    )


    html(
        f'<div '
        f'class="verdict'
        f'{"" if result else " false"}" '
        f'role="status" '
        f'aria-live="polite">'

        f'<div class="verdict-bool">'
        f'{str(result)}'
        f'</div>'

        f'<div>'

        f'<div class="verdict-title">'
        f'{title}'
        f'</div>'

        f'<div class="verdict-desc">'
        f'{explanation}'
        f'</div>'

        f'</div>'

        f'</div>'
    )


# =========================================================
# Export full proof
# =========================================================

def proof_text(
    trace,
):

    lines = []


    for i, step in enumerate(
        trace,
        1,
    ):

        details = visual_details(
            step,
            trace,
        )


        lines.extend(
            [
                (
                    f"Step {i} · "
                    f"{details['kind']}"
                ),

                explain_step(
                    step,
                    trace,
                ),
            ]
        )


        if step.get(
            "premises"
        ):

            lines.append(
                "Premises: "
                +
                "; ".join(
                    describe_atom(
                        p
                    )

                    for p
                    in step[
                        "premises"
                    ]
                )
            )


        lines.extend(
            [
                (
                    "Conclusion: "
                    + describe_atom(
                        step[
                            "conclusion"
                        ]
                    )
                ),

                "",
            ]
        )


    return "\n".join(
        lines
    )


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.markdown(
        "## Puzzle settings"
    )


    puzzle_index = st.selectbox(
        "Puzzle",

        range(
            len(
                puzzles
            )
        ),

        key="puzzle_index",

        format_func=lambda i:
            (
                f"Puzzle {i + 1} · "
                f"{len(puzzles[i]['givens'])} givens"
            ),

        on_change=change_puzzle,
    )


    algorithm = st.selectbox(
        "Full-grid method",

        [
            "Forward Chaining",
            "Backward Chaining",
        ],

        key="algorithm",

        on_change=clear_solve,
    )


    st.caption(
        "This method applies to the full-grid "
        "solver. Cell queries and Tutor Mode "
        "use backward chaining."
    )


    st.divider()


    st.markdown(
        "### Read the board"
    )


    board_legend(
        vertical=True
    )


    st.caption(
        "Rows run from top to bottom. "
        "Columns run from left to right."
    )


    st.divider()


    st.caption(
        "Knowledge Representation "
        "& Logical Inference"
    )


# =========================================================
# Current puzzle
# =========================================================

givens = convert_cells(
    puzzles[
        puzzle_index
    ][
        "givens"
    ]
)


# =========================================================
# Hero
# =========================================================

html(
    '<header class="hero">'

    '<h1>'
    'Sudoku Logic Solver'
    '</h1>'

    '<p>'
    'Solve the grid. '
    'Test a claim. '
    'Follow the proof.'
    '</p>'

    '<div class="hero-meta">'

    f'<span>'
    f'Puzzle {puzzle_index + 1}'
    f'</span>'

    f'<span>'
    f'{len(givens)} givens'
    f'</span>'

    f'<span>'
    f'{n} × {n} grid · '
    f'{box_h} × {box_w} boxes'
    f'</span>'

    '</div>'

    '</header>'
)


# =========================================================
# Main tabs
# =========================================================

solve_tab, query_tab, tutor_tab = (
    st.tabs(
        [
            "Puzzle & Solve",
            "Cell Query",
            "Tutor Mode",
        ]
    )
)


# =========================================================
# Puzzle & Solve
# =========================================================

with solve_tab:

    section(
        "Solve the complete Sudoku",

        (
            "Derive the grid from the "
            "original givens using logical inference."
        ),
    )


    board_col, control_col = (
        st.columns(
            [
                1.25,
                1,
            ],

            gap="large",
        )
    )


    record = st.session_state.get(
        "solve_record"
    )


    if (
        record
        and (
            record["puzzle"],
            record["algorithm"],
        )
        != (
            puzzle_index,
            algorithm,
        )
    ):

        record = None


    with board_col:

        html(
            board_html(
                (
                    record["grid"]

                    if record

                    else givens
                ),
                givens,
            )
        )


        board_legend()


    with control_col:

        with st.container(
            border=True,
            key="solver_panel",
        ):

            html(
                '<div class="meta-label">'
                'Inference method'
                '</div>'

                f'<div class="method-name">'
                f'{escape(algorithm)}'
                f'</div>'
            )


            st.caption(
                "Apply Sudoku constraints until the "
                "rules have established every value "
                "they can prove."
            )


            if st.button(
                "Solve puzzle",

                type="primary",

                use_container_width=True,

                key="solve_button",
            ):

                clear_solve()


                try:

                    with st.spinner(
                        f"Solving with "
                        f"{algorithm.lower()}…"
                    ):

                        start = (
                            time.perf_counter()
                        )


                        solver = (
                            solve_full_grid_fc

                            if (
                                algorithm
                                == "Forward Chaining"
                            )

                            else solve_full_grid_bc
                        )


                        solved = solver(
                            n,
                            box_h,
                            box_w,
                            dict(givens),
                        )


                        elapsed = (
                            time.perf_counter()
                            - start
                        )


                    st.session_state[
                        "solve_record"
                    ] = dict(
                        puzzle=
                            puzzle_index,

                        algorithm=
                            algorithm,

                        grid=
                            solved,

                        elapsed=
                            elapsed,
                    )


                except Exception as exc:

                    st.session_state["solve_error"] = (
                        "The solver could not finish. No result from this attempt "
                        f"is available. Details: {exc}"
                    )

                # Rebuild both columns after success or failure; never leave an
                # earlier grid or elapsed time visible after a failed retry.
                st.rerun()

            if st.session_state.get("solve_error"):
                st.error(st.session_state["solve_error"])


            if record:

                count = len(
                    record["grid"]
                )


                html(
                    '<div class="stat-pair">'

                    '<div>'

                    f'<strong>'
                    f'{count}/{n*n}'
                    f'</strong>'

                    '<span>'
                    'Cells established'
                    '</span>'

                    '</div>'

                    '<div>'

                    f'<strong>'
                    f'{record["elapsed"]:.3f} s'
                    f'</strong>'

                    '<span>'
                    'Solve time'
                    '</span>'

                    '</div>'

                    '</div>'
                )


                note(
                    (
                        "The grid is fully solved."

                        if count == n * n

                        else (
                            "The current rules reached "
                            "a partial solution. "
                            "Unresolved cells remain empty."
                        )
                    )
                )


                st.button(
                    "Reset board",

                    on_click=
                        clear_solve,

                    use_container_width=
                        True,
                )


            else:

                st.caption(
                    f"Start with {len(givens)} given cells. "
                    f"Inferred values are teal and underlined."
                )


        note(
            "Explore a single claim in Cell Query, "
            "then open Tutor Mode to see why it follows."
        )


# =========================================================
# Cell Query
# =========================================================

with query_tab:

    section(
        "Test a cell proposition",

        (
            "Choose a row, column and value. "
            "Backward chaining returns True or False."
        ),
    )


    input_col, query_board_col = (
        st.columns(
            [
                1,
                1,
            ],

            gap="large",
        )
    )


    with input_col:

        qcols = st.columns(
            3
        )


        coords = []


        for (
            col,
            label,
            key,
        ) in zip(
            qcols,

            (
                "Row",
                "Column",
                "Value",
            ),

            (
                "query_row",
                "query_col",
                "query_value",
            ),
        ):

            with col:

                coords.append(
                    int(
                        st.number_input(
                            label,

                            min_value=1,

                            max_value=n,

                            value=1,

                            step=1,

                            key=key,

                            on_change=
                                clear_query,
                        )
                    )
                )


        qr, qc, qv = (
            coords
        )


        html(
            '<div class="query-claim">'

            '<div class="meta-label">'
            'Proposition being tested'
            '</div>'

            '<strong>'

            f'Cell ({qr}, {qc}) '
            f'= {qv}'

            '</strong>'

            '</div>'
        )


        if st.button(
            "Check entailment",

            type="primary",

            use_container_width=True,

            key="query_button",
        ):

            clear_query()


            try:

                with st.spinner(
                    "Checking the proposition…"
                ):

                    kb = (
                        build_definite_kb(
                            n,
                            box_h,
                            box_w,
                            dict(givens),
                        )
                    )


                    query = atom(
                        "Is",
                        qr,
                        qc,
                        qv,
                    )


                    trace = []


                    start = (
                        time.perf_counter()
                    )


                    result = (
                        pl_bc_entails(
                            kb,
                            query,
                            trace=trace,
                        )
                    )


                    elapsed = (
                        time.perf_counter()
                        - start
                    )


                st.session_state[
                    "query_record"
                ] = dict(
                    puzzle=
                        puzzle_index,

                    query=
                        tuple(coords),

                    result=
                        bool(result),

                    trace=
                        trace,

                    elapsed=
                        elapsed,
                )


            except Exception as exc:

                st.error(
                    "The query could not be completed: "
                    f"{exc}"
                )


        query_record = (
            st.session_state.get(
                "query_record"
            )
        )


        if (
            query_record
            and (
                query_record[
                    "puzzle"
                ]
                != puzzle_index

                or query_record[
                    "query"
                ]
                != tuple(coords)
            )
        ):

            query_record = None


        if query_record:

            render_verdict(
                query_record
            )


            st.caption(
                "Backward chaining · "
                f"{query_record['elapsed']:.3f} s · "
                "query time excludes KB construction"
            )


            if query_record[
                "result"
            ]:

                note(
                    f"{len(query_record['trace'])} "
                    f"proof steps recorded. "
                    f"Open Tutor Mode to follow "
                    f"the reasoning."
                )


        else:

            st.caption(
                "The highlighted cell is your query target. "
                "Its value is not assumed before the check."
            )


    with query_board_col:

        html(
            board_html(
                givens,
                givens,
                query_target=
                    (
                        qr,
                        qc,
                    ),
            )
        )


        st.caption(
            f"Q marks the query target: "
            f"row {qr}, column {qc} · "
            f"Original givens"
        )


# =========================================================
# Tutor Mode
# =========================================================

with tutor_tab:

    section(
        "Understand the proof",

        (
            "Read the key reasons, then explore "
            "the proof one step at a time."
        ),
    )


    if query_record is None:

        note(
            "Start in Cell Query: enter a row, "
            "column and value, then select "
            "Check entailment."
        )


    else:

        qr, qc, qv = (
            query_record[
                "query"
            ]
        )


        trace = (
            query_record[
                "trace"
            ]
        )


        render_verdict(
            query_record
        )


        html(
            '<div class="proof-summary">'

            f'<span class="pill">'
            f'Cell ({qr}, {qc}) = {qv}'
            f'</span>'

            '<span>'
            'Backward chaining'
            '</span>'

            f'<span>'
            f'{len(trace)} recorded steps'
            f'</span>'

            '</div>'
        )


        if not query_record[
            "result"
        ]:

            note(
                "This query has no successful proof trace. "
                "Try a different proposition in Cell Query."
            )


        elif not trace:

            note(
                "The solver returned True but supplied "
                "no proof steps. A trace-enabled solver "
                "is required for Tutor Mode."
            )


        else:

            rows, conclusion = (
                key_reasoning(
                    trace,
                    atom(
                        "Is",
                        qr,
                        qc,
                        qv,
                    ),
                )
            )


            html(
                '<h3 class="subhead key-reasoning-head">'
                'Key Reasoning'
                '</h3>'
            )


            html(
                '<p class="key-reasoning-caption">'
                'Each row explains a direct premise '
                'of the final inference. '
                '× marks a value ruled out.'
                '</p>'
            )


            if rows:

                pieces = [
                    '<div class="reasoning-list">'
                ]


                for row in rows:

                    cls = (
                        "source-given"

                        if (
                            row["source"]
                            == "Given"
                        )

                        else (
                            "source-derived"
                        )
                    )


                    pieces.append(
                        '<div class="reason-row">'

                        f'<div class="value-badge">'
                        f'×{row["value"]}'
                        f'</div>'

                        '<div>'

                        f'<span '
                        f'class="source-badge {cls}">'
                        f'{row["source"]}'
                        f'</span>'

                        '</div>'

                        f'<div class="reason-text">'
                        f'{escape(row["reason"])}'
                        f'</div>'

                        '</div>'
                    )


                html(
                    "".join(
                        pieces
                    )
                    +
                    '</div>'
                )


            else:

                note(
                    "This proposition is an original "
                    "given; no elimination rows are needed."
                )


            html(
                '<div class="conclusion">'

                '<h3>'
                'Final Inference'
                '</h3>'

                f'<p>'
                f'{escape(conclusion)}'
                f'</p>'

                '</div>'
            )


            st.divider()


            section(
                "Visual Reasoning",

                (
                    "S marks the supporting cell; "
                    "T marks the current reasoning target."
                ),
            )


            total = len(
                trace
            )


            if (
                "proof_step"
                not in st.session_state
            ):

                st.session_state[
                    "proof_step"
                ] = 1


            st.session_state[
                "proof_step"
            ] = max(
                1,
                min(
                    total,
                    st.session_state[
                        "proof_step"
                    ],
                ),
            )


            prev, step_col, nxt = (
                st.columns(
                    [
                        .9,
                        .48,
                        1,
                    ]
                )
            )


            with prev:

                st.button(
                    "← Previous",

                    key=
                        "previous_step",

                    use_container_width=
                        True,

                    disabled=(
                        st.session_state[
                            "proof_step"
                        ]
                        == 1
                    ),

                    on_click=
                        move_step,

                    args=(
                        -1,
                        total,
                    ),
                )


            with step_col:

                selected = int(
                    st.number_input(
                        "Proof step",

                        min_value=1,

                        max_value=
                            total,

                        step=1,

                        key=
                            "proof_step",

                        label_visibility=
                            "collapsed",
                    )
                )


            with nxt:

                st.button(
                    "Next →",

                    key=
                        "next_step",

                    type=
                        "primary",

                    use_container_width=
                        True,

                    disabled=(
                        selected
                        == total
                    ),

                    on_click=
                        move_step,

                    args=(
                        1,
                        total,
                    ),
                )


            html(
                f'<div '
                f'class="progress-track" '
                f'role="progressbar" '
                f'aria-label="Proof progress" '
                f'aria-valuemin="1" '
                f'aria-valuemax="{total}" '
                f'aria-valuenow="{selected}">'

                f'<div '
                f'class="progress-fill" '
                f'style="width:'
                f'{selected / total * 100:.2f}%">'
                f'</div>'

                f'</div>'
            )


            current = trace[
                selected - 1
            ]


            details = visual_details(
                current,
                trace,
            )


            html(
                '<div class="proof-summary">'

                f'<span class="pill teal">'
                f'Step {selected} of {total}'
                f'</span>'

                f'<span>'
                f'{escape(details["kind"])}'
                f'</span>'

                '</div>'
            )


            visual_col, explanation_col = (
                st.columns(
                    [
                        1.1,
                        1,
                    ],

                    gap="large",
                )
            )


            with visual_col:

                html(
                    board_html(
                        board_state(
                            givens,
                            trace,
                            selected,
                        ),

                        givens,

                        source=
                            details[
                                "source"
                            ],

                        target=
                            details[
                                "target"
                            ],

                        target_note=
                            details[
                                "note"
                            ],
                    )
                )


                board_legend(
                    visual=True
                )


                st.caption(
                    "×value means elimination. "
                    "The target cell stays unfilled "
                    "until a value is proved."
                )


            with explanation_col:

                card = (
                    '<div class="step-card">'

                    f'<h4>'
                    f'{escape(details["kind"])}'
                    f'</h4>'
                )


                for label, value in (
                    (
                        "Supporting information",
                        details[
                            "support"
                        ],
                    ),

                    (
                        "Rule applied",
                        details[
                            "rule"
                        ],
                    ),

                    (
                        "Inference",
                        details[
                            "result"
                        ],
                    ),
                ):

                    card += (
                        '<div class="step-field">'

                        f'<div class="meta-label">'
                        f'{label}'
                        f'</div>'

                        f'<strong>'
                        f'{escape(value)}'
                        f'</strong>'

                        '</div>'
                    )


                html(
                    card
                    + '</div>'
                )


                html(
                    '<div class="step-explanation">'

                    f'{escape(explain_step(current, trace))}'

                    '</div>'
                )


            st.divider()


            showing = (
                st.session_state.get(
                    "show_full_trace",
                    False,
                )
            )


            trace_col, export_col = (
                st.columns(
                    [
                        2,
                        1,
                    ]
                )
            )


            with trace_col:

                st.button(
                    (
                        "Hide"

                        if showing

                        else "Show"
                    )
                    +
                    f" complete proof trace · "
                    f"{total} steps",

                    key=
                        "toggle_full_trace",

                    on_click=
                        toggle_trace,

                    use_container_width=
                        True,
                )


            with export_col:

                st.download_button(
                    "Download proof",

                    proof_text(
                        trace
                    ),

                    file_name=(
                        f"puzzle_"
                        f"{puzzle_index + 1}"
                        f"_proof_"
                        f"{qr}_{qc}_{qv}"
                        f".txt"
                    ),

                    mime=
                        "text/plain",

                    use_container_width=
                        True,
                )


            if showing:

                st.caption(
                    "Every recorded step is preserved "
                    "in dependency order. Expand any "
                    "step for its premises and conclusion."
                )


                for i, step in enumerate(
                    trace,
                    1,
                ):

                    info = visual_details(
                        step,
                        trace,
                    )


                    with st.expander(
                        f"Step {i} · "
                        f"{info['kind']} · "
                        f"{describe_atom(step['conclusion'])}"
                    ):

                        st.write(
                            explain_step(
                                step,
                                trace,
                            )
                        )


                        st.markdown(
                            "**Rule:** "
                            + info[
                                "rule"
                            ]
                        )


                        if step.get(
                            "premises"
                        ):

                            st.markdown(
                                "**Premises**"
                            )


                            for premise in step[
                                "premises"
                            ]:

                                st.write(
                                    "• "
                                    + describe_atom(
                                        premise
                                    )
                                )


                        st.markdown(
                            "**Conclusion:** "
                            + describe_atom(
                                step[
                                    "conclusion"
                                ]
                            )
                        )


# =========================================================
# Footer
# =========================================================

html(
    '<div class="footer-note">'
    'Sudoku Logic Solver · '
    'Built on propositional rules '
    'and recorded proofs.'
    '</div>'
)
