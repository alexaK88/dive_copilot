# Browser

Serves the Dive Copilot browser client and opens AssemblyAI Voice Agent sessions with **inline session configuration**.

## Run it

```sh
AGENT=dive_copilot python deployment/browser/server.py
```

Open `http://localhost:3000` and start the call.

The browser deployment no longer requires a stored AssemblyAI agent or any `AGENT_ID` value.

## How it works

`GET /session-config` returns two things in one non-cacheable response:

- a fresh 60-second AssemblyAI Voice Agent token;
- the inline session configuration built from `agents/<AGENT>.jsonc`.

The first WebSocket message is therefore:

```json
{
  "type": "session.update",
  "session": {
    "system_prompt": "...",
    "greeting": "...",
    "input": {"...": "..."},
    "output": {"voice": "anna"},
    "tools": []
  }
}
```

There is no `agent_id` lookup or stored-agent binding in the browser flow.

The `@file:prompts/...` prompt reference used by the agent file is resolved by `server.py` before the session config is sent to the browser. Mission-specific keyterms and transcription context are merged into the **first** `session.update`, before `session.ready`.

## Tool execution

The agent's HTTP tool URLs stay server-side.

For inline sessions, the browser registers tools as function tools. When AssemblyAI emits `tool.call`, `app.js` sends the tool name and arguments to:

```text
POST /tool
```

`server.py` looks up the original `http` configuration in `agents/dive_copilot.jsonc`, calls the mission backend, and returns the result. The browser then sends `tool.result` back to AssemblyAI after the corresponding reply phase completes.

This keeps backend endpoints/headers out of the Voice Agent session schema and avoids dependence on stored-agent HTTP tool execution.

## Voice lifecycle

The client uses explicit states:

```text
idle → connecting → listening → processing → speaking
```

with `error` and `disconnected` recovery states.

It also includes:

- a 15-second `session.ready` timeout;
- duplicate-session prevention;
- microphone and AudioContext cleanup;
- clean `session.end` handling;
- retry behavior after failures;
- `DIVE_VOICE_DEBUG()` for safe deployed-session diagnostics.

## Environment

| Variable | Purpose |
| --- | --- |
| `ASSEMBLYAI_API_KEY` | Required. Stays on the server. |
| `AGENT` | Agent configuration file to load. Defaults to `dive_copilot`. |
| `PORT` | Render supplies this automatically; local default is 3000. |

`AGENT_ID` and `AGENT_ID_DIVE_COPILOT` are intentionally ignored by this browser deployment.

## Hosting

`render.yaml` configures the service with only:

```text
ASSEMBLYAI_API_KEY
AGENT=dive_copilot
```

A deleted or stale stored AssemblyAI agent can therefore no longer prevent Render from starting.

Anyone with the public browser URL can start sessions billed to the configured AssemblyAI account.
