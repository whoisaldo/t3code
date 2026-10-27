# #22095 re-verify on 36d4d711b7: scenarios a-d with real HID input and Julius's listeners in the app renderer.
# runner3: the other app is our own fixture window over T3's sidebar, raised with SIGUSR1 (no activation) and clicked;
# aborts if that click did not make the fixture frontmost. Turns off Playwright's CDP focus emulation first, so the
# app renderer sees native focus/blur, and records document.hasFocus() before the click.
# usage: runner3.py <tag> <scenario a|b|c|d> <attempts> [record]
import json, subprocess, sys, time, urllib.request
W = "."  # work directory with input/osinput, perm, repro22095/ and run3/
EV = f"{W}/repro22095/events.jsonl"
TAG, SC, N = sys.argv[1], sys.argv[2], int(sys.argv[3]); RECORD = len(sys.argv) > 4
TARGET = {"a": ("cross-site-iframe", 1289, 665), "b": ("cross-site-iframe", 1289, 665),
          "c": ("top-frame", 1275, 271), "d": ("cross-site-iframe", 1289, 665)}[SC]
OTHER_APP = SC in ("b", "c", "d")
FRAME = {"top-frame": "top", "cross-site-iframe": "cross-site"}[TARGET[0]]
def call(ep, fn="", arg=None):
    req = urllib.request.Request(f"http://127.0.0.1:18796/{ep}", data=json.dumps({"fn": fn, "arg": arg}).encode(), method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=60).read() or b"null")
def locked():
    out = subprocess.run(["ioreg", "-n", "Root", "-d1", "-a"], capture_output=True, text=True).stdout
    i = out.find("CGSSessionScreenIsLocked"); return i >= 0 and "<true/>" in out[i:i + 80]
def osinput(*a):
    if locked(): raise SystemExit("screen locked: no input sent")
    subprocess.run([f"{W}/input/osinput", *map(str, a)], check=True)
def frontmost(): return subprocess.run([f"{W}/perm"], capture_output=True, text=True).stdout.strip().splitlines()[-1]
def shot(name): subprocess.run(["screencapture", "-x", "-R200,120,1440,920", f"{W}/run3/shots/{name}.png"], check=True)
FOCUS = '() => document.activeElement && document.activeElement.tagName'
COMPOSER = '() => document.querySelector("[contenteditable=true][aria-label^=Message]")?.innerText ?? null'
FRONT = '({app, BrowserWindow}) => { const w = BrowserWindow.getAllWindows()[0]; app.focus({steal: true}); w.focus(); return w.isFocused(); }'
MAIN_FOCUSED = '({BrowserWindow}) => BrowserWindow.getAllWindows()[0].isFocused()'
RELOAD = '({webContents}) => { webContents.getAllWebContents().find(x => x.getType() === "webview").reload(); return true; }'
FIELD = 'async ({webContents}, name) => { const wv = webContents.getAllWebContents().find(x => x.getType() === "webview"); const f = wv.mainFrame.framesInSubtree.find(f => (f === wv.mainFrame ? "top" : new URL(f.url).searchParams.get("name")) === name); return await f.executeJavaScript("document.getElementById(\\"field\\").value"); }'
CLEAR = 'async (page) => { const ed = page.locator("[contenteditable=true][aria-label^=Message]").first(); await ed.click(); await page.keyboard.press("Meta+A"); await page.keyboard.press("Backspace"); return true; }'
subprocess.run(["mkdir", "-p", f"{W}/run3/shots"])
NOEMU = 'async (page) => { const s = await page.context().newCDPSession(page); await s.send("Emulation.setFocusEmulationEnabled", {enabled: false}); globalThis.__noEmuSession = s; return true; }'
call("pw", NOEMU)
results = []
for i in range(1, N + 1):
    if locked(): raise SystemExit("screen locked: stopping before attempt %d" % i)
    call("main", RELOAD); time.sleep(2.5)
    call("main", FRONT); time.sleep(0.4)
    call("pw", CLEAR); time.sleep(0.3)
    rec = None
    if RECORD and i == 1:
        rec = subprocess.Popen(["screencapture", "-x", "-V", "12", "-R", "200,120,1440,920", f"{W}/run3/shots/{TAG}-attempt1-recording.mov"]); time.sleep(1.5)
    if OTHER_APP:
        subprocess.run(["kill", "-USR1", open(f"{W}/run3/fixture.pid").read().strip()], check=True); time.sleep(0.4)
        osinput("click", 335, 450); time.sleep(0.8)
        if "TrifectaFixture" not in frontmost(): raise SystemExit("fixture click did not activate the fixture: " + frontmost())
    before = {"appFocus": call("page", FOCUS), "appHasFocus": call("page", "() => document.hasFocus()"), "mainWindowFocused": call("main", MAIN_FOCUSED), "frontmost": frontmost(), "composer": call("page", COMPOSER)}
    if before["appHasFocus"] != (not OTHER_APP): raise SystemExit("unexpected document.hasFocus() before click: " + json.dumps(before))
    if i == 1: shot(f"{TAG}-attempt1-0-before")
    call("console")  # drop anything logged before the click
    t0 = int(time.time() * 1000)
    osinput("click", TARGET[1], TARGET[2]); time.sleep(0.05)
    focus50 = call("page", FOCUS); time.sleep(0.45)
    after_click = {"appFocusAbout50ms": focus50, "mainWindowFocused": call("main", MAIN_FOCUSED), "frontmost": frontmost()}
    if i == 1: shot(f"{TAG}-attempt1-1-after-click")
    osinput("keys", "test"); time.sleep(0.8)
    if i == 1: shot(f"{TAG}-attempt1-2-after-typing")
    if rec: rec.wait()
    lines = [l["text"] for l in call("console")]
    evs = sorted((json.loads(l) for l in open(EV) if l.strip()), key=lambda e: e["t"])
    evs = [e for e in evs if e["t"] >= t0]
    keys = {}
    for e in evs:
        if e["type"] == "keydown": keys.setdefault(e["frame"], []).append(e["key"])
    field = call("main", FIELD, FRAME); composer = (call("page", COMPOSER) or "").strip()
    landed = "field" if field == "test" and not composer else "composer" if "test" in composer else f"other(field={field!r},composer={composer!r})"
    r = {"scenario": SC, "attempt": i, "target": TARGET[0], "before": before, "afterClick": after_click,
         "consoleLines": lines, "appGotKeyLines": sum(1 for l in lines if l.startswith("app got key")),
         "pageKeydownsByFrame": keys, "fieldValue": field, "composer": composer, "landed": landed}
    results.append(r)
    print(json.dumps({k: r[k] for k in ("scenario", "attempt", "landed", "appGotKeyLines")}), "focus50:", focus50, "| console:", lines, flush=True)
json.dump(results, open(f"{W}/run3/{TAG}-results.json", "w"), indent=1)
