// Two-origin test server for #22095. Top page on :18711 embeds a same-origin iframe,
// a cross-origin same-site iframe (localhost:18712) and a cross-site iframe (127.0.0.1:18712).
// Every frame logs pointerdown/focusin/keydown/input to its own origin's /log (JSONL on disk).
import http from "node:http";
import fs from "node:fs";
const LOG = process.argv[2];
fs.writeFileSync(process.argv[3], String(process.pid));
const logger = (frame) => `<script>
const frame=${JSON.stringify(frame)};
const send=(e,extra)=>fetch('/log',{method:'POST',body:JSON.stringify({t:Date.now(),frame,origin:location.origin,type:e.type,trusted:e.isTrusted,key:e.key,target:(e.target&&e.target.id)||(e.target&&e.target.tagName),value:document.getElementById('field')?.value,...extra})});
for(const t of ['pointerdown','focusin','keydown','input']) addEventListener(t,e=>send(e),true);
addEventListener('input',()=>{document.getElementById('echo').textContent='value: '+document.getElementById('field').value;},true);
</script>`;
const field = (label) => `<label style="font:16px system-ui">${label}<br><input id="field" autocomplete="off" style="font:20px system-ui;width:300px;height:36px"></label><div id="echo" style="font:16px monospace;margin-top:6px">value: </div>`;
const framePage = (frame) => `<!doctype html><html><body style="margin:0;padding:12px;background:#eef;font:14px system-ui">${field(frame + " input")}${logger(frame)}</body></html>`;
const top = `<!doctype html><html><head><title>22095 repro</title></head><body style="margin:0;font:14px system-ui">
<div style="position:absolute;left:20px;top:20px">${field("top-frame input")}</div>
<iframe id="same" src="http://localhost:18711/frame?name=same-origin" style="position:absolute;left:20px;top:140px;width:360px;height:110px;border:2px solid #888"></iframe>
<iframe id="xorigin" src="http://localhost:18712/frame?name=cross-origin-same-site" style="position:absolute;left:20px;top:270px;width:360px;height:110px;border:2px solid #c80"></iframe>
<iframe id="xsite" src="http://127.0.0.1:18712/frame?name=cross-site" style="position:absolute;left:20px;top:400px;width:360px;height:110px;border:2px solid #c00"></iframe>
${logger("top")}</body></html>`;
const handler = (port) => (req, res) => {
  const url = new URL(req.url, "http://x");
  if (req.method === "POST" && url.pathname === "/log") { let b = ""; req.on("data", (c) => (b += c)); req.on("end", () => { fs.appendFileSync(LOG, b.replace(/\n/g, " ") + "\n"); res.end("ok"); }); return; }
  res.setHeader("content-type", "text/html; charset=utf-8");
  if (url.pathname === "/frame") return res.end(framePage(url.searchParams.get("name") ?? "frame"));
  if (port === 18711 && url.pathname === "/") return res.end(top);
  res.statusCode = 404; res.end("not found");
};
http.createServer(handler(18711)).listen(18711, "127.0.0.1");
http.createServer(handler(18711)).listen(18711, "::1");
http.createServer(handler(18712)).listen(18712, "127.0.0.1");
http.createServer(handler(18712)).listen(18712, "::1");
console.log("listening 18711 18712");
