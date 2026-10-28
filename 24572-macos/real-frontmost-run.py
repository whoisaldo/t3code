# #24572 lookup rows with REAL frontmost apps (activated by real clicks), unmodified production scripts,
# and the production capture command (screencapture -l <id> -o -x -t png) on the resolved window.
import json, os, signal, subprocess, sys, time
W = "/tmp/trifecta-desktop-work"; R = f"{W}/run24572"
pid = {n: int(open(f"{W}/pid2-{n}").read()) for n in "ABCDE"}
CLICK = {"A": (215, 548), "B": (462, 671), "C": (1150, 330), "D": (1050, 640), "E": (1708, 671)}
def osinput(*a): subprocess.run([f"{W}/input/osinput", *map(str, a)], check=True)
def lookup(tag):
    out = f"{R}/{tag}.trace"
    if os.path.exists(out): os.remove(out)
    lbl = f"com.whoisaldo.trifecta-desktop.lookup"
    subprocess.run([f"{W}/job.sh", "lookup", f"{R}/aqua-lookup.sh", out], check=True, capture_output=True)
    for _ in range(60):
        if os.path.exists(out): break
        time.sleep(0.25)
    subprocess.run(["launchctl", "bootout", f"gui/501/{lbl}"], capture_output=True)
    txt = open(out).read()
    sec = {}; cur = None
    for line in txt.splitlines():
        if line.startswith("## "): cur = line[3:]; sec[cur] = ""; continue
        if cur: sec[cur] += line
    probe = json.loads(sec["probe"])
    return probe, {v: (json.loads(sec[v]) if sec[v].strip() else None) for v in ("before", "after")}
def capture(tag, wid):
    png = f"{R}/{tag}-capture-window-{wid}.png"
    r = subprocess.run(["/usr/sbin/screencapture", "-l", str(wid), "-o", "-x", "-t", "png", png], capture_output=True, text=True)
    ok = r.returncode == 0 and os.path.exists(png) and open(png, "rb").read(8) == b"\x89PNG\r\n\x1a\n"
    return {"rc": r.returncode, "stderr": r.stderr.strip(), "png": os.path.basename(png) if ok else None}
# After D is minimized it stays minimized; it runs last.
cases = [
  ("M2-valid-pid-A-with-same-name-B-in-front", "A", "B"),
  ("M2-valid-pid-B", "B", None),
  ("M4-floating-only-app-C", "C", None),
  ("M4-app-E-floating-above-its-normal-window", "E", None),
  ("M4-minimized-only-app-D", "D", None),
]
results = []
attempt = int(sys.argv[1])
for name, target, raise_after in cases:
    osinput("click", *CLICK[target])
    time.sleep(0.8)
    if target == "D": os.kill(pid["D"], signal.SIGUSR2); time.sleep(1.2)  # minimize D's only window after activating it
    if raise_after: os.kill(pid[raise_after], signal.SIGUSR1); time.sleep(0.6)
    probe, res = lookup(f"{name}-attempt{attempt}")
    fixture_rows = [w for w in probe["windows"] if w["ownerName"] == "TrifectaProbeWin"]
    row = {"case": name, "attempt": attempt, "frontmost": probe["frontmost"],
           "fixtureCgOrder": [{k: w[k] for k in ("i", "id", "layer", "ownerPid")} for w in fixture_rows]}
    for v in ("before", "after"):
        r = res[v]
        row[v] = None if r is None else {"id": r["id"], "ownerPid": r["owner"]["processId"], "ownerName": r["owner"]["name"]}
        if r is not None and attempt == 1: row[v]["capture"] = capture(f"{name}-{v}", r["id"])
    results.append(row)
    print(json.dumps({k: row[k] for k in ("case", "before", "after")}), "front:", probe["frontmost"]["pid"], probe["frontmost"]["name"], flush=True)
json.dump({"pids": pid, "results": results}, open(f"{R}/results-attempt{attempt}.json", "w"), indent=1)
