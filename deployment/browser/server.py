#!/usr/bin/env python3
"""Serve the Dive Copilot browser client using inline Voice Agent sessions.

The AssemblyAI API key and tool HTTP configuration stay on this server. The
browser receives only a short-lived Voice Agent token plus the non-secret
session configuration it must send in the first ``session.update`` message.

This deliberately does *not* publish or look up a stored AssemblyAI agent, so a
stale ``AGENT_ID`` can no longer prevent the service from starting.
"""

import copy
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from lib import ApiError, aai, load_env, read_agent, required  # noqa: E402


AGENT: dict[str, Any] = {}
SESSION_CONFIG: dict[str, Any] = {}
PAGE = ""


def _resolve_prompt(value: Any) -> Any:
    """Resolve the starter's ``@file:...`` prompt notation for inline use."""
    if not isinstance(value, str) or not value.startswith("@file:"):
        return value

    relative = value[len("@file:"):].strip()
    path = (ROOT / "agents" / relative).resolve()
    agents_root = (ROOT / "agents").resolve()
    if agents_root not in path.parents:
        raise ValueError(f"Prompt path escapes agents directory: {relative}")
    return path.read_text(encoding="utf-8")


def _inline_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """Convert a stored-agent tool definition to an inline function tool.

    HTTP execution metadata stays server-side. The browser sends tool calls to
    this process through /tool; this process then calls the configured backend.
    """
    public = copy.deepcopy(tool)
    public.pop("http", None)
    public["type"] = "function"
    return public


def build_inline_session(agent: dict[str, Any]) -> dict[str, Any]:
    """Translate agents/<name>.jsonc into a Voice Agent session.update body."""
    session: dict[str, Any] = {}

    if "system_prompt" in agent:
        session["system_prompt"] = _resolve_prompt(agent["system_prompt"])
    if "greeting" in agent:
        session["greeting"] = agent["greeting"]
    if agent.get("input"):
        session["input"] = copy.deepcopy(agent["input"])
    if agent.get("tools"):
        session["tools"] = [_inline_tool(tool) for tool in agent["tools"]]

    # Stored-agent JSON uses voice.voice_id. Inline session configuration uses
    # output.voice.
    voice_id = (agent.get("voice") or {}).get("voice_id")
    if voice_id:
        session["output"] = {"voice": voice_id}

    return session


def public_agent() -> dict[str, Any]:
    """Diagnostic representation safe to expose in the browser."""
    return {
        "name": AGENT.get("name", "Dive Copilot"),
        "mode": "inline",
        "session": copy.deepcopy(SESSION_CONFIG),
    }


def _tool_http_config(name: str) -> dict[str, Any] | None:
    for tool in AGENT.get("tools", []):
        if tool.get("name") == name:
            return tool.get("http")
    return None


def _headers_from_config(config: Any) -> dict[str, str]:
    if isinstance(config, dict):
        return {str(k): str(v) for k, v in config.items()}
    headers: dict[str, str] = {}
    if isinstance(config, list):
        for item in config:
            if isinstance(item, dict) and item.get("name") is not None:
                headers[str(item["name"])] = str(item.get("value", ""))
    return headers


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute one agent HTTP tool without exposing its endpoint to the client."""
    http = _tool_http_config(name)
    if not http:
        return {"ok": False, "error": f"Unknown or non-HTTP tool: {name}"}

    method = str(http.get("http_method") or "POST").upper()
    url = str(http.get("url") or "")
    if not url:
        return {"ok": False, "error": f"Tool {name} has no HTTP URL"}

    headers = _headers_from_config(http.get("headers"))
    data = None

    if method in {"GET", "DELETE"}:
        if arguments:
            query = urllib.parse.urlencode(arguments, doseq=True)
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{query}"
    else:
        headers.setdefault("Content-Type", "application/json")
        data = json.dumps(arguments).encode("utf-8")

    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": err.code,
            "error": raw or f"HTTP {err.code}",
        }
    except (urllib.error.URLError, TimeoutError) as err:
        return {"ok": False, "error": str(err)}

    try:
        result: Any = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        result = {"text": raw}

    return {"ok": True, "status": status, "result": result}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(
        self,
        status: int,
        body: bytes,
        content_type: str,
        *,
        cache_control: str = "no-store",
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache_control)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: Any) -> None:
        self._send(status, json.dumps(payload).encode("utf-8"), "application/json")

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]

        if path == "/session-config":
            try:
                token = aai("/token?product=voice_agent&expires_in_seconds=60")
                if not token.get("token"):
                    raise ApiError("GET /token", 502, "response contained no token")
                self._json(200, {
                    "token": token["token"],
                    "agent": {
                        "name": AGENT.get("name", "Dive Copilot"),
                        "mode": "inline",
                    },
                    "session": SESSION_CONFIG,
                })
            except ApiError as err:
                print(err)
                self._json(502, {
                    "error": "could not prepare voice session",
                    "detail": str(err),
                })
            return

        # Kept for simple diagnostics and compatibility with older clients.
        if path == "/token":
            try:
                token = aai("/token?product=voice_agent&expires_in_seconds=60")
                self._json(200, token)
            except ApiError as err:
                print(err)
                self._json(502, {"error": "token request failed"})
            return

        if path == "/agent":
            self._json(200, public_agent())
            return

        if path == "/app.js":
            self._send(
                200,
                (HERE / "app.js").read_bytes(),
                "text/javascript",
                cache_control="no-cache",
            )
            return

        self._send(200, PAGE.encode("utf-8"), "text/html", cache_control="no-cache")

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        if path != "/tool":
            self._json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            name = payload.get("name")
            arguments = payload.get("arguments") or {}
            if not isinstance(name, str) or not name:
                raise ValueError("tool name is required")
            if not isinstance(arguments, dict):
                raise ValueError("tool arguments must be an object")

            result = execute_tool(name, arguments)
            self._json(200, result)
        except (ValueError, json.JSONDecodeError) as err:
            self._json(400, {"ok": False, "error": str(err)})
        except Exception as err:  # keep tool failure from crashing the server
            print(f"Tool proxy error: {err}")
            self._json(500, {"ok": False, "error": "tool execution failed"})

    def log_message(self, *args) -> None:  # quiet; explicit errors are printed
        pass


def main() -> None:
    global AGENT, SESSION_CONFIG, PAGE
    load_env()
    required("ASSEMBLYAI_API_KEY", "get one at https://www.assemblyai.com/dashboard/api-keys")

    name = os.environ.get("AGENT", "dive_copilot")
    AGENT = read_agent(name)
    SESSION_CONFIG = build_inline_session(AGENT)

    print(f'Voice agent: "{AGENT.get("name", name)}" (inline session configuration)')
    print("Stored AGENT_ID values are ignored by the browser deployment.")

    page_agent = {
        "name": AGENT.get("name", "Dive Copilot"),
        "mode": "inline",
    }
    PAGE = ((HERE / "index.html").read_text(encoding="utf-8")
            .replace("{{AGENT_NAME}}", page_agent["name"])
            .replace("{{AGENT_JSON}}", json.dumps(page_agent).replace("<", "\\u003c")))

    fixed = os.environ.get("PORT")
    port = int(fixed) if fixed else 3000
    while True:
        try:
            server = ThreadingHTTPServer(("", port), Handler)
            break
        except OSError:
            if fixed or port >= 3010:
                raise
            port += 1

    print(f"Talk to it: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
