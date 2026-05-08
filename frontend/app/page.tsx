// Server Component — no data fetching, no env vars.
// MN-003: placeholder shell. Signal display added in MN-004.
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold tracking-tight text-white">
        Market News
      </h1>
      <p className="mt-4 text-lg text-gray-400">
        Signal display coming soon — under development (MN-004).
      </p>
      <p className="mt-2 text-sm text-gray-600">
        Current production:{" "}
        <a
          href="https://mshmwr.github.io/market-news/"
          className="underline hover:text-gray-400"
          target="_blank"
          rel="noopener noreferrer"
        >
          GitHub Pages
        </a>
      </p>
    </main>
  );
}
