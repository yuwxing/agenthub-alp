import agents from '../../data/agents.json';

const API_ENDPOINT = 'https://api.deepseek.com/v1/chat/completions';
const API_MODEL = 'deepseek-chat';

const agentIndex = agents.map((a: any) =>
  `  ${a.id} ${a.name}: ${a.description}`
).join('\n');

const SYSTEM_PROMPT = `你是 AgentHub OS 的 30 概念 x 5 动作智能体执行引擎。
用户会描述需求并指定团队，请模拟每个智能体的执行结果。

规则：
1. 输出必须是 JSON，格式: {"steps": [{"agent_id": "C01", "result": {"思考": "...", "输出": "..."}}]}
2. 每个智能体要有"思考"(推理过程)和"输出"(执行产物)
3. 概念智能体（C01-C30）负责分析/定义/推理，动作智能体（A01-A30）负责执行/生成/操作
4. 结果应串联：后一个智能体应参考前一个的输出
5. 用中文输出
6. 只输出 JSON，不要 markdown 包裹

可用智能体：
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
    const team: any[] = body.team || [];
    const userInput = (body.input || '').trim();

    if (!userInput || !team.length) {
      return new Response(JSON.stringify({ error: 'input 和 team 不能为空' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    const apiKey = context.env.DEEPSEEK_API_KEY || '';
    if (!apiKey) {
      // Fallback: generate simple offline results without API
      const steps = team.map((agent, idx) => ({
        agent_id: agent.agent_id || '',
        name: agent.name || '',
        role: agent.role || '',
        status: 'done',
        result: {
          阶段: `步骤${idx + 1}`,
          智能体: agent.name || agent.agent_id,
          思考: `${agent.name} 正在处理：${userInput}`,
          输出: `${agent.name} 已完成"${agent.role}"阶段的分析与执行`,
        },
      }));
      return new Response(JSON.stringify({ steps, mode: 'offline' }), {
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    const teamDesc = team.map((a, i) =>
      `步骤${i + 1}: ${a.agent_id} (${a.name}) - ${a.role || '通用处理'}`
    ).join('\n');

    const payload = {
      model: API_MODEL,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: `用户需求: ${userInput}\n\n执行团队:\n${teamDesc}\n\n请模拟每个智能体的执行结果并返回 JSON。` },
      ],
      temperature: 0.5,
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
    let steps = parsed.steps || (Array.isArray(parsed) ? parsed : []);

    // Enrich with agent metadata
    const agentMap = new Map(agents.map((a: any) => [a.id, a]));
    steps = steps.map((s: any) => {
      const agent = agentMap.get(s.agent_id || '');
      return {
        agent_id: s.agent_id || '',
        name: agent?.name || '',
        role: '',
        status: 'done',
        result: s.result || { 输出: s.output || '执行完成' },
      };
    });

    return new Response(JSON.stringify({ steps, mode: 'online' }), {
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }
}
