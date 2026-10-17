// The page's client. Identical to the one in the JS starter: the
// audio worklets, the websocket session, and the transcript and event panes.
const $ = (id) => document.getElementById(id)
// The rate the API speaks. Both worklets resample, since a browser may
// ignore the rate an AudioContext asks for.
const WIRE_RATE = 24_000
let AGENT = window.AGENT || { name: 'Dive Copilot', mode: 'inline' }

// Scratch buffers are reused: allocating on the audio thread causes glitches.
const CAPTURE_WORKLET = `
  class CaptureProcessor extends AudioWorkletProcessor {
    constructor() {
      super();
      this._ratio = sampleRate / ${WIRE_RATE};
      this._pos = 0;
      this._prev = 0;
      this._src = null;
      this._out = null;
    }
    _toPcm(samples, len) {
      const pcm = new Int16Array(len);
      for (let i = 0; i < len; i++) {
        const s = Math.max(-1, Math.min(1, samples[i]));
        pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      return pcm;
    }
    process(inputs) {
      const ch = inputs[0]?.[0];
      if (!ch) return true;
      if (this._ratio === 1) {
        const pcm = this._toPcm(ch, ch.length);
        this.port.postMessage(pcm.buffer, [pcm.buffer]);
        return true;
      }
      const n = ch.length;
      if (!this._src || this._src.length < n + 1) {
        this._src = new Float32Array(n + 1);
        this._out = new Float32Array(Math.ceil((n + 1) / this._ratio) + 2);
      }
      const src = this._src;
      const out = this._out;
      src[0] = this._prev;
      src.set(ch, 1);
      let outLen = 0;
      let pos = this._pos;
      while (pos < n) {
        const i = Math.floor(pos);
        const frac = pos - i;
        out[outLen++] = src[i] + (src[i + 1] - src[i]) * frac;
        pos += this._ratio;
      }
      this._pos = pos - n;
      this._prev = ch[n - 1];
      if (outLen) {
        const pcm = this._toPcm(out, outLen);
        this.port.postMessage(pcm.buffer, [pcm.buffer]);
      }
      return true;
    }
  }
  registerProcessor('capture', CaptureProcessor);
`

// A ring buffer rather than one AudioBufferSource per chunk, which drifts and
// clicks under jitter. Posting 'stop' empties it for barge-in.
const PLAYBACK_WORKLET = `
  class PlaybackProcessor extends AudioWorkletProcessor {
    constructor() {
      super();
      this._ring = new Float32Array(sampleRate * 30);
      this._writePos = 0;
      this._readPos = 0;
      this._available = 0;
      this._step = ${WIRE_RATE} / sampleRate;
      this._rsPos = 0;
      this._rsPrev = 0;
      // After a gap the speaker sits at zero, so interpolating from the
      // pre-gap _rsPrev would click. Reset it instead.
      this._drained = false;
      this.port.onmessage = (e) => {
        if (e.data === 'stop') {
          this._writePos = this._readPos = this._available = 0;
          this._rsPos = this._rsPrev = 0;
          return;
        }
        const int16 = new Int16Array(e.data);
        // int16[-1] would make _rsPrev NaN, silencing the ring for good.
        if (!int16.length) return;
        if (this._drained) {
          this._rsPrev = 0;
          this._rsPos = 0;
          this._drained = false;
        }
        if (this._step === 1) {
          for (let i = 0; i < int16.length; i++) this._push(int16[i] / 32768);
          return;
        }
        const n = int16.length;
        let pos = this._rsPos;
        while (pos < n) {
          const i = Math.floor(pos);
          const frac = pos - i;
          const a = i === 0 ? this._rsPrev : int16[i - 1] / 32768;
          const b = int16[i] / 32768;
          this._push(a + (b - a) * frac);
          pos += this._step;
        }
        this._rsPos = pos - n;
        this._rsPrev = int16[n - 1] / 32768;
      };
    }
    _push(v) {
      if (this._available < this._ring.length) {
        this._ring[this._writePos] = v;
        this._writePos = (this._writePos + 1) % this._ring.length;
        this._available++;
      }
    }
    process(inputs, outputs) {
      const output = outputs[0];
      const out = output[0];
      const cap = this._ring.length;
      for (let i = 0; i < out.length; i++) {
        if (this._available > 0) {
          out[i] = this._ring[this._readPos];
          this._readPos = (this._readPos + 1) % cap;
          this._available--;
        } else {
          out[i] = 0;
          this._drained = true;
        }
      }
      // Mono source, stereo sink.
      for (let ch = 1; ch < output.length; ch++) output[ch].set(out);
      return true;
    }
  }
  registerProcessor('playback', PlaybackProcessor);
`

const blobUrl = (code) =>
  URL.createObjectURL(new Blob([code], { type: 'application/javascript' }))

let latencyTurn = null
let latencyTurnNumber = 0

function startLatencyTurn() {
  latencyTurn = {
    id: ++latencyTurnNumber,

    stoppedAt: performance.now(),

    transcriptAt: null,
    toolCallAt: null,

    firstReplyStartedAt: null,
    lastReplyStartedAt: null,

    firstAudioAt: null,
    replyDoneAt: null,

    replyDoneCount: 0,
  }
}

function msBetween(a, b) {
  if (a == null || b == null) {
    return null
  }

  return Math.round(b - a)
}

function printLatencyTurn() {
  if (!latencyTurn) {
    return
  }

  console.table({
    "speech stopped → final transcript":
      msBetween(
        latencyTurn.stoppedAt,
        latencyTurn.transcriptAt
      ),

    "speech stopped → tool call":
      msBetween(
        latencyTurn.stoppedAt,
        latencyTurn.toolCallAt
      ),

    "speech stopped → first reply phase":
      msBetween(
        latencyTurn.stoppedAt,
        latencyTurn.firstReplyStartedAt
      ),

    "speech stopped → first audio":
      msBetween(
        latencyTurn.stoppedAt,
        latencyTurn.firstAudioAt
      ),

    "final transcript → first audio":
      msBetween(
        latencyTurn.transcriptAt,
        latencyTurn.firstAudioAt
      ),

    "last reply start → first audio":
      msBetween(
        latencyTurn.lastReplyStartedAt,
        latencyTurn.firstAudioAt
      ),

    "reply.done events":
      latencyTurn.replyDoneCount,
  })
}

let ws, captureCtx, playbackCtx, playback, capture, mic, callStart, timer
let voiceState = 'idle'
let sessionReady = false
let currentSessionId = null
let readyTimeout = null
let intentionalStop = false
let sessionHadError = false
let pendingToolResults = []
let replyIdle = false

const READY_TIMEOUT_MS = 15_000

// --- microphones ---
// Labels stay empty until mic permission is granted, so this runs again after
// getUserMedia.
async function listMics() {
  if (!navigator.mediaDevices?.enumerateDevices) return
  const devices = await navigator.mediaDevices.enumerateDevices()
  const inputs = devices
    .filter((device) => device.kind === 'audioinput')
    // Chrome's synthetic entries alias a real device and duplicate it.
    .filter((device) => device.deviceId !== 'default' && device.deviceId !== 'communications')
  const select = $('mic')
  const chosen = select.value
  select.replaceChildren()
  const auto = document.createElement('option')
  auto.value = ''
  auto.textContent = 'Default microphone'
  select.append(auto)
  inputs.forEach((device, i) => {
    const option = document.createElement('option')
    option.value = device.deviceId
    option.textContent = device.label || `Microphone ${i + 1}`
    select.append(option)
  })
  if (chosen && inputs.some((device) => device.deviceId === chosen)) select.value = chosen
}
listMics()
navigator.mediaDevices?.addEventListener?.('devicechange', listMics)

$('btn').onclick = () => {
  if (['idle', 'error', 'disconnected'].includes(voiceState)) {
    start()
  } else {
    stop()
  }
}
$('log-toggle').onclick = () => {
  const hidden = document.body.classList.toggle('no-side')
  $('log-toggle').textContent = hidden ? 'Show' : 'Hide'
}

// --- side pane tabs ---
let agentLoaded = false

function showTab(name) {
  for (const tab of ['events', 'agent']) {
    $('tab-' + tab).classList.toggle('on', tab === name)
    $(tab + '-body').hidden = tab !== name
  }
  if (name === 'agent' && !agentLoaded) {
    agentLoaded = true
    fetch('/agent', { cache: 'no-store' })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((agent) => {
        if (agent?.name) {
          AGENT = {
            name: agent.name || AGENT.name,
            mode: agent.mode || 'inline',
          }
          window.AGENT = AGENT
        }
        $('agent-body').replaceChildren()
        const pre = document.createElement('pre')
        pre.textContent = JSON.stringify(agent, null, 2)
        $('agent-body').append(pre)
      })
      .catch(() => {
        agentLoaded = false
        $('agent-body').textContent = 'Could not load the agent.'
      })
  }
}
$('tab-events').onclick = () => showTab('events')
$('tab-agent').onclick = () => showTab('agent')

async function addWorklet(ctx, code, name) {
  const url = blobUrl(code)
  try {
    await ctx.audioWorklet.addModule(url)
  } finally {
    URL.revokeObjectURL(url)
  }
  return new AudioWorkletNode(ctx, name)
}

async function fetchSessionConfig() {
  // The server returns a short-lived token and the inline Voice Agent session
  // configuration together. No stored AssemblyAI agent id is involved.
  const res = await fetch('/session-config', { cache: 'no-store' })
  let body = {}
  try {
    body = await res.json()
  } catch (_) {
    // A non-JSON response is surfaced below as a normal bootstrap failure.
  }

  if (!res.ok) {
    throw new Error(body.error || `voice bootstrap failed (HTTP ${res.status})`)
  }
  if (!body.token) {
    throw new Error('voice bootstrap returned no session token')
  }
  if (!body.session || typeof body.session !== 'object') {
    throw new Error('voice bootstrap returned no inline session configuration')
  }

  AGENT = {
    name: body.agent?.name || AGENT.name || 'Dive Copilot',
    mode: 'inline',
  }
  window.AGENT = AGENT
  return body
}

function buildSessionConfig(baseSession) {
  const session = JSON.parse(JSON.stringify(baseSession || {}))
  const speechContext = window.DIVE_SPEECH_CONTEXT
  if (speechContext) {
    session.input = session.input || {}
    session.input.keyterms = speechContext.keyterms ?? session.input.keyterms ?? []
    session.input.transcription_prompt =
      speechContext.transcription_prompt ?? session.input.transcription_prompt ?? ''
  }
  return session
}

async function executeToolCall(msg) {
  const res = await fetch('/tool', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: msg.name,
      arguments: msg.arguments ?? {},
    }),
  })

  let body = {}
  try {
    body = await res.json()
  } catch (_) {
    body = { ok: false, error: `tool proxy returned HTTP ${res.status}` }
  }

  if (!res.ok) {
    return {
      ok: false,
      error: body.error || `tool proxy failed (HTTP ${res.status})`,
    }
  }
  return body
}

function sendToolResult(socket, item) {
  if (ws !== socket || socket.readyState !== WebSocket.OPEN) return
  const payload = item.response?.ok
    ? item.response.result
    : {
        ok: false,
        error: item.response?.error || 'tool execution failed',
        status: item.response?.status,
      }

  socket.send(JSON.stringify({
    type: 'tool.result',
    call_id: item.callId,
    result: JSON.stringify(payload ?? {}),
  }))
  logEvent('up', 'tool.result', `${item.name} ${item.callId}`)
}

function flushToolResults(socket) {
  if (!replyIdle || ws !== socket || socket.readyState !== WebSocket.OPEN) return
  const ready = pendingToolResults.filter((item) => item.response)
  pendingToolResults = pendingToolResults.filter((item) => !item.response)
  ready.forEach((item) => sendToolResult(socket, item))
}

function describeSessionError(msg) {
  const code = String(msg?.code || '').toLowerCase()
  const message = String(msg?.message || '').trim()

  if (code === 'agent_not_found') {
    return 'agent unavailable (agent_not_found) — retry after deployment sync'
  }
  if (code === 'unauthorized') {
    return 'voice authentication failed — check the AssemblyAI API key'
  }
  if (code === 'forbidden') {
    return 'voice session is not permitted for this account'
  }
  if (code === 'agent_init_failed' || code === 'agent_timeout') {
    return 'agent initialization failed — retry the call'
  }
  if (code === 'server_error') {
    return 'voice service temporarily unavailable — retry the call'
  }
  return message || (code ? `voice session error (${code})` : 'voice session error')
}

function clearReadyTimeout() {
  if (readyTimeout) clearTimeout(readyTimeout)
  readyTimeout = null
}

function cleanupAudio() {
  playback?.port.postMessage('stop')
  capture?.disconnect?.()
  playback?.disconnect?.()
  mic?.getTracks().forEach((track) => track.stop())

  const captureToClose = captureCtx
  const playbackToClose = playbackCtx
  captureCtx = playbackCtx = playback = capture = mic = null

  captureToClose?.close?.().catch?.(() => {})
  playbackToClose?.close?.().catch?.(() => {})
}

function resetControls({ retry = false } = {}) {
  clearInterval(timer)
  timer = null
  clearPartials()
  open.forEach((run) => paint(run, true))
  open.clear()
  $('btn').disabled = false
  $('mic').disabled = false
  $('btn').textContent = retry ? 'Retry call' : 'Start call'
  $('btn').classList.remove('live')
}

function finishConnection({ state = 'idle', detail, retry = false } = {}) {
  clearReadyTimeout()
  sessionReady = false
  currentSessionId = null
  callStart = null
  cleanupAudio()
  resetControls({ retry })
  setStatus(state, detail)
}

async function start() {
  if (!['idle', 'error', 'disconnected'].includes(voiceState)) return

  intentionalStop = false
  sessionHadError = false
  sessionReady = false
  currentSessionId = null
  pendingToolResults = []
  replyIdle = false
  clearReadyTimeout()

  // Clean up any resources left by a previous failed attempt before opening a
  // new session.
  cleanupAudio()
  if (ws && ws.readyState <= WebSocket.OPEN) {
    try { ws.close() } catch (_) {}
  }
  ws = null

  $('btn').disabled = true
  $('mic').disabled = true
  $('btn').textContent = 'Connecting…'
  setStatus('connecting', 'connecting voice link')

  try {
    const { token, session: baseSession } = await fetchSessionConfig()
    const inlineSession = buildSessionConfig(baseSession)

    // Two contexts, created from the user gesture path so Safari/Chrome can
    // start audio without a separate permission interaction.
    captureCtx = new AudioContext({ sampleRate: WIRE_RATE })
    playbackCtx = new AudioContext({ sampleRate: WIRE_RATE })
    await Promise.all([captureCtx.resume(), playbackCtx.resume()])

    playback = await addWorklet(playbackCtx, PLAYBACK_WORKLET, 'playback')
    playback.connect(playbackCtx.destination)

    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('microphone access is not available in this browser')
    }

    const deviceId = $('mic').value
    mic = await navigator.mediaDevices.getUserMedia({
      audio: {
        // A preference, not `exact`: an unplugged device falls back.
        ...(deviceId ? { deviceId } : {}),
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: false,
        autoGainControl: false,
      },
    })
    listMics()

    capture = await addWorklet(captureCtx, CAPTURE_WORKLET, 'capture')
    captureCtx.createMediaStreamSource(mic).connect(capture)

    const url = new URL('wss://agents.assemblyai.com/v1/ws')
    url.searchParams.set('token', token)
    const socket = new WebSocket(url)
    ws = socket

    // The API takes base64 inside JSON, not binary frames.
    capture.port.onmessage = ({ data }) => {
      if (!sessionReady || ws !== socket || socket.readyState !== WebSocket.OPEN) return
      const bytes = new Uint8Array(data)
      let binary = ''
      for (let i = 0; i < bytes.length; i += 0x8000) {
        binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000))
      }
      socket.send(JSON.stringify({ type: 'input.audio', audio: btoa(binary) }))
      logEvent('up', 'input.audio')
    }

    socket.onopen = () => {
      if (ws !== socket) return

      // Inline configuration is the first message on the socket. This avoids
      // stored-agent lookup entirely and includes mission-specific speech
      // context before the first user utterance.
      socket.send(JSON.stringify({
        type: 'session.update',
        session: inlineSession,
      }))
      logEvent('up', 'session.update', `${AGENT.name} (inline)`)

      readyTimeout = setTimeout(() => {
        if (ws !== socket || sessionReady) return
        sessionHadError = true
        console.error('Voice session did not reach session.ready within timeout', {
          agent: AGENT.name,
          mode: AGENT.mode,
          timeoutMs: READY_TIMEOUT_MS,
        })
        try { socket.close() } catch (_) {}
        finishConnection({
          state: 'error',
          detail: 'agent did not become ready — retry the call',
          retry: true,
        })
        if (ws === socket) ws = null
      }, READY_TIMEOUT_MS)
    }

    socket.onmessage = ({ data }) => {
      if (ws !== socket) return

      let msg
      try {
        msg = JSON.parse(data)
      } catch (error) {
        console.error('Could not parse Voice Agent event', error, data)
        return
      }

      switch (msg.type) {
        case 'session.ready': {
          clearReadyTimeout()
          sessionReady = true
          currentSessionId = msg.session_id || null

          callStart = Date.now()
          timer = setInterval(tick, 1000)
          tick()

          setStatus('listening')
          $('btn').disabled = false
          $('btn').textContent = 'End call'
          $('btn').classList.add('live')
          $('mic').disabled = true

          logEvent('down', msg.type, msg.session_id)
          break
        }

        case 'input.speech.started':
          replyIdle = false
          playback?.port.postMessage('stop')
          setStatus('listening')
          logEvent('down', msg.type)
          break

        case 'input.speech.stopped':
          startLatencyTurn()
          setStatus('processing')
          logEvent('down', msg.type)
          break

        case 'reply.started': {
          replyIdle = false
          const now = performance.now()
          if (latencyTurn) {
            if (latencyTurn.firstReplyStartedAt == null) {
              latencyTurn.firstReplyStartedAt = now
            }
            latencyTurn.lastReplyStartedAt = now
          }
          setStatus('speaking')
          logEvent('down', msg.type)
          break
        }

        case 'reply.audio': {
          if (latencyTurn && latencyTurn.firstAudioAt == null) {
            latencyTurn.firstAudioAt = performance.now()
            printLatencyTurn()
          }

          const raw = atob(msg.data)
          const bytes = new Uint8Array(raw.length)
          for (let i = 0; i < raw.length; i++) {
            bytes[i] = raw.charCodeAt(i)
          }
          playback?.port.postMessage(bytes.buffer, [bytes.buffer])
          logEvent('down', msg.type)
          break
        }

        case 'reply.done':
          if (latencyTurn) {
            latencyTurn.replyDoneCount += 1
            latencyTurn.replyDoneAt = performance.now()
          }
          replyIdle = true
          setStatus('listening')
          if (msg.status === 'interrupted') {
            playback?.port.postMessage('stop')
            // Match AssemblyAI's recommended interactive-tool behavior: an
            // interrupted reply abandons pending results from that reply.
            pendingToolResults = []
          } else {
            flushToolResults(socket)
          }
          logEvent('down', msg.type, msg.status)
          break

        // text is the full transcript so far, so it replaces.
        case 'transcript.user.delta':
          partial('you', msg.text)
          logEvent('down', msg.type, msg.text)
          break

        // delta is the next word only, so it appends.
        case 'transcript.agent.delta':
          logEvent('down', msg.type, msg.delta)
          if (msg.reply_id && msg.reply_id === printedReply) break
          if (msg.reply_id !== liveReply) {
            liveReply = msg.reply_id
            dropPartial('agent')
          }
          partial('agent', appendDelta(partialText.agent || '', msg.delta))
          break

        case 'transcript.user':
          if (latencyTurn && latencyTurn.transcriptAt == null) {
            latencyTurn.transcriptAt = performance.now()
          }
          addLine('you', msg.text)
          logEvent('down', msg.type, msg.text)
          break

        case 'transcript.agent':
          printedReply = msg.reply_id ?? printedReply
          addLine('agent', msg.text)
          logEvent('down', msg.type, msg.text)
          break

        case 'tool.call': {
          if (latencyTurn && latencyTurn.toolCallAt == null) {
            latencyTurn.toolCallAt = performance.now()
          }
          const args = JSON.stringify(msg.arguments ?? {})
          addLine('tool', `${msg.name}(${args})`)
          logEvent('down', msg.type, `${msg.name} ${args}`)

          const item = {
            callId: msg.call_id,
            name: msg.name,
            response: null,
          }
          pendingToolResults.push(item)
          executeToolCall(msg)
            .then((response) => {
              item.response = response
              flushToolResults(socket)
            })
            .catch((error) => {
              item.response = { ok: false, error: error?.message || 'tool execution failed' }
              flushToolResults(socket)
            })
          break
        }

        case 'session.ended':
          logEvent('down', msg.type)
          if (ws === socket) {
            ws = null
            finishConnection({ state: 'idle' })
          }
          try { socket.close() } catch (_) {}
          break

        case 'session.error': {
          sessionHadError = true
          const detail = describeSessionError(msg)
          console.error('Voice Agent session error', {
            code: msg.code,
            message: msg.message,
            agent: AGENT.name,
            mode: AGENT.mode,
            sessionId: currentSessionId,
          })
          logEvent('down', msg.type, `${msg.code}: ${msg.message}`)
          if (ws === socket) {
            ws = null
            finishConnection({ state: 'error', detail, retry: true })
          }
          try { socket.close() } catch (_) {}
          break
        }

        default:
          logEvent('down', msg.type)
      }
    }

    socket.onclose = (event) => {
      clearReadyTimeout()
      if (ws !== socket) return
      ws = null

      if (intentionalStop) {
        finishConnection({ state: 'idle' })
        return
      }
      if (sessionHadError) {
        // session.error already rendered a specific, actionable message.
        cleanupAudio()
        resetControls({ retry: true })
        return
      }

      const detail = event.reason
        ? `voice link closed: ${event.reason}`
        : `voice link closed (${event.code})`
      finishConnection({ state: 'disconnected', detail, retry: true })
    }

    socket.onerror = () => {
      if (ws !== socket || intentionalStop || sessionHadError) return
      sessionHadError = true
      console.error('Voice WebSocket connection failed', { agent: AGENT.name, mode: AGENT.mode })
      ws = null
      finishConnection({
        state: 'error',
        detail: 'voice connection failed — retry the call',
        retry: true,
      })
      try { socket.close() } catch (_) {}
    }
  } catch (error) {
    console.error('Could not start voice session', error)
    if (ws) {
      try { ws.close() } catch (_) {}
      ws = null
    }
    finishConnection({
      state: 'error',
      detail: error?.message || 'could not start voice session',
      retry: true,
    })
  }
}

function stop() {
  intentionalStop = true
  clearReadyTimeout()
  sessionReady = false

  const socket = ws
  ws = null

  if (socket?.readyState === WebSocket.OPEN) {
    try {
      socket.send(JSON.stringify({ type: 'session.end' }))
      logEvent('up', 'session.end')
    } catch (_) {}
    // Give session.end a brief chance to flush, then close locally. Event
    // handlers ignore this socket because it is no longer the active one.
    setTimeout(() => {
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        try { socket.close() } catch (_) {}
      }
    }, 500)
  } else if (socket) {
    try { socket.close() } catch (_) {}
  }

  finishConnection({ state: 'idle' })
  intentionalStop = false
}

function setStatus(state, detail) {
  voiceState = state
  $('status').className = 'status ' + state
  $('status-text').textContent = detail || state
  $('status').title = detail || state
}

// Small read-only hook for debugging a deployed build without exposing the
// AssemblyAI API key or session token.
window.DIVE_VOICE_DEBUG = () => ({
  state: voiceState,
  agent: { ...AGENT },
  sessionId: currentSessionId,
  socketState: ws?.readyState ?? null,
})

// $4.50 an hour, the list price at assemblyai.com/pricing. Billing is per
// session minute, so the running figure is an estimate, not an invoice.
const COST_PER_SECOND = 4.5 / 3600

function tick() {
  const seconds = Math.floor((Date.now() - callStart) / 1000)
  $('elapsed').textContent =
    Math.floor(seconds / 60) + ':' + String(seconds % 60).padStart(2, '0')
  $('cost').textContent = '$' + (seconds * COST_PER_SECOND).toFixed(3)
}

// --- transcript ---
const partialText = {}
const partialEl = {}
// The full reply arrives once its audio has been sent, which beats the audio
// playing out, so deltas keep coming after the line is printed. printedReply
// stops them rebuilding the same sentence underneath it.
let liveReply = null
let printedReply = null

// Deltas arrive with a leading space sometimes and without it other times, so
// add one only when neither side has one and the delta is not punctuation.
const ATTACHES_LEFT = /^[.,!?;:%°)\]}…'"’”]/
const NO_SPACE_AFTER = /[([{$\-\/'"‘“]$/

function appendDelta(text, delta) {
  if (!delta) return text
  if (!text) return delta
  if (/^\s/.test(delta) || /\s$/.test(text)) return text + delta
  if (ATTACHES_LEFT.test(delta) || NO_SPACE_AFTER.test(text)) return text + delta
  return text + ' ' + delta
}

function dropPartial(who) {
  partialEl[who]?.remove()
  delete partialEl[who]
  delete partialText[who]
}

function transcriptLine(who, text, cls) {
  const line = document.createElement('div')
  line.className = 'line ' + who + (cls ? ' ' + cls : '')
  const label = document.createElement('span')
  label.className = 'who'
  label.textContent = who === 'agent' ? AGENT.name : who
  const body = document.createElement('span')
  body.className = 'said'
  body.textContent = text
  line.append(label, body)
  return line
}

function clearEmpty(el) {
  const empty = el.querySelector('.empty')
  if (empty) empty.remove()
}

function scroll(el) {
  el.scrollTop = el.scrollHeight
}

function partial(who, text) {
  clearEmpty($('transcript'))
  partialText[who] = text
  if (partialEl[who]) {
    partialEl[who].querySelector('.said').textContent = text
  } else {
    partialEl[who] = transcriptLine(who, text, 'partial')
    $('transcript').append(partialEl[who])
  }
  scroll($('transcript'))
}

function addLine(who, text) {
  clearEmpty($('transcript'))
  dropPartial(who)
  $('transcript').append(transcriptLine(who, text))
  scroll($('transcript'))
}

function clearPartials() {
  for (const who of Object.keys(partialEl)) dropPartial(who)
  liveReply = printedReply = null
}

// --- event log ---
// Audio frames arrive ~190 times a second each way, so these types hold a row
// open and count into it. Both streams run at once, hence a row per key.
const COALESCE = new Set([
  'input.audio',
  'reply.audio',
  'transcript.user.delta',
  'transcript.agent.delta',
])
const open = new Map()

function eventRow(direction, type, detail) {
  const row = document.createElement('div')
  row.className = 'event ' + direction
  const at = document.createElement('span')
  at.className = 'at'
  at.textContent = (callStart ? (Date.now() - callStart) / 1000 : 0).toFixed(1) + 's'
  const arrow = document.createElement('span')
  arrow.className = 'dir'
  arrow.textContent = direction === 'up' ? '↑' : '↓'
  const name = document.createElement('span')
  name.className = 'type'
  name.textContent = type
  const count = document.createElement('span')
  count.className = 'count'
  const info = document.createElement('span')
  info.className = 'detail'
  if (detail) info.textContent = detail
  row.append(at, arrow, name, count, info)
  return row
}

// Ten repaints a second, plus one when the run closes.
function paint(live, final) {
  const now = performance.now()
  if (!final && now - live.painted < 100) return
  live.painted = now
  live.row.querySelector('.count').textContent = live.count > 1 ? '×' + live.count : ''
  if (live.detail) live.row.querySelector('.detail').textContent = live.detail
}

function logEvent(direction, type, detail) {
  const log = $('events-body')
  clearEmpty(log)
  const key = direction + ' ' + type
  const live = open.get(key)
  if (live) {
    live.count += 1
    if (detail) live.detail = detail
    paint(live)
    return
  }
  // A real event closes the open runs, so the next burst starts a new row.
  if (!COALESCE.has(type)) {
    open.forEach((run) => paint(run, true))
    open.clear()
  }
  // Only follow the tail if the reader is there.
  const atBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 40
  const row = eventRow(direction, type, detail)
  log.append(row)
  while (log.children.length > 400) log.firstChild.remove()
  if (COALESCE.has(type)) open.set(key, { row, count: 1, detail, painted: 0 })
  if (atBottom) scroll(log)
}
