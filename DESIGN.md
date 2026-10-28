---
name: Orbot Focus Flow
colors:
  primary: "#FFCB83"
  on-primary: "#221B12"
  primary-hover: "#FFDAA6"
  canvas: "#151A23"
  surface: "#1C2330"
  elevated: "#242E3C"
  text: "#F5F7FA"
  muted: "#B0BAC8"
  border: "#374455"
  success: "#83D6AA"
  error: "#FF9298"
  warning: "#FFCB83"
typography:
  headline: { fontFamily: Segoe UI, fontSize: 30px, fontWeight: 700, lineHeight: 1.2 }
  title: { fontFamily: Segoe UI, fontSize: 20px, fontWeight: 600, lineHeight: 1.3 }
  body: { fontFamily: Segoe UI, fontSize: 15px, fontWeight: 400, lineHeight: 1.5 }
  label: { fontFamily: Segoe UI, fontSize: 14px, fontWeight: 600, lineHeight: 1.3 }
  small: { fontFamily: Segoe UI, fontSize: 13px, fontWeight: 400, lineHeight: 1.5 }
  mono: { fontFamily: Consolas, fontSize: 13px, fontWeight: 400, lineHeight: 1.5 }
spacing: { xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px }
rounded: { none: 0px, sm: 4px, md: 8px }
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    padding: 12px
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    padding: 16px
---

## Overview
User-selected concept 3, Focus Flow: a queue-first Vietnamese Windows workspace. Horizontal navigation, ordered queue on the left and active Quest on the right. Preserve the existing Python/Tk app and asynchronous controller. Native Segoe UI supports Vietnamese and Windows scaling.

## Colors
Amber highlights the current task and main action. Slate layers separate the queue and focus panel. Green indicates verified reward receipt. Warning/error states include readable labels.

## Typography
Use Segoe UI for the interface and Consolas only in the log. Respect Windows DPI scaling. Avoid tiny status text.

## Layout
Default 1360 by 900 with a 1040 by 740 minimum. Horizontal navigation switches between catalog, queue and log. Queue and focus stay visible together. The decorative banner adapts to available height. Connection controls and port live in Settings. The log is collapsed to an activity summary initially; opening its full view preserves workspace space at small sizes. Run/Stop stay visible in the focus footer.

## Elevation & Depth
Flat surfaces and one-pixel borders; no gradients or shadows.

## Shapes
Native rectangular controls, softly rounded queue selection, consistent padding and the existing orbital mark. A bundled original slate/amber panorama is decorative, not actual Quest artwork.

## Components
The connection status, selected Quest detail, progress bar, and log have distinct roles. Use labeled native buttons with keyboard focus. Empty lists explain the next action. Unsupported, expired, failed, completed, and stopped Quests remain distinct.

Security guidance uses an elevated callout with a 3px amber left edge, a bold amber title and body text. The connection dialog explains the debugging-port risk; the footer note turns amber while connected; closing Orbot while Discord's port is still open shows a reminder dialog (Quay lại / Đã hiểu, đóng Orbot) with the steps to quit Discord.

The queue is an ordered list independent of table selection and filters. Quests can be added once, moved up/down, removed, or cleared before running. The queue tab shows position, progress and the current state, including receiving Orbs. Show the pending count on the tab and distinguish an exhausted queue from a stopped or blocked queue. Keep unfinished entries after stopping. Auto-claim is on by default, runs after confirmed completion, and does not prevent the next Quest after an ordinary claim failure.

## Do's and Don'ts
- Keep network and CDP calls off the UI thread.
- Never present sample Quests as real or client-side progress as server completion.
- Disable conflicting controls while running; always keep Stop available.
- Provide a separate, clearly labeled demo mode for offline inspection.
- Never close Discord silently; tell the user when its debugging port is still open and how to close it.
