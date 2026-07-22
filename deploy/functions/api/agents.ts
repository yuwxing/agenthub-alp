import agents from '../../data/agents.json';

export async function onRequest(context) {
  return new Response(JSON.stringify(agents), {
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
  });
}
