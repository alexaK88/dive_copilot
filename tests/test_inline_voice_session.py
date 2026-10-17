from backend import app as _backend_app  # noqa: F401 - keeps project import path exercised
from deployment.browser import server
from lib import read_agent


def test_inline_session_expands_prompt_and_removes_http_metadata(monkeypatch):
    monkeypatch.setenv("AGENT", "dive_copilot")
    agent = read_agent("dive_copilot")

    session = server.build_inline_session(agent)

    assert session["system_prompt"].startswith("You are Dive Copilot")
    assert "@file:" not in session["system_prompt"]
    assert session["greeting"] == "Dive Copilot online. Ready for mission support."
    assert session["output"] == {"voice": "anna"}
    assert session["tools"]
    assert all(tool["type"] == "function" for tool in session["tools"])
    assert all("http" not in tool for tool in session["tools"])


def test_browser_inline_mode_does_not_depend_on_agent_id(monkeypatch):
    monkeypatch.setenv("AGENT_ID", "agent_deleted_or_stale")
    monkeypatch.setenv("AGENT_ID_DIVE_COPILOT", "another_stale_id")

    agent = read_agent("dive_copilot")
    session = server.build_inline_session(agent)

    assert "agent_id" not in session
    assert session["system_prompt"]
    assert len(session["tools"]) == len(agent["tools"])
