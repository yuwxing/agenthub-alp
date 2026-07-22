/**
 * AgentHub ALP — MCP Server 示例 (TypeScript/Node.js)
 * 
 * 作为 Skills 与 PolarDB 之间的桥梁，通过 MCP 协议暴露 ALP 智能体操作能力。
 * 运行方式:
 *   npx tsx alp-mcp-server.ts --port 8000
 * 
 * 依赖:
 *   npm install @modelcontextprotocol/sdk polar-connector pg
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Pool } from "pg";

// PolarDB 连接池
let pool: Pool;

function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      connectionString: process.env.POLARDB_DSN,
      max: 10,
      idleTimeoutMillis: 30000,
    });
  }
  return pool;
}

// ── ALP Skills 工具定义 ──

const TOOLS = [
  {
    name: "data-query",
    description: "查询 PolarDB 结构化数据（绑定 C09 data Worker）",
    inputSchema: {
      type: "object",
      properties: {
        sql: { type: "string", description: "SQL 查询语句" },
        params: { type: "object", description: "查询参数" },
        limit: { type: "integer", default: 100 },
      },
      required: ["sql"],
    },
  },
  {
    name: "vector-store",
    description: "将内容向量化存储（绑定 C07 memory Worker）",
    inputSchema: {
      type: "object",
      properties: {
        content: { type: "string" },
        metadata: { type: "object" },
        memoryType: {
          type: "string",
          enum: ["short-term", "long-term"],
        },
      },
      required: ["content"],
    },
  },
  {
    name: "similarity-search",
    description: "向量相似性搜索（绑定 C07 memory Worker）",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        topK: { type: "integer", default: 5 },
        threshold: { type: "number", default: 0.7 },
      },
      required: ["query"],
    },
  },
  {
    name: "knowledge-retrieval",
    description: "RAG 知识检索（绑定 C08 knowledge Worker）",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        topK: { type: "integer", default: 3 },
      },
      required: ["query"],
    },
  },
  {
    name: "statistical-analysis",
    description: "数据统计分析（绑定 A04 analyze Worker）",
    inputSchema: {
      type: "object",
      properties: {
        data: { type: "array" },
        analysisType: {
          type: "string",
          enum: ["descriptive", "trend", "correlation", "distribution"],
        },
      },
      required: ["data", "analysisType"],
    },
  },
  {
    name: "report-generator",
    description: "生成结构化报告（绑定 A09 generate Worker）",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string" },
        sections: { type: "array" },
        format: {
          type: "string",
          enum: ["markdown", "html", "json"],
          default: "markdown",
        },
      },
      required: ["title", "sections"],
    },
  },
];

const server = new Server(
  {
    name: "alp-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// ── 处理函数 ──

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS,
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "data-query":
      return await handleDataQuery(args);
    case "vector-store":
      return handleVectorStore(args);
    case "similarity-search":
      return handleSimilaritySearch(args);
    case "knowledge-retrieval":
      return handleKnowledgeRetrieval(args);
    case "statistical-analysis":
      return handleStatisticalAnalysis(args);
    case "report-generator":
      return handleReportGenerator(args);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

async function handleDataQuery(args: any) {
  const sql = args.sql;
  const limit = args.limit || 100;

  try {
    const client = await getPool().connect();
    const result = await client.query(sql);
    client.release();

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            columns: result.fields.map((f: any) => f.name),
            rows: result.rows.slice(0, limit),
            rowCount: result.rowCount,
          }),
        },
      ],
    };
  } catch (err: any) {
    return {
      content: [{ type: "text", text: `查询失败: ${err.message}` }],
      isError: true,
    };
  }
}

function handleVectorStore(args: any) {
  // 调用 embedding API 并写入 PolarDB pgvector
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({
          memoryId: crypto.randomUUID(),
          status: "stored",
        }),
      },
    ],
  };
}

function handleSimilaritySearch(args: any) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({
          results: [],
          totalCount: 0,
        }),
      },
    ],
  };
}

function handleKnowledgeRetrieval(args: any) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({
          chunks: [
            {
              content: `与 '${args.query || ""}' 相关的知识片段`,
              source: "knowledge-base",
              relevance: 0.95,
            },
          ],
        }),
      },
    ],
  };
}

function handleStatisticalAnalysis(args: any) {
  const data = args.data || [];
  const analysisType = args.analysisType || "descriptive";
  const values = data.map((d: any) => (typeof d === "number" ? d : d.value || 0));

  const n = values.length;
  const mean = values.reduce((a: number, b: number) => a + b, 0) / n;
  const sorted = [...values].sort((a, b) => a - b);

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({
          statistics: {
            mean,
            median: sorted[Math.floor(n / 2)],
            min: sorted[0],
            max: sorted[n - 1],
            count: n,
          },
          insights: [`${n} 条数据 ${analysisType} 分析完成`],
        }),
      },
    ],
  };
}

function handleReportGenerator(args: any) {
  const title = args.title;
  const sections = args.sections || [];

  let report = `# ${title}\n\n`;
  for (const section of sections) {
    if (typeof section === "string") {
      report += `## ${section}\n\n内容区域\n\n`;
    } else {
      report += `## ${section.heading || ""}\n\n${section.content || ""}\n\n`;
    }
  }

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({ report, format: args.format || "markdown", length: report.length }),
      },
    ],
  };
}

// ── 启动 ──

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ALP MCP Server running on stdio");
}

main().catch(console.error);
