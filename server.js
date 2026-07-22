const http = require('http');
const fs = require('fs');
const path = require('path');
const mime = {
  '.html': 'text/html','.js':'application/javascript','.css':'text/css',
  '.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml',
  '.json':'application/json','.woff2':'font/woff2','.ico':'image/x-icon'
};
const ROOT = 'D:\\ACV-v1';

function loadAllAgents() {
  const agents = [];
  for (const dir of ['concept', 'action']) {
    const base = path.join(ROOT, 'AgentHub', dir);
    try {
      for (const entry of fs.readdirSync(base, { withFileTypes: true })) {
        if (!entry.isDirectory()) continue;
        const p = path.join(base, entry.name, 'agent.json');
        if (fs.existsSync(p)) {
          const data = JSON.parse(fs.readFileSync(p, 'utf8'));
          agents.push(data);
        }
      }
    } catch (e) { /* skip */ }
  }
  return agents;
}

const ALL_AGENTS = loadAllAgents();

http.createServer((req, res) => {
  // API: GET /api/agents
  if (req.url === '/api/agents') {
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    });
    res.end(JSON.stringify(ALL_AGENTS));
    return;
  }
  // Static file
  let fp = path.join(ROOT, req.url === '/' ? 'index.html' : req.url);
  let ext = path.extname(fp);
  fs.readFile(fp, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not Found'); return; }
    res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' });
    res.end(data);
  });
}).listen(3001, '127.0.0.1', () => console.log('Server running at http://127.0.0.1:3001'));
