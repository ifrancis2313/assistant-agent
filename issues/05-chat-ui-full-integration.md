# Chat UI & Full Integration

**Type:** AFK
**Blocked by:** #3 (Task List UI) + #4 (Agent Core)
**User stories covered:** 9, 10, 11, 12, 17

## What to build

Build the chat panel and wire everything together into the final split-panel layout. After this slice the app is fully functional as an MVP — you can talk to the agent, it creates tasks, and the task panel updates to show them.

**Chat panel:**
- Scrollable message thread showing user and assistant messages with visual distinction (alignment, color)
- Input box at the bottom with send button (also submits on Enter)
- Sends POST /chat, displays the response, scrolls to the latest message
- Shows a loading indicator while waiting for the agent response

**Split-panel layout:**
- Desktop (≥768px): chat panel on the left, task panel on the right, both full height
- Mobile (<768px): task panel stacked above chat panel, or tabbed — whichever feels more natural on a phone

**Task panel refresh:**
After each agent turn, the task panel re-fetches its current view. This ensures tasks created or modified by the agent appear immediately without a manual refresh.

**API client:**
All fetch calls go through a typed client module. This is the single place to update base URLs or add auth headers later.

## Acceptance criteria

- [ ] Chat panel displays a message thread with visual distinction between user and assistant
- [ ] Sending a message calls POST /chat and displays the response
- [ ] A loading indicator is shown while the agent is responding
- [ ] Task panel automatically refreshes after each agent response
- [ ] Typing a task in chat causes it to appear in the task panel within the same turn
- [ ] Layout is split side-by-side on desktop and usable on a 390px mobile screen
- [ ] Pressing Enter in the input box submits the message
- [ ] Empty chat state shown on first load (e.g. a welcome message or prompt)

## Blocked by

#3 — Task List UI
#4 — Agent Core — Task Capture & Retrieval
