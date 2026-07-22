import json
from datetime import datetime

def run(input_data, context):
    report_lines = ["# AgentHub 自动分析报告", f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    task = context.get("task", "")
    if task:
        report_lines.append(f"> 任务: {task}")
        report_lines.append("")
    data = input_data or {}
    if isinstance(data, dict):
        for key, val in data.items():
            if key in ("error",):
                continue
            if isinstance(val, (int, float)):
                report_lines.append(f"- **{key}**: {val}")
            elif isinstance(val, dict):
                report_lines.append(f"\n### {key}")
                for k2, v2 in val.items():
                    report_lines.append(f"  - {k2}: {v2}")
            elif isinstance(val, list):
                report_lines.append(f"\n### {key} ({len(val)} 条)")
                for item in val[:10]:
                    report_lines.append(f"  - {json.dumps(item, ensure_ascii=False)}")
            else:
                report_lines.append(f"- **{key}**: {val}")
    report = "\n".join(report_lines)
    return {"report": report, "length": len(report)}
