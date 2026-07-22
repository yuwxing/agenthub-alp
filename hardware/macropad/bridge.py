"""AgentHub Macropad Bridge — Raw HID → API"""
import json
import os
import sys
import time
import urllib.request

try:
    import hid
except ImportError:
    print("Install: pip install hidapi")
    sys.exit(1)

AGENTHUB_URL = os.environ.get("AGENTHUB_URL", "http://localhost:3457")
AGENT_MAP = {
    0:  {"id": "C02", "name": "goal",     "icon": "🎯"},
    1:  {"id": "C19", "name": "context",  "icon": "🌐"},
    2:  {"id": "C09", "name": "data",     "icon": "💾"},
    3:  {"id": "C24", "name": "plan",     "icon": "🗺️"},
    4:  {"id": "A01", "name": "create",   "icon": "✨"},
    5:  {"id": "A06", "name": "execute",  "icon": "▶️"},
    6:  {"id": "A04", "name": "analyze",  "icon": "📊"},
    7:  {"id": "A03", "name": "search",   "icon": "🔍"},
    8:  {"id": "",    "name": "input",    "icon": "📝"},
    9:  {"id": "",    "name": "generate", "icon": "🤖"},
    10: {"id": "",    "name": "run",      "icon": "🚀"},
    11: {"id": "",    "name": "clear",    "icon": "⚡"},
}

def api_post(path, data):
    url = f"{AGENTHUB_URL}{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        print(f"[Bridge] API error: {e}")
        return None

def find_macropad():
    for dev in hid.enumerate(0xFEED, 0x0A0A):
        return hid.device(dev["vendor_id"], dev["product_id"])
    return None


def main():
    print("[Bridge] AgentHub Macropad Bridge")
    print(f"[Bridge] API → {AGENTHUB_URL}")
    print("[Bridge] Waiting for macropad...")

    last_report = {}  # track press/release

    while True:
        pad = find_macropad()
        if pad is None:
            time.sleep(2)
            continue

        try:
            pad.open(0xFEED, 0x0A0A)
            pad.set_nonblocking(True)
            print("[Bridge] Macropad connected!")

            while True:
                buf = pad.read(32, timeout_ms=500)
                if buf and len(buf) > 0:
                    idx = buf[0]
                    if idx < 12:
                        agent = AGENT_MAP.get(idx)
                        if not agent:
                            continue

                        icon = agent["icon"]
                        name = agent["name"]
                        print(f"[Bridge] Key: {icon} {name} (idx={idx})")

                        if name == "input":
                            print("[Bridge] Pressed 输入 — open input dialog on host")
                        elif name == "generate":
                            print("[Bridge] Pressed 生成 — call generate-team")
                            api_post("/api/generate-team", {"input": ""})
                        elif name == "run":
                            print("[Bridge] Pressed 执行 — call execute-pipeline")
                            api_post("/api/workflow", {"input": "", "team": [], "mode": "full"})
                        elif name == "clear":
                            print("[Bridge] Pressed 清空")
                        elif agent["id"]:
                            a_id = agent["id"]
                            print(f"[Bridge] Triggering {a_id} ({name})")
                            api_post("/api/workflow", {
                                "input": "",
                                "team": [{"agent_id": a_id, "name": name, "role": ""}],
                                "mode": "simple"
                            })
        except Exception as e:
            print(f"[Bridge] Error: {e}")
            pad.close()
            time.sleep(2)

if __name__ == "__main__":
    main()
