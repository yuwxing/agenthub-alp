-- AgentHub ALP — PolarDB for PostgreSQL Schema
-- Requires: pgvector extension

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

/* ── Agent 元数据 ── */
CREATE TABLE alp_agents (
  id VARCHAR(10) PRIMARY KEY,          -- C01, A01, ...
  name VARCHAR(50) NOT NULL,
  type VARCHAR(10) NOT NULL CHECK (type IN ('concept','action')),
  description TEXT,
  skills JSONB DEFAULT '[]',            -- 绑定的 Skills 列表
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agents_type ON alp_agents(type);

/* ── 任务表 ── */
CREATE TABLE alp_tasks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_input TEXT NOT NULL,
  team JSONB,                           -- Agent 团队 [{agent_id, name, role}]
  dag JSONB,                            -- 执行 DAG [{step, worker, dependsOn[]}]
  status VARCHAR(20) DEFAULT 'pending'
    CHECK (status IN ('pending','running','done','failed','cancelled')),
  analysis TEXT,                        -- LLM 分析结果
  error TEXT,                           -- 错误信息
  total_tokens INT DEFAULT 0,
  total_latency_ms INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

CREATE INDEX idx_tasks_status ON alp_tasks(status);
CREATE INDEX idx_tasks_created ON alp_tasks(created_at DESC);

/* ── 执行步骤记录 ── */
CREATE TABLE alp_execution_steps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  task_id UUID NOT NULL REFERENCES alp_tasks(id) ON DELETE CASCADE,
  agent_id VARCHAR(10) NOT NULL REFERENCES alp_agents(id),
  step_index INT NOT NULL,
  status VARCHAR(20) DEFAULT 'pending'
    CHECK (status IN ('pending','running','done','failed','skipped')),
  input_context JSONB,
  output_result JSONB,
  thinking TEXT,                         -- Agent 推理过程
  tokens_used INT DEFAULT 0,
  latency_ms INT DEFAULT 0,
  error TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

CREATE INDEX idx_steps_task ON alp_execution_steps(task_id);
CREATE INDEX idx_steps_agent ON alp_execution_steps(agent_id);

/* ── 记忆表 (向量存储) ── */
CREATE TABLE alp_memories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id VARCHAR(10) NOT NULL REFERENCES alp_agents(id),
  type VARCHAR(20) NOT NULL CHECK (type IN ('short-term','long-term','episodic')),
  content TEXT NOT NULL,
  embedding vector(1536),               -- DeepSeek embedding dimension
  metadata JSONB DEFAULT '{}',
  weight FLOAT DEFAULT 1.0,             -- 记忆权重 (用于遗忘机制)
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_accessed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memories_agent ON alp_memories(agent_id);
CREATE INDEX idx_memories_type ON alp_memories(type);
CREATE INDEX idx_memories_embedding ON alp_memories
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

/* ── 知识库 (RAG) ── */
CREATE TABLE alp_knowledge (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source VARCHAR(100),                  -- 来源 (文件/URL/用户输入)
  title TEXT,
  content TEXT NOT NULL,
  chunk_index INT,
  embedding vector(1536),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_knowledge_embedding ON alp_knowledge
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 200);

/* ── Skills 注册表 ── */
CREATE TABLE alp_skills (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) NOT NULL UNIQUE,
  version VARCHAR(20) NOT NULL,
  description TEXT,
  source VARCHAR(20) NOT NULL CHECK (source IN ('nacos','aliyun','custom','mcp')),
  endpoint VARCHAR(500),                -- MCP endpoint or API URL
  parameters JSONB DEFAULT '{}',         -- 入参定义
  outputs JSONB DEFAULT '{}',           -- 出参定义
  status VARCHAR(10) DEFAULT 'active' CHECK (status IN ('active','deprecated','disabled')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_skills_name ON alp_skills(name);

/* ── Agent-Skill 绑定 ── */
CREATE TABLE alp_agent_skills (
  agent_id VARCHAR(10) NOT NULL REFERENCES alp_agents(id),
  skill_id UUID NOT NULL REFERENCES alp_skills(id),
  priority INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (agent_id, skill_id)
);

/* ── 审计日志 ── */
CREATE TABLE alp_audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  task_id UUID REFERENCES alp_tasks(id),
  agent_id VARCHAR(10),
  action VARCHAR(50) NOT NULL,           -- task.created / step.started / etc
  detail JSONB,
  ip_address INET,
  created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE alp_audit_logs_2026q1 PARTITION OF alp_audit_logs
  FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE alp_audit_logs_2026q2 PARTITION OF alp_audit_logs
  FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE TABLE alp_audit_logs_2026q3 PARTITION OF alp_audit_logs
  FOR VALUES FROM ('2026-07-01') TO ('2026-10-01');
CREATE TABLE alp_audit_logs_2026q4 PARTITION OF alp_audit_logs
  FOR VALUES FROM ('2026-10-01') TO ('2027-01-01');

CREATE INDEX idx_audit_task ON alp_audit_logs(task_id);
CREATE INDEX idx_audit_created ON alp_audit_logs(created_at DESC);

/* ── 初始化 60 个智能体 ── */
INSERT INTO alp_agents (id, name, type, description) VALUES
-- 概念层 C01-C30
('C01','agent','concept','智能体自身的描述与元数据'),
('C02','goal','concept','目标定义与达成标准'),
('C03','task','concept','可执行的工作单元'),
('C04','object','concept','被处理的实体'),
('C05','state','concept','实体或系统的当前状态'),
('C06','skill','concept','智能体具备的能力'),
('C07','memory','concept','短期与长期记忆管理'),
('C08','knowledge','concept','领域知识与规则库'),
('C09','data','concept','结构化与非结构化数据'),
('C10','tool','concept','可调用的外部工具'),
('C11','resource','concept','可调用的能力与资产'),
('C12','user','concept','人类用户的画像与偏好'),
('C13','environment','concept','运行环境与上下文'),
('C14','time','concept','时间相关的调度与约束'),
('C15','event','concept','发生的事件与触发'),
('C16','rule','concept','业务规则与逻辑约束'),
('C17','result','concept','执行结果与产出'),
('C18','feedback','concept','反馈收集与闭环'),
('C19','context','concept','当前环境与任务背景'),
('C20','intent','concept','用户真正目的'),
('C21','attribute','concept','对象特征'),
('C22','relation','concept','对象之间连接'),
('C23','process','concept','连续任务链'),
('C24','plan','concept','达成目标的路径'),
('C25','constraint','concept','限制条件'),
('C26','priority','concept','决策排序'),
('C27','confidence','concept','结果可信程度'),
('C28','capability','concept','Agent拥有的可执行能力集合'),
('C29','identity','concept','智能体的唯一标识与人格边界'),
('C30','objective','concept','可衡量的目标结果'),
-- 动作层 A01-A30
('A01','create','action','创建新实体'),
('A02','read','action','读取已有数据'),
('A03','search','action','搜索与发现'),
('A04','analyze','action','分析与洞察'),
('A05','plan','action','制定执行计划'),
('A06','execute','action','执行任务'),
('A07','compare','action','比较与差异分析'),
('A08','predict','action','预测未来趋势'),
('A09','generate','action','生成内容'),
('A10','verify','action','验证与校验'),
('A11','learn','action','学习与适应'),
('A12','update','action','更新现有数据'),
('A13','store','action','存储数据'),
('A14','retrieve','action','检索已存信息'),
('A15','communicate','action','跨智能体通信'),
('A16','understand','action','解析输入'),
('A17','extract','action','从数据获取信息'),
('A18','transform','action','格式转换'),
('A19','classify','action','分组判断'),
('A20','match','action','找关联对象'),
('A21','simulate','action','预测场景'),
('A22','optimize','action','寻找最佳方案'),
('A23','decide','action','选择方案'),
('A24','negotiate','action','Agent之间协调'),
('A25','delegate','action','分配任务'),
('A26','sync','action','更新状态'),
('A27','monitor','action','持续观察'),
('A28','recover','action','异常处理'),
('A29','evolve','action','自我改进'),
('A30','allocate','action','分配资源、任务、计算能力');
