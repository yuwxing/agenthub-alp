import agents from '../../data/agents.json';

const API_ENDPOINT = 'https://api.deepseek.com/v1/chat/completions';
const API_MODEL = 'deepseek-chat';

const agentIndex = agents.map((a: any) =>
  `  ${a.id} (${a.type}) ${a.name}: ${a.description}`
).join('\n');

const SYSTEM_PROMPT = `你是 AgentHub OS 的智能体编排引擎。
你的任务是根据用户的需求描述，从以下 60 个基础智能体中挑选最合适的组合来组成 Agent 团队。

规则：
1. 输出必须是 JSON，格式: {"team": [{"agent_id": "C01", "role": "负责什么"}]}
2. team 中应包含概念智能体（负责"是什么"）和动作智能体（负责"怎么做"）
3. 按执行先后顺序排列
4. 概念智能体在前（定义目标/数据/上下文），动作智能体在后（执行/分析/生成）
5. team_size 控制在 4-6 个
6. 只选确实相关的，不要硬凑

可用智能体列表：
${agentIndex}`;

export async function onRequest(context: any) {
  const { request } = context;

  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    });
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }

  try {
    const body = await request.json();
    const userInput = (body.input || '').trim();
    if (!userInput) {
      return new Response(JSON.stringify({ error: 'input 不能为空' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    const apiKey = context.env.DEEPSEEK_API_KEY || '';
    if (!apiKey) {
      return new Response(JSON.stringify({ error: '服务端未配置 API Key' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    const payload = {
      model: API_MODEL,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: `用户需求: ${userInput}\n\n请只返回 JSON，格式: {"team": [{"agent_id": "C01", "role": "负责什么"}]}` },
      ],
      temperature: 0.3,
    };

    const resp = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await resp.json();
    if (data.error) {
      throw new Error(`API error: ${JSON.stringify(data.error)}`);
    }

    const choice = data.choices?.[0];
    let content = choice?.message?.content || choice?.message?.reasoning_content || '';
    content = content.trim();
    if (content.startsWith('```')) {
      content = content.split('\n').slice(1).join('\n').replace(/```[\s\S]*$/, '').trim();
    }

    let parsed = JSON.parse(content);
    const team = parsed.team || (Array.isArray(parsed) ? parsed : []);

    const enriched = team.map((item: any) => {
      const aid = item.agent_id || '';
      const agent = agents.find((a: any) => a.id === aid);
      return agent ? {
        agent_id: agent.id,
        name: agent.name,
        type: agent.type,
        description: agent.description,
        role: item.role || '',
      } : null;
    }).filter(Boolean);

    return new Response(JSON.stringify({
      team: enriched,
      analysis: '基于 LLM 推理的 Agent 团队推荐',
    }), {
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }
}
