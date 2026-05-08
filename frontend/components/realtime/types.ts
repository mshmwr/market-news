/**
 * Real-time price data structure.
 *
 * @remarks
 * Stub reserved for MN-004 WebSocket or polling feed.
 * No consumer exists in MN-003. No live network connection is established.
 *
 * MN-004 implementation notes:
 * - `ticker` matches the format used in docs/signals.json (e.g. "NVDA", "^GSPC", "BTC-USD")
 * - `timestamp` is ISO 8601 UTC
 * - `price` is in USD
 */
export interface RealtimePrice {
  ticker: string;
  price: number;
  timestamp: string;
}
