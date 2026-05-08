// MN-004: Home page — Server Component with ISR revalidate:300.
// Fetches signals.json and news.json from raw.githubusercontent.com.
// Passes plain JSON data to PageClient (no Date objects — fully serializable).

import { fetchSignals, fetchNews } from '@/lib/data';
import PageClient from '@/components/layout/PageClient';

export const revalidate = 300; // ISR: 5-minute revalidation window

export default async function HomePage() {
  const [signalsData, news] = await Promise.all([fetchSignals(), fetchNews()]);

  const signals = signalsData?.signals ?? [];
  const generatedAt = signalsData?.generated_at ?? null;

  // newsError: news fetch genuinely failed (empty array returned by fetchNews on error)
  // We can't distinguish "no articles" from "fetch failed" purely from length,
  // so we track it via a separate boolean passed down.
  // For now, treat empty news as a potential error only if signals loaded successfully.
  const newsError = news.length === 0;

  return (
    <PageClient
      signals={signals}
      news={news}
      generatedAt={generatedAt}
      newsError={newsError}
    />
  );
}
