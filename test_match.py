# SPDX-License-Identifier: MIT
"""Offline tests for rtc-work job matching (the pure routing logic)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rtc_work.__main__ import match_jobs, job_tags

JOBS = [
    {"job_id": "a", "status": "open", "category": "code", "reward_rtc": 5, "tags": "python,cli"},
    {"job_id": "b", "status": "open", "category": "research", "reward_rtc": 2, "tags": ""},
    {"job_id": "c", "status": "claimed", "category": "code", "reward_rtc": 9, "tags": ""},
    {"job_id": "d", "status": "open", "category": "design", "reward_rtc": 1, "tags": "ui"},
    {"job_id": "e", "status": "open", "category": "misc", "reward_rtc": 8, "tags": "python"},
]

# The shapes the live node actually serves. `agent_jobs.tags` is a TEXT column
# written with json.dumps() (default '[]') and returned verbatim by
# GET /agent/jobs, so tags arrive as a JSON *string*, never as a list. The CSV
# fixtures above are hand-written and were the only shape ever exercised.
NODE_JOBS = [
    {"job_id": "n1", "status": "open", "category": "other", "reward_rtc": 5,
     "tags": '["python", "scraping"]'},
    {"job_id": "n2", "status": "open", "category": "other", "reward_rtc": 3, "tags": "[]"},
    {"job_id": "n3", "status": "open", "category": "data", "reward_rtc": 2,
     "tags": '["Python"]'},
]

fails = 0
def check(c, label):
    global fails
    print(("  PASS: " if c else "  FAIL: ") + label)
    if not c: fails += 1

# skill filter by category
r = match_jobs(JOBS, ["code"], 0)
check([j["job_id"] for j in r] == ["a"], "category=code -> only open job a (claimed c excluded)")

# skill match via tags (job e is misc category but tagged python)
r = match_jobs(JOBS, ["python"], 0)
check(set(j["job_id"] for j in r) == {"a", "e"}, "skill=python matches via tags (a tagged python,cli + e tagged python)")

# reward floor
r = match_jobs(JOBS, [], 5)
check(set(j["job_id"] for j in r) == {"a", "e"}, "min_reward=5 keeps a(5),e(8)")

# sorted by reward desc
r = match_jobs(JOBS, [], 0)
check([j["job_id"] for j in r] == ["e", "a", "b", "d"], "sorted reward desc, claimed excluded")

# empty skills matches all open above floor
r = match_jobs(JOBS, [], 0)
check(all(j["status"] == "open" for j in r), "never returns non-open jobs")

# --- the node's real wire shape (json.dumps'd TEXT column) ---

r = match_jobs(NODE_JOBS, ["python"], 0)
check(set(j["job_id"] for j in r) == {"n1", "n3"},
      "skill=python matches node-served JSON tags '[\"python\", ...]'")

r = match_jobs(NODE_JOBS, ["scraping"], 0)
check([j["job_id"] for j in r] == ["n1"], "second tag in a JSON tag list still matches")

r = match_jobs(NODE_JOBS, ["data"], 0)
check([j["job_id"] for j in r] == ["n3"], "category matching unaffected by tag parsing")

r = match_jobs(NODE_JOBS, ["nosuchskill"], 0)
check(r == [], "a skill nobody tagged matches nothing")

check(job_tags({"tags": "[]"}) == set(), "node's empty-tags default '[]' yields no tags")
check(job_tags({"tags": '["python", "scraping"]'}) == {"python", "scraping"}, "JSON string tags")
check(job_tags({"tags": "python, cli"}) == {"python", "cli"}, "legacy CSV tags still parse")
check(job_tags({"tags": ["Python", " CLI "]}) == {"python", "cli"}, "already-decoded list")
check(job_tags({"tags": ""}) == set(), "empty tag string yields no tags")
check(job_tags({}) == set(), "missing tags key yields no tags")
check(job_tags({"tags": None}) == set(), "null tags yields no tags")
check(job_tags({"tags": "[not valid json"}) == set(), "malformed JSON tags degrade to no tags")
check(job_tags({"tags": '["python"]'}) == {"python"}, "single-element JSON tag list")

print("\n" + ("ALL PASS" if fails == 0 else f"{fails} FAILED"))
raise SystemExit(1 if fails else 0)
