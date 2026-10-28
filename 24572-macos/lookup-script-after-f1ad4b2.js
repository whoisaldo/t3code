
ObjC.import("CoreGraphics");
ObjC.import("AppKit");
function run() {
  const app = $.NSWorkspace.sharedWorkspace.frontmostApplication;
  if (app.isNil()) return "";
  const pid = app.processIdentifier;
  const appName = String(app.localizedName.js || "");
  const list = $.CGWindowListCopyWindowInfo(
    $.kCGWindowListOptionOnScreenOnly | $.kCGWindowListExcludeDesktopElements,
    $.kCGNullWindowID,
  );
  $.CFMakeCollectable(list);
  const count = $.CFArrayGetCount(list);
  for (let i = 0; i < count; i++) {
    const w = ObjC.castRefToObject($.CFArrayGetValueAtIndex(list, i));
    if (w.objectForKey("kCGWindowLayer").js !== 0) continue;
    const ownerPid = w.objectForKey("kCGWindowOwnerPID").js;
    const ownerName = String(ObjC.unwrap(w.objectForKey("kCGWindowOwnerName")) || "");
    // Nested apps such as Device Hub can be frontmost while NSWorkspace reports PID -1.
    if (pid > 0 ? ownerPid !== pid : !appName || ownerName !== appName) continue;
    const b = ObjC.deepUnwrap(w.objectForKey("kCGWindowBounds"));
    return JSON.stringify({
      id: w.objectForKey("kCGWindowNumber").js,
      title: String(ObjC.unwrap(w.objectForKey("kCGWindowName")) || ""),
      bounds: { x: b.X, y: b.Y, width: b.Width, height: b.Height },
      owner: {
        name: appName || ownerName,
        processId: ownerPid,
        path: String(app.bundleURL.path.js || ""),
        bundleId: String(app.bundleIdentifier.js || ""),
      },
    });
  }
  return "";
}