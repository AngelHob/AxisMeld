# File-window hotbox release ownership

Date: 2026-10-11. This closes the explicitly deferred Phase 2B GUI boundary. The
old `release-cross-window` failure remains a red baseline, not a passing test.

## Scope and evidence

- `view3d_axismeld_hotbox_release.cc` installs a priority modal only in its source
  window. `wm_event_do_handlers` dispatches only the receiving window's handlers.
- `EVT_FILESELECT_FULL_OPEN` creates the real receiver after the command returns.
  This is the precise handoff point; polling windows from a timer is insufficient.
- The 2026-09-09 spec says "this batch" and "deferred independent design", not a
  permanent prohibition. The current GUI-completion request includes this gap.
- Topbar File already invokes native Blender operators. Space/File does not bind
  OpenScene or SaveSceneAs. Add only `file.open` and `file.save_as`, without default
  shortcuts, mapped to native invoke-only file selection. Keep independent Options
  disabled and leave New/Revert/new windows and other existing boundaries alone.

## Small native change

An optional internal file-select handoff callback on a modal handler is invoked
only by `EVT_FILESELECT_FULL_OPEN`. A release guard registers it when the
same source window already has the pending file-select operator, or the exact
reviewed File invocation has a transient token. Open's unsaved-scene confirmation
and Save As's modified-image confirmation copy operator properties before they
start the selector. A hidden, skip-save token on only those two native operators
preserves that precise chain; inherited shortcuts never set it. The callback
accepts only that exact operator or token and creates a receiver guard sharing the captured
trigger/mouse state, clearing the match after one handoff. Escape invalidates the
pending chain while draining remaining releases. There is no global keyboard interceptor, OS-key sampling,
generic window migration flag, timer polling, or new public WM API.

Both source and receiver therefore consume the still-owned releases, including
split delivery in either order. A fresh non-repeat press retires the matching old
capture and passes through; unrelated keys/mouse motion pass through. Completion
wakes the companion handler for prompt cleanup. The capture stores no editor or
region pointers. Source destruction invalidates the capture; receiver close
detaches it and allows remaining owned releases to drain in the surviving source.

Window deactivation only retains ownership when the explicitly paired other
window is live and active. External focus loss invalidates the shared state and
passes the event through. This preserves lost-release recovery without swallowing
future input. File cancellation writes nothing and cannot retain a dead receiver.

## Validation

- Keep the original cross-window leakage assertion. Its prior failure is recorded
  in `gui-final-regression/release-cross-window/runner.log` (candidate 05481ec...).
- The old test's `ShowWindow(SW_HIDE)` after receiver creation is an actual focus
  loss. Do not hide the receiver while asserting uninterrupted ownership; test
  deactivation separately and retain the existing focus-loss expectations.
- Exercise actual Space/File Open and Save As, captured releases in the receiver,
  split source/receiver release delivery, fresh input and Escape cancellation.
  Include the native dirty-scene/modified-image confirmation before the selector,
  keeping Space held through the explicit confirmation, and confirmation cancel.
  No file is selected/confirmed/written by these tests.
- Exercise source/receiver close and external focus loss, then assert no stale
  guard and normal future input. Retain same-window priority/lost-release tests.
- Preserve payload identities except the two reviewed File leaf bindings;
  Options and all other File/Window leaves remain unchanged. Retain inherited
  Ctrl+O/Ctrl+S behavior and regenerate input references after adding two unbound
  semantic commands. Native changes require a new build and installed GUI pass.

## Recorded regression evidence

The original WINDOW probe failed before this change. Build 06 (`aebdd29e...`)
passes the unchanged release-leakage assertion and all seven expanded ownership
cases: receiver-only, either split-delivery order, fresh press after lost release,
external deactivation, receiver close, and source close. Evidence is in the local
tool output (the runner does not automatically save a log with `--artifacts`).
The receiver is a real native FILE_BROWSER window; the probe itself never reads or writes a file.
This does not replace the separate real Space/File entry and native confirmation
chain regression. Build 06 also exposed the parser's missing two File semantic
commands, fixed with an exact-admission native regression before Build 07.

Build 07 (`793731a1...`) passes both `release` and all seven `release-cross-window`
cases in captured tool stdout. The release owner is rerunning the complete batch
with explicit log persistence under the local audit directory:
`gui-release-07/release/runner.log` and
`gui-release-07/release-cross-window/runner.log`. Only the completed batch's real
logs, binary SHA and exit codes are final release evidence; the earlier artifact
directories alone contain no logs.
The same-window test now requires exactly
the two reviewed File bodies, retaining disabled Options and every other old
File/Window restriction. The focus fixture establishes an actual private OS focus
window before sending the WM deactivation event: event simulation does not update
GHOST's active-window state, while the simulation flag deliberately drops OS input
queue events. Both shared guards must retire before future releases are delivered.
Earlier fixture failures remain in tool receipts and are not reported as passes.
