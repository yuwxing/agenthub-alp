"""AgentHub Macropad Bridge — F13-F24 mode (no Raw HID needed)"""
import json
import os
import sys
import urllib.request

try:
    from pynput import keyboard
except ImportError:
    print("Install: pip install pynput")
    sys.exit(1)

AGENTHUB_URL = os.environ.get("AGENTHUB_URL", "http://localhost:3457")
F_KEY_MAP = {
    keyboard.Key.f13:  {"id": "C02", "name": "goal",     "icon": "🎯"},
    keyboard.Key.f14:  {"id": "C19", "name": "context",  "icon": "🌐"},
    keyboard.Key.f15:  {"id": "C09", "name": "data",     "icon": "💾"},
    keyboard.Key.f16:  {"id": "C24", "name": "plan",     "icon": "🗺️"},
    keyboard.Key.f17:  {"id": "A01", "name": "create",   "icon": "✨"},
    keyboard.Key.f18:  {"id": "A06", "name": "execute",  "icon": "▶️"},
    keyboard.Key.f19:  {"id": "A04", "name": "analyze",  "icon": "📊"},
    keyboard.Key.f20:  {"id": "A03", "name": "search",   "icon": "🔍"},
    keyboard.Key.f21:  {"id": "",    "name": "input",    "icon": "📝"},
    keyboard.Key.f22:  {"id": "",    "name": "generate", "icon": "🤖"},
    keyboard.Key.f23:  {"id": "",    "name": "run",      "icon": "🚀"},
    keyboard.Key.f24:  {"id": "",    "name": "clear",    "icon": "⚡"},
}

def api_post(path, data):
    url = f"{AGENTHUB_URL}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        print(f"[Bridge] API error: {e}")
        return None

def on_press(key):
    agent = F_KEY_MAP.get(key)
    if not agent:
        return
    icon, name, aid = agent["icon"], agent["name"], agent["id"]
    print(f"[Bridge] {icon} {name}")

    if name == "generate":
        api_post("/api/generate-team", {"input": ""})
    elif name == "run":
        api_post("/api/workflow", {"input": "", "team": [], "mode": "full"})
    elif aid:
        api_post("/api/workflow", {
            "input": "",
            "team": [{"agent_id": aid, "name": name, "role": ""}],
            "mode": "simple"
        })

def main():
    print(f"[Bridge] AgentHub Macropad Bridge (F13-F24 mode)")
    print(f"[Bridge] API → {AGENTHUB_URL}")
    print(f"[Bridge] Running. Press F13-F24 on your macropad.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
