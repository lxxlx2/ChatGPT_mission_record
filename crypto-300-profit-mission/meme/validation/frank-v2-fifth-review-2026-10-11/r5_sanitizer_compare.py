import importlib.util, json, glob, sys
from collections import Counter
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
base = load("base", "/home/claude/r5base/crypto-300-profit-mission/local-agent/mission_agent/mission_control/evidence_sync.py")
pinned = load("pinned", "/home/claude/r5wt/crypto-300-profit-mission/local-agent/mission_agent/mission_control/evidence_sync.py")
fixed = load("fixed", "/home/claude/r5fix/crypto-300-profit-mission/local-agent/mission_agent/mission_control/evidence_sync.py")
files = sorted(glob.glob(sys.argv[1] + "/**/*.json", recursive=True))
strings = []
def walk(o, p):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(k, str) and not base.BANNED.search(k): walk(v, p + "." + k)
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, f"{p}[{i}]")
    elif isinstance(o, str): strings.append(o)
for f in files: walk(json.load(open(f)), "")
probes = ["file:///Users/alice/x.db", "profile: ok", "reconfile: 3", "file transfer note", "deposit ~ approx 3",
          "https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/frank-wallet-v2-d0-readonly-20261011/x.json",
          "https://solana-mainnet.g.alchemy.com/v2/FAKE_TEST_KEY_1234567890abcdef", "contact ops.person@example.com now",
          "https://api.example.com/abc123def456", "https://api.example.com/v1/token/abc", "https://github.com/x/y/private/notes",
          "https://solscan.io/tx/5wqKv5YuurRKUaJAK5fZtFrNg6GocVZuTTiAPWYrYDaswyUArwAZurpbZFU6WBjHp5z5Bt5bPCkLNKVQHfS6yigx"]
strings += probes
d_fixed_base = [s for s in strings if fixed.safe(s) != base.safe(s)]
d_fixed_pinned = [s for s in strings if fixed.safe(s) != pinned.safe(s)]
d_pinned_base = [s for s in strings if pinned.safe(s) != base.safe(s)]
print(f"strings={len(strings)} files={len(files)}")
print("fixed vs base(70745a5c) differences:", len(d_fixed_base), [s[:60] for s in d_fixed_base])
print("fixed vs pinned(2309beab) differences:", len(d_fixed_pinned), [s[:60] for s in d_fixed_pinned])
print("pinned vs base differences (documents the N2/N3 regressions):", len(d_pinned_base))
