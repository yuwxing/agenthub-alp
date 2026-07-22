def run(input_data, context):
    rows = _rows(input_data)
    if not rows:
        return {"error": "no data"}
    col = context.get("classify_by", "")
    if not col and rows:
        col = list(rows[0].keys())[-1]
    if col not in (rows[0] or {}):
        return {"error": f"column '{col}' not found"}
    groups = {}
    for r in rows:
        key = str(r.get(col, "unknown"))
        groups.setdefault(key, []).append(r)
    summary = {k: len(v) for k, v in sorted(groups.items(), key=lambda x: -len(x[1]))}
    return {
        "column": col,
        "groups": summary,
        "group_count": len(groups),
        "sample": {k: v[:2] for k, v in list(groups.items())[:3]},
    }

def _rows(data):
    if isinstance(data, dict) and "rows" in data:
        return data["rows"]
    if isinstance(data, list):
        return data
    return None
