# AgentHub ALP — 实施计划

## 阶段总览

| 阶段 | 时间 | 目标 | 交付物 |
|------|------|------|--------|
| P0 初赛 | 当前 | 方案设计 + 前端原型 | 架构文档、演示站 |
| P1 基础设施 | 第 1-2 周 | 部署 AgentTeams 全家桶 | 可访问的 Matrix 房间 + Manager |
| P2 Worker 开发 | 第 3-4 周 | 60 个 Worker 定义 + Skills 绑定 | Worker CRD YAML 文件 |
| P3 链路打通 | 第 5-6 周 | 前端 → AgentTeams → Skills | 端到端可调用的演示 |
| P4 数据与可观测 | 第 7-8 周 | PolarDB + RocketMQ + AgentLoop | 完整的多 Agent 协同系统 |
| P5 优化与提交 | 第 9-10 周 | 性能调优 + 文档完善 | 最终提交版本 |

---

## P0 — 初赛 (已完成)

### 交付物

| 交付物 | 说明 | 状态 |
|--------|------|------|
| 方案设计文档 | `design/architecture.md` | ✅ |
| 实施计划文档 | `roadmap.md` | ✅ |
| 前端演示站 | `https://agenthub.we-aigo.cn` | ✅ 可在线访问 |
| 智能体定义 | AgentHub/ 60 个智能体元数据 | ✅ |

### 前端演示站功能清单

- [x] 60 个 ALP 智能体键盘（概念层 30 + 动作层 30）
- [x] 语音输入识别 (Web Speech API)
- [x] 文本输入 + 键盘模式切换
- [x] 多智能体自动匹配（关键词 + 语义规则）
- [x] 8 步执行流水线可视化
- [x] 智能体贡献展示面板
- [x] 多领域输出（故事、图像描述、分析报告、课件等）
- [x] 层切换过滤（概念层/动作层/系统层）
- [x] 顶栏功能按钮（布局说明、主题、设置、帮助）

---

## P1 — 基础设施部署 (第 1-2 周)

### 1.1 服务器准备

| 选项 | 规格 | 用途 | 预估费用 |
|------|------|------|---------|
| 阿里云 ECS | 4 核 8GB + 100GB 云盘 | AgentTeams + PolarDB | ~300 元/月 |
| PolarDB | 2 核 4GB (按量付费) | 向量存储 + 关系数据 | ~100 元/月 |
| RocketMQ | 按量付费 | 事件总线 | ~50 元/月 |
| 域名 SSL | 已有 | agenthub.we-aigo.cn | 已付费 |

### 1.2 安装 AgentTeams

```bash
# 服务器初始化
apt install docker.io docker-compose -y

# 安装 AgentTeams
bash <(curl -sSL https://raw.githubusercontent.com/agentscope-ai/AgentTeams/main/install/agentteams-install.sh)
```

配置项：
- LLM Provider: `openai-compat`
- API Key: DeepSeek API Key（已有）
- Base URL: `https://api.deepseek.com/v1`
- Model: `deepseek-chat`

### 1.3 验证清单

- [ ] `http://<服务器IP>:18088` 打开 Element Web
- [ ] Manager 自动打招呼
- [ ] Worker 能在 Matrix 房间内回复
- [ ] 域名 `agenthub.we-aigo.cn` 解析到 ECS
- [ ] Higress Gateway 配置 TLS

---

## P2 — Worker 开发 (第 3-4 周)

### 2.1 Worker 清单

编写 60 个 Worker 的声明式定义：

**概念层 C01-C30（30 个 Worker）**

```yaml
apiVersion: agentteams.io/v1
kind: Worker
metadata:
  name: worker-{id}      # e.g. c02-goal
  labels:
    alp-layer: concept
    alp-id: "{id}"       # e.g. C02
spec:
  runtime: openclaw
  displayName: "{name}"
  description: "{description}"
  skills:
    - name: "{skill-name}"
      source: nacos
```

**动作层 A01-A30（30 个 Worker）**

同上结构，`alp-layer: action`，运行时可选 `openclaw` 或 `hermes`。

### 2.2 Skills 注册 (Nacos)

在 Nacos 中注册核心 Skills：

| Skill | 绑定 Worker | 功能 |
|-------|------------|------|
| `data-query@v1` | C09 data | 查询 PolarDB 结构化数据 |
| `knowledge-retrieval@v1` | C08 knowledge | RAG 向量检索 |
| `goal-definition@v1` | C02 goal | 目标定义与 KPI 解析 |
| `task-decomposition@v1` | C03 task | 任务拆解与优先级分配 |
| `statistical-analysis@v1` | A04 analyze | 统计分析/趋势检测 |
| `report-generator@v1` | A09 generate | 报告生成/格式化输出 |
| `data-validator@v1` | A10 verify | 数据校验/质量检查 |
| `context-extraction@v1` | C19 context | 上下文提取与管理 |
| `plan-generator@v1` | C24 plan | 执行计划 DAG 生成 |
| `time-series-forecast@v1` | A08 predict | 时序预测分析 |

### 2.3 Worker 测试

```bash
# 逐个创建 Worker
agt create worker -f workers/c02-goal.yaml
agt create worker -f workers/c09-data.yaml
agt create worker -f workers/a04-analyze.yaml

# 在 Matrix 房间中测试
@c09-data "查询 2024 年销售数据"
@a04-analyze "分析销售趋势"
```

---

## P3 — 链路打通 (第 5-6 周)

### 3.1 Cloudflare Functions 改造

当前模拟执行的 API 改造为对接 AgentTeams Manager：

```
改造前: CF Function → DeepSeek API (模拟执行)
改造后: CF Function → Matrix Client → AgentTeams Manager → Worker 集群
```

### 3.2 前端接入 Matrix

```javascript
// 前端通过 matrix-js-sdk 连接 Matrix 房间
import sdk from 'matrix-js-sdk';

const client = sdk.createClient({
  baseUrl: "https://agenthub.we-aigo.cn/matrix",
  accessToken: "..."
});

// 监听房间事件
client.on("Room.timeline", (event) => {
  const content = event.getContent();
  if (content.format === "org.agentteams.alp") {
    updateUI(content.formatted_body);
  }
});
```

### 3.3 链路验证

```
用户输入 "分析学生英语成绩"
  → CF Function POST /api/execute
    → Manager 拆解任务
      → C19 获取上下文
      → C09 查询成绩 (PolarDB)
      → A04 分析分布 (Skills)
      → A09 生成报告 (Skills)
  → 状态实时推送到前端
  → 人类在 Element Web 中观察
```

---

## P4 — 数据与可观测 (第 7-8 周)

### 4.1 PolarDB 集成

```sql
-- 任务表
CREATE TABLE alp_tasks (
  id UUID PRIMARY KEY,
  user_input TEXT,
  team JSONB, dag JSONB,
  status VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 执行记录
CREATE TABLE alp_execution_logs (
  id UUID PRIMARY KEY,
  task_id UUID REFERENCES alp_tasks(id),
  agent_id VARCHAR(10),
  input_context JSONB, output_result JSONB,
  tokens_used INT, latency_ms INT,
  status VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 向量记忆 (pgvector)
CREATE TABLE alp_memories (
  id UUID PRIMARY KEY,
  agent_id VARCHAR(10), content TEXT,
  embedding vector(1536),
  memory_type VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_memories_embedding
  ON alp_memories USING ivfflat (embedding vector_cosine_ops);
```

### 4.2 RocketMQ 事件主题

```yaml
topics:
  - name: "alp-task-event"
    queueNum: 8
  - name: "alp-step-event"
    queueNum: 8
  - name: "alp-human-intervention"
    queueNum: 4
```

### 4.3 AgentLoop 接入

```yaml
observability:
  traces:
    - endpoint: "http://agentloop:4318/v1/traces"
      exportIntervalMs: 1000
  metrics:
    - name: "alp.step.duration"    type: histogram
    - name: "alp.task.token.usage" type: counter
    - name: "alp.worker.error.rate" type: gauge
```

---

## P5 — 优化与提交 (第 9-10 周)

### 5.1 性能优化

- Worker 冷启动优化（预拉取 Skills 镜像）
- DAG 执行并行度调优
- Matrix 房间消息压缩
- PolarDB 查询性能优化（索引 + 连接池）

### 5.2 文档完善

- [ ] 补充 UnifiedModel 完整数据模型定义
- [ ] 编写 Skills SDK 接口规范
- [ ] 补充安全审计与权限控制文档
- [ ] 编写性能测试报告

### 5.3 最终提交

- [ ] 前端演示站可访问 (`agenthub.we-aigo.cn`)
- [ ] 架构设计文档定稿
- [ ] 部署运维手册
- [ ] 演示视频 / 录屏

---

## 关键依赖

| 依赖 | 获取方式 | 备注 |
|------|---------|------|
| ECS 服务器 | 阿里云 | 4 核 8GB 起 |
| PolarDB | 阿里云 RDS | pgvector 插件 |
| RocketMQ | 阿里云 MQ / 自建 | 4.0+ |
| Nacos | AgentTeams 自带 | — |
| DeepSeek API Key | 已有 | 所有 LLM 调用 |
| 域名证书 | 已有 | `agenthub.we-aigo.cn` |
| 云 Skills | skills.aliyun.com | 按需注册 |
