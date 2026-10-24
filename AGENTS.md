# Four in a Row AI Project

## Project purpose

Build a clear, testable Connect Four AI project for a university presentation and
a short live demo. The application will become a playable strategy coach with
visible AI reasoning.

## Source specifications

Read `AGENTS/rules2`, `AGENTS/rules3`, `docs/overall-plan`, and
`docs/frontend` before changing a relevant layer. The `AGENTS/` files contain
the detailed architecture, algorithm, and layer requirements for this initial
project version.

## Non-negotiable workflow

1. Work on one requested layer only; do not begin the next layer early.
2. State a short 3–6 line plan before writing code.
3. Preserve documented public interfaces and keep every agent interchangeable
   through `choose_move(board) -> column`.
4. Write and run tests with every feature. Report real command output and never
   weaken tests simply to make them pass.
5. Keep random behavior deterministic with an explicit `random.Random(seed)`.
6. A search agent must restore the supplied board exactly before returning.
7. Use Python 3.10+, pygame, numpy, matplotlib, pandas, pytest, and the
   standard library only. Do not add dependencies without approval.
8. Prefer readable, typed, documented code. Keep constants in `config.py` and
   avoid global mutable state.

## End-of-layer handoff

Finish each requested layer by reporting changed files, the test command and
real results, a short plain-language explanation, limitations or assumptions,
and a suggested Git commit message. Then wait for the next requested layer.
