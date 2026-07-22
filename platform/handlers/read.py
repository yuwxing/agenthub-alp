import csv, json, os

def run(input_data, context):
    path = input_data if isinstance(input_data, str) else context.get("input_path", "")
    if not path or not os.path.exists(path):
        return {"error": "file not found", "path": path}
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        with open(path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        return {"format": "csv", "rows": rows, "count": len(rows), "columns": list(rows[0].keys()) if rows else []}
    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {"format": "json", "data": data}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return {"format": "text", "content": text, "length": len(text)}
