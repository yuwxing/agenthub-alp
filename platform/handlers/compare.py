def run(input_data, context):
    rows = _rows(input_data)
    if not rows or len(rows) < 2:
        return {"error": "need at least 2 records to compare"}
    group_col = context.get("compare_by", "")
    val_col = context.get("compare_value", "")
    if not group_col and rows:
        keys = list(rows[0].keys())
        group_col = keys[0] if keys else ""
        val_col = keys[-1] if len(keys) > 1 else ""
    groups = {}
    for r in rows:
        g = str(r.get(group_col, "?"))
        v = _num(r.get(val_col))
        if v is not None:
            groups.setdefault(g, []).append(v)
    result = {}
    for g, vals in groups.items():
        result[g] = {
            "count": len(vals),
            "avg": round(sum(vals) / len(vals), 2),
            "min": round(min(vals), 2),
            "max": round(max(vals), 2),
        }
    return {
        "group_column": group_col,
        "value_column": val_col,
        "groups": result,
        "group_count": len(result),
    }

def _rows(data):
    if isinstance(data, dict) and "rows" in data:
        return data["rows"]
    if isinstance(data, list):
        return data
    return None

def _num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except:
        return None
