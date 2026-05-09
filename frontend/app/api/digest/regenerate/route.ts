import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const REPO = 'mshmwr/market-news';
const WORKFLOW = 'daily-digest.yml';
const COOLDOWN_MS = 12 * 60 * 60 * 1000;

interface Run {
  status: string;
  conclusion: string | null;
  created_at: string;
}

async function ghFetch(path: string, token: string, init?: RequestInit) {
  return fetch(`https://api.github.com${path}`, {
    ...init,
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28',
      ...(init?.headers || {}),
    },
  });
}

export async function POST() {
  const token = process.env.GITHUB_DISPATCH_TOKEN;
  if (!token) {
    return NextResponse.json(
      { ok: false, error: 'GITHUB_DISPATCH_TOKEN not configured on server' },
      { status: 500 },
    );
  }

  const listRes = await ghFetch(
    `/repos/${REPO}/actions/workflows/${WORKFLOW}/runs?per_page=20`,
    token,
  );
  if (!listRes.ok) {
    return NextResponse.json(
      { ok: false, error: `list runs failed: ${listRes.status}` },
      { status: 502 },
    );
  }
  const { workflow_runs }: { workflow_runs: Run[] } = await listRes.json();

  const active = workflow_runs.find(
    (r) => r.status === 'in_progress' || r.status === 'queued',
  );
  if (active) {
    return NextResponse.json(
      { ok: false, code: 'running', error: '已有正在執行的任務 / A run is already in progress' },
      { status: 409 },
    );
  }

  const lastSuccess = workflow_runs.find(
    (r) => r.status === 'completed' && r.conclusion === 'success',
  );
  if (lastSuccess) {
    const elapsed = Date.now() - new Date(lastSuccess.created_at).getTime();
    if (elapsed < COOLDOWN_MS) {
      const nextAvailable = new Date(
        new Date(lastSuccess.created_at).getTime() + COOLDOWN_MS,
      ).toISOString();
      return NextResponse.json(
        {
          ok: false,
          code: 'cooldown',
          error: '距離上次成功觸發未滿 12 小時 / Less than 12h since last successful run',
          nextAvailable,
        },
        { status: 429 },
      );
    }
  }

  const dispatchRes = await ghFetch(
    `/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    token,
    {
      method: 'POST',
      body: JSON.stringify({ ref: 'main' }),
    },
  );
  if (dispatchRes.status !== 204) {
    const text = await dispatchRes.text();
    return NextResponse.json(
      { ok: false, error: `dispatch failed: ${dispatchRes.status} ${text}` },
      { status: 502 },
    );
  }

  return NextResponse.json({ ok: true });
}
