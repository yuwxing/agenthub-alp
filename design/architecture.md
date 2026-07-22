# AgentHub ALP — 智能体语言键盘 方案设计

## 1. 项目概述

AgentHub ALP（Agent Language Protocol）定义了一套 60 个基础智能体的原语系统，覆盖**概念层（C01-C30）：描述世界的名词**和**动作层（A01-A30）：执行操作的行为动词**。用户通过语音或文本输入自然语言需求，系统自动匹配相关智能体组成多智能体团队，在 **AgentTeams** 框架下协同完成任务。

### 1.1 核心创新

- **ALP 原语系统**：60 个标准化智能体原语，将人类自然语言需求映射为结构化多智能体协作流程
- **QWERTY 键盘隐喻**：以物理键盘布局映射智能体组织方式，降低理解和操作门槛
- **端到端可视化**：从语音输入→智能体匹配→团队组建→任务执行→结果输出的全流程可视化

### 1.2 比赛要求映射

| 比赛要求 | 本方案实现 | 状态 |
|---------|-----------|------|
| AgentTeams（必须） | 60 个 Worker CRD 映射 60 个 ALP 智能体 | 待部署 |
| 云 Skills（推荐） | Worker 按需绑定 Skills，通过 Nacos 注册发现 | 待注册 |
| Nacos（推荐） | Skills 注册中心、Agent 配置管理 | 待部署 |
| Higress（推荐） | AI 网关统一入口，模型路由与凭据管理 | 待部署 |
| PolarDB（推荐） | 向量+关系存储，支持记忆与 RAG | 待集成 |
| UnifiedModel（推荐） | 统一数据建模（Agent、Task、Memory、Log） | 已定义 |
| RocketMQ（推荐） | 事件驱动与异步任务解耦 | 待集成 |
| AgentLoop（推荐） | Agent 推理轨迹与可观测性 | 待接入 |

---

## 2. 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                    用户层 (Frontend)                       │
│  agenthub.we-aigo.cn (Cloudflare Pages)                   │
│  ┌──────────┐ ┌──────────────────┐ ┌──────────────────┐  │
│  │ 智能体键盘  │ │ AI Command Core  │ │ 右侧面板          │  │
│  │ (60键原语) │ │ (语音/文本/分析)   │ │ (状态/结果/日志)  │  │
│  └────┬─────┘ └────────┬─────────┘ └────────┬─────────┘  │
└───────┼────────────────┼─────────────────────┼────────────┘
        │                │                     │
        ▼                ▼                     ▼
┌──────────────────────────────────────────────────────────┐
│            网关层 (Cloudflare Functions)                   │
│  POST /api/agents   → 智能体元数据查询                     │
│  POST /api/parse    → 自然语言→ALP指令翻译                  │
│  POST /api/execute  → 转发给 AgentTeams Manager             │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│               协同层 (AgentTeams + Higress)                │
│                                                           │
│  ┌──────────────────────────────────────┐                │
│  │  Higress AI Gateway                   │                │
│  │  ─ 模型路由 (DeepSeek/Qwen)           │                │
│  │  ─ MCP Server 代理                    │                │
│  │  ─ 凭据管理 (Worker 不可见真实 Key)    │                │
│  │  ─ Nacos Skills 注册与发现             │                │
│  └────────────────┬─────────────────────┘                │
│                   │                                       │
│  ┌────────────────▼─────────────────────┐                │
│  │  AgentTeams Controller                │                │
│  │  ─ Worker CRD / Team CRD / Human CRD  │                │
│  │  ─ 声明式资源管理                      │                │
│  │  ─ Matrix 协议通信 (Tuwunel)           │                │
│  └────────────────┬─────────────────────┘                │
│                   │                                       │
│     ┌─────────────┼─────────────┐                         │
│     ▼             ▼             ▼                         │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐                      │
│ │Manager  │ │Worker A │ │Worker B │ ...                   │
│ │(调度与   │ │(概念层   │ │(动作层   │                      │
│ │ 拆解)    │ │ C01~C30)│ │ A01~A30)│                      │
│ └─────────┘ └─────────┘ └─────────┘                      │
└────────────────────────┬─────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
     ┌──────────┐ ┌──────────┐ ┌──────────┐
     │ 云 Skills │ │ PolarDB  │ │ RocketMQ │
     │ - 数据查询 │ │ - 向量记忆 │ │ - 事件总线 │
     │ - 统计分析 │ │ - 任务日志 │ │ - 异步通知 │
     │ - 报告生成 │ │ - RAG     │ │ - 状态广播 │
     └──────────┘ └──────────┘ └──────────┘
           │
           ▼
     ┌──────────┐
     │AgentLoop │
     │ - 轨迹追踪 │
     │ - 性能监控 │
     │ - 成本分析 │
     └──────────┘
```

### 2.1 前端层 (Cloudflare Pages)

当前已部署在 `agenthub.we-aigo.cn`，包含：

- **智能体键盘**：60 个按键按 QWERTY 布局排列，每个按键对应一个 ALP 原语（概念层蓝色、动作层绿色、系统层琥珀色）
- **AI Command Core**：语音识别（Web Speech API）+ 文本输入，将用户需求发送到后端
- **多智能体匹配引擎**：基于关键词和语义规则，从 60 个智能体中匹配最相关的 12 个组成团队
- **执行流程面板**：展示 8 步流水线（Understand→Intent→Goal→Analyze→Plan→Execute→Evaluate→Result）
- **结果展示区**：根据输入自动识别领域（故事创作、图像生成、数据分析、教学课件等）并展示对应结果

### 2.2 网关层 (Cloudflare Functions)

提供三个核心 API：

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/agents` | GET | 返回 60 个智能体的元数据（名称、描述、ID、类型） |
| `/api/parse` | POST | 将用户自然语言解析为 ALP 指令序列（待对接 AgentTeams） |
| `/api/execute` | POST | 向 AgentTeams Manager 提交执行请求（待对接 AgentTeams） |

### 2.3 协同层 (AgentTeams + Higress)

使用 **AgentTeams** 框架作为多智能体协同平台：

- **Manager Agent**：接收用户需求，拆解为子任务，按 DAG 调度 Worker
- **Worker Agents**：60 个 Worker 分别对应 60 个 ALP 原语，通过声明式 YAML 定义
- **Matrix 房间通信**：所有 Agent 在 Matrix 房间内实时通信，人类可随时加入观察/干预
- **Higress AI Gateway**：统一模型路由、凭据安全管理、MCP Server 代理
- **Nacos**：Skills 注册中心，Worker 按需发现和调用

---

## 3. ALP 智能体原语系统

### 3.1 设计理念

ALP 受编程语言类型系统和物理键盘布局启发：概念层类似"数据类型"定义问题域，动作层类似"函数"定义操作域，组合起来可以表达任意复杂任务。

### 3.2 概念层 (C01-C30) — 描述世界

| 编号 | 名称 | 描述 |
|------|------|------|
| C01 | agent | 智能体自身的描述与元数据 |
| C02 | goal | 目标定义与达成标准 |
| C03 | task | 可执行的工作单元 |
| C04 | object | 被处理的实体 |
| C05 | state | 实体或系统的当前状态 |
| C06 | skill | 智能体具备的能力 |
| C07 | memory | 短期与长期记忆管理 |
| C08 | knowledge | 领域知识与规则库 |
| C09 | data | 结构化与非结构化数据 |
| C10 | tool | 可调用的外部工具 |
| C11-C30 | ... | 资源、用户、环境、时间、事件、规则等 |

### 3.3 动作层 (A01-A30) — 执行操作

| 编号 | 名称 | 描述 |
|------|------|------|
| A01 | create | 创建新实体 |
| A02 | read | 读取已有数据 |
| A03 | search | 搜索与发现 |
| A04 | analyze | 分析与洞察 |
| A05 | plan | 制定执行计划 |
| A06 | execute | 执行任务 |
| A07 | compare | 比较与差异分析 |
| A08 | predict | 预测未来趋势 |
| A09 | generate | 生成内容 |
| A10 | verify | 验证与校验 |
| A11-A30 | ... | 学习、更新、存储、检索、通信等 |

---

## 4. 多智能体协作流程

### 4.1 端到端执行流程

```
用户输入："帮我分析广东中考英语趋势并生成课件"
    │
    ▼
┌─────────────┐
│ 1. 意图理解  │  Manager 用 LLM 分析用户意图
│    (Manager) │  → 识别领域：教育分析 + 课件生成
└──────┬──────┘  → 选择概念层：[C02, C03, C08, C09, C19, C20, C24]
       │           → 选择动作层：[A04, A05, A06, A08, A09, A10]
       ▼
┌─────────────┐
│ 2. 概念定义  │  C02(目标) → 定义"分析中考英语趋势"的目标与KPI
│ (Concept    │  C19(上下文) → 提取"广东中考英语"的领域上下文
│  Workers)   │  C09(数据) → 获取历年考试数据
       │      │  C24(计划) → 制定分析→生成课件的执行计划
       ▼
┌─────────────┐
│ 3. 动作执行  │  A04(分析) → 统计题型分布、难度系数、趋势变化
│  (Action    │  A08(预测) → 预测2026年题型变化方向
│   Workers)  │  A09(生成) → 生成包含趋势图表的课件内容
       │      │  A10(验证) → 检查内容准确性和完整性
       ▼
┌─────────────┐
│ 4. 结果输出  │  课件 + 分析报告 → 推送到前端展示
│   (Output)   │  存储到 PolarDB → 纳入记忆库
└─────────────┘
```

### 4.2 Manager 任务拆解算法

```
function decomposeTask(userInput):
    // 1. 意图分析
    intent = LLM.analyze(userInput)
    conceptIds = selectConcepts(intent)   // 如 [C02, C19, C09, C24]
    actionIds  = selectActions(intent)    // 如 [A04, A08, A09, A10]

    // 2. 生成执行 DAG
    dag = buildDAG(conceptIds, actionIds)

    // 3. 通过 Matrix 创建团队房间
    room = matrix.createRoom("task-{uuid}")
    for agent in dag:
        room.invite(agent)
    room.invite(humanUser)  // 人类全程可见

    // 4. 按 DAG 顺序执行
    for step in dag:
        context = room.getContext()
        result  = step.agent.execute(context, step.skills)
        room.postMessage(result)
```

### 4.3 Worker 声明式定义 (YAML)

```yaml
apiVersion: agentteams.io/v1
kind: Worker
metadata:
  name: analyze-worker
  labels:
    alp-layer: action
    alp-id: A04
spec:
  runtime: openclaw
  displayName: "分析智能体 (A04)"
  description: "执行数据分析与洞察"
  skills:
    - name: "statistical-analysis"  source: nacos
    - name: "trend-detection"       source: aliyun
  mcpServers:
    - name: "compute"
      endpoint: "mcp://compute-engine:8000"
```

### 4.4 团队编排 (Team CRD)

```yaml
apiVersion: agentteams.io/v1
kind: Team
metadata:
  name: analysis-team
spec:
  manager: manager-agent
  workers:
    - name: "context-worker"    # C19
    - name: "goal-worker"       # C02
    - name: "data-worker"       # C09
    - name: "analyze-worker"    # A04
    - name: "predict-worker"    # A08
    - name: "generate-worker"   # A09
  coordination:
    order: sequential
    contextPassing: matrix
  observability:
    agentLoop: true
    roomVisibility: all
```

---

## 5. 数据模型 (UnifiedModel)

```yaml
models:
  - name: "Agent"
    fields:
      - id: string        # C01~C30 / A01~A30
      - name: string      # 智能体名称
      - type: enum        # concept / action
      - description: text # 职责描述
      - skills: array     # 绑定的 Skills 列表
      - mcpServers: array # MCP 服务器端点

  - name: "Task"
    fields:
      - id: uuid
      - userInput: text
      - team: json        # 选中的智能体列表
      - dag: json         # 执行计划 DAG
      - status: enum      # pending/running/done/failed
      - createdAt: datetime
      - completedAt: datetime

  - name: "ExecutionLog"
    fields:
      - taskId: uuid
      - agentId: string
      - stepIndex: int
      - inputContext: json
      - outputResult: json
      - tokensUsed: int
      - latencyMs: int
      - status: enum

  - name: "Memory"
    fields:
      - agentId: string
      - content: text
      - embedding: vector(1536)
      - memoryType: enum  # short-term / long-term
      - createdAt: datetime
```

---

## 6. 部署架构

### 6.1 前端 (已部署)

| 组件 | 技术 | 地址 |
|------|------|------|
| 静态站点 | Cloudflare Pages | `https://agenthub.we-aigo.cn` |
| API 网关 | Cloudflare Functions | `/api/*` |
| 语音识别 | Web Speech API | 浏览器原生 |

### 6.2 协同层 (待部署)

| 组件 | 配置 | 用途 |
|------|------|------|
| 服务器 | 4 核 8GB + 100GB 云盘 | 运行 AgentTeams + 数据库 |
| AgentTeams | Helm chart | 多智能体协同框架 |
| Higress | Ingress Gateway | AI 网关 + 模型路由 |
| Nacos | AgentTeams 内置 | Skills 注册中心 |

### 6.3 数据层 (待集成)

| 组件 | 用途 |
|------|------|
| PolarDB for PostgreSQL | 关系存储 + pgvector 向量索引 |
| RocketMQ | 事件总线 + 异步消息 |
| MinIO | 共享文件系统 (大体积数据交换) |

### 6.4 网络架构

```
用户 → Cloudflare CDN → Cloudflare Pages
                           │
                           ▼
                    Higress AI Gateway (K8s)
                     ├─ /api/* → AgentTeams
                     ├─ /matrix/* → Tuwunel
                     └─ /element/* → Element Web
```

---

## 7. 当前进度

### 已完成
- [x] 60 个 ALP 智能体定义 (AgentHub/)
- [x] 智能体键盘前端 UI (Cloudflare Pages)
- [x] 语音输入 + 文本输入
- [x] 多智能体匹配引擎
- [x] 执行结果展示面板
- [x] 自定义域名 `agenthub.we-aigo.cn`

### 待完成
- [ ] 部署 AgentTeams 基础设施
- [ ] 编写 60 个 Worker 声明式定义
- [ ] 注册 Skills 到 Nacos
- [ ] 对接 AgentTeams Manager（前端 → Manager 全链路）
- [ ] 集成 PolarDB + RocketMQ + AgentLoop
