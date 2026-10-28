
ObjC.import("CoreGraphics");
ObjC.import("AppKit");
function run() {
  const app = $.NSWorkspace.sharedWorkspace.frontmostApplication;
  if (app.isNil()) return "";
  const pid = app.processIdentifier;
  const list = $.CGWindowListCopyWindowInfo(
    $.kCGWindowListOptionOnScreenOnly | $.kCGWindowListExcludeDesktopElements,
    $.kCGNullWindowID,
  );
  $.CFMakeCollectable(list);
  const count = $.CFArrayGetCount(list);
  for (let i = 0; i < count; i++) {
    const w = ObjC.castRefToObject($.CFArrayGetValueAtIndex(list, i));
    if (w.objectForKey("kCGWindowOwnerPID").js !== pid) continue;
    if (w.objectForKey("kCGWindowLayer").js !== 0) continue;
    const b = ObjC.deepUnwrap(w.objectForKey("kCGWindowBounds"));
    return JSON.stringify({
      id: w.objectForKey("kCGWindowNumber").js,
      title: String(ObjC.unwrap(w.objectForKey("kCGWindowName")) || ""),
      bounds: { x: b.X, y: b.Y, width: b.Width, height: b.Height },
      owner: {
        name: String(app.localizedName.js || ObjC.unwrap(w.objectForKey("kCGWindowOwnerName")) || ""),
        processId: pid,
        path: String(app.bundleURL.path.js || ""),
        bundleId: String(app.bundleIdentifier.js || ""),
      },
    });
  }
  return "";
}