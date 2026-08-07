# Contributing to rtc-work

`rtc-work` is the demand-side client for the RustChain RIP-302 agent job
market. It is intentionally small: pure stdlib, one file of commands, one
pure matching function, one tolerant TOML parser. Keep it that way.

## Development setup

No build step and no runtime dependencies beyond the Python standard
library. From a checkout:

```bash
git clone https://github.com/Scottcjn/rtc-work.git
cd rtc-work
python3 -m venv .venv && . .venv/bin/activate
```

## Running the tests

The matching/routing logic is pure and tested offline:

```bash
python3 test_match.py
```

`test_match.py` exercises `match_jobs` and `load_manifest` with no network.
Do not add a test that hits a live node — point at a testnet (`--node`) or
mock the `_get`/`_post` helpers.

## What makes a good contribution

- **Stay flat.** Flat routing only — no DAG/recursive subcontracting. This
  is deliberate: recursion worsens cold-start and turns escrow into chaotic
  money-risk. A PR that adds recursive dispatch will not be merged.
- **Money never moves on the worker's side.** `claim` and `deliver` reserve
  and report; escrow is the *poster's* and releases only on the poster's
  `/accept`. Any new command must preserve this.
- **Confirm before network writes.** Mutating commands require explicit
  confirmation unless `--yes`. Read-only commands (`jobs`, `watch`, `rep`)
  never prompt.
- **One pure function for testability.** New filtering or ranking logic
  belongs in a pure, no-network function (like `match_jobs`) so it can be
  unit-tested offline, not inside a `cmd_*` handler.

Documentation improvements — docstrings, README clarity, examples — are
always welcome.

## Pull requests

- One logical change per PR; a docs-only PR should not also refactor code.
- Match the existing style (no auto-formatter reflow unless the whole file
  is touched).
- Make sure `python3 test_match.py` passes before requesting review.

## Reporting issues

If the live node changes an endpoint shape, open an issue with the new
shape and the endpoint path so the client can be re-pinned. The endpoints
are deliberately pinned to `rip302_agent_economy.py` rather than discovered.
