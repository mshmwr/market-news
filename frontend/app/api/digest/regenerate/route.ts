import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const REPO = 'mshmwr/market-news';
const WORKFLOW = 'daily-digest.yml';

export async function POST() {
  const token = process.env.GITHUB_DISPATCH_TOKEN;
  if (!token) {
    return NextResponse.json(
      { ok: false, error: 'GITHUB_DISPATCH_TOKEN not configured on server' },
      { status: 500 },
    );
  }

  const res = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: 'POST',
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${token}`,
        'X-GitHub-Api-Version': '2022-11-28',
      },
      body: JSON.stringify({ ref: 'main' }),
    },
  );

  if (res.status !== 204) {
    const text = await res.text();
    return NextResponse.json(
      { ok: false, error: `GitHub API ${res.status}: ${text}` },
      { status: 502 },
    );
  }

  return NextResponse.json({ ok: true });
}
