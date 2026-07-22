"""Phase 1: 用现有键盘模拟 Macropad — Ctrl+Shift+字母 触发 Agent"""
import json, os, sys, urllib.request

try:
    import keyboard
except ImportError:
    print("Install: pip install keyboard")
    sys.exit(1)

AGENTHUB_URL = os.environ.get("AGENTHUB_URL", "http://localhost:3457")

HOTKEYS = {
    "ctrl+shift+g": {"id": "C02", "name": "goal",     "icon": "goal",     "desc": "目标"},
    "ctrl+shift+h": {"id": "C19", "name": "context",  "icon": "context",  "desc": "上下文"},
    "ctrl+shift+d": {"id": "C09", "name": "data",     "icon": "data",     "desc": "数据"},
    "ctrl+shift+p": {"id": "C24", "name": "plan",     "icon": "plan",     "desc": "规划"},
    "ctrl+shift+r": {"id": "A01", "name": "create",   "icon": "create",   "desc": "创建"},
    "ctrl+shift+e": {"id": "A06", "name": "execute",  "icon": "execute",  "desc": "执行"},
    "ctrl+shift+a": {"id": "A04", "name": "analyze",  "icon": "analyze",  "desc": "分析"},
    "ctrl+shift+s": {"id": "A03", "name": "search",   "icon": "search",   "desc": "搜索"},
    "ctrl+shift+i": {"id": "_input",    "name": "input",     "icon": "input",     "desc": "聚焦输入框"},
    "ctrl+enter":   {"id": "_generate", "name": "generate",  "icon": "generate",  "desc": "生成团队"},
    "ctrl+shift+space": {"id": "_run",  "name": "run",       "icon": "run",       "desc": "执行管道"},
    "ctrl+shift+x": {"id": "_clear",    "name": "clear",     "icon": "clear",     "desc": "清空面板"},
}

def api_post(path, data):
    url = f"{AGENTHUB_URL}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        print(f"  HTTP {e.code}: {detail[:200]}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def on_trigger(agent):
    icon, name, aid = agent["icon"], agent["name"], agent["id"]
    print(f"\n--- {icon} {name} ({agent.get('desc','')}) ---")

    default_input = "AgentHub OS intelligent agent collaboration task"

    if aid == "_input":
        print("  Focus input box (on AgentBrain page)")
    elif aid == "_generate":
        print("  Calling generate-team...")
        r = api_post("/api/generate-team", {"input": default_input})
        if r:
            team_ids = [m["agent_id"] for m in (r.get("team") or [])]
            print(f"  Team: {' -> '.join(team_ids)}")
    elif aid == "_run":
        print("  Calling execute-pipeline...")
        r = api_post("/api/workflow", {"input": default_input, "team": [], "mode": "full"})
        if r:
            print(f"  Execution complete")
    elif aid == "_clear":
        print("  Cleared")
    elif aid:
        print(f"  Triggering {aid}...")
        r = api_post("/api/workflow", {
            "input": default_input,
            "team": [{"agent_id": aid, "name": name, "role": agent.get("desc", "")}],
            "mode": "simple"
        })
        if r:
            status = r.get("node_status", {})
            results = r.get("node_results", {})
            print(f"  Done: {aid}")
            for nid, s in list(status.items())[:3]:
                res = results.get(nid, {})
                if isinstance(res, dict):
                    rkeys = list(res.keys())[:3]
                    print(f"    {nid}: {', '.join(rkeys)}")

def main():
    print("=" * 56)
    print("  AgentHub Macropad - Phase 1 (Software Bridge)")
    print(f"  Backend: {AGENTHUB_URL}")
    print("  Hotkeys:")
    for combo, a in HOTKEYS.items():
        print(f"    {combo:20s} -> {a['icon']} {a['name']}")
    print("=" * 56)
    print("  Running. Press Ctrl+Shift+X to exit.\n")

    for combo, agent in HOTKEYS.items():
        keyboard.add_hotkey(combo, lambda a=agent: on_trigger(a))

    keyboard.wait("ctrl+shift+x")
    print("Exited.")

if __name__ == "__main__":
    main()
