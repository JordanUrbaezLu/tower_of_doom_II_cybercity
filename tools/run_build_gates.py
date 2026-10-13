"""Run EVERY gate line of tools/build_map.ps1 against the REPO, without building (the "TREE SAFE" proof).

Why it exists (2026-10-03): build gates read the repo after the sync, and a peer's harness that evaluates a
shipping module with callee stubs (test_retriever_native.js, teleporter/test_states.js) dies on any new
namespaced call it has no stub for. Two FULL builds died that day ~10 minutes in on such lines, after each
landing session had run only "its own" gates. Run this after landing and before saying TREE SAFE.

It parses the forms build_map.ps1 uses:
    [$x =] & node|python [-B] (Join-Path $PSScriptRoot "<gate>") <args> [2>&1 | Out-String]
    @('node'|'python'[, '-B'], (Join-Path $PSScriptRoot '<gate>'), '--check')
    & node $GeomKey selftest
Lines whose arguments are $variables (the post-link ledgers, the navmesh mesh, the size-pass verify) cannot run
outside a build: they are LISTED at the top of the output as "not run", never silently dropped.
It is read-only, wired into nothing, and never touches the deployed tree. A gate that is red on the repo is
red for the next build too, whoever owns it: tell its owner.

usage: python tools/run_build_gates.py [substring filter]      (~7 minutes for the whole list)
"""
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
src = open(os.path.join("tools", "build_map.ps1"), encoding="utf-8", errors="replace").read()

cmds = []
not_run = []
# 2026-10-03 17:30 (haven v4): the first version matched only lines that START with `&`, so every captured-output
# gate (`$x = & node (...) 2>&1 | Out-String`: arity, hints, assets, geometry, crown convex, the Lua harness list and
# ~17 more) and the `@('python', '-B', ...)` fx list were never run, and a "TREE SAFE" from it covered 87 of ~110
# lines. Both forms are read now; what still cannot run outside a build (a `$variable` argument) is LISTED, not hidden.
for m in re.finditer(r'^\s*(?:\$\w+\s*=\s*)?&\s+(node|python)(?:\s+-B)?\s+\(Join-Path \$PSScriptRoot ["\']([^"\']+)["\']\)([^\n]*)$', src, re.M):
    exe, rel, rest = m.group(1), m.group(2).replace("\\", "/"), m.group(3)
    rest = re.sub(r'\s*2>&1(\s*\|\s*Out-String)?\s*$', '', rest)
    if "$" in rest or "|" in rest:
        not_run.append("tools/" + rel + rest)
        continue
    args = [x for t in re.findall(r"""'([^']+)'|"([^"]+)"|(--?[\w-]+)""", rest) for x in t if x]
    cmds.append([exe] + (["-B"] if exe == "python" else []) + ["tools/" + rel] + args)
for m in re.finditer(r"@\('(node|python)'(?:, '-B')?, \(Join-Path \$PSScriptRoot '([^']+)'\)((?:, '[^']*')*)\)", src):
    exe, rel, rest = m.group(1), m.group(2).replace("\\", "/"), m.group(3)
    cmds.append([exe] + (["-B"] if exe == "python" else []) + ["tools/" + rel] + re.findall(r"'([^']*)'", rest))
if re.search(r"&\s+node\s+\$GeomKey\s+selftest", src):
    cmds.append(["node", "tools/geom_key.js", "selftest"])     # called through $GeomKey, a pre-build gate

seen, uniq = set(), []
for c in cmds:
    k = " ".join(c)
    if k not in seen and (len(sys.argv) < 2 or sys.argv[1] in k):
        seen.add(k)
        uniq.append(c)
print("gates:", len(uniq), "| not runnable outside a build (a $variable argument):", len(not_run))
for line in not_run:
    print("   not run:", line.strip()[:150])

bad = []
t_all = time.time()
for c in uniq:
    t0 = time.time()
    try:
        r = subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
        rc = r.returncode
        tail = (r.stdout + r.stderr).strip().split("\n")[-1][:170]
    except subprocess.TimeoutExpired:
        rc, tail = -1, "TIMEOUT"
    if rc != 0:
        bad.append((c, tail))
    print("%s %5.1fs %s" % ("OK  " if rc == 0 else "FAIL", time.time() - t0, " ".join(c)[:110])
          + ("" if rc == 0 else "\n        " + tail))

print("\nTOTAL %.0fs, failures: %d" % (time.time() - t_all, len(bad)))
for c, tail in bad:
    print("  FAIL", " ".join(c))
    print("       ", tail)
sys.exit(1 if bad else 0)
