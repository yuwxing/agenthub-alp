let allAgents = [];
let currentType = 'concept';
let selectedId = null;

async function loadAgents() {
  const res = await fetch('data/agents.json');
  allAgents = await res.json();
  document.getElementById('agentCount').textContent = allAgents.length;
  renderGrid();
}

function switchTab(type) {
  currentType = type;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.type === type));
  renderGrid();
}

function filterAgents() {
  renderGrid();
}

function renderGrid() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  const filtered = allAgents.filter(a => {
    if (a.type !== currentType) return false;
    if (!q) return true;
    return a.id.toLowerCase().includes(q) || a.name.toLowerCase().includes(q) || (a.description || '').toLowerCase().includes(q);
  });
  const grid = document.getElementById('agentGrid');
  grid.innerHTML = filtered.map(a => `
    <div class="agent-item ${selectedId === a.id ? 'active' : ''}"
         onclick="selectAgent('${a.id}')"
         data-id="${a.id}">
      <div class="ai-avatar">${emoji(a.name)}</div>
      <div class="ai-info">
        <div class="ai-name">${a.name}</div>
        <div class="ai-id">${a.id}</div>
      </div>
      <span class="ai-type ${a.type}">${a.type === 'concept' ? '概' : '动'}</span>
    </div>
  `).join('');
}

function emoji(name) {
  const map = {
    agent:'🤖', goal:'🎯', task:'📋', object:'📦', state:'⚡', skill:'🛠️',
    memory:'🧠', knowledge:'📚', data:'💾', tool:'🔧', resource:'📡', user:'👤',
    environment:'🌍', time:'⏰', event:'🔔', rule:'📏', result:'✅', feedback:'🔄',
    context:'🌐', intent:'💡', attribute:'🏷️', relation:'🔗', process:'⚙️',
    plan:'🗺️', constraint:'🔒', priority:'📊', confidence:'📈',
    capability:'🎯', identity:'🪪', objective:'📐',
    create:'✨', read:'📖', search:'🔍', analyze:'📊', execute:'▶️',
    compare:'⚖️', predict:'🔮', generate:'🪄', verify:'✔️', learn:'📖',
    update:'🔄', store:'💾', retrieve:'🔎', communicate:'📨',
    understand:'🧐', extract:'🗂️', transform:'🔄', classify:'📑',
    match:'🔗', simulate:'🎮', optimize:'⚡', decide:'🤔',
    negotiate:'🤝', delegate:'📤', sync:'🔄', monitor:'📡',
    recover:'🚑', evolve:'🧬', allocate:'📊'
  };
  return map[name.toLowerCase()] || '⚪';
}

function selectAgent(id) {
  selectedId = id;
  const a = allAgents.find(x => x.id === id);
  if (!a) return;
  renderGrid();
  document.getElementById('detailTitle').textContent = `ℹ️ ${a.name}`;
  document.getElementById('detailContent').innerHTML = `
    <div class="dr-header">
      <div class="dr-avatar">${emoji(a.name)}</div>
      <div>
        <h3>${a.name}</h3>
        <div class="dr-id">${a.id} · ${a.type === 'concept' ? '概念' : '动作'}</div>
      </div>
    </div>
    <div class="dr-section">
      <h4>📖 用途</h4>
      <div class="dr-desc">${a.description}</div>
    </div>
    <div class="dr-section">
      <h4>🏷️ 标签</h4>
      <div class="dr-tags">
        <span class="dr-tag">${a.type === 'concept' ? '概念原语' : '动作原语'}</span>
        <span class="dr-tag">基础智能体</span>
      </div>
    </div>
    <div class="dr-section">
      <h4>🔗 可关联</h4>
      <div class="dr-tags" id="drRelated"></div>
    </div>
  `;
  const related = allAgents.filter(x => x.id !== id && x.type !== a.type).slice(0, 5);
  document.getElementById('drRelated').innerHTML = related.map(x =>
    `<span class="dr-tag" style="cursor:pointer" onclick="selectAgent('${x.id}')">${x.name}</span>`
  ).join('');
  consoleLog(`选中智能体: ${a.id} ${a.name}`);
}

/* ── Brain ── */
async function generateTeam() {
  const input = document.getElementById('taskInput').value.trim();
  if (!input) {
    document.getElementById('teamBody').innerHTML = '<div class="bt-empty">请先输入需求描述</div>';
    return;
  }
  document.getElementById('teamHint').textContent = '🤔 正在分析需求…';
  document.getElementById('teamBody').innerHTML = '<div class="bt-empty">⏳ 调用 LLM 推理中…</div>';
  consoleLog('🧠 正在调用 LLM 分析需求并组建 Agent 团队…');

  try {
    const res = await fetch('/api/generate-team', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    const team = data.team || [];
    if (team.length === 0) {
      document.getElementById('teamBody').innerHTML = '<div class="bt-empty">LLM 未返回有效团队</div>';
      return;
    }

    document.getElementById('teamHint').textContent = `✨ LLM 推荐 ${team.length} 个智能体`;
    const body = document.getElementById('teamBody');
    body.innerHTML = '';
    team.forEach((a, i) => {
      if (i > 0) {
        const arrow = document.createElement('span');
        arrow.className = 'team-arrow';
        arrow.textContent = '→';
        body.appendChild(arrow);
      }
      const el = document.createElement('span');
      el.className = 'team-agent';
      el.title = a.role || a.description;
      el.innerHTML = `<span class="ta-avatar">${emoji(a.name)}</span> ${a.name}`;
      el.onclick = () => selectAgent(a.agent_id);
      body.appendChild(el);
    });

    consoleLog(`🧠 Agent 团队已组建 (LLM): ${team.map(t => t.agent_id).join(' → ')}`);
    consoleLog(`   ${data.analysis || ''}`);
    // 自动触发执行
    executePipeline(team, input);

  } catch (err) {
    document.getElementById('teamBody').innerHTML = `<div class="bt-empty">❌ 请求失败: ${err.message}</div>`;
    document.getElementById('teamHint').textContent = '推荐失败';
    consoleLog(`❌ LLM 调用失败: ${err.message}`);
  }
}

function pickRelated(list, input, count) {
  const keywords = input.toLowerCase().split(/[\s,，。、]+/);
  const scored = list.map(a => {
    let score = 0;
    const desc = (a.name + ' ' + (a.description || '')).toLowerCase();
    for (const kw of keywords) {
      if (desc.includes(kw)) score += 5;
      if (a.name.toLowerCase().includes(kw)) score += 10;
    }
    return { agent: a, score };
  });
  return scored.sort((a, b) => b.score - a.score).slice(0, count).map(s => s.agent);
}

async function executePipeline(team, input) {
  const body = document.getElementById('execBody');
  const status = document.getElementById('execStatus');
  body.innerHTML = '';
  status.textContent = '⏳ 执行中…';

  team.forEach((a, i) => {
    const step = document.createElement('div');
    step.className = 'exec-step';
    step.id = `exec-step-${i}`;
    step.innerHTML = `
      <span class="exec-dot pending"></span>
      <span class="exec-agent">${emoji(a.name)} ${a.agent_id}</span>
      <span class="exec-action">→ ${a.role || 'execute'}</span>
      <span class="exec-result">等待…</span>
    `;
    body.appendChild(step);
  });

  try {
    const res = await fetch('/api/execute-pipeline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team, input })
    });
    const data = await res.json();
    const steps = data.steps || [];

    steps.forEach((s, i) => {
      const el = document.getElementById(`exec-step-${i}`);
      if (!el) return;
      const dot = el.querySelector('.exec-dot');
      const result = el.querySelector('.exec-result');
      if (s.status === 'done') {
        dot.className = 'exec-dot done';
        const summary = summarizeResult(s.result);
        result.textContent = summary;
      } else if (s.status === 'error') {
        dot.className = 'exec-dot pending';
        result.textContent = '❌ ' + (s.result?.error || 'error');
      } else {
        dot.className = 'exec-dot pending';
        result.textContent = '⏭ skipped';
      }
    });

    status.textContent = '✅ 执行完成';
    consoleLog('✅ 执行管道已完成');

    // 显示最后一步的报告（如果有）
    const last = steps[steps.length - 1];
    if (last && last.result && last.result.report) {
      consoleLog('📄 最终报告已生成');
    }
  } catch (err) {
    status.textContent = '❌ 执行失败';
    consoleLog('❌ 执行失败: ' + err.message);
  }
}

function summarizeResult(r) {
  if (!r) return '-';
  if (r.error) return '❌ ' + r.error;
  if (r.report) return '📄 报告 (' + r.length + ' 字)';
  if (r.row_count !== undefined) return '📊 ' + r.row_count + ' 行';
  if (r.count !== undefined) return '📦 ' + r.count + ' 条';
  if (r.group_count !== undefined) return '📁 ' + r.group_count + ' 组';
  if (r.groups) return '📁 ' + Object.keys(r.groups).length + ' 组';
  const keys = Object.keys(r).filter(k => !['format','columns','sample'].includes(k));
  return keys.length > 0 ? '✓ ' + keys.slice(0, 3).join(', ') : '✓ done';
}

function clearBrain() {
  document.getElementById('taskInput').value = '';
  document.getElementById('teamBody').innerHTML = '<div class="bt-empty">输入上方需求，系统将自动组建最优智能体团队</div>';
  document.getElementById('execBody').innerHTML = '<div class="be-empty">等待执行…</div>';
  document.getElementById('execStatus').textContent = '就绪';
  document.getElementById('teamHint').textContent = '输入需求后自动推荐';
  consoleLog('已清空面板');
}

/* ── Console ── */
function switchConsole(el, tab) {
  document.querySelectorAll('.ctab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
}

function consoleLog(msg) {
  const body = document.getElementById('consoleBody');
  const line = document.createElement('div');
  line.className = 'console-log';
  line.textContent = msg;
  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}

loadAgents();
consoleLog('AgentHub OS v1.0 已启动');
