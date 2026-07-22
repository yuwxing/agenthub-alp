import json, os, sys, subprocess, tempfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from engine import execute_pipeline

PORT = 3456
AGENTS_PATH = Path(__file__).parent / "data" / "agents.json"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
API_MODEL = "deepseek-chat"
if not API_KEY:
    API_KEY = os.environ.get("OPENAI_API_KEY", "")
    API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
    API_MODEL = "gpt-4o-mini"
if not API_KEY:
    print("未找到 API KEY（请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY）", file=sys.stderr)
    sys.exit(1)

with open(AGENTS_PATH, encoding="utf-8") as f:
    AGENTS = json.load(f)

SYSTEM_PROMPT = """你是 AgentHub OS 的智能体编排引擎。
你的任务是根据用户的需求描述，从以下 60 个基础智能体中挑选最合适的组合来组成 Agent 团队。

规则：
1. 输出必须是 JSON 数组，每个元素包含 agent_id 和 role 字段
2. team 中应包含概念智能体（负责"是什么"）和动作智能体（负责"怎么做"）
3. 按执行先后顺序排列
4. 概念智能体在前（定义目标/数据/上下文），动作智能体在后（执行/分析/生成）
5. team_size 控制在 4-6 个
6. 只选确实相关的，不要硬凑

可用智能体列表："""

# 构建 agent 目录字符串
agent_index = "\n".join(
    f"  {a['id']} ({a['type']}) {a['name']}: {a['description']}"
    for a in AGENTS
)
SYSTEM_PROMPT += "\n" + agent_index


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/generate-team":
            self._handle_generate_team()
        elif self.path == "/api/execute-pipeline":
            self._handle_execute_pipeline()
        else:
            self.send_error(404)

    def _handle_generate_team(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        user_input = body.get("input", "").strip()
        if not user_input:
            self._json(400, {"error": "input 不能为空"})
            return

        try:
            payload = json.dumps({
                "model": API_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"用户需求: {user_input}\n\n请只返回 JSON（不要 markdown 包裹），格式: {{\"team\": [{{\"agent_id\": \"C01\", \"role\": \"负责什么\"}}]}}"},
                ],
                "temperature": 0.3,
            })
            # write payload to file to avoid shell encoding issues
            tmp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
            tmp.write(payload)
            tmp.close()
            # curl through SOCKS proxy (required in this network)
            result = subprocess.run([
                "curl.exe", "-s", "--socks5", "127.0.0.1:10808",
                "--connect-timeout", "15", "--max-time", "25",
                API_ENDPOINT,
                "-H", f"Authorization: Bearer {API_KEY}",
                "-H", "Content-Type: application/json",
                "-d", f"@{tmp.name}",
            ], capture_output=True, encoding="utf-8", timeout=30)
            os.unlink(tmp.name)
            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()
            if result.returncode != 0 or not stdout:
                raise RuntimeError(f"curl error (rc={result.returncode}): {stderr or 'empty response'}")
            body = json.loads(stdout)
            if "error" in body:
                raise RuntimeError(f"OpenAI API: {body['error']}")
            choice = body.get("choices", [{}])[0]
            msg = choice.get("message") if isinstance(choice.get("message"), dict) else {}
            raw_content = msg.get("content")
            content = (raw_content or "")
            if not isinstance(content, str):
                content = str(content) if content is not None else ""
            content = content.strip()
            if not content and isinstance(msg.get("reasoning_content"), str):
                content = msg["reasoning_content"].strip()
            if not content:
                raise RuntimeError("API 返回了空内容")
            # strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(content)
            team = data.get("team", data) if isinstance(data, dict) else data
            if isinstance(team, list):
                # 给每个 agent 补全信息
                result = []
                for item in team:
                    aid = item.get("agent_id", "")
                    agent = next((a for a in AGENTS if a["id"] == aid), None)
                    if agent:
                        result.append({
                            "agent_id": agent["id"],
                            "name": agent["name"],
                            "type": agent["type"],
                            "description": agent["description"],
                            "role": item.get("role", ""),
                        })
                self._json(200, {"team": result, "analysis": "基于 LLM 推理的 Agent 团队推荐"})
            else:
                self._json(200, {"team": [], "analysis": "无法解析推荐结果"})

                self._json(200, {"team": [], "analysis": "无法解析推荐结果"})

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[ERROR] {tb}", file=sys.stderr)
            self._json(500, {"error": str(e), "trace": tb.split(chr(10))[-8:]})

    def _handle_execute_pipeline(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        team = body.get("team", [])
        user_input = body.get("input", "")
        input_path = body.get("input_path", "")
        if not team:
            self._json(400, {"error": "team 不能为空"})
            return
        steps = execute_pipeline(team, user_input, input_path)
        self._json(200, {"steps": steps})

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        msg = "[AgentHub] %s %s %s" % args
        sys.stderr.buffer.write((msg + "\n").encode("utf-8"))


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    msg = "[AgentHub] Server started -> http://localhost:%d\n[AgentHub] API: POST http://localhost:%d/api/generate-team\n" % (PORT, PORT)
    sys.stderr.buffer.write(msg.encode("utf-8"))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
