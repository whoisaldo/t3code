// Native window fixture for #24572 (v2). Args: <title> <x> <y> <w> <h> <mode> <pidfile>
// mode: normal | floating | minimized | both (floating + normal in one process)
// SIGUSR1: order every window front without activating the app.
import AppKit
let a = CommandLine.arguments
let rect = NSRect(x: Double(a[2])!, y: Double(a[3])!, width: Double(a[4])!, height: Double(a[5])!)
let mode = a[6]
try? "\(getpid())".write(toFile: a[7], atomically: true, encoding: .utf8)
let app = NSApplication.shared
app.setActivationPolicy(.regular)
var windows: [NSWindow] = []
func make(_ title: String, _ r: NSRect, _ level: NSWindow.Level) -> NSWindow {
  let w = NSWindow(contentRect: r, styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
  w.title = title; w.isReleasedWhenClosed = false; w.level = level; w.orderFrontRegardless(); windows.append(w); return w
}
switch mode {
case "floating": _ = make(a[1], rect, .floating)
case "both":
  _ = make(a[1] + "-normal", rect, .normal)
  _ = make(a[1] + "-floating", rect.offsetBy(dx: 40, dy: -40), .floating)
default:
  let w = make(a[1], rect, .normal)
  if mode == "minimized" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { w.miniaturize(nil) } }
}
signal(SIGUSR1, SIG_IGN)
let src = DispatchSource.makeSignalSource(signal: SIGUSR1, queue: .main)
src.setEventHandler { for w in windows where !w.isMiniaturized { w.orderFrontRegardless() } }
src.resume()
app.run()
