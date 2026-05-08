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

  // newsError: null return from fetchNews means fetch/parse failure.
  // Empty array [] means server returned valid JSON with no articles (rare but valid).
  const newsError = news === null;
  const newsList = news ?? [];

  return (
    <PageClient
      signals={signals}
      news={newsList}
      generatedAt={generatedAt}
      newsError={newsError}
    />
  );
}
