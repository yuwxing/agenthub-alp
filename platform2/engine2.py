import json, traceback, os, uuid
from datetime import datetime

from memory import Memory

# ── Node types ──────────────────────────────────────────
NODE_HANDLER = "handler"       # execute an agent handler
NODE_PARALLEL = "parallel"     # run children in parallel
NODE_CONDITION = "condition"   # if/else branch
NODE_LOOP = "loop"             # repeat until condition met
NODE_SUBFLOW = "subflow"       # call another DAG
NODE_MERGE = "merge"           # collect parallel results

# ── DAG definition ──────────────────────────────────────
class WorkflowDAG:
    def __init__(self, workflow_id=None):
        self.workflow_id = workflow_id or f"wf_{uuid.uuid4().hex[:8]}"
        self.nodes = {}       # node_id -> dict
        self.edges = []       # (from_id, to_id)
        self.entry_nodes = [] # node_ids with no dependencies

    def add_node(self, node_id, node_type=NODE_HANDLER, agent_id=None, name=None,
                 config=None, handler_fn=None, children=None):
        self.nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "agent_id": agent_id,
            "name": name,
            "config": config or {},
            "handler_fn": handler_fn,
            "children": children or [],
        }

    def add_edge(self, from_id, to_id):
        self.edges.append((from_id, to_id))

    def build(self):
        parents = {nid: [] for nid in self.nodes}
        for f, t in self.edges:
            parents[t].append(f)
        self.entry_nodes = [nid for nid, p in parents.items() if not p]
        return self

    def to_dict(self):
        return {
            "workflow_id": self.workflow_id,
            "nodes": {k: {kk: vv for kk, vv in v.items() if kk != "handler_fn"}
                      for k, v in self.nodes.items()},
            "edges": self.edges,
            "entry_nodes": self.entry_nodes,
        }


# ── Workflow Engine ─────────────────────────────────────
class WorkflowEngine:
    def __init__(self, memory=None):
        self.memory = memory or Memory()
        self._handlers = {}

    def register_handler(self, name, fn):
        self._handlers[name] = fn

    def get_handler(self, name):
        return self._handlers.get(name)

    def get_all_handlers(self):
        return dict(self._handlers)

    def execute(self, dag, input_data, session_id=None):
        session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        dag.build()
        results = {}
        node_status = {}
        # build reverse dep map
        dependents = {nid: [] for nid in dag.nodes}
        for f, t in dag.edges:
            dependents[f].append(t)

        self.memory.clear_short_term()
        self.memory.set_short("session_id", session_id)
        self.memory.set_short("input", input_data)
        self.memory.save_workflow(session_id, dag.workflow_id, "running", "", dag.to_dict())

        def node_ready(nid):
            for f, t in dag.edges:
                status = node_status.get(f)
                if t == nid and status not in ("done", "error", "skipped"):
                    return False
            return True

        # sequential topological execution
        queue = dag.entry_nodes[:]
        executed = set()

        while queue:
            nid = queue.pop(0)
            if nid in executed:
                continue
            if not node_ready(nid):
                queue.append(nid)
                continue

            executed.add(nid)
            node = dag.nodes[nid]
            node_status[nid] = "running"
            self.memory.set_short(f"node_{nid}_status", "running")

            try:
                if node["type"] == NODE_HANDLER:
                    result = self._run_handler(node, input_data)
                elif node["type"] == NODE_PARALLEL:
                    result = self._run_parallel(node, input_data)
                elif node["type"] == NODE_CONDITION:
                    result = self._run_condition(node, input_data)
                elif node["type"] == NODE_LOOP:
                    result = self._run_loop(node, input_data)
                elif node["type"] == NODE_MERGE:
                    result = self._run_merge(node, results)
                else:
                    result = {"error": f"unknown node type: {node['type']}"}

                results[nid] = result
                node_status[nid] = "done" if "error" not in result else "error"
                self.memory.set_short(f"node_{nid}_result", result)
                self.memory.set_short(f"node_{nid}_status", node_status[nid])

                agent_id = node.get("agent_id", nid)
                self.memory.record_episode(
                    session_id, agent_id, node.get("name", nid),
                    f"{node['type']}:{nid}",
                    {"input": str(input_data)[:200]},
                    {"result": str(result)[:200]},
                    node_status[nid]
                )
                self.memory.save_workflow(session_id, dag.workflow_id, "running", nid, dag.to_dict())

                # enqueue dependents
                for dep_nid in dependents.get(nid, []):
                    if dep_nid not in executed and dep_nid not in queue:
                        queue.append(dep_nid)
            except Exception as e:
                results[nid] = {"error": str(e), "trace": traceback.format_exc().splitlines()[-5:]}
                node_status[nid] = "error"
                self.memory.set_short(f"node_{nid}_status", "error")
                for dep_nid in dependents.get(nid, []):
                    if dep_nid not in executed and dep_nid not in queue:
                        queue.append(dep_nid)

        final = self.memory.get_short("output", results.get("output", results))
        report = self._build_report(session_id, dag, results, node_status)
        self.memory.set_short("_report", report)
        self.memory.set_short("output", final)
        self.memory.save_workflow(session_id, dag.workflow_id, "completed", "", dag.to_dict(), report)
        return report

    def _run_handler(self, node, input_data):
        aid = node["agent_id"]
        name = node.get("name") or aid or ""
        config = node["config"]
        fn = self._handlers.get(aid) or self._handlers.get(name)
        if fn is None:
            fn = self._handlers.get(name.lower()) if name else None
        if fn is None:
            return {"note": f"no handler for agent {aid} ({name})", "skipped": True}
        ctx = self.memory.get_all_short()
        ctx.update({"config": config})
        # determine input: use specific input_ref or pass through
        input_ref = config.get("input_ref")
        if input_ref:
            data = self.memory.get_short(input_ref, {})
        else:
            data = input_data if isinstance(input_data, dict) else {"input": str(input_data)}
        return fn(data, ctx, self.memory)

    def _run_parallel(self, node, input_data):
        children = node.get("children", [])
        child_results = {}
        for child_id in children:
            fn = self._handlers.get(child_id)
            if fn:
                try:
                    ctx = self.memory.get_all_short()
                    data = input_data if isinstance(input_data, dict) else {"input": str(input_data)}
                    child_results[child_id] = fn(data, ctx, self.memory)
                except Exception as e:
                    child_results[child_id] = {"error": str(e)}
            else:
                child_results[child_id] = {"error": f"handler not found: {child_id}"}
        return {"parallel_results": child_results, "count": len(child_results)}

    def _run_condition(self, node, input_data):
        config = node.get("config", {})
        cond_fn_name = config.get("condition")
        cond_fn = self._handlers.get(f"cond:{cond_fn_name}")
        if cond_fn:
            decision = cond_fn(input_data, self.memory.get_all_short(), self.memory)
        else:
            field = config.get("field", "condition_result")
            expected = config.get("expected", True)
            actual = input_data.get(field) if isinstance(input_data, dict) else None
            decision = actual == expected
        branch = config.get("true_branch") if decision else config.get("false_branch")
        if branch and branch in self._handlers:
            result = self._handlers[branch](input_data, self.memory.get_all_short(), self.memory)
            return {"condition": decision, "branch": branch, "result": result}
        return {"condition": decision, "branch": branch or "none", "note": "no handler for branch"}

    def _run_loop(self, node, input_data, max_iter=20):
        config = node.get("config", {})
        body = config.get("body_handler")
        cond_name = config.get("until")
        cond_fn = self._handlers.get(f"cond:{cond_name}") if cond_name else None
        results = []
        data = input_data
        for i in range(max_iter):
            if cond_fn:
                decision = cond_fn(data, self.memory.get_all_short(), self.memory)
                if decision:
                    break
            elif config.get("max_iter"):
                if i >= config["max_iter"]:
                    break
            if body and body in self._handlers:
                result = self._handlers[body](data, self.memory.get_all_short(), self.memory)
                results.append(result)
                if isinstance(result, dict):
                    data = result
            else:
                results.append({"iteration": i, "note": "no body handler"})
                break
        return {"loop_iterations": len(results), "results": results}

    def _run_subflow(self, node, input_data, session_id, max_workers):
        config = node.get("config", {})
        sub_dag = config.get("dag")
        if sub_dag and isinstance(sub_dag, WorkflowDAG):
            return self.execute(sub_dag, input_data, session_id, max_workers)
        return {"note": "no subflow dag defined"}

    def _run_merge(self, node, results):
        config = node.get("config", {})
        source_ids = config.get("from", [])
        merged = {}
        for sid in source_ids:
            if sid in results:
                r = results[sid]
                if isinstance(r, dict):
                    if "parallel_results" in r:
                        merged.update(r["parallel_results"])
                    elif "results" in r:
                        merged[sid] = r["results"]
                    else:
                        merged[sid] = r
                else:
                    merged[sid] = r
        return merged

    def _build_report(self, session_id, dag, results, node_status):
        report = {
            "workflow_id": dag.workflow_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_nodes": len(dag.nodes),
                "completed": sum(1 for s in node_status.values() if s == "done"),
                "errors": sum(1 for s in node_status.values() if s == "error"),
                "skipped": sum(1 for s in node_status.values() if s == "skipped"),
            },
            "node_status": node_status,
            "node_results": {},
        }
        for nid in dag.nodes:
            r = results.get(nid)
            if r:
                if isinstance(r, dict) and len(str(r)) > 500:
                    summary = {k: v for k, v in r.items()
                               if k in ("note", "count", "status", "condition", "loop_iterations",
                                        "row_count", "group_count")}
                    summary["_truncated"] = True
                    report["node_results"][nid] = summary
                else:
                    report["node_results"][nid] = r
        return report
