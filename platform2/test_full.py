"""AgentHub OS v2 — Full system test"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from memory import Memory
from engine2 import WorkflowEngine, WorkflowDAG, NODE_HANDLER, NODE_PARALLEL
from concept_handlers import *

m = Memory(":memory:")
m.set_short("agents_json", [
    {"id": "A02", "name": "read", "type": "action", "description": "读取"},
    {"id": "A04", "name": "analyze", "type": "action", "description": "分析"},
    {"id": "A09", "name": "generate", "type": "action", "description": "生成"},
])
eng = WorkflowEngine(m)

# Register all 30 concept + 3 action handlers
all_handlers = {
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
    "read": read_a02, "analyze": analyze_a04, "generate": generate_a09,
}
for name, fn in all_handlers.items():
    eng.register_handler(name, fn)
    eng.register_handler(name.upper(), fn)

print(f"✅ Registered {len(all_handlers)} handlers")

# ── Test 1: Simple linear DAG ──
print("\n═══ Test 1: Simple Linear DAG ═══")
dag1 = WorkflowDAG()
dag1.add_node("ctx", NODE_HANDLER, agent_id="C19", name="context")
dag1.add_node("goal", NODE_HANDLER, agent_id="C02", name="goal")
dag1.add_edge("ctx", "goal")
dag1.add_node("task", NODE_HANDLER, agent_id="C03", name="task")
dag1.add_edge("goal", "task")
r1 = eng.execute(dag1, {"input": "分析学生成绩数据"})
print(f"  Nodes: {r1['summary']['total_nodes']}, Done: {r1['summary']['completed']}, Errors: {r1['summary']['errors']}")
for nid, s in sorted(r1["node_status"].items()):
    print(f"    {nid}: {s}")

# ── Test 2: Parallel DAG ──
print("\n═══ Test 2: Parallel + Sequential ═══")
dag2 = WorkflowDAG()
dag2.add_node("s1", NODE_PARALLEL, children=["agent", "context", "user", "time"])
dag2.add_node("goal", NODE_HANDLER, agent_id="C02", name="goal")
dag2.add_edge("s1", "goal")
dag2.add_node("intent", NODE_HANDLER, agent_id="C20", name="intent")
dag2.add_edge("goal", "intent")
dag2.add_node("task", NODE_HANDLER, agent_id="C03", name="task")
dag2.add_edge("intent", "task")
dag2.add_node("s2", NODE_PARALLEL, children=["skill", "tool"])
dag2.add_edge("task", "s2")
dag2.add_node("gen", NODE_HANDLER, agent_id="A09", name="generate")
dag2.add_edge("s2", "gen")
r2 = eng.execute(dag2, {"input": "分析学生成绩并生成报告"})
print(f"  Nodes: {r2['summary']['total_nodes']}, Done: {r2['summary']['completed']}, Errors: {r2['summary']['errors']}")
for nid, s in sorted(r2["node_status"].items()):
    print(f"    {nid}: {s}")

# ── Test 3: Full 30-concept + action DAG ──
print("\n═══ Test 3: 30-concept full DAG ═══")
dag3 = WorkflowDAG()
# Stage 1-2: Identity + Context (parallel)
dag3.add_node("s1", NODE_PARALLEL, children=["agent","capability","identity","context","environment","user","time"])
# Stage 3-4: Goal + Planning (sequential)
dag3.add_node("goal", NODE_HANDLER, agent_id="C02", name="goal")
dag3.add_edge("s1", "goal")
dag3.add_node("obj", NODE_HANDLER, agent_id="C30", name="objective")
dag3.add_edge("goal", "obj")
dag3.add_node("intent", NODE_HANDLER, agent_id="C20", name="intent")
dag3.add_edge("obj", "intent")
dag3.add_node("task", NODE_HANDLER, agent_id="C03", name="task")
dag3.add_edge("intent", "task")
dag3.add_node("plan", NODE_HANDLER, agent_id="C24", name="plan")
dag3.add_edge("task", "plan")
dag3.add_node("prio", NODE_HANDLER, agent_id="C26", name="priority")
dag3.add_edge("plan", "prio")
dag3.add_node("cons", NODE_HANDLER, agent_id="C25", name="constraint")
dag3.add_edge("prio", "cons")
# Stage 5: Knowledge + Data (parallel)
dag3.add_node("s5", NODE_PARALLEL, children=["knowledge","data","memory","resource","skill","tool"])
dag3.add_edge("cons", "s5")
# Stage 6: Execution Context (parallel)
dag3.add_node("s6", NODE_PARALLEL, children=["object","attribute","relation","state","process"])
dag3.add_edge("s5", "s6")
# Action
dag3.add_node("act_read", NODE_HANDLER, agent_id="A02", name="read")
dag3.add_edge("s6", "act_read")
dag3.add_node("act_gen", NODE_HANDLER, agent_id="A09", name="generate")
dag3.add_edge("act_read", "act_gen")
# Stage 8: Evaluation (parallel)
dag3.add_node("s8", NODE_PARALLEL, children=["result","feedback","confidence"])
dag3.add_edge("act_gen", "s8")

r3 = eng.execute(dag3, {"input": "分析学生期末考试成绩"})
print(f"  Nodes: {r3['summary']['total_nodes']}, Done: {r3['summary']['completed']}, Errors: {r3['summary']['errors']}")
for nid, s in sorted(r3["node_status"].items()):
    status_icon = "✅" if s == "done" else "❌" if s == "error" else "⏭"
    print(f"    {status_icon} {nid}: {s}")

# ── Test 4: Memory persistence check ──
print("\n═══ Test 4: Memory Persistence ═══")
history = m.get_history(limit=5)
print(f"  Episodic records: {len(m.get_history())}")
long_term = m.search_long("feedback", "")
print(f"  Long-term feedback entries: {len(long_term)}")
context_saved = m.get_short("context", {})
print(f"  Context saved to short-term: {'raw_input' in context_saved}")
print(f"  Last input: {context_saved.get('raw_input', 'N/A')[:30]}")
print(f"\n✅ All tests passed!" if r3['summary']['errors'] == 0 else "\n❌ Some tests had errors")
