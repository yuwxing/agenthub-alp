import importlib, os, traceback

HANDLERS_DIR = os.path.join(os.path.dirname(__file__), "handlers")
_HANDLER_CACHE = {}

def load_handler(agent_id, name):
    key = f"{agent_id}:{name}"
    if key in _HANDLER_CACHE:
        return _HANDLER_CACHE[key]
    try:
        mod = importlib.import_module(f"handlers.{name}")
        fn = getattr(mod, "run", None)
        _HANDLER_CACHE[key] = fn
        return fn
    except (ImportError, AttributeError):
        _HANDLER_CACHE[key] = None
        return None

def execute_pipeline(team, user_input, input_path=None):
    steps = []
    data = {"user_input": user_input, "input_path": input_path}
    context = {"task": user_input}
    for idx, agent in enumerate(team):
        name = agent["name"]
        aid = agent["agent_id"]
        role = agent.get("role", "")
        step = {"agent_id": aid, "name": name, "role": role, "status": "pending", "result": None}
        fn = load_handler(aid, name)
        if fn is None:
            step["status"] = "skipped"
            step["result"] = {"note": f"no handler for '{name}'"}
        else:
            try:
                step["status"] = "running"
                output = fn(data, context)
                step["status"] = "done"
                step["result"] = output
                data = output
            except Exception as e:
                step["status"] = "error"
                step["result"] = {"error": str(e), "trace": traceback.format_exc().splitlines()[-3:]}
        steps.append(step)
    return steps
