# Browser

Serves a page with a call button. Useful for iterating on an agent before putting it on a phone number.

## 1. Publish an agent

```sh
AGENT=http-tools python publish.py
```

## 2. Run it

```sh
python deployment/browser/server.py
```

Open http://localhost:3000 and start the call.

## 3. Iterate

Edit the file in [agents/](../../agents/), run `python publish.py`, and start another call. When the agent behaves the way you want, see [deployment/telephony](../telephony/).

---

## What it does

Publishes `agents/<AGENT>.jsonc` on startup if it has no id yet, so a fresh clone works with only an API key.

`GET /session-config` validates the currently published agent and mints a fresh 60-second AssemblyAI session token in the same non-cacheable response. The page uses the returned agent id rather than trusting the id embedded in cached HTML, which prevents stale-agent/session mismatches. The API key never reaches the page. `GET /token` remains available for diagnostics and backwards compatibility.

The page streams the microphone as 24 kHz PCM16 over `wss://agents.assemblyai.com/v1/ws`, plays the reply back, and discards queued audio when you interrupt. Capture and playback each run in their own AudioContext with a resampling worklet, so a browser that refuses to open a context at 24 kHz still sounds right.

The side pane has two tabs. Events lists every websocket frame in both directions, with audio runs collapsed into counts. Agent shows the published agent as the API stored it, read only, served by `GET /agent`. Tool header values and LLM keys are stripped from that response, but the system prompt is in it, so on a public deployment anyone opening the page can read it.

The first session message contains only `{ agent_id }`. Prompt, voice, tools and turn detection are read from the stored agent, which is why the browser and the phone behave the same. Mission-specific speech context is applied in a second `session.update` only after `session.ready`.

The client keeps an explicit connection lifecycle (`idle`, `connecting`, `listening`, `processing`, `speaking`, `error`, `disconnected`). Failed initialization no longer silently falls back to `idle`: the error stays visible and the call button becomes **Retry call**. A 15-second readiness timeout also catches sessions that open a WebSocket but never become ready.

## Environment

| | |
| --- | --- |
| `ASSEMBLYAI_API_KEY` | Required. Stays in this process. |
| `AGENT` | Which file in `agents/` to serve. Defaults to `minimal`. |
| `AGENT_ID_<NAME>` | The id `python publish.py` saved for that file. Connected to as it is. |
| `AGENT_ID` | Overrides the per-file keys, for serving one specific agent. |
| `PORT` | Defaults to 3000, moves to the next free port if taken. |

## Editing the page

The server is [server.py](server.py), the page is [index.html](index.html) and the client is [app.js](app.js), all served as they are. Save and refresh.

## Hosting

`render.yaml` is configured for one-click deploys. Render prompts for `ASSEMBLYAI_API_KEY` during Blueprint creation, sets `AGENT=dive_copilot`, and leaves `AGENT_ID` empty. Render sets `PORT` itself.

For the hosted Dive Copilot deployment, leave `AGENT_ID` empty unless you intentionally want to pin one specific AssemblyAI agent. With no id set, the service publishes/updates the `Dive Copilot` agent by name on boot and returns that live id to the browser through `/session-config`. This avoids carrying a stale local `.env` agent id into the hosted session.

Anyone with the URL can start sessions billed to your key.
