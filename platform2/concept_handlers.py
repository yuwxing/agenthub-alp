"""30 概念智能体处理函数 + 5 动作智能体处理函数
每个函数签名: fn(input_data: dict, context: dict, memory: Memory) -> dict
"""
import json, os, csv
from datetime import datetime

# ═══════════════════════════════════════════════════════
# Stage 1 — Identity & Capability (身份层)
# ═══════════════════════════════════════════════════════

def agent_c01(data, ctx, mem):
    """C01 agent — 智能体自身的描述与元数据"""
    agent_info = {
        "agent_id": "C01",
        "name": "agent",
        "type": "concept",
        "description": "智能体自身的描述与元数据",
    }
    mem.set_short("agent_meta", agent_info)
    mem.set_short("agent_id", agent_info["agent_id"])
    return agent_info

def capability_c28(data, ctx, mem):
    """C28 capability — Agent拥有的可执行能力集合"""
    task = data.get("input", ctx.get("input", ""))
    all_agents = mem.get_short("agents_json", [])
    goal = mem.get_short("goal", {})
    capabilities = []
    for a in all_agents:
        desc = a.get("description", "")
        if any(kw in desc or kw in task for kw in ["分析", "生成", "读取", "分类", "比较", "分配"]):
            capabilities.append({"agent_id": a["id"], "name": a["name"], "desc": desc})
    result = {"capabilities": capabilities, "count": len(capabilities)}
    mem.set_short("capabilities", result)
    return result

def identity_c29(data, ctx, mem):
    """C29 identity — 智能体的唯一标识与人格边界"""
    identities = {
        "system": "AgentHub OS v2.0",
        "session": mem.get_short("session_id", "unknown"),
        "agents_in_team": mem.get_short("team_selection", []),
        "boundaries": ["只使用已注册的智能体", "每个智能体只执行其能力范围内的任务"],
    }
    mem.set_short("identity", identities)
    return identities


# ═══════════════════════════════════════════════════════
# Stage 2 — Context & Environment (上下文层)
# ═══════════════════════════════════════════════════════

def context_c19(data, ctx, mem):
    """C19 context — 当前环境与任务背景"""
    user_input = data.get("input", ctx.get("input", ""))
    context = {
        "raw_input": user_input,
        "timestamp": datetime.utcnow().isoformat(),
        "source": data.get("source", "user"),
        "language": "zh-CN",
    }
    mem.set_short("context", context)
    return context

def environment_c13(data, ctx, mem):
    """C13 environment — 运行环境与上下文"""
    env = {
        "platform": "AgentHub OS",
        "version": "2.0",
        "mode": ctx.get("config", {}).get("mode", "auto"),
        "available_memory": True,
        "runtime": "python3",
    }
    mem.set_short("environment", env)
    return env

def user_c12(data, ctx, mem):
    """C12 user — 人类用户的画像与偏好"""
    user_input = data.get("input", ctx.get("input", ""))
    user_info = mem.get_long("user", "profile", {"anonymous": True})
    intent = mem.get_short("intent", {})
    user = {
        "profile": user_info,
        "current_input": user_input,
        "intent": intent.get("intent", "unknown"),
        "preferences": user_info.get("preferences", {}),
    }
    mem.set_short("user", user)
    return user

def time_c14(data, ctx, mem):
    """C14 time — 时间相关的调度与约束"""
    now = datetime.utcnow()
    time_info = {
        "current": now.isoformat(),
        "hour": now.hour,
        "day_of_week": now.weekday(),
        "constraints": ctx.get("config", {}).get("time_constraints", []),
    }
    mem.set_short("time", time_info)
    return time_info


# ═══════════════════════════════════════════════════════
# Stage 3 — Goal & Intent (目标层)
# ═══════════════════════════════════════════════════════

def goal_c02(data, ctx, mem):
    """C02 goal — 目标定义与达成标准"""
    user_input = data.get("input", ctx.get("input", ""))
    keywords = {
        "分析": "完成数据分析和洞察",
        "生成": "生成内容或报告",
        "分类": "完成数据分类和分组",
        "比较": "完成对比分析",
        "读取": "读取和加载数据",
        "分配": "分配任务或资源",
        "预测": "预测未来趋势",
        "规划": "制定执行计划",
    }
    detected = "执行用户指定的任务"
    for kw, goal_desc in keywords.items():
        if kw in user_input:
            detected = goal_desc
            break
    goal = {
        "description": detected,
        "criteria": ["所有步骤执行完成", "无错误"],
        "status": "defined",
    }
    mem.set_short("goal", goal)
    return goal

def objective_c30(data, ctx, mem):
    """C30 objective — 可衡量的目标结果"""
    goal = mem.get_short("goal", {})
    objective = {
        "measurable": goal.get("criteria", []),
        "success_criteria": [
            "所有智能体返回 status=done",
            "最终输出包含结果",
        ],
        "status": "defined",
    }
    mem.set_short("objective", objective)
    return objective

def intent_c20(data, ctx, mem):
    """C20 intent — 用户真正目的"""
    user_input = data.get("input", ctx.get("input", ""))
    intent_type = "unknown"
    if any(kw in user_input for kw in ["分析", "统计", "趋势"]):
        intent_type = "analysis"
    elif any(kw in user_input for kw in ["生成", "创建", "写"]):
        intent_type = "generation"
    elif any(kw in user_input for kw in ["分类", "分组"]):
        intent_type = "classification"
    elif any(kw in user_input for kw in ["比较", "对比"]):
        intent_type = "comparison"
    elif any(kw in user_input for kw in ["读取", "加载", "查看"]):
        intent_type = "reading"
    intent = {"intent": intent_type, "original": user_input, "confidence": 0.85}
    mem.set_short("intent", intent)
    return intent


# ═══════════════════════════════════════════════════════
# Stage 4 — Planning (规划层)
# ═══════════════════════════════════════════════════════

def task_c03(data, ctx, mem):
    """C03 task — 可执行的工作单元"""
    goal = mem.get_short("goal", {})
    intent = mem.get_short("intent", {})
    tasks = []
    template = {
        "analysis": [
            {"id": "T1", "name": "数据加载", "action": "read", "deps": []},
            {"id": "T2", "name": "数据分析", "action": "analyze", "deps": ["T1"]},
            {"id": "T3", "name": "结果整理", "action": "generate", "deps": ["T2"]},
        ],
        "generation": [
            {"id": "T1", "name": "读取输入", "action": "read", "deps": []},
            {"id": "T2", "name": "生成内容", "action": "generate", "deps": ["T1"]},
        ],
        "classification": [
            {"id": "T1", "name": "读取数据", "action": "read", "deps": []},
            {"id": "T2", "name": "分类处理", "action": "classify", "deps": ["T1"]},
            {"id": "T3", "name": "生成报告", "action": "generate", "deps": ["T2"]},
        ],
        "comparison": [
            {"id": "T1", "name": "读取数据", "action": "read", "deps": []},
            {"id": "T2", "name": "比较分析", "action": "compare", "deps": ["T1"]},
            {"id": "T3", "name": "生成报告", "action": "generate", "deps": ["T2"]},
        ],
        "reading": [
            {"id": "T1", "name": "读取数据", "action": "read", "deps": []},
        ],
    }
    tasks = template.get(intent.get("intent"), template["analysis"])
    result = {"tasks": tasks, "count": len(tasks), "goal": goal.get("description", "")}
    mem.set_short("task_list", tasks)
    return result

def plan_c24(data, ctx, mem):
    """C24 plan — 达成目标的路径"""
    tasks = mem.get_short("task_list", [])
    plan = {
        "steps": [{"step": i+1, "task": t["name"], "action": t["action"]}
                  for i, t in enumerate(tasks)],
        "total_steps": len(tasks),
        "status": "ready",
    }
    mem.set_short("plan", plan)
    return plan

def priority_c26(data, ctx, mem):
    """C26 priority — 决策排序"""
    tasks = mem.get_short("task_list", [])
    priorities = []
    for i, t in enumerate(tasks):
        p = "high" if i == 0 else "medium" if i < 3 else "low"
        priorities.append({"task": t["name"], "priority": p, "order": i+1})
    result = {"priorities": priorities}
    mem.set_short("priorities", result)
    return result

def constraint_c25(data, ctx, mem):
    """C25 constraint — 限制条件"""
    tasks = mem.get_short("task_list", [])
    task_deps = {}
    for t in tasks:
        task_deps[t["id"]] = t.get("deps", [])
    constraints = {
        "dependencies": task_deps,
        "rules": ["任务必须按依赖顺序执行", "每个任务只能执行一次"],
    }
    mem.set_short("constraints", constraints)
    return constraints


# ═══════════════════════════════════════════════════════
# Stage 5 — Knowledge & Data (知识层)
# ═══════════════════════════════════════════════════════

def knowledge_c08(data, ctx, mem):
    """C08 knowledge — 领域知识与规则库"""
    task = data.get("input", ctx.get("input", ""))
    knowledge = mem.search_long("knowledge", task)
    relations = mem.query_relations(predicate="related_to")
    known = []
    for r in relations:
        known.append({"subject": r["subject"], "object": r["object"]})
    result = {"knowledge_found": knowledge, "relations": known, "count": len(known)}
    mem.set_short("knowledge", result)
    return result

def data_c09(data, ctx, mem):
    """C09 data — 结构化与非结构化数据"""
    input_path = data.get("input_path", ctx.get("input_path", ""))
    user_input = data.get("input", ctx.get("input", ""))
    data_info = {"source": input_path or "user_input", "raw": user_input, "format": "text"}
    if input_path and os.path.exists(input_path):
        ext = os.path.splitext(input_path)[1].lower()
        data_info["format"] = ext.lstrip(".") if ext else "text"
        data_info["path"] = input_path
    mem.set_short("data_info", data_info)
    return data_info

def memory_c07(data, ctx, mem):
    """C07 memory — 短期与长期记忆管理"""
    session_id = mem.get_short("session_id", "")
    history = mem.get_history(limit=10)
    short_term = mem.get_all_short()
    long_term_facts = {}
    for ns in ["user", "knowledge", "workflow"]:
        rows = mem.search_long(ns, "")
        long_term_facts[ns] = rows
    result = {
        "session_id": session_id,
        "short_term_keys": list(short_term.keys()),
        "recent_history": len(history),
        "long_term_facts": {k: len(v) for k, v in long_term_facts.items()},
    }
    mem.set_short("memory_state", result)
    return result

def resource_c11(data, ctx, mem):
    """C11 resource — 可调用的能力与资产"""
    agents_json = mem.get_short("agents_json", [])
    concept_count = sum(1 for a in agents_json if a.get("type") == "concept")
    action_count = sum(1 for a in agents_json if a.get("type") == "action")
    resources = {
        "agents_total": len(agents_json),
        "concept_agents": concept_count,
        "action_agents": action_count,
        "available": True,
    }
    mem.set_short("resources", resources)
    return resources

def skill_c06(data, ctx, mem):
    """C06 skill — 智能体具备的能力"""
    agents_json = mem.get_short("agents_json", [])
    skills = []
    for a in agents_json:
        if a.get("type") == "action":
            skills.append({"agent_id": a["id"], "name": a["name"], "desc": a.get("description", "")})
    result = {"skills": skills, "count": len(skills)}
    mem.set_short("skills", result)
    return result

def tool_c10(data, ctx, mem):
    """C10 tool — 可调用的外部工具"""
    tools = [
        {"name": "read", "desc": "读取CSV/JSON/TXT文件"},
        {"name": "analyze", "desc": "数据分析统计"},
        {"name": "classify", "desc": "数据分类分组"},
        {"name": "compare", "desc": "比较差异分析"},
        {"name": "generate", "desc": "生成报告内容"},
        {"name": "memory_store", "desc": "持久化存储"},
        {"name": "memory_retrieve", "desc": "检索已存信息"},
    ]
    result = {"tools": tools, "count": len(tools)}
    mem.set_short("tools", result)
    return result


# ═══════════════════════════════════════════════════════
# Stage 6 — Execution Context (执行上下文层)
# ═══════════════════════════════════════════════════════

def object_c04(data, ctx, mem):
    """C04 object — 被处理的实体"""
    user_input = data.get("input", ctx.get("input", ""))
    task_list = mem.get_short("task_list", [])
    objects = []
    for t in task_list:
        objects.append({"task": t["name"], "type": "data", "status": "pending"})
    result = {"objects": objects, "count": len(objects)}
    mem.set_short("objects", result)
    return result

def attribute_c21(data, ctx, mem):
    """C21 attribute — 对象特征"""
    objects = mem.get_short("objects", {}).get("objects", [])
    attributes = []
    for obj in objects:
        attributes.append({
            "entity": obj["task"],
            "attributes": {"type": obj["type"], "status": obj["status"], "priority": "medium"},
        })
    result = {"attributes": attributes}
    mem.set_short("attributes", result)
    return result

def relation_c22(data, ctx, mem):
    """C22 relation — 对象之间连接"""
    tasks = mem.get_short("task_list", [])
    relations = []
    for t in tasks:
        for dep in t.get("deps", []):
            dep_task = next((x for x in tasks if x["id"] == dep), None)
            if dep_task:
                relations.append({
                    "from": dep_task["name"],
                    "to": t["name"],
                    "type": "depends_on",
                })
                mem.add_relation(dep_task["name"], "depends_on", t["name"])
    result = {"relations": relations}
    mem.set_short("relations", result)
    return result

def state_c05(data, ctx, mem):
    """C05 state — 实体或系统的当前状态"""
    node_status = {}
    for key in list(mem.get_all_short().keys()):
        if key.startswith("node_") and key.endswith("_status"):
            node_id = key.replace("_status", "").replace("node_", "")
            node_status[node_id] = mem.get_short(key)
    state = {
        "phase": "execution",
        "node_status": node_status,
        "memory_snapshot": list(mem.get_all_short().keys()),
    }
    mem.set_short("state", state)
    return state

def process_c23(data, ctx, mem):
    """C23 process — 连续任务链"""
    tasks = mem.get_short("task_list", [])
    chain = [{"position": i+1, "task": t["name"], "id": t["id"]}
             for i, t in enumerate(tasks)]
    result = {"chain": chain, "length": len(chain), "status": "active"}
    mem.set_short("process", result)
    return result


# ═══════════════════════════════════════════════════════
# Stage 7 — Execution Control (控制层)
# ═══════════════════════════════════════════════════════

def event_c15(data, ctx, mem):
    """C15 event — 发生的事件与触发"""
    events = [{
        "type": "workflow_started",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "user_input",
    }]
    mem.set_short("events", events)
    return {"events": events, "count": len(events)}

def rule_c16(data, ctx, mem):
    """C16 rule — 业务规则与逻辑约束"""
    rules = [
        {"id": "R1", "rule": "概念智能体必须先于动作智能体执行",
         "enforced_by": "engine2.py topological sort"},
        {"id": "R2", "rule": "每个节点执行结果必须持久化到 memory",
         "enforced_by": "engine2.py callback"},
        {"id": "R3", "rule": "出错节点不影响同级节点执行",
         "enforced_by": "engine2.py parallel executor"},
    ]
    mem.set_short("rules", rules)
    return {"rules": rules}


# ═══════════════════════════════════════════════════════
# Stage 8 — Evaluation (评估层)
# ═══════════════════════════════════════════════════════

def result_c17(data, ctx, mem):
    """C17 result — 执行结果与产出"""
    node_results = {}
    for key in list(mem.get_all_short().keys()):
        if key.startswith("node_") and key.endswith("_result"):
            node_id = key.replace("_result", "").replace("node_", "")
            node_results[node_id] = mem.get_short(key)
    report = mem.get_short("_report", {})
    result = {
        "execution_report": report,
        "node_results_summary": list(node_results.keys()),
        "output": mem.get_short("output", ""),
    }
    mem.set_short("result", result)
    return result

def feedback_c18(data, ctx, mem):
    """C18 feedback — 反馈收集与闭环"""
    node_status = {}
    for key in list(mem.get_all_short().keys()):
        if key.startswith("node_") and key.endswith("_status"):
            node_id = key.replace("_status", "").replace("node_", "")
            node_status[node_id] = mem.get_short(key)
    errors = [k for k, v in node_status.items() if v == "error"]
    feedback = {
        "completed": sum(1 for v in node_status.values() if v == "done"),
        "errors": errors,
        "suggestions": ["重试出错节点"] if errors else [],
        "feedback_loop": "closed",
    }
    mem.set_short("feedback", feedback)
    mem.store_long("feedback", f"session_{mem.get_short('session_id')}", feedback)
    return feedback

def confidence_c27(data, ctx, mem):
    """C27 confidence — 结果可信程度"""
    node_status = {}
    for key in list(mem.get_all_short().keys()):
        if key.startswith("node_") and key.endswith("_status"):
            node_id = key.replace("_status", "").replace("node_", "")
            node_status[node_id] = mem.get_short(key)
    total = len(node_status) or 1
    errors = sum(1 for v in node_status.values() if v == "error")
    done = sum(1 for v in node_status.values() if v == "done")
    confidence = done / total if total > 0 else 0
    result = {
        "confidence_score": round(confidence, 2),
        "done_ratio": f"{done}/{total}",
        "errors": errors,
        "assessment": "高" if confidence > 0.8 else "中" if confidence > 0.5 else "低",
    }
    mem.set_short("confidence", result)
    return result


# ═══════════════════════════════════════════════════════
# Action Handlers (重新实现 — 本地文件版本)
# ═══════════════════════════════════════════════════════

def read_a02(data, ctx, mem):
    path = data.get("input_path", ctx.get("input_path", ""))
    if not path or not os.path.exists(path):
        text = data.get("input", ctx.get("input", ""))
        return {"format": "text", "content": text, "length": len(text)}
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        import csv
        with open(path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        return {"format": "csv", "rows": rows, "count": len(rows), "columns": list(rows[0].keys()) if rows else []}
    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            data_json = json.load(f)
        return {"format": "json", "data": data_json}
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return {"format": "text", "content": content, "length": len(content)}

def analyze_a04(data, ctx, mem):
    rows = data.get("rows", [])
    if not rows:
        return {"error": "no data to analyze"}
    numeric_cols = []
    for c in (rows[0] or {}):
        try:
            float(str(rows[0][c]).replace(",", "").replace("%", "").strip())
            numeric_cols.append(c)
        except: pass
    result = {"row_count": len(rows), "columns": list(rows[0].keys()) if rows else []}
    for col in numeric_cols[:5]:
        vals = []
        for r in rows:
            try: vals.append(float(str(r[col]).replace(",", "").replace("%", "").strip()))
            except: pass
        if vals:
            s_vals = sorted(vals)
            result[col] = {
                "min": round(min(vals), 2), "max": round(max(vals), 2),
                "avg": round(sum(vals)/len(vals), 2),
                "median": round(s_vals[len(s_vals)//2], 2),
            }
    return result

def classify_a19(data, ctx, mem):
    rows = data.get("rows", [])
    if not rows:
        return {"error": "no data to classify"}
    col = data.get("classify_column", list(rows[0].keys())[0] if rows else "")
    groups = {}
    for r in rows:
        key = r.get(col, "unknown")
        groups.setdefault(key, []).append(r)
    return {"group_count": len(groups), "groups": {k: len(v) for k, v in groups.items()}}

def compare_a07(data, ctx, mem):
    left = data.get("left", data.get("rows", []))
    right = data.get("right", [])
    if not right:
        right = left
    if not left:
        return {"error": "no data to compare"}
    l_keys = set(left[0].keys()) if left else set()
    r_keys = set(right[0].keys()) if right else set()
    return {
        "columns_only_in_left": list(l_keys - r_keys),
        "columns_only_in_right": list(r_keys - l_keys),
        "columns_common": list(l_keys & r_keys),
        "similarity": round(len(l_keys & r_keys) / max(len(l_keys | r_keys), 1), 2),
    }

def generate_a09(data, ctx, mem):
    content = data.get("input", ctx.get("input", ""))
    if not content:
        content = str(data) if data else "无输入"
    report_lines = [
        f"## AgentHub OS 执行报告",
        f"",
        f"**输入**: {str(content)[:200]}",
        f"**时间**: {datetime.utcnow().isoformat()}",
        f"",
        f"### 执行摘要",
    ]
    for key in sorted(mem.get_all_short().keys()):
        if key.startswith("node_") and key.endswith("_status"):
            nid = key.replace("node_", "").replace("_status", "")
            status = mem.get_short(key)
            report_lines.append(f"- **{nid}**: {status}")
    report_lines.extend([f"", f"---", f"*由 AgentHub OS 自动生成*"])
    report = "\n".join(report_lines)
    return {"report": report, "length": len(report)}
