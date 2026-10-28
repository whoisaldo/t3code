// OS-level input via CGEvent at the HID tap (same path as a physical mouse/keyboard).
// osinput click <x> <y>        global display points, top-left origin
// osinput keys <chars>         lowercase a-z only, as virtual key codes
// osinput where                print cursor position
import CoreGraphics
import Foundation
let args = CommandLine.arguments
let src = CGEventSource(stateID: .hidSystemState)
func post(_ e: CGEvent?) { e?.post(tap: .cghidEventTap) }
func sleepMs(_ ms: UInt32) { usleep(ms * 1000) }
let keyCodes: [Character: CGKeyCode] = ["a":0,"s":1,"d":2,"f":3,"h":4,"g":5,"z":6,"x":7,"c":8,"v":9,"b":11,"q":12,"w":13,"e":14,"r":15,"y":16,"t":17,"o":31,"u":32,"i":34,"p":35,"l":37,"j":38,"k":40,"n":45,"m":46]
switch args[1] {
case "click":
  let p = CGPoint(x: Double(args[2])!, y: Double(args[3])!)
  post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: p, mouseButton: .left)); sleepMs(80)
  post(CGEvent(mouseEventSource: src, mouseType: .leftMouseDown, mouseCursorPosition: p, mouseButton: .left)); sleepMs(60)
  post(CGEvent(mouseEventSource: src, mouseType: .leftMouseUp, mouseCursorPosition: p, mouseButton: .left))
case "move":
  let p = CGPoint(x: Double(args[2])!, y: Double(args[3])!)
  post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: p, mouseButton: .left))
case "keys":
  for ch in args[2] {
    guard let k = keyCodes[ch] else { fatalError("unsupported key \(ch)") }
    post(CGEvent(keyboardEventSource: src, virtualKey: k, keyDown: true)); sleepMs(40)
    post(CGEvent(keyboardEventSource: src, virtualKey: k, keyDown: false)); sleepMs(80)
  }
case "where":
  let e = CGEvent(source: nil)!; print(e.location.x, e.location.y)
default: fatalError("usage")
}
