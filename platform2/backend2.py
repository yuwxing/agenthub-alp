"""AgentHub OS v2 — 工作流引擎 + 持久记忆 + 30概念处理函数"""
import json, os, sys, uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).parent
AGENTS_PATH = ROOT / "data" / "agents.json"
PORT = int(os.environ.get("PORT", 3457))

from memory import Memory
from engine2 import WorkflowEngine, WorkflowDAG, NODE_HANDLER, NODE_PARALLEL, NODE_CONDITION, NODE_LOOP, NODE_MERGE
from concept_handlers import *

memory = Memory()
engine = WorkflowEngine(memory)

with open(AGENTS_PATH, encoding="utf-8") as f:
    AGENTS = json.load(f)

# ── Register all 35 handlers ───────────────────────────
HANDLER_MAP = {
    # Concept — Stage 1: Identity
    "C01": agent_c01, "C28": capability_c28, "C29": identity_c29,
    # Concept — Stage 2: Context
    "C19": context_c19, "C13": environment_c13, "C12": user_c12, "C14": time_c14,
    # Concept — Stage 3: Goal
    "C02": goal_c02, "C30": objective_c30, "C20": intent_c20,
    # Concept — Stage 4: Planning
    "C03": task_c03, "C24": plan_c24, "C26": priority_c26, "C25": constraint_c25,
    # Concept — Stage 5: Knowledge
    "C08": knowledge_c08, "C09": data_c09, "C07": memory_c07,
    "C11": resource_c11, "C06": skill_c06, "C10": tool_c10,
    # Concept — Stage 6: Execution Context
    "C04": object_c04, "C21": attribute_c21, "C22": relation_c22,
    "C05": state_c05, "C23": process_c23,
    # Concept — Stage 7: Control
    "C15": event_c15, "C16": rule_c16,
    # Concept — Stage 8: Evaluation
    "C17": result_c17, "C18": feedback_c18, "C27": confidence_c27,
    # Action
    "A02": read_a02, "A04": analyze_a04, "A19": classify_a19,
    "A07": compare_a07, "A09": generate_a09,
    # Name-based fallback
    "agent": agent_c01, "capability": capability_c28, "identity": identity_c29,
    "context": context_c19, "environment": environment_c13, "user": user_c12, "time": time_c14,
    "goal": goal_c02, "objective": objective_c30, "intent": intent_c20,
    "task": task_c03, "plan": plan_c24, "priority": priority_c26, "constraint": constraint_c25,
    "knowledge": knowledge_c08, "data": data_c09, "memory": memory_c07,
    "resource": resource_c11, "skill": skill_c06, "tool": tool_c10,
    "object": object_c04, "attribute": attribute_c21, "relation": relation_c22,
    "state": state_c05, "process": process_c23,
    "event": event_c15, "rule": rule_c16,
    "result": result_c17, "feedback": feedback_c18, "confidence": confidence_c27,
    "read": read_a02, "analyze": analyze_a04, "classify": classify_a19,
    "compare": compare_a07, "generate": generate_a09,
}

for name, fn in HANDLER_MAP.items():
    engine.register_handler(name, fn)
    engine.register_handler(name.upper(), fn)

# store agents in memory for handlers
memory.set_short("agents_json", AGENTS)


def build_dag_from_team(team, user_input):
    """Convert LLM-recommended team into a DAG."""
    dag = WorkflowDAG(workflow_id=f"wf_{uuid.uuid4().hex[:8]}")
    prev_id = None
    for i, agent in enumerate(team):
        aid = agent.get("agent_id", f"n{i}")
        nid = f"{aid}_{i}"
        dag.add_node(nid, NODE_HANDLER, agent_id=aid, name=agent.get("name", ""),
                     config={"role": agent.get("role", "")})
        if prev_id:
            dag.add_edge(prev_id, nid)
        prev_id = nid
    return dag


def build_full_dag(team, user_input, input_path=""):
    """Build a DAG with concept → parallel → action → evaluate stages."""
    dag = WorkflowDAG(workflow_id=f"wf_{uuid.uuid4().hex[:8]}")

    # Stage 1-2: Identity + Context (parallel)
    dag.add_node("stage1_2", NODE_PARALLEL, children=[
        "C01", "C28", "C29", "C19", "C13", "C12", "C14"
    ])

    # Stage 3-4: Goal + Planning (sequential)
    dag.add_node("C02", agent_id="C02")
    dag.add_edge("stage1_2", "C02")
    dag.add_node("C30", agent_id="C30")
    dag.add_edge("C02", "C30")
    dag.add_node("C20", agent_id="C20")
    dag.add_edge("C30", "C20")
    dag.add_node("C03", agent_id="C03")
    dag.add_edge("C20", "C03")
    dag.add_node("C24", agent_id="C24")
    dag.add_edge("C03", "C24")
    dag.add_node("C26", agent_id="C26")
    dag.add_edge("C24", "C26")
    dag.add_node("C25", agent_id="C25")
    dag.add_edge("C26", "C25")

    # Stage 5: Knowledge + Data (parallel)
    dag.add_node("stage5", NODE_PARALLEL, children=[
        "C08", "C09", "C07", "C11", "C06", "C10"
    ])
    dag.add_edge("C25", "stage5")

    # Stage 6: Execution Context (parallel)
    dag.add_node("stage6", NODE_PARALLEL, children=[
        "C04", "C21", "C22", "C05", "C23"
    ])
    dag.add_edge("stage5", "stage6")

    # Action agents (sequential — follow team order)
    prev = "stage6"
    concept_ids = {a["id"] for a in AGENTS if a["type"] == "concept"}
    for i, agent in enumerate(team):
        aid = agent.get("agent_id", "")
        if aid in concept_ids:
            continue
        nid = f"action_{aid}_{i}"
        dag.add_node(nid, NODE_HANDLER, agent_id=aid, name=agent.get("name", ""),
                     config={"role": agent.get("role", ""), "input_ref": "output"})
        dag.add_edge(prev, nid)
        prev = nid

    # Stage 8: Evaluation (parallel)
    dag.add_node("stage8", NODE_PARALLEL, children=["C17", "C18", "C27"])
    dag.add_edge(prev, "stage8")
    dag.add_node("merge", NODE_MERGE, config={"from": ["C17", "C18", "C27"]})
    dag.add_edge("stage8", "merge")

    return dag


class Handler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/memory":
            self._json(200, {
                "short_term": memory.get_all_short(),
                "long_term_namespaces": ["user", "knowledge", "feedback"],
            })
        elif self.path == "/api/handlers":
            self._json(200, {"handlers": list(engine.get_all_handlers().keys())})
        elif self.path == "/api/agents":
            self._json(200, AGENTS)
        elif self.path == "/api/history":
            self._json(200, {"episodes": memory.get_history(limit=50)})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/workflow":
            self._handle_workflow()
        elif self.path == "/api/generate-team":
            self._handle_generate_team()
        elif self.path == "/api/workflow-status":
            self._handle_workflow_status()
        else:
            self.send_error(404)

    def _handle_workflow(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        user_input = body.get("input", "")
        team = body.get("team", [])
        mode = body.get("mode", "full")

        if not user_input:
            self._json(400, {"error": "input required"})
            return
        if not team:
            self._json(400, {"error": "team required"})
            return

        try:
            if mode == "simple":
                dag = build_dag_from_team(team, user_input)
            else:
                dag = build_full_dag(team, user_input, body.get("input_path", ""))

            input_data = {
                "input": user_input,
                "input_path": body.get("input_path", ""),
                "source": "user",
            }
            report = engine.execute(dag, input_data)
            self._json(200, report)
        except Exception as e:
            import traceback
            self._json(500, {"error": str(e), "trace": traceback.format_exc().splitlines()[-10:]})

    def _handle_generate_team(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        user_input = body.get("input", "").strip()
        if not user_input:
            self._json(400, {"error": "input required"})
            return
        try:
            concept_ids = [a["id"] for a in AGENTS if a["type"] == "concept"]
            action_ids = [a["id"] for a in AGENTS if a["type"] == "action"]
            kw_map = {
                "分析": ["C02","C20","C03","C09","A04","A02"], "生成": ["C02","C20","C03","A09","A02"],
                "分类": ["C02","C20","C03","A19","A02"], "比较": ["C02","C20","C03","A07","A02"],
                "分配": ["C28","C02","C03","A30","A25"], "规划": ["C02","C24","C03","A05","A06"],
                "预测": ["C27","C02","C03","A08","A21"], "阅读": ["C02","C03","C09","A02","A04"],
            }
            selected = None
            for kw, ids in kw_map.items():
                if kw in user_input:
                    selected = ids
                    break
            if not selected:
                selected = ["C02","C20","C03","C09","A02","A04"]
            team = []
            for aid in selected:
                agent = next((a for a in AGENTS if a["id"] == aid), None)
                if agent:
                    team.append({
                        "agent_id": agent["id"], "name": agent["name"],
                        "type": agent["type"], "description": agent["description"],
                        "role": ""
                    })
            self._json(200, {"team": team, "analysis": "基于关键词匹配的 Agent 团队推荐"})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _handle_workflow_status(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        session_id = body.get("session_id", "")
        workflow_id = body.get("workflow_id", "")
        wf = memory.get_workflow(session_id, workflow_id) if session_id and workflow_id else None
        history = memory.get_history(limit=20)
        self._json(200, {
            "workflow": wf,
            "recent_episodes": history,
            "short_term_summary": list(memory.get_all_short().keys()),
        })

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        msg = "[AgentHub-v2] %s %s %s" % args
        print(msg, file=sys.stderr, flush=True)


if __name__ == "__main__":
    os.chdir(ROOT)
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    handler_names = list(HANDLER_MAP.keys())[:10]
    print(f"[AgentHub-v2] Server → http://localhost:{PORT}", file=sys.stderr, flush=True)
    print(f"[AgentHub-v2] Memory DB → {memory.db_path}", file=sys.stderr, flush=True)
    print(f"[AgentHub-v2] Registered {len(HANDLER_MAP)} handlers: {handler_names}...", file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        memory.close()
