# Rules for AI agents working in this repo

**Team (Onyx):**

| Who | Role here | Commit author | Branch prefix | Sign-off |
|---|---|---|---|---|
| Gilfoyle (OpenClaw) | Engineer: core service, links | `Gilfoyle (OpenClaw)` | `gilfoyle/` | `— Gilfoyle` |
| Monica (Hermes Agent) | Engineer: adapters, mock devices, web UI | `Monica (Hermes Agent)` | `monica/` | `— Monica` |
| Dinesh (Hermes Agent) | Engineer: image prep, web UI | `Dinesh (Hermes Agent)` | `dinesh/` | `— Dinesh` |
| Winston (Hermes Agent) | QA: tests every PR after peer review; regression tests under `tests/` only | `Winston (Hermes Agent)` | `winston/` | `— Winston` |
| Jared | Product Owner: issues and acceptance criteria; no code | n/a | n/a | `— Jared` |
| Richard (Claude) | CTO: final review, merge, deploys to the Pi | n/a | `claude/` | n/a |

**Review order:** peer review by another engineer (findings grouped CRITICAL / WARNING / INFO), then Winston's QA report (`QA: PASS` / `QA: FAIL`), then Richard's final review and merge. Move the PR's stage label as each step finishes: `needs-peer-review` → `needs-qa` → `ready-for-cto` (or `changes-requested`). Peer reviewers here: Gilfoyle ↔ Monica; Dinesh's PRs go to Monica. Never push to a teammate's branch.

Read `docs/ARCHITECTURE.md` before starting any task. Follow these rules exactly.

## Project
golden-gate runs on a Raspberry Pi 3 (Debian 13, **Python 3.13**) and exposes devices that only offer their own Wi-Fi AP or Bluetooth (first: an Instax SHARE SP-2 printer) as a web UI and HTTP API on the lab LAN.
- Code lives in the `golden_gate/` package: `core/` (registry, job queue, link arbitration, HTTP API), `adapters/<kind>/` (one package per device, each with a mock device), `links/` (`wifi_ap`, `ble`). Web UI static files go in `golden_gate/ui/`. Pi setup goes in `deploy/`.
- **The adapter contract is `golden_gate/core/adapter.py`.** Core talks to devices only through it. Don't change it in a feature PR; if it needs to change, open a separate small PR and say why.
- Commands: `pip install -e ".[dev]"` then `python -m pytest -q` (all tests) · `python -m pytest tests/<file>.py` (one file).

## Workflow
- One git worktree per task, started from an up-to-date `main`. Do only the task you were given; minimal changes, no unrelated refactors.
- Run the tests after every change and fix failures before moving on. Add or update tests for every behaviour you change.
- If unsure between approaches, pick the simpler one and explain the alternative in the PR description.

## Commits, branches and PRs
- Conventional prefixes `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`; subject under ~50 characters.
- Never push to `main` (it's protected). One branch per task: `<your-prefix>/<task-name>`. PR description says `Closes #N` and includes:
  1. **What** changed and **why**
  2. **How you tested it**: commands and their summary lines
  3. **Self-review**: CRITICAL / WARNING / INFO, ending "X critical, Y warnings, Z info". Fix all CRITICAL first. **A violation of any rule in this file is always CRITICAL.**
  4. **Uncertainties**
- Keep PRs small: one issue per PR.

## Code rules
- **Allowed dependencies only:** `aiohttp` (HTTP server), `pillow` (images), `bleak` (BLE, optional extra), `pytest` + `pytest-asyncio` (dev). Everything else is the standard library (`asyncio`, `tomllib`, `dataclasses`, `struct`, ...). Adding any other package is CRITICAL.
- **Async everywhere** in core and adapters (asyncio). No threads unless wrapping a blocking library call with `asyncio.to_thread`.
- **Tests never touch the network, radios or hardware.** Use the mock devices (in-process asyncio servers bound to 127.0.0.1 on a random port) and fakes for `links/`. No `nmcli`, D-Bus or real sockets to devices in tests.
- **Secrets** (device PINs, pairing keys) come only from `/etc/golden-gate/secrets.env` (via config) or test fixtures with fake values. Never hard-code a real PIN, never log a secret, never return one from the API. The Instax default PIN is a config default, not a literal in adapter code.
- **Consumables:** any action that uses film or changes device settings has `confirm=True`. Nothing in code, tests or CI may send a print to real hardware. The first real print is Christopher's.
- **Network safety:** `wlan0` never gets a default route; device networks are never bridged or routed to the LAN. Link code must pass `never-default`/equivalent explicitly.
- **Fixtures:** protocol fixtures must come from real device captures (Richard records them on the Pi and commits them under `tests/fixtures/`) or be built from the protocol spec and labelled as such in the test. Never invent device responses and present them as recorded.
- **Third-party protocol code:** the Instax packet format follows `instax-api` by James Sutton (MIT). Write our own client; if you adapt any of its code, keep its MIT copyright notice in that file and credit it in `README.md`. Don't depend on the PyPI package (broken on Python 3.13, and it logs the PIN).
- **Uploads:** accept only images, cap size (10 MB), store under the configured upload dir with generated names (never the client's filename in a path).
- **Report only test results you just observed.** Before reporting counts, push, then run the tests on a clean checkout of the pushed branch and paste the summary line.
- Style: PEP 8, type hints on public functions, 4-space indentation.

## Out of scope (don't modify unless the issue explicitly asks)
- `.github/`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `.gitignore`, `golden_gate/core/adapter.py` (see above), `pyproject.toml` dependencies.

## Safety
- Never commit secrets, `.env` or `secrets.env` files.
- Agents can't reach the Pi or the LAN; Richard deploys. Don't write code that assumes you tested on hardware.
- If an issue is ambiguous or conflicts with `docs/ARCHITECTURE.md`, the architecture wins; say so in the PR and tag Jared.
