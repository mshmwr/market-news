const ALLOWED_ORIGIN = 'https://mshmwr.github.io';

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders(req) });
    }
    if (req.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    const origin = req.headers.get('Origin') || '';
    if (!origin.startsWith(ALLOWED_ORIGIN) && !origin.includes('translate.goog')) {
      return new Response('Forbidden', { status: 403 });
    }

    const res = await fetch(
      'https://api.github.com/repos/mshmwr/market-news/actions/workflows/update-news.yml/dispatches',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.GH_PAT}`,
          'Accept': 'application/vnd.github+json',
          'Content-Type': 'application/json',
          'User-Agent': 'market-news-worker',
        },
        body: JSON.stringify({ ref: 'main' }),
      }
    );

    return new Response(null, {
      status: res.ok ? 204 : res.status,
      headers: corsHeaders(req),
    });
  },
};

function corsHeaders(req) {
  const origin = req.headers.get('Origin') || ALLOWED_ORIGIN;
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}
