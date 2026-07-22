def run(input_data, context):
    rows = _get_rows(input_data)
    if not rows:
        return {"error": "no data to analyze"}
    numeric_cols = _find_numeric_cols(rows)
    result = {"row_count": len(rows), "columns": list(rows[0].keys()) if rows else []}
    for col in numeric_cols:
        vals = [_to_num(r[col]) for r in rows if _to_num(r[col]) is not None]
        if vals:
            result[col] = {
                "min": round(min(vals), 2),
                "max": round(max(vals), 2),
                "avg": round(sum(vals) / len(vals), 2),
                "median": round(sorted(vals)[len(vals)//2], 2),
            }
    text_cols = [c for c in (rows[0] or {}) if c not in numeric_cols]
    for col in text_cols[:3]:
        vals = [r.get(col, "") for r in rows]
        freq = {}
        for v in vals:
            freq[v] = freq.get(v, 0) + 1
        top = sorted(freq.items(), key=lambda x: -x[1])[:5]
        result[f"{col}_distribution"] = dict(top)
    return result

def _get_rows(data):
    if isinstance(data, dict) and "rows" in data:
        return data["rows"]
    if isinstance(data, list):
        return data
    return None

def _find_numeric_cols(rows):
    if not rows:
        return []
    return [c for c in rows[0] if any(_to_num(r.get(c)) is not None for r in rows[:10])]

def _to_num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except:
        return None
