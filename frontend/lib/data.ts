// MN-004: ISR data fetch helpers.
// Both functions fetch from raw.githubusercontent.com with revalidate: 300 (5 min).
// On any error (non-2xx, network, parse failure) they return null/[] — never throw.

import type { SignalsResponse, NewsItem } from './types';

const RAW_BASE =
  'https://raw.githubusercontent.com/mshmwr/market-news/main/docs';

const REVALIDATE = 300; // signals update daily; news every 30 min — 5 min cache is sufficient

export async function fetchSignals(): Promise<SignalsResponse | null> {
  try {
    const res = await fetch(`${RAW_BASE}/signals.json`, {
      next: { revalidate: REVALIDATE },
    });
    if (!res.ok) return null;
    const json = (await res.json()) as unknown;
    if (
      typeof json !== 'object' ||
      json === null ||
      !('signals' in json) ||
      !Array.isArray((json as { signals: unknown }).signals)
    ) {
      return null;
    }
    return json as SignalsResponse;
  } catch {
    return null;
  }
}

// MN-009: latest digest HTML, fetched as raw text. Returns null on any
// failure (non-2xx / network) — caller renders an empty placeholder.
export async function fetchDigest(): Promise<string | null> {
  try {
    const res = await fetch(`${RAW_BASE}/digest-latest.html`, {
      next: { revalidate: REVALIDATE },
    });
    if (!res.ok) return null;
    const text = await res.text();
    return text || null;
  } catch {
    return null;
  }
}

// Returns null on fetch error (non-2xx / network / parse failure) to allow
// callers to distinguish "fetch failed" from "genuinely empty news array".
export async function fetchNews(): Promise<NewsItem[] | null> {
  try {
    const res = await fetch(`${RAW_BASE}/news.json`, {
      next: { revalidate: REVALIDATE },
    });
    if (!res.ok) return null;
    const json = (await res.json()) as unknown;
    if (!Array.isArray(json)) return null;
    return json as NewsItem[];
  } catch {
    return null;
  }
}
