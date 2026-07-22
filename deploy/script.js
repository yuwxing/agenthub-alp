/* AgentHub ALP — 智能体语言键盘 V1.0 */

/* ── Agent Data ── */
let allAgents = [];
let agentMap = {};
let currentTeam = [];
let isProcessing = false;
let execStartTime = 0;

/* ── Keyboard Layout (QWERTY, 6 rows, 3 layers) ── */
const LAYERS = { concept: 'blue', action: 'green', system: 'orange' };

const KEY_ROWS = [
  // Row 0: Esc + Fn row (orange / system + misc)
  [
    { label:'Esc', lyr:'system', w:1.2 },
    { label:'F1', lyr:'system', w:1 },
    { label:'F2', lyr:'system', w:1 },
    { label:'F3', lyr:'system', w:1 },
    { label:'F4', lyr:'system', w:1 },
    { label:'F5', lyr:'system', w:1 },
    { label:'F6', lyr:'system', w:1 },
    { label:'F7', lyr:'system', w:1 },
    { label:'F8', lyr:'system', w:1 },
    { label:'F9', lyr:'system', w:1 },
    { label:'F10', lyr:'system', w:1 },
    { label:'F11', lyr:'system', w:1 },
    { label:'F12', lyr:'system', w:1 },
  ],
  // Row 1: Number row (blue — concept C01-C10)
  [
    { label:'~', lyr:'blank', w:1 },
    { label:'1', lyr:'concept', agent:'C01', w:1 },
    { label:'2', lyr:'concept', agent:'C02', w:1 },
    { label:'3', lyr:'concept', agent:'C03', w:1 },
    { label:'4', lyr:'concept', agent:'C04', w:1 },
    { label:'5', lyr:'concept', agent:'C05', w:1 },
    { label:'6', lyr:'concept', agent:'C06', w:1 },
    { label:'7', lyr:'concept', agent:'C07', w:1 },
    { label:'8', lyr:'concept', agent:'C08', w:1 },
    { label:'9', lyr:'concept', agent:'C09', w:1 },
    { label:'0', lyr:'concept', agent:'C10', w:1 },
    { label:'-', lyr:'blank', w:1 },
    { label:'=', lyr:'blank', w:1 },
    { label:'←', lyr:'blank', w:1.6 },
  ],
  // Row 2: Q row (blue — concept C11-C20)
  [
    { label:'⇥', lyr:'blank', w:1.4 },
    { label:'Q', lyr:'concept', agent:'C11', w:1 },
    { label:'W', lyr:'concept', agent:'C12', w:1 },
    { label:'E', lyr:'concept', agent:'C13', w:1 },
    { label:'R', lyr:'concept', agent:'C14', w:1 },
    { label:'T', lyr:'concept', agent:'C15', w:1 },
    { label:'Y', lyr:'concept', agent:'C16', w:1 },
    { label:'U', lyr:'concept', agent:'C17', w:1 },
    { label:'I', lyr:'concept', agent:'C18', w:1 },
    { label:'O', lyr:'concept', agent:'C19', w:1 },
    { label:'P', lyr:'concept', agent:'C20', w:1 },
    { label:'[', lyr:'blank', w:1 },
    { label:']', lyr:'blank', w:1 },
    { label:'\\', lyr:'blank', w:1.4 },
  ],
  // Row 3: A row (blue — concept C21-C30)
  [
    { label:'⇪', lyr:'blank', w:1.6 },
    { label:'A', lyr:'concept', agent:'C21', w:1 },
    { label:'S', lyr:'concept', agent:'C22', w:1 },
    { label:'D', lyr:'concept', agent:'C23', w:1 },
    { label:'F', lyr:'concept', agent:'C24', w:1 },
    { label:'G', lyr:'concept', agent:'C25', w:1 },
    { label:'H', lyr:'concept', agent:'C26', w:1 },
    { label:'J', lyr:'concept', agent:'C27', w:1 },
    { label:'K', lyr:'concept', agent:'C28', w:1 },
    { label:'L', lyr:'concept', agent:'C29', w:1 },
    { label:';', lyr:'concept', agent:'C30', w:1 },
    { label:"'", lyr:'blank', w:1 },
    { label:'↵', lyr:'blank', w:2 },
  ],
  // Row 4: Z row (green — action A01-A12)
  [
    { label:'⇧', lyr:'blank', w:1.6 },
    { label:'Z', lyr:'action', agent:'A01', w:1 },
    { label:'X', lyr:'action', agent:'A02', w:1 },
    { label:'C', lyr:'action', agent:'A03', w:1 },
    { label:'V', lyr:'action', agent:'A04', w:1 },
    { label:'B', lyr:'action', agent:'A05', w:1 },
    { label:'N', lyr:'action', agent:'A06', w:1 },
    { label:'M', lyr:'action', agent:'A07', w:1 },
    { label:',', lyr:'action', agent:'A08', w:1 },
    { label:'.', lyr:'action', agent:'A09', w:1 },
    { label:'/', lyr:'action', agent:'A10', w:1 },
    { label:'⇧', lyr:'blank', w:1.8 },
  ],
  // Row 5: Bottom row (green — action A11-A20)
  [
    { label:'^', lyr:'action', agent:'A11', w:1.2 },
    { label:'⊞', lyr:'action', agent:'A12', w:1.2 },
    { label:'⌥', lyr:'action', agent:'A13', w:1.2 },
    { label:'␣', lyr:'action', agent:'A14', w:3, spaceLabel:'SPACE' },
    { label:'⌥', lyr:'action', agent:'A17', w:1.2 },
    { label:'⊞', lyr:'action', agent:'A18', w:1.2 },
    { label:'☰', lyr:'action', agent:'A19', w:1.2 },
    { label:'^', lyr:'action', agent:'A20', w:1.2 },
  ],
  // Row 6: System / Fn row (orange — action A21-A30 + exec)
  [
    { label:'Fn1', lyr:'system', agent:'A21', w:1 },
    { label:'Fn2', lyr:'system', agent:'A22', w:1 },
    { label:'Fn3', lyr:'system', agent:'A23', w:1 },
    { label:'Fn4', lyr:'system', agent:'A24', w:1 },
    { label:'Fn5', lyr:'system', agent:'A25', w:1 },
    { label:'Fn6', lyr:'system', agent:'A26', w:1 },
    { label:'Fn7', lyr:'system', agent:'A27', w:1 },
    { label:'Fn8', lyr:'system', agent:'A28', w:1 },
    { label:'Fn9', lyr:'system', agent:'A29', w:1 },
    { label:'Fn10', lyr:'system', agent:'A30', w:1 },
    { label:'🚀 执行', lyr:'system', type:'exec', w:2.5 },
    { label:'✕ 清空', lyr:'system', type:'clear', w:1.5 },
  ],
];

/* ── Init ── */
async function loadAgents() {
  try {
    const res = await fetch('data/agents.json');
    allAgents = await res.json();
    allAgents.forEach(a => agentMap[a.id] = a);
  } catch (e) {
    consoleLog('⚠️ 无法加载 agents.json: ' + e.message);
  }
  renderKeyboard();
  renderAgentStatus();
  document.getElementById('sysAgentCount').textContent = allAgents.length;
}

/* ── Render Keyboard ── */
function renderKeyboard() {
  const container = document.getElementById('keyboardContainer');
  container.innerHTML = KEY_ROWS.map((row, ri) => {
    const keys = row.map(k => renderKey(k, ri));
    return `<div class="kb-row">${keys.join('')}</div>`;
  }).join('');
}

function renderKey(k) {
  if (k.type === 'exec') {
    return `<div class="kb-exec-btn" onclick="executeCurrentTeam()">🚀 执 行</div>`;
  }
  if (k.type === 'clear') {
    return `<div class="kb-key system w15" onclick="clearAll()" title="清空所有">
      <span class="kk-agent" style="font-size:11px">✕ 清空</span>
    </div>`;
  }

  const agent = k.agent ? agentMap[k.agent] : null;
  const lyr = k.lyr || 'blank';
  const cls = lyr === 'blank' ? 'kb-key blank' : `kb-key ${lyr}`;
  const wCls = k.w ? ` w${k.w}`.replace('.','_') : ' w1';
  const title = agent ? `${agent.name} — ${agent.description}` : k.label || '';

  let content = '';
  if (lyr === 'blank') {
    content = `<span style="font-size:9px;color:var(--text3)">${k.label}</span>`;
  } else if (agent) {
    const id = k.agent;
    const displayName = agent.name;
    content = `
      <span class="kk-agent">${id}</span>
      <span class="kk-label">${displayName}</span>
      <div class="kb-key-detail">
        <div class="kkd-name">${displayName}</div>
        <div class="kkd-desc">${agent.description || ''}</div>
      </div>`;
  } else {
    content = `<span style="font-size:10px;color:var(--text3)">${k.label}</span>`;
  }

  const clickHandler = agent ? `onclick="triggerAgent('${k.agent}')"` : '';

  return `<div class="${cls}${wCls}" ${clickHandler} title="${title}">${content}</div>`;
}

/* ── Trigger Agent ── */
async function triggerAgent(agentId) {
  const agent = agentMap[agentId];
  if (!agent) return;

  // Visual press
  document.querySelectorAll('.kb-key').forEach(el => {
    if (el.textContent.includes(agentId)) el.classList.add('pressed');
  });
  setTimeout(() => document.querySelectorAll('.kb-key.pressed').forEach(el => el.classList.remove('pressed')), 150);

  consoleLog(`⌨️ 触发智能体: ${agentId} ${agent.name}`);

  const input = document.getElementById('taskInput').value.trim() || `${agent.name} 处理`;

  const team = [{ agent_id: agentId, name: agent.name, role: agent.name }];
  currentTeam = team;
  await executePipeline(team, input);
}

/* ── AI Command Core ── */
function setInput(text) {
  document.getElementById('taskInput').value = text;
  document.getElementById('taskInput').focus();
  document.getElementById('sampleHints').style.display = 'none';
}

function listenCommand() {
  const mic = document.getElementById('micButton');
  mic.textContent = '⏳';
  mic.style.background = 'linear-gradient(135deg,#f02020,#f06020)';

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = 'zh-CN';
    rec.interimResults = false;
    rec.onresult = (e) => {
      const text = e.results[0][0].transcript;
      document.getElementById('taskInput').value = text;
      consoleLog(`🎤 语音识别: ${text}`);
      processInput(text);
      resetMic();
    };
    rec.onerror = () => resetMic();
    rec.start();
  } else {
    // Fallback: simulate
    setTimeout(() => {
      document.getElementById('taskInput').value = '分析学生英语成绩数据，生成个性化学习计划';
      consoleLog('🎤 语音模拟: 分析学生英语成绩数据，生成个性化学习计划');
      processInput(document.getElementById('taskInput').value);
      resetMic();
    }, 1000);
  }

  function resetMic() {
    mic.textContent = '🎤';
    mic.style.background = '';
  }
}

async function processInput(text) {
  if (!text.trim() || isProcessing) return;
  isProcessing = true;
  document.getElementById('taskInput').disabled = true;

  // Show analysis progress
  showAnalysisProgress(1);

  try {
    const res = await fetch('/api/generate-team', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: text })
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || `HTTP ${res.status}`);
    }

    showAnalysisProgress(4);
    const data = await res.json();
    const team = data.team || [];

    if (team.length === 0) {
      consoleLog('⚠️ LLM 未推荐任何智能体');
      isProcessing = false;
      document.getElementById('taskInput').disabled = false;
      showAnalysisProgress(0);
      return;
    }

    currentTeam = team;
    consoleLog(`🧠 组建团队 (${team.length} 智能体): ${team.map(t => t.agent_id).join(' → ')}`);

    // Update analysis panel
    document.getElementById('agentCountBadge').innerHTML = `已识别 <strong>${team.length}</strong> 个相关智能体`;

    // Show team in result panel
    showResultPending(team);

    // Highlight matching keys
    team.forEach(t => triggerKeyGlow(t.agent_id));

    showAnalysisProgress(6);

    // Auto-execute after brief delay
    setTimeout(async () => {
      await executePipeline(team, text);
      isProcessing = false;
      document.getElementById('taskInput').disabled = false;
      showAnalysisProgress(8);
    }, 500);

  } catch (err) {
    consoleLog(`❌ 分析失败: ${err.message}`);
    showResultError(err.message);
    isProcessing = false;
    document.getElementById('taskInput').disabled = false;
    showAnalysisProgress(0);
  }
}

function showAnalysisProgress(step) {
  const steps = document.querySelectorAll('.cc-step');
  steps.forEach((s, i) => {
    s.classList.remove('active', 'done');
    const stepNum = Math.floor(i / 2); // Account for arrow separators
    if (stepNum < step) s.classList.add('done');
    else if (stepNum === step) s.classList.add('active');
  });
}

function triggerKeyGlow(agentId) {
  // Find and highlight the key matching this agent
  document.querySelectorAll('.kb-key').forEach(el => {
    if (el.textContent.includes(agentId)) {
      el.style.boxShadow = '0 0 20px rgba(74,218,106,0.4)';
      el.style.borderColor = 'var(--green-glow)';
      setTimeout(() => {
        el.style.boxShadow = '';
        el.style.borderColor = '';
      }, 3000);
    }
  });
}

/* ── Execute Pipeline ── */
async function executePipeline(team, input) {
  if (!team || team.length === 0) {
    consoleLog('⚠️ 没有智能体可执行');
    return;
  }

  execStartTime = performance.now();
  updateRuntime();

  // Show flow status
  updateFlowStatus(5);
  consoleLog(`⚡ 开始执行管道 (${team.length} 步)`);

  currentTeam = team;
  showResultPending(team);

  try {
    const res = await fetch('/api/execute-pipeline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team, input })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    const steps = data.steps || [];
    consoleLog(`✅ 执行完成 (${steps.length} 步)`);
    updateFlowStatus(7);
    showResultDone(steps, team);

    steps.forEach((s, i) => {
      if (s.result) {
        const summary = summarizeStepResult(s.result);
        consoleLog(`  [${s.agent_id}] ${summary}`);
      }
    });

    const last = steps[steps.length - 1];
    if (last && last.result && last.result.report) {
      consoleLog('📄 最终报告已生成');
    }

  } catch (err) {
    consoleLog(`❌ 执行管道失败: ${err.message}`);
    updateFlowStatus(0);
    showResultError(err.message);
  }

  updateRuntime();
  updateFlowStatus(8);

  // Update agent status
  renderAgentStatus();
}

function updateFlowStatus(step) {
  const items = document.querySelectorAll('.sb-flow-item');
  items.forEach((el, i) => {
    el.classList.remove('active', 'done');
    if (i < step) el.classList.add('done');
    else if (i === step) el.classList.add('active');
  });
}

function summarizeStepResult(r) {
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

/* ── Execution Results Panel ── */
function showResultPending(team) {
  const body = document.getElementById('resultBody');
  if (!body) return;
  body.innerHTML = team.map((a, i) =>
    `<div class="sb-result-item" id="res-${i}">
      <div class="sbr-agent">⏳ ${a.agent_id || a.name}</div>
      <div class="sbr-summary">等待执行…</div>
    </div>`
  ).join('');
}

function showResultDone(steps, team) {
  const body = document.getElementById('resultBody');
  if (!body) return;
  body.innerHTML = steps.map((s, i) => {
    const summary = s.result ? summarizeStepResult(s.result) : '✓ 完成';
    const name = team[i]?.name || s.agent_id || `步骤 ${i+1}`;
    return `<div class="sb-result-item done">
      <div class="sbr-agent">✅ ${s.agent_id} ${name}</div>
      <div class="sbr-summary">${summary}</div>
    </div>`;
  }).join('');
}

function showResultError(msg) {
  const body = document.getElementById('resultBody');
  if (!body) return;
  body.innerHTML = `<div class="sb-result-item error">
    <div class="sbr-agent">❌ 执行失败</div>
    <div class="sbr-summary">${msg}</div>
  </div>`;
}

function updateRuntime() {
  const el = document.getElementById('sysRuntime');
  if (!el) return;
  const elapsed = ((performance.now() - execStartTime) / 1000).toFixed(1);
  el.textContent = elapsed + 's';
  if (isProcessing) {
    setTimeout(updateRuntime, 500);
  }
}

/* ── Execute current team (from exec button) ── */
async function executeCurrentTeam() {
  let team = currentTeam;
  const input = document.getElementById('taskInput').value.trim();

  if (!team || team.length === 0) {
    // Try to build team from input
    if (input) {
      return processInput(input);
    }
    consoleLog('⚠️ 没有智能体团队，请先输入需求');
    return;
  }

  await executePipeline(team, input || '执行任务');
}

/* ── Clear ── */
function clearAll() {
  currentTeam = [];
  document.getElementById('taskInput').value = '';
  document.getElementById('agentCountBadge').innerHTML = '已识别 <strong>0</strong> 个相关智能体';
  showAnalysisProgress(0);
  updateFlowStatus(0);
  document.getElementById('sysRuntime').textContent = '0.0s';
  document.getElementById('resultBody').innerHTML = '<div class="sb-result-item"><span class="sbr-empty">等待执行…</span></div>';
  consoleLog('已清空所有');

  document.querySelectorAll('.kb-key').forEach(el => {
    el.style.boxShadow = '';
    el.style.borderColor = '';
  });
}

/* ── Sidebar: Agent Status ── */
function renderAgentStatus() {
  const list = document.getElementById('agentStatusList');
  if (!list) return;

  // Sort: concepts first, then actions
  const sorted = [...allAgents].sort((a, b) => a.id.localeCompare(b.id));
  // Use the first characters of the name for emoji
  const statuses = ['active', 'ready', 'avail', 'idle'];

  list.innerHTML = sorted.map(a => {
    const dot = a.type === 'concept' ? 'ready' : 'avail';
    return `<div class="sb-agent-item" onclick="triggerAgent('${a.id}')" title="${a.description || ''}">
      <span class="sba-dot ${dot}"></span>
      <span class="sba-id">${a.id}</span>
      <span class="sba-name">${a.name}</span>
    </div>`;
  }).join('');
}

/* ── Header / Nav actions ── */
function switchLayer(layer) {
  const label = document.querySelector('.kb-layout-tag');
  if (label) label.textContent = `QWERTY — 当前层: ${layer === 'concept' ? '概念层 (蓝)' : layer === 'action' ? '动作层 (绿)' : '系统层 (橙)'}`;
  consoleLog(`🔄 切换至 ${layer} 层`);
}

function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  sb.style.display = sb.style.display === 'none' ? '' : 'none';
}

function openMarket() {
  consoleLog('🏪 智能体市场 (即将推出)');
}

/* ── Console ── */
function consoleLog(msg) {
  const body = document.getElementById('consoleBody');
  if (!body) return;
  const line = document.createElement('div');
  line.textContent = msg;
  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}

/* ── Task Input: Enter to trigger ── */
document.addEventListener('DOMContentLoaded', () => {
  loadAgents();

  const input = document.getElementById('taskInput');
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      processInput(input.value);
    }
  });
  input.addEventListener('focus', () => {
    document.getElementById('sampleHints').style.display = 'flex';
  });
  input.addEventListener('blur', () => {
    setTimeout(() => { document.getElementById('sampleHints').style.display = 'none'; }, 200);
  });

  // Physical keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey) {
      const key = e.key.toUpperCase();
      // Map physical keys to agents
      const physMap = {
        '1':'C01','2':'C02','3':'C03','4':'C04','5':'C05',
        '6':'C06','7':'C07','8':'C08','9':'C09','0':'C10',
        'Q':'C11','W':'C12','E':'C13','R':'C14','T':'C15',
        'Y':'C16','U':'C17','I':'C18','O':'C19','P':'C20',
        'A':'C21','S':'C22','D':'C23','F':'C24','G':'C25',
        'H':'C26','J':'C27','K':'C28','L':'C29',';':'C30',
        'Z':'A01','X':'A02','C':'A03','V':'A04','B':'A05',
        'N':'A06','M':'A07',',':'A08','.':'A09','/':'A10',
      };
      const aid = physMap[key];
      if (aid) {
        e.preventDefault();
        triggerAgent(aid);
      }
      if (key === 'ENTER') {
        e.preventDefault();
        executeCurrentTeam();
      }
    }
  });

  consoleLog('AgentHub ALP 智能体语言键盘 V1.0 已启动');
  consoleLog('⌨️ 点击键盘按键或使用 Ctrl+Shift+字母 触发智能体');
  consoleLog('🎤 支持语音输入 (点击麦克风按钮)');
});
